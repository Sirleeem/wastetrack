from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="resident")  # resident, officer, admin
    phone = db.Column(db.String(40))
    is_active_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    reports = db.relationship("Report", back_populates="reporter", foreign_keys="Report.reporter_id")
    assigned_reports = db.relationship(
        "Report", back_populates="officer", foreign_keys="Report.officer_id"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self) -> bool:
        """Flask-Login active flag (honours admin deactivation)."""
        return bool(self.is_active_user)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_officer(self) -> bool:
        return self.role == "officer"

    @property
    def is_resident(self) -> bool:
        return self.role == "resident"


class Report(db.Model):
    __tablename__ = "reports"

    STATUSES = (
        "submitted",
        "verified",
        "rejected",
        "assigned",
        "scheduled",
        "in_progress",
        "completed",
    )
    CATEGORIES = (
        "household",
        "illegal_dump",
        "overflow",
        "blocked_drainage",
        "commercial",
        "public_space",
        "other",
    )
    URGENCIES = ("low", "medium", "high")

    id = db.Column(db.Integer, primary_key=True)
    tracking_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    category = db.Column(db.String(40), nullable=False)
    description = db.Column(db.Text, nullable=False)
    address = db.Column(db.String(255))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(255))
    urgency = db.Column(db.String(20), default="medium")
    status = db.Column(db.String(30), default="submitted", index=True)
    admin_notes = db.Column(db.Text)
    scheduled_date = db.Column(db.Date)
    collection_order = db.Column(db.Integer)  # from optimization
    created_at = db.Column(db.DateTime, default=utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    completed_at = db.Column(db.DateTime)

    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    officer_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    assigned_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    reporter = db.relationship("User", foreign_keys=[reporter_id], back_populates="reports")
    officer = db.relationship("User", foreign_keys=[officer_id], back_populates="assigned_reports")
    assigned_by = db.relationship("User", foreign_keys=[assigned_by_id])
    history = db.relationship(
        "StatusHistory",
        back_populates="report",
        order_by="StatusHistory.created_at",
        cascade="all, delete-orphan",
    )

    def status_label(self) -> str:
        return self.status.replace("_", " ").title()

    def category_label(self) -> str:
        return self.category.replace("_", " ").title()

    def urgency_label(self) -> str:
        return (self.urgency or "medium").title()


class StatusHistory(db.Model):
    __tablename__ = "status_history"

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey("reports.id"), nullable=False)
    old_status = db.Column(db.String(30))
    new_status = db.Column(db.String(30), nullable=False)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    report = db.relationship("Report", back_populates="history")
    user = db.relationship("User")


class OptimizationRun(db.Model):
    __tablename__ = "optimization_runs"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    report_ids = db.Column(db.Text)  # comma-separated ordered ids
    estimated_distance_km = db.Column(db.Float)
    notes = db.Column(db.String(255))

    created_by = db.relationship("User")
