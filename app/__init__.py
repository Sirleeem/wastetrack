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


def _configure_logging(app: Flask) -> None:
    level = logging.DEBUG if app.debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app.logger.setLevel(level)


def _bootstrap_users(app: Flask) -> None:
    """Create demo data and/or bootstrap admin on empty database."""
    from app.models import User

    if User.query.first():
        return

    if app.config.get("SEED_DEMO_DATA"):
        _seed_demo_data()
        app.logger.info("Seeded demo users and sample reports")
        return

    password = app.config.get("ADMIN_PASSWORD") or ""
    if not password:
        app.logger.warning(
            "Empty database and no ADMIN_PASSWORD set. "
            "Set ADMIN_PASSWORD (and optionally ADMIN_EMAIL) or SEED_DEMO_DATA=true."
        )
        return

    admin = User(
        name=app.config.get("ADMIN_NAME") or "System Administrator",
        email=(app.config.get("ADMIN_EMAIL") or "admin@example.com").lower().strip(),
        role="admin",
    )
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    app.logger.info("Bootstrap admin created: %s", admin.email)


def _seed_demo_data() -> None:
    from datetime import timedelta
    import random

    from app.models import Report, User, utcnow
    from app.utils import generate_tracking_code, transition_status

    admin = User(name="System Admin", email="admin@waste.local", role="admin", phone="08010000001")
    admin.set_password("admin123")
    officer1 = User(
        name="Musa Collection", email="officer@waste.local", role="officer", phone="08010000002"
    )
    officer1.set_password("officer123")
    officer2 = User(
        name="Aisha Field", email="officer2@waste.local", role="officer", phone="08010000003"
    )
    officer2.set_password("officer123")
    resident = User(
        name="Ahmad Resident", email="resident@waste.local", role="resident", phone="08010000004"
    )
    resident.set_password("resident123")

    db.session.add_all([admin, officer1, officer2, resident])
    db.session.flush()

    samples = [
        ("illegal_dump", "Illegal dumping near market entrance", 10.3158, 9.8442, "high"),
        ("overflow", "Public bin overflowing by bus stop", 10.3105, 9.8501, "high"),
        ("blocked_drainage", "Drainage blocked with plastic waste", 10.3182, 9.8390, "medium"),
        ("household", "Uncollected household refuse for 3 days", 10.3050, 9.8455, "medium"),
        ("public_space", "Waste scattered at playground", 10.3210, 9.8520, "low"),
        ("commercial", "Shop waste bags left on roadside", 10.3125, 9.8412, "medium"),
        ("overflow", "Skip nearly full at housing estate", 10.3088, 9.8488, "high"),
        ("illegal_dump", "Construction debris dumped on open plot", 10.3175, 9.8550, "medium"),
    ]

    statuses_cycle = ["submitted", "verified", "assigned", "scheduled", "in_progress", "completed"]
    for i, (cat, desc, lat, lon, urg) in enumerate(samples):
        status = statuses_cycle[i % len(statuses_cycle)]
        r = Report(
            tracking_code=generate_tracking_code(),
            category=cat,
            description=desc,
            address=f"Bauchi sample location #{i + 1}",
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
