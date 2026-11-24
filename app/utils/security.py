"""Praktik keamanan dasar: autentikasi API key, otorisasi berbasis role, dan security header."""
import hashlib
import secrets
from functools import wraps

from flask import g, request

from ..extensions import db
from .errors import APIError

API_KEY_HEADER = "X-API-Key"


def generate_api_key():
    """API key acak yang aman (pakai modul secrets, bukan random)."""
    return "stk_" + secrets.token_urlsafe(24)


def hash_api_key(raw_key):
    """Database hanya menyimpan hash. Kalau DB bocor, API key asli tetap aman."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def require_auth(*allowed_roles):
    """Decorator untuk controller.

    @require_auth()                    -> cukup login (role apa saja)
    @require_auth("admin", "analyst")  -> hanya role tertentu
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            from ..models import User

            raw_key = request.headers.get(API_KEY_HEADER, "").strip()
            if not raw_key:
                raise APIError(401, f"Header {API_KEY_HEADER} wajib diisi.")

            user = db.session.execute(
                db.select(User).where(User.api_key_hash == hash_api_key(raw_key))
            ).scalar_one_or_none()
            if user is None or not user.is_active:
                raise APIError(401, "API key tidak valid atau akun nonaktif.")

            if allowed_roles and user.role not in allowed_roles:
                raise APIError(
                    403,
                    "Role kamu tidak punya akses ke aksi ini.",
                    details={"required_roles": list(allowed_roles), "your_role": user.role},
                )

            g.current_user = user
            return view_func(*args, **kwargs)

        return wrapper

    return decorator


def register_security_headers(app):
    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Cache-Control", "no-store")
        # halaman /docs butuh script Swagger UI dari CDN, endpoint lain cukup 'none'
        if request.path != "/docs":
            response.headers.setdefault("Content-Security-Policy", "default-src 'none'")
        return response
