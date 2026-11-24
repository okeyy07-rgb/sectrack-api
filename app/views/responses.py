"""Format response sukses yang konsisten.

{
  "success": true,
  "message": "...",          (opsional)
  "data": {...} / [...],
  "meta": {"page": 1, ...}   (khusus list)
}
"""
from flask import jsonify, request

from ..utils.errors import APIError


def success(data=None, status=200, message=None, meta=None, headers=None):
    body = {"success": True}
    if message:
        body["message"] = message
    body["data"] = data
    if meta is not None:
        body["meta"] = meta
    response = jsonify(body)
    response.status_code = status
    if headers:
        response.headers.update(headers)
    return response


def no_content():
    return "", 204


def get_json_body():
    """Pastikan request memakai Content-Type: application/json dan body-nya JSON object."""
    if not request.is_json:
        raise APIError(415, "Content-Type harus application/json.")
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise APIError(400, "Body request harus berupa JSON object yang valid.")
    return data
