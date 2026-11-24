import pytest

from app import create_app
from app.extensions import db
from app.seed import run_seed

ADMIN = {"X-API-Key": "stk_demo_admin_key"}
ANALYST = {"X-API-Key": "stk_demo_analyst_key"}
REPORTER = {"X-API-Key": "stk_demo_reporter_key"}


@pytest.fixture()
def app():
    """Setiap test memakai database SQLite in-memory baru yang sudah di-seed."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        run_seed()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
