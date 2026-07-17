import os
import secrets
import string
from functools import wraps

from flask import abort, current_app, flash, redirect, url_for
from flask_login import current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import StatusHistory, utcnow


def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if current_user.role not in roles:
                flash("You do not have permission to access that page.", "danger")
                return redirect(url_for("main.home"))
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def allowed_file(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


def save_upload(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        return None
    original = secure_filename(file_storage.filename)
    token = secrets.token_hex(8)
    name = f"{token}_{original}"
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], name)
    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    file_storage.save(path)
    return name


def generate_tracking_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "WM-" + "".join(secrets.choice(alphabet) for _ in range(8))


def transition_status(report, new_status: str, user, note: str | None = None) -> None:
    old = report.status
    if old == new_status and not note:
        return
    report.status = new_status
    report.updated_at = utcnow()
    if new_status == "completed":
        report.completed_at = utcnow()
    history = StatusHistory(
        report_id=report.id,
        old_status=old,
        new_status=new_status,
        note=note,
        user_id=user.id if user else None,
    )
    db.session.add(history)


def status_badge_class(status: str) -> str:
    mapping = {
        "submitted": "secondary",
        "verified": "info",
        "rejected": "danger",
        "assigned": "primary",
        "scheduled": "warning",
        "in_progress": "orange",
        "completed": "success",
    }
    return mapping.get(status, "secondary")


def urgency_badge_class(urgency: str) -> str:
    return {"high": "danger", "medium": "warning", "low": "success"}.get(
        (urgency or "medium").lower(), "secondary"
    )
