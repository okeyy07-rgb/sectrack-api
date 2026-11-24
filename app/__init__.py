"""Application factory SecTrack API."""
import os

from flask import Flask

from .config import INSTANCE_DIR, config_by_name
from .extensions import db, migrate


def create_app(config_name=None):
    config_name = config_name or os.getenv("FLASK_ENV_NAME", "development")
    app = Flask(__name__, instance_path=INSTANCE_DIR)
    app.config.from_object(config_by_name.get(config_name, config_by_name["development"]))
    app.json.sort_keys = False

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    # render_as_batch=True supaya ALTER TABLE di SQLite tetap aman lewat Alembic
    migrate.init_app(app, db, render_as_batch=True)

    # import models supaya terdaftar di metadata SQLAlchemy (dipakai migration)
    from . import models  # noqa: F401

    from .controllers import register_blueprints
    from .utils.errors import register_error_handlers
    from .utils.security import register_security_headers
    from .cli import register_cli

    register_blueprints(app)
    register_error_handlers(app)
    register_security_headers(app)
    register_cli(app)

    return app
