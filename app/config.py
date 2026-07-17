import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _normalize_database_url(url: str) -> str:
    """Support Heroku/Railway-style postgres:// URLs and relative sqlite paths."""
    if not url:
        return url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    # Absolute Windows sqlite path: sqlite:///C:\... already fine with four slashes style
    return url


def _default_sqlite_uri() -> str:
    instance = BASE_DIR / "instance"
    instance.mkdir(parents=True, exist_ok=True)
    # Four slashes for absolute path on all platforms
    db_path = (instance / "waste_management.db").resolve()
    return "sqlite:///" + db_path.as_posix()


class Config:
    """Base configuration shared by all environments."""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-only-change-me"
    # Empty DATABASE_URL (common on Render when left blank) → SQLite
    _db_url = (os.environ.get("DATABASE_URL") or "").strip()
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(_db_url or _default_sqlite_uri())
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER",
        str(BASE_DIR / "app" / "static" / "uploads"),
    )
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

    # Session / cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(
        seconds=int(os.environ.get("SESSION_LIFETIME_SECONDS", 60 * 60 * 12))
    )

    # App behaviour
    SEED_DEMO_DATA = os.environ.get("SEED_DEMO_DATA", "false").lower() in ("1", "true", "yes")
    SHOW_DEMO_CREDENTIALS = os.environ.get("SHOW_DEMO_CREDENTIALS", "false").lower() in (
        "1",
        "true",
        "yes",
    )
    PREFERRED_URL_SCHEME = os.environ.get("PREFERRED_URL_SCHEME", "http")
    BEHIND_PROXY = os.environ.get("BEHIND_PROXY", "false").lower() in ("1", "true", "yes")

    # Bootstrap admin (created only when database has no users)
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
    ADMIN_NAME = os.environ.get("ADMIN_NAME", "System Administrator")


class DevelopmentConfig(Config):
    DEBUG = True
    SEED_DEMO_DATA = os.environ.get("SEED_DEMO_DATA", "true").lower() in ("1", "true", "yes")
    SHOW_DEMO_CREDENTIALS = os.environ.get("SHOW_DEMO_CREDENTIALS", "true").lower() in (
        "1",
        "true",
        "yes",
    )


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "true").lower() in (
        "1",
        "true",
        "yes",
    )
    REMEMBER_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = os.environ.get("PREFERRED_URL_SCHEME", "https")
    BEHIND_PROXY = os.environ.get("BEHIND_PROXY", "true").lower() in ("1", "true", "yes")
    SEED_DEMO_DATA = os.environ.get("SEED_DEMO_DATA", "false").lower() in ("1", "true", "yes")
    SHOW_DEMO_CREDENTIALS = False

    # SQLite needs check_same_thread for some workers; Postgres uses pool
    @staticmethod
    def init_engine_options(uri: str) -> dict:
        opts = {"pool_pre_ping": True}
        if uri.startswith("sqlite"):
            opts["connect_args"] = {"check_same_thread": False}
        else:
            opts["pool_size"] = int(os.environ.get("DB_POOL_SIZE", "5"))
            opts["max_overflow"] = int(os.environ.get("DB_MAX_OVERFLOW", "10"))
        return opts


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SEED_DEMO_DATA = False
    SHOW_DEMO_CREDENTIALS = False
    SECRET_KEY = "test-secret"


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config():
    name = os.environ.get("FLASK_ENV") or os.environ.get("APP_ENV") or "development"
    name = name.lower().strip()
    if name in ("prod", "production"):
        return ProductionConfig
    if name in ("test", "testing"):
        return TestingConfig
    return DevelopmentConfig
