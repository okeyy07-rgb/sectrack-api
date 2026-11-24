"""Format error response yang konsisten untuk SEMUA jenis error.

Bentuknya selalu:
{
  "success": false,
  "error": {"code": "VALIDATION_ERROR", "message": "...", "details": {...}}
}
"""
import logging

from flask import jsonify
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

from ..extensions import db

logger = logging.getLogger(__name__)

HTTP_ERROR_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    415: "UNSUPPORTED_MEDIA_TYPE",
    422: "VALIDATION_ERROR",
    429: "TOO_MANY_REQUESTS",
}


class APIError(Exception):
    """Exception yang dilempar controller kalau ada kondisi error yang disengaja."""

    def __init__(self, status, message, code=None, details=None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.code = code or HTTP_ERROR_CODES.get(status, "ERROR")
        self.details = details


def error_response(status, code, message, details=None):
    body = {"success": False, "error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return jsonify(body), status


def register_error_handlers(app):
    @app.errorhandler(APIError)
    def handle_api_error(err):
        return error_response(err.status, err.code, err.message, err.details)

    @app.errorhandler(ValidationError)
    def handle_validation_error(err):
        return error_response(
            422, "VALIDATION_ERROR", "Data yang dikirim tidak valid.", err.messages
        )

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(err):
        db.session.rollback()
        logger.warning("IntegrityError: %s", err.orig)
        return error_response(
            409,
            "CONFLICT",
            "Operasi bertentangan dengan aturan integritas data (duplikat atau masih direferensikan).",
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        messages = {
            404: "Resource yang dicari tidak ditemukan.",
            405: "HTTP method ini tidak didukung untuk endpoint tersebut.",
            413: "Ukuran request terlalu besar (maksimal 1 MB).",
        }
        code = HTTP_ERROR_CODES.get(err.code, "HTTP_ERROR")
        return error_response(err.code, code, messages.get(err.code, err.description))

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        # detail error hanya masuk log server, tidak dibocorkan ke client
        db.session.rollback()
        logger.exception("Unhandled error")
        return error_response(500, "INTERNAL_ERROR", "Terjadi kesalahan di server.")
