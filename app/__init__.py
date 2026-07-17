import logging
import os
from pathlib import Path

from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import ProductionConfig, get_config
from app.extensions import db, login_manager


def create_app(config_class=None):
    if config_class is None:
        config_class = get_config()

    app = Flask(__name__)
    app.config.from_object(config_class)
    _apply_runtime_env(app)

    # Engine options (pool for Postgres; thread-safe SQLite)
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = ProductionConfig.init_engine_options(uri)

    # Ensure folders exist
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    (Path(app.root_path).parent / "instance").mkdir(parents=True, exist_ok=True)

    # Trust X-Forwarded-* when behind nginx / load balancer
    if app.config.get("BEHIND_PROXY"):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    _configure_logging(app)

    db.init_app(app)
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.resident import resident_bp
    from app.routes.officer import officer_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(resident_bp)
    app.register_blueprint(officer_bp)
    app.register_blueprint(admin_bp)

    @app.context_processor
    def inject_helpers():
        from app.utils import status_badge_class, urgency_badge_class

        return {
            "status_badge_class": status_badge_class,
            "urgency_badge_class": urgency_badge_class,
            "show_demo_credentials": app.config.get("SHOW_DEMO_CREDENTIALS", False),
        }

    @app.get("/health")
    def health():
        """Load balancer / container health check (no auth)."""
        from sqlalchemy import text

        try:
            db.session.execute(text("SELECT 1"))
            db_ok = True
        except Exception as exc:  # noqa: BLE001
            app.logger.warning("Health DB check failed: %s", exc)
            db_ok = False
        status = 200 if db_ok else 503
        return (
            jsonify(
                {
                    "status": "ok" if db_ok else "degraded",
                    "database": "up" if db_ok else "down",
                    "service": "wastetrack",
                }
            ),
            status,
        )

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(self)")
        if not app.debug:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        return response

    with app.app_context():
        db.create_all()
        _bootstrap_users(app)

    return app


def _truthy(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).lower() in ("1", "true", "yes")


def _apply_runtime_env(app: Flask) -> None:
    """Re-read env vars on every boot (class attributes are frozen at import)."""
    from app.config import _normalize_database_url, _default_sqlite_uri

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or app.config.get("SECRET_KEY")
    db_url = (os.environ.get("DATABASE_URL") or "").strip()
    app.config["SQLALCHEMY_DATABASE_URI"] = _normalize_database_url(
        db_url or app.config.get("SQLALCHEMY_DATABASE_URI") or _default_sqlite_uri()
    )
    # Default ON so academic deploys always get admin@waste.local etc.
    # Set SEED_DEMO_DATA=false on Render to disable.
    app.config["SEED_DEMO_DATA"] = _truthy("SEED_DEMO_DATA", "true")
    app.config["SHOW_DEMO_CREDENTIALS"] = _truthy("SHOW_DEMO_CREDENTIALS", "true")
    app.config["BEHIND_PROXY"] = _truthy(
        "BEHIND_PROXY",
        "true" if not app.debug else "false",
    )
    app.config["SESSION_COOKIE_SECURE"] = _truthy(
        "SESSION_COOKIE_SECURE",
        "true" if not app.debug else "false",
    )
    app.config["ADMIN_EMAIL"] = os.environ.get("ADMIN_EMAIL", app.config.get("ADMIN_EMAIL"))
    app.config["ADMIN_PASSWORD"] = os.environ.get(
        "ADMIN_PASSWORD", app.config.get("ADMIN_PASSWORD") or ""
    )
    app.config["ADMIN_NAME"] = os.environ.get("ADMIN_NAME", app.config.get("ADMIN_NAME"))
    app.config["OFFICER_EMAIL"] = os.environ.get("OFFICER_EMAIL", "").strip().lower()
    app.config["OFFICER_PASSWORD"] = os.environ.get("OFFICER_PASSWORD", "")
    app.config["OFFICER_NAME"] = os.environ.get("OFFICER_NAME", "Collection Officer")
    app.config["SETUP_SECRET"] = os.environ.get("SETUP_SECRET", "")


def _configure_logging(app: Flask) -> None:
    level = logging.DEBUG if app.debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app.logger.setLevel(level)


def _upsert_user(email: str, name: str, role: str, password: str, phone: str = "") -> bool:
    """Create or update a user by email. Returns True if created."""
    from app.models import User

    email = (email or "").strip().lower()
    if not email or not password:
        return False
    user = User.query.filter_by(email=email).first()
    created = False
    if not user:
        user = User(email=email, name=name or email.split("@")[0], role=role, phone=phone or None)
        db.session.add(user)
        created = True
    else:
        user.name = name or user.name
        user.role = role
        if phone:
            user.phone = phone
    user.is_active_user = True
    user.set_password(password)
    db.session.commit()
    return created


