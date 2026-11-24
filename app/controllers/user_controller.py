from flask import Blueprint, g
from sqlalchemy import or_

from ..extensions import db
from ..models import Asset, Finding, Incident, User
from ..models.constants import ROLES
from ..utils.audit import apply_changes, log_action
from ..utils.errors import APIError
from ..utils.query import (
    apply_sorting,
    get_choice_arg,
    get_object_or_404,
    get_search_term,
    like_pattern,
    paginate,
)
from ..utils.security import generate_api_key, hash_api_key, require_auth
from ..views import UserCreateSchema, UserOutputSchema, UserUpdateSchema, get_json_body, no_content, success

bp = Blueprint("users", __name__, url_prefix="/api/v1/users")

create_schema = UserCreateSchema()
update_schema = UserUpdateSchema()
output_schema = UserOutputSchema()

SORT_FIELDS = ("name", "email", "role", "created_at")


@bp.get("/me")
@require_auth()
def me():
    return success(output_schema.dump(g.current_user))


@bp.get("")
@require_auth("admin")
def list_users():
    stmt = db.select(User)
    term = get_search_term()
    if term:
        pattern = like_pattern(term)
        stmt = stmt.where(
            or_(User.name.ilike(pattern, escape="\\"), User.email.ilike(pattern, escape="\\"))
        )
    role = get_choice_arg("role", ROLES)
    if role:
        stmt = stmt.where(User.role == role)
    stmt = apply_sorting(stmt, User, SORT_FIELDS, default="name")
    items, meta = paginate(stmt)
    return success(output_schema.dump(items, many=True), meta=meta)


@bp.post("")
@require_auth("admin")
def create_user():
    data = create_schema.load(get_json_body())
    exists = db.session.execute(db.select(User).where(User.email == data["email"])).scalar_one_or_none()
    if exists:
        raise APIError(409, "Email sudah terdaftar.", details={"email": data["email"]})

    raw_key = generate_api_key()
    user = User(name=data["name"], email=data["email"], role=data["role"], api_key_hash=hash_api_key(raw_key))
    user.set_password(data["password"])
    db.session.add(user)
    db.session.flush()
    log_action("create", "user", user.id, {"email": user.email, "role": user.role})
    db.session.commit()

    body = output_schema.dump(user)
    body["api_key"] = raw_key  # hanya ditampilkan SEKALI saat dibuat
    return success(
        body,
        status=201,
        message="User dibuat. Simpan api_key ini, karena tidak akan ditampilkan lagi.",
        headers={"Location": f"/api/v1/users/{user.id}"},
    )


@bp.get("/<int:user_id>")
@require_auth("admin")
def get_user(user_id):
    return success(output_schema.dump(get_object_or_404(User, user_id, "User")))


@bp.patch("/<int:user_id>")
@require_auth("admin")
def update_user(user_id):
    user = get_object_or_404(User, user_id, "User")
    data = update_schema.load(get_json_body())

    if user.id == g.current_user.id and (data.get("role", "admin") != "admin" or data.get("is_active") is False):
        raise APIError(400, "Admin tidak bisa menurunkan role atau menonaktifkan akunnya sendiri.")

    password = data.pop("password", None)
    changes = apply_changes(user, data)
    if password:
        user.set_password(password)
        changes["password"] = "changed"
    if changes:
        log_action("update", "user", user.id, changes)
    db.session.commit()
    return success(output_schema.dump(user), message="User diperbarui.")


@bp.post("/<int:user_id>/rotate-key")
@require_auth("admin")
def rotate_api_key(user_id):
    """Ganti API key (misalnya kalau key lama bocor). Key lama langsung tidak berlaku."""
    user = get_object_or_404(User, user_id, "User")
    raw_key = generate_api_key()
    user.api_key_hash = hash_api_key(raw_key)
    log_action("update", "user", user.id, {"api_key": "rotated"})
    db.session.commit()
    return success({"id": user.id, "api_key": raw_key}, message="API key baru dibuat. Key lama sudah tidak berlaku.")


@bp.delete("/<int:user_id>")
@require_auth("admin")
def delete_user(user_id):
    user = get_object_or_404(User, user_id, "User")
    if user.id == g.current_user.id:
        raise APIError(400, "Admin tidak bisa menghapus akunnya sendiri.")

    used = {
        "assets": db.session.scalar(db.select(db.func.count()).where(Asset.owner_id == user.id)),
        "findings": db.session.scalar(db.select(db.func.count()).where(Finding.reported_by_id == user.id)),
        "incidents": db.session.scalar(
            db.select(db.func.count()).where(
                or_(Incident.reporter_id == user.id, Incident.assignee_id == user.id)
            )
        ),
    }
    if any(used.values()):
        raise APIError(
            409,
            "User masih terhubung dengan data lain. Nonaktifkan saja (is_active=false) supaya histori tetap utuh.",
            details=used,
        )

    log_action("delete", "user", user.id, {"email": user.email})
    db.session.delete(user)
    db.session.commit()
    return no_content()
