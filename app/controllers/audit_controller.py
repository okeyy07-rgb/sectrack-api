from flask import Blueprint

from ..extensions import db
from ..models import AuditLog
from ..models.constants import AUDIT_ACTIONS
from ..utils.query import apply_sorting, get_choice_arg, get_int_arg, get_object_or_404, paginate
from ..utils.security import require_auth
from ..views import AuditLogOutputSchema, success

bp = Blueprint("audit_logs", __name__, url_prefix="/api/v1/audit-logs")

output_schema = AuditLogOutputSchema()
ENTITIES = ("user", "asset", "vulnerability", "finding", "incident")


@bp.get("")
@require_auth("admin")
def list_audit_logs():
    """Read-only. Tidak ada POST/PUT/DELETE supaya jejak audit tidak bisa dimanipulasi lewat API."""
    stmt = db.select(AuditLog)
    action = get_choice_arg("action", AUDIT_ACTIONS)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    entity = get_choice_arg("entity", ENTITIES)
    if entity:
        stmt = stmt.where(AuditLog.entity == entity)
    user_id = get_int_arg("user_id", min_value=1)
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    stmt = apply_sorting(stmt, AuditLog, ("created_at",), default="-created_at")
    items, meta = paginate(stmt)
    return success(output_schema.dump(items, many=True), meta=meta)


@bp.get("/<int:log_id>")
@require_auth("admin")
def get_audit_log(log_id):
    return success(output_schema.dump(get_object_or_404(AuditLog, log_id, "Audit log")))