def _bootstrap_users(app: Flask) -> None:
    """Create demo accounts and/or env-based admin & officer accounts.

    - SEED_DEMO_DATA=true → always ensure demo admin/officer/resident
    - ADMIN_EMAIL + ADMIN_PASSWORD → always upsert admin (works even if residents exist)
    - OFFICER_EMAIL + OFFICER_PASSWORD → always upsert officer
    """
    from app.models import User

    if app.config.get("SEED_DEMO_DATA"):
        created = _ensure_demo_users()
        if _reports_empty():
            _seed_sample_reports()
        app.logger.info(
            "Demo accounts ready: admin@waste.local / officer@waste.local / "
            "resident@waste.local (password ends with 123). updated=%s",
            created,
        )

    admin_pw = (app.config.get("ADMIN_PASSWORD") or "").strip()
    admin_email = (app.config.get("ADMIN_EMAIL") or "").strip().lower()
    if admin_pw and admin_email:
        created = _upsert_user(
            admin_email,
            app.config.get("ADMIN_NAME") or "System Administrator",
            "admin",
            admin_pw,
        )
        app.logger.info(
            "Admin account %s: %s",
            "created" if created else "updated",
            admin_email,
        )
    elif not User.query.filter_by(role="admin").first() and not app.config.get("SEED_DEMO_DATA"):
        app.logger.warning(
            "No admin user in database. Set SEED_DEMO_DATA=true or "
            "ADMIN_EMAIL + ADMIN_PASSWORD, or open /auth/setup with SETUP_SECRET."
        )

    officer_pw = (app.config.get("OFFICER_PASSWORD") or "").strip()
    officer_email = (app.config.get("OFFICER_EMAIL") or "").strip().lower()
    if officer_pw and officer_email:
        created = _upsert_user(
            officer_email,
            app.config.get("OFFICER_NAME") or "Collection Officer",
            "officer",
            officer_pw,
        )
        app.logger.info(
            "Officer account %s: %s",
            "created" if created else "updated",
            officer_email,
        )


def _reports_empty() -> bool:
    from app.models import Report

    return Report.query.first() is None


def _ensure_demo_users() -> int:
    """Create demo users if missing; always reset known demo passwords."""
    from app.models import User

    specs = [
        {
            "email": "admin@waste.local",
            "name": "System Admin",
            "role": "admin",
            "phone": "08010000001",
            "password": "admin123",
        },
        {
            "email": "officer@waste.local",
            "name": "Musa Collection",
            "role": "officer",
            "phone": "08010000002",
            "password": "officer123",
        },
        {
            "email": "officer2@waste.local",
            "name": "Aisha Field",
            "role": "officer",
            "phone": "08010000003",
            "password": "officer123",
        },
        {
            "email": "resident@waste.local",
            "name": "Ahmad Resident",
            "role": "resident",
            "phone": "08010000004",
            "password": "resident123",
        },
    ]
    touched = 0
    for spec in specs:
        user = User.query.filter_by(email=spec["email"]).first()
        if not user:
            user = User(
                email=spec["email"],
                name=spec["name"],
                role=spec["role"],
                phone=spec["phone"],
                is_active_user=True,
            )
            db.session.add(user)
            touched += 1
        else:
            user.name = spec["name"]
            user.role = spec["role"]
            user.phone = spec["phone"]
            user.is_active_user = True
            touched += 1
        user.set_password(spec["password"])
    db.session.commit()
    return touched


def _seed_sample_reports() -> None:
    from datetime import timedelta
    import random

    from app.models import Report, User, utcnow
    from app.utils import generate_tracking_code, transition_status

    admin = User.query.filter_by(email="admin@waste.local").first()
    officer1 = User.query.filter_by(email="officer@waste.local").first()
    officer2 = User.query.filter_by(email="officer2@waste.local").first()
    resident = User.query.filter_by(email="resident@waste.local").first()
    if not all([admin, officer1, officer2, resident]):
        return

    samples = [
        ("illegal_dump", "Illegal dumping near Wunti Market entrance", 10.3158, 9.8442, "high"),
        ("overflow", "Public bin overflowing at Yelwa bus stop", 10.3105, 9.8501, "high"),
        ("blocked_drainage", "Drainage blocked with plastic near Railway Quarters", 10.3182, 9.8390, "medium"),
        ("household", "Uncollected household refuse for 3 days in New GRA", 10.3050, 9.8455, "medium"),
        ("public_space", "Waste scattered near ATBU main gate area", 10.3210, 9.8520, "low"),
        ("commercial", "Shop waste bags left on roadside by Central Market", 10.3125, 9.8412, "medium"),
        ("overflow", "Skip nearly full at Fadaman Mada housing area", 10.3088, 9.8488, "high"),
        ("illegal_dump", "Construction debris dumped on open plot along Jos Road", 10.3175, 9.8550, "medium"),
    ]

    statuses_cycle = ["submitted", "verified", "assigned", "scheduled", "in_progress", "completed"]
    for i, (cat, desc, lat, lon, urg) in enumerate(samples):
        status = statuses_cycle[i % len(statuses_cycle)]
        r = Report(
            tracking_code=generate_tracking_code(),
            category=cat,
            description=desc,
            address=[
                "Wunti Market, Bauchi",
                "Yelwa Junction, Bauchi",
                "Railway Quarters, Bauchi",
                "New GRA, Bauchi",
                "ATBU Main Gate area, Bauchi",
                "Central Market roadside, Bauchi",
                "Fadaman Mada, Bauchi",
                "Along Jos Road, Bauchi",
            ][i],
            latitude=lat + random.uniform(-0.002, 0.002),
            longitude=lon + random.uniform(-0.002, 0.002),
            urgency=urg,
            status="submitted",
            reporter_id=resident.id,
            created_at=utcnow() - timedelta(days=random.randint(0, 10)),
        )
        if status in ("assigned", "scheduled", "in_progress", "completed"):
            r.officer_id = officer1.id if i % 2 == 0 else officer2.id
            r.assigned_by_id = admin.id
        if status in ("scheduled", "in_progress", "completed"):
            r.scheduled_date = (utcnow() + timedelta(days=i % 3)).date()
            r.collection_order = (i % 4) + 1
        if status == "completed":
            r.completed_at = utcnow() - timedelta(hours=random.randint(1, 48))

        db.session.add(r)
        db.session.flush()
        transition_status(r, "submitted", resident, note="Seed report")
        if status != "submitted":
            for s in statuses_cycle:
                if s == "submitted":
                    continue
                transition_status(r, s, admin, note=f"Seed transition to {s}")
                if s == status:
                    break

    db.session.commit()
