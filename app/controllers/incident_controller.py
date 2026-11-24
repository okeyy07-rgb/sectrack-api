from flask import Blueprint, g, request
from sqlalchemy import or_

from ..extensions import db
from ..models import Asset, Incident, User
from ..models.constants import INCIDENT_CATEGORIES, INCIDENT_STATUSES, SEVERITY_LEVELS
from ..utils.audit import apply_changes, log_action
from ..utils.errors import APIError
from ..utils.query import (
    apply_sorting,
    get_choice_arg,
    get_datetime_arg,
    get_int_arg,
    get_object_or_404,
    get_search_term,
    like_pattern,
    paginate,
)
from ..utils.security import require_auth
from ..views import IncidentInputSchema, IncidentOutputSchema, get_json_body, no_content, success

bp = Blueprint("incidents", __name__, url_prefix="/api/v1/incidents")

input_schema = IncidentInputSchema()
output_schema = IncidentOutputSchema()

SORT_FIELDS = ("occurred_at", "created_at", "updated_at", "title")
OPTIONAL_FIELDS = ("asset_id", "assignee_id")


def _validate_relations(data):
    errors = {}
    if data.get("asset_id") is not None and db.session.get(Asset, data["asset_id"]) is None:
        errors["asset_id"] = ["Aset tidak ditemukan."]
    if data.get("assignee_id") is not None:
        assignee = db.session.get(User, data["assignee_id"])
        if assignee is None or not assignee.is_active:
            errors["assignee_id"] = ["User tidak ditemukan atau nonaktif."]
        elif assignee.role not in ("admin", "analyst"):
            errors["assignee_id"] = ["Insiden hanya bisa ditugaskan ke analyst atau admin."]
    if errors:
        raise APIError(422, "Data yang dikirim tidak valid.", details=errors)


@bp.get("")
@require_auth()
def list_incidents():
    stmt = db.select(Incident)

    term = get_search_term()
    if term:
        pattern = like_pattern(term)
        stmt = stmt.where(
            or_(Incident.title.ilike(pattern, escape="\\"), Incident.description.ilike(pattern, escape="\\"))
        )
    for name, choices in (
        ("status", INCIDENT_STATUSES),
        ("category", INCIDENT_CATEGORIES),
        ("severity", SEVERITY_LEVELS),
    ):
        value = get_choice_arg(name, choices)
        if value:
            stmt = stmt.where(getattr(Incident, name) == value)
    for name in ("asset_id", "assignee_id", "reporter_id"):
        value = get_int_arg(name, min_value=1)
        if value:
            stmt = stmt.where(getattr(Incident, name) == value)

    # filter rentang tanggal kejadian
    date_from = get_datetime_arg("from")
    if date_from:
        stmt = stmt.where(Incident.occurred_at >= date_from)
    date_to = get_datetime_arg("to")
    if date_to:
        stmt = stmt.where(Incident.occurred_at <= date_to)

    stmt = apply_sorting(stmt, Incident, SORT_FIELDS, default="-occurred_at")
    items, meta = paginate(stmt)
    return success(output_schema.dump(items, many=True), meta=meta)


@bp.post("")
@require_auth()  # semua role boleh melapor insiden
def create_incident():
    data = input_schema.load(get_json_body())
    if g.current_user.role == "reporter" and (
        data.get("assignee_id") is not None or data.get("status", "new") != "new"
    ):
        raise APIError(403, "Reporter hanya bisa membuat laporan baru, tidak bisa menentukan assignee atau status.")
    _validate_relations(data)

    status = data.pop("status")
    incident = Incident(**data, reporter_id=g.current_user.id)
    incident.apply_status(status)
    db.session.add(incident)
    db.session.flush()
    log_action("create", "incident", incident.id, {"title": incident.title, "severity": incident.severity})
    db.session.commit()
    return success(
        output_schema.dump(incident),
        status=201,
        message="Insiden dilaporkan.",
        headers={"Location": f"/api/v1/incidents/{incident.id}"},
    )


@bp.get("/<int:incident_id>")
@require_auth()
def get_incident(incident_id):
    return success(output_schema.dump(get_object_or_404(Incident, incident_id, "Insiden")))


@bp.put("/<int:incident_id>")
@bp.patch("/<int:incident_id>")
@require_auth("admin", "analyst")
def update_incident(incident_id):
    incident = get_object_or_404(Incident, incident_id, "Insiden")
    is_patch = request.method == "PATCH"
    data = input_schema.load(get_json_body(), partial=is_patch)
    if not is_patch:
        for field in OPTIONAL_FIELDS:
            data.setdefault(field, None)
    _validate_relations(data)

    changes = {}
    new_status = data.pop("status", None)
    if new_status and new_status != incident.status:
        changes["status"] = {"from": incident.status, "to": new_status}
        incident.apply_status(new_status)
    changes.update(apply_changes(incident, data))

    if changes:
        log_action("update", "incident", incident.id, changes)
    db.session.commit()
    return success(output_schema.dump(incident), message="Insiden diperbarui.")


@bp.delete("/<int:incident_id>")
@require_auth("admin")
def delete_incident(incident_id):
    incident = get_object_or_404(Incident, incident_id, "Insiden")
    log_action("delete", "incident", incident.id, {"title": incident.title})
    db.session.delete(incident)
    db.session.commit()
    return no_content()
