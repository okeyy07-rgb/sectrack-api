from flask import Blueprint, g

from ..extensions import db
from ..models import Asset, Finding, Vulnerability
from ..models.constants import FINDING_STATUSES, SEVERITY_LEVELS
from ..utils.audit import apply_changes, log_action
from ..utils.errors import APIError
from ..utils.query import apply_sorting, get_choice_arg, get_int_arg, get_object_or_404, paginate
from ..utils.security import require_auth
from ..views import FindingCreateSchema, FindingOutputSchema, FindingUpdateSchema, get_json_body, no_content, success

bp = Blueprint("findings", __name__, url_prefix="/api/v1/findings")

create_schema = FindingCreateSchema()
update_schema = FindingUpdateSchema()
output_schema = FindingOutputSchema()

SORT_FIELDS = ("found_at", "status", "created_at", "updated_at")


@bp.get("")
@require_auth()
def list_findings():
    stmt = db.select(Finding).join(Finding.vulnerability)

    status = get_choice_arg("status", FINDING_STATUSES)
    if status:
        stmt = stmt.where(Finding.status == status)
    asset_id = get_int_arg("asset_id", min_value=1)
    if asset_id:
        stmt = stmt.where(Finding.asset_id == asset_id)
    vulnerability_id = get_int_arg("vulnerability_id", min_value=1)
    if vulnerability_id:
        stmt = stmt.where(Finding.vulnerability_id == vulnerability_id)
    # filter lewat relasi: severity milik kerentanannya
    severity = get_choice_arg("severity", SEVERITY_LEVELS)
    if severity:
        stmt = stmt.where(Vulnerability.severity == severity)

    stmt = apply_sorting(stmt, Finding, SORT_FIELDS, default="-found_at")
    items, meta = paginate(stmt)
    return success(output_schema.dump(items, many=True), meta=meta)


@bp.post("")
@require_auth("admin", "analyst")
def create_finding():
    data = create_schema.load(get_json_body())

    errors = {}
    if db.session.get(Asset, data["asset_id"]) is None:
        errors["asset_id"] = ["Aset tidak ditemukan."]
    if db.session.get(Vulnerability, data["vulnerability_id"]) is None:
        errors["vulnerability_id"] = ["Kerentanan tidak ditemukan."]
    if errors:
        raise APIError(422, "Data yang dikirim tidak valid.", details=errors)

    duplicate = db.session.execute(
        db.select(Finding).where(
            Finding.asset_id == data["asset_id"], Finding.vulnerability_id == data["vulnerability_id"]
        )
    ).scalar_one_or_none()
    if duplicate:
        raise APIError(
            409,
            "Kerentanan ini sudah tercatat di aset tersebut. Update temuan yang lama saja.",
            details={"existing_finding_id": duplicate.id},
        )

    status = data.pop("status")
    finding = Finding(**data, reported_by_id=g.current_user.id)
    finding.apply_status(status)
    db.session.add(finding)
    db.session.flush()
    log_action(
        "create",
        "finding",
        finding.id,
        {"asset_id": finding.asset_id, "vulnerability_id": finding.vulnerability_id},
    )
    db.session.commit()
    return success(
        output_schema.dump(finding),
        status=201,
        message="Temuan dicatat.",
        headers={"Location": f"/api/v1/findings/{finding.id}"},
    )


@bp.get("/<int:finding_id>")
@require_auth()
def get_finding(finding_id):
    return success(output_schema.dump(get_object_or_404(Finding, finding_id, "Temuan")))


@bp.patch("/<int:finding_id>")
@require_auth("admin", "analyst")
def update_finding(finding_id):
    """Yang bisa diubah hanya status dan notes. Aset & kerentanannya tetap,
    kalau salah input lebih baik hapus lalu buat temuan baru."""
    finding = get_object_or_404(Finding, finding_id, "Temuan")
    data = update_schema.load(get_json_body())
    if not data:
        raise APIError(400, "Tidak ada field yang diubah. Kirim 'status' dan/atau 'notes'.")

    changes = {}
    if "status" in data and data["status"] != finding.status:
        changes["status"] = {"from": finding.status, "to": data["status"]}
        finding.apply_status(data.pop("status"))
    data.pop("status", None)
    changes.update(apply_changes(finding, data))

    if changes:
        log_action("update", "finding", finding.id, changes)
    db.session.commit()
    return success(output_schema.dump(finding), message="Temuan diperbarui.")


@bp.delete("/<int:finding_id>")
@require_auth("admin")
def delete_finding(finding_id):
    finding = get_object_or_404(Finding, finding_id, "Temuan")
    log_action(
        "delete",
        "finding",
        finding.id,
        {"asset_id": finding.asset_id, "vulnerability_id": finding.vulnerability_id},
    )
    db.session.delete(finding)
    db.session.commit()
    return no_content()
