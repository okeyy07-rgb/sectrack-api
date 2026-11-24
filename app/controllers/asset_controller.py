from flask import Blueprint, g, request
from sqlalchemy import or_

from ..extensions import db
from ..models import Asset, User
from ..models.constants import ASSET_TYPES, CRITICALITY_LEVELS
from ..utils.audit import apply_changes, log_action
from ..utils.errors import APIError
from ..utils.query import (
    apply_sorting,
    get_choice_arg,
    get_int_arg,
    get_object_or_404,
    get_search_term,
    like_pattern,
    paginate,
)
from ..utils.security import require_auth
from ..views import AssetInputSchema, AssetOutputSchema, get_json_body, no_content, success

bp = Blueprint("assets", __name__, url_prefix="/api/v1/assets")

input_schema = AssetInputSchema()
output_schema = AssetOutputSchema()

SORT_FIELDS = ("name", "asset_type", "created_at", "updated_at")
OPTIONAL_FIELDS = ("ip_address", "location", "description")


def _validate_relations(data):
    """Cek owner_id benar-benar ada (422 kalau tidak)."""
    if "owner_id" in data:
        owner = db.session.get(User, data["owner_id"])
        if owner is None or not owner.is_active:
            raise APIError(422, "Data yang dikirim tidak valid.", details={"owner_id": ["User tidak ditemukan atau nonaktif."]})


def _ensure_unique_name(name, current_id=None):
    stmt = db.select(Asset).where(Asset.name == name)
    if current_id:
        stmt = stmt.where(Asset.id != current_id)
    if db.session.execute(stmt).scalar_one_or_none():
        raise APIError(409, "Nama aset sudah dipakai.", details={"name": name})


@bp.get("")
@require_auth()
def list_assets():
    stmt = db.select(Asset)

    term = get_search_term()
    if term:
        pattern = like_pattern(term)
        stmt = stmt.where(
            or_(
                Asset.name.ilike(pattern, escape="\\"),
                Asset.ip_address.ilike(pattern, escape="\\"),
                Asset.location.ilike(pattern, escape="\\"),
            )
        )
    asset_type = get_choice_arg("asset_type", ASSET_TYPES)
    if asset_type:
        stmt = stmt.where(Asset.asset_type == asset_type)
    criticality = get_choice_arg("criticality", CRITICALITY_LEVELS)
    if criticality:
        stmt = stmt.where(Asset.criticality == criticality)
    owner_id = get_int_arg("owner_id", min_value=1)
    if owner_id:
        stmt = stmt.where(Asset.owner_id == owner_id)

    stmt = apply_sorting(stmt, Asset, SORT_FIELDS, default="name")
    items, meta = paginate(stmt)
    return success(output_schema.dump(items, many=True), meta=meta)


@bp.post("")
@require_auth("admin", "analyst")
def create_asset():
    data = input_schema.load(get_json_body())
    data.setdefault("owner_id", g.current_user.id)
    _validate_relations(data)
    _ensure_unique_name(data["name"])

    asset = Asset(**data)
    db.session.add(asset)
    db.session.flush()  # supaya asset.id sudah terisi untuk audit log
    log_action("create", "asset", asset.id, {"name": asset.name})
    db.session.commit()
    return success(
        output_schema.dump(asset),
        status=201,
        message="Aset berhasil ditambahkan.",
        headers={"Location": f"/api/v1/assets/{asset.id}"},
    )


@bp.get("/<int:asset_id>")
@require_auth()
def get_asset(asset_id):
    return success(output_schema.dump(get_object_or_404(Asset, asset_id, "Aset")))


@bp.put("/<int:asset_id>")
@bp.patch("/<int:asset_id>")
@require_auth("admin", "analyst")
def update_asset(asset_id):
    asset = get_object_or_404(Asset, asset_id, "Aset")
    is_patch = request.method == "PATCH"
    # PUT = ganti seluruh data (field wajib harus ada), PATCH = ubah sebagian
    data = input_schema.load(get_json_body(), partial=is_patch)
    if not is_patch:
        for field in OPTIONAL_FIELDS:
            data.setdefault(field, None)

    _validate_relations(data)
    if "name" in data:
        _ensure_unique_name(data["name"], current_id=asset.id)

    changes = apply_changes(asset, data)
    if changes:
        log_action("update", "asset", asset.id, changes)
    db.session.commit()
    return success(output_schema.dump(asset), message="Aset diperbarui.")


@bp.delete("/<int:asset_id>")
@require_auth("admin")
def delete_asset(asset_id):
    asset = get_object_or_404(Asset, asset_id, "Aset")
    if asset.findings or asset.incidents:
        raise APIError(
            409,
            "Aset masih punya temuan atau insiden, jadi tidak bisa dihapus.",
            details={"findings": len(asset.findings), "incidents": len(asset.incidents)},
        )
    log_action("delete", "asset", asset.id, {"name": asset.name})
    db.session.delete(asset)
    db.session.commit()
    return no_content()
