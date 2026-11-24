"""Endpoint umum: info API, health check, dan dokumentasi (OpenAPI + Swagger UI)."""
import os

from flask import Blueprint, current_app, send_from_directory
from sqlalchemy import text

from ..extensions import db
from ..views import success

bp = Blueprint("main", __name__)

SWAGGER_HTML = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <title>SecTrack API Docs</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.ui = SwaggerUIBundle({ url: "/openapi.yaml", dom_id: "#swagger-ui" });
  </script>
</body>
</html>"""


@bp.get("/")
def index():
    return success(
        {
            "name": "SecTrack API",
            "description": "REST API pencatatan aset, kerentanan, temuan, dan insiden keamanan.",
            "version": "1.0.0",
            "docs": "/docs",
            "openapi": "/openapi.yaml",
            "health": "/api/v1/health",
        }
    )


@bp.get("/api/v1/health")
def health():
    db.session.execute(text("SELECT 1"))
    return success({"status": "ok", "database": "connected"})


@bp.get("/openapi.yaml")
def openapi_spec():
    docs_dir = os.path.join(current_app.root_path, "..", "docs")
    return send_from_directory(os.path.abspath(docs_dir), "openapi.yaml", mimetype="application/yaml")


@bp.get("/docs")
def swagger_ui():
    return SWAGGER_HTML, 200, {"Content-Type": "text/html; charset=utf-8"}
