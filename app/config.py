"""Konfigurasi aplikasi.

Nilai sensitif (SECRET_KEY, DATABASE_URL) dibaca dari environment variable
atau file .env, jadi tidak perlu di-hardcode di source code.
"""
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-ganti-di-production")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///" + os.path.join(INSTANCE_DIR, "sectrack.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Batasi ukuran request body (1 MB) supaya tidak bisa dibanjiri payload besar.
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024

    DEFAULT_PER_PAGE = 10
    MAX_PER_PAGE = 100


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config_by_name = {
    "development": Config,
    "production": Config,
    "testing": TestConfig,
}
