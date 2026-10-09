from flask import Blueprint, render_template

from app.extensions import db
from app.models import Report

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    """Public landing page — always shown (even when signed in)."""
    try:
        total = Report.query.count()
        collected = Report.query.filter_by(status="completed").count()
        open_now = Report.query.filter(
            Report.status.notin_(["completed", "rejected"])
        ).count()
    except Exception:
        # Table may not exist yet on a fresh instance — render honest zeros.
        total = collected = open_now = 0
    stats = {"total": total, "collected": collected, "open_now": open_now}
    return render_template("main/home.html", stats=stats)


@main_bp.route("/about")
def about():
    return render_template("main/about.html")


@main_bp.route("/faq")
def faq():
    return render_template("main/faq.html")
