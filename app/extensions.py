"""Objek extension dibuat di sini supaya bisa di-import dari mana saja
tanpa circular import."""
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()
migrate = Migrate()


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """SQLite secara default TIDAK mengecek foreign key.
    Pragma ini menyalakannya supaya integritas data tetap terjaga."""
    module = type(dbapi_connection).__module__
    if module.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
