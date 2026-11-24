"""Helper untuk pencarian, filter, sorting, dan pagination lewat query string."""
from datetime import datetime

from flask import current_app, request

from ..extensions import db
from .errors import APIError


def get_object_or_404(model, object_id, label):
    obj = db.session.get(model, object_id)
    if obj is None:
        raise APIError(404, f"{label} dengan id {object_id} tidak ditemukan.")
    return obj


def get_choice_arg(name, choices):
    value = request.args.get(name)
    if value is None or value == "":
        return None
    if value not in choices:
        raise APIError(
            400,
            f"Nilai parameter '{name}' tidak valid.",
            code="INVALID_QUERY_PARAM",
            details={name: f"Pilihan yang valid: {', '.join(choices)}"},
        )
    return value


def get_int_arg(name, default=None, min_value=None, max_value=None):
    raw = request.args.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        raise APIError(400, f"Parameter '{name}' harus angka bulat.", code="INVALID_QUERY_PARAM")
    if (min_value is not None and value < min_value) or (max_value is not None and value > max_value):
        raise APIError(
            400,
            f"Parameter '{name}' harus di antara {min_value} dan {max_value}.",
            code="INVALID_QUERY_PARAM",
        )
    return value


def get_float_arg(name):
    raw = request.args.get(name)
    if raw is None or raw == "":
        return None
    try:
        return float(raw)
    except ValueError:
        raise APIError(400, f"Parameter '{name}' harus angka.", code="INVALID_QUERY_PARAM")


def get_datetime_arg(name):
    raw = request.args.get(name)
    if raw is None or raw == "":
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        raise APIError(
            400,
            f"Parameter '{name}' harus format tanggal ISO 8601, contoh 2026-11-01 atau 2026-11-01T08:00:00.",
            code="INVALID_QUERY_PARAM",
        )


def get_search_term(name="q"):
    term = request.args.get(name, "").strip()
    if len(term) > 100:
        raise APIError(400, "Kata kunci pencarian maksimal 100 karakter.", code="INVALID_QUERY_PARAM")
    return term or None


def like_pattern(term):
    """Escape karakter wildcard supaya input user tidak bisa memanipulasi LIKE."""
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def apply_sorting(stmt, model, allowed_fields, default="-created_at"):
    """?sort=field (ascending) atau ?sort=-field (descending).
    Hanya kolom yang ada di whitelist yang boleh dipakai."""
    sort = request.args.get("sort", default)
    descending = sort.startswith("-")
    field = sort.lstrip("-")
    if field not in allowed_fields:
        raise APIError(
            400,
            "Parameter 'sort' tidak valid.",
            code="INVALID_QUERY_PARAM",
            details={"sort": f"Field yang bisa dipakai: {', '.join(allowed_fields)} (tambah '-' untuk descending)"},
        )
    column = getattr(model, field)
    return stmt.order_by(column.desc() if descending else column.asc(), model.id.asc())


def paginate(stmt):
    """Mengembalikan (items, meta) dari ?page=&per_page="""
    page = get_int_arg("page", default=1, min_value=1, max_value=100000)
    per_page = get_int_arg(
        "per_page",
        default=current_app.config["DEFAULT_PER_PAGE"],
        min_value=1,
        max_value=current_app.config["MAX_PER_PAGE"],
    )
    pagination = db.paginate(stmt, page=page, per_page=per_page, error_out=False)
    meta = {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "total_pages": pagination.pages,
    }
    return pagination.items, meta
