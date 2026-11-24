from flask import g, request

from ..extensions import db
from ..models import AuditLog


def log_action(action, entity, entity_id=None, detail=None):
    """Catat aktivitas ke tabel audit_logs.
    Dipanggil sebelum commit, jadi ikut satu transaksi dengan perubahan datanya."""
    user = getattr(g, "current_user", None)
    db.session.add(
        AuditLog(
            user_id=user.id if user else None,
            action=action,
            entity=entity,
            entity_id=entity_id,
            detail=detail,
            ip_address=request.remote_addr,
        )
    )


def _jsonable(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def apply_changes(obj, data):
    """Set atribut model dari dict `data` dan kembalikan daftar field yang benar-benar berubah.
    Hasilnya dipakai untuk detail audit log: {"field": {"from": lama, "to": baru}}."""
    changes = {}
    for field, new_value in data.items():
        old_value = getattr(obj, field)
        if old_value != new_value:
            changes[field] = {"from": _jsonable(old_value), "to": _jsonable(new_value)}
            setattr(obj, field, new_value)
    return changes
