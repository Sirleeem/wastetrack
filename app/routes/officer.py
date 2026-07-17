from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Report
from app.utils import role_required, transition_status

officer_bp = Blueprint("officer", __name__, url_prefix="/officer")


@officer_bp.route("/dashboard")
@login_required
@role_required("officer")
def dashboard():
    tasks = (
        Report.query.filter_by(officer_id=current_user.id)
        .filter(Report.status.in_(["assigned", "scheduled", "in_progress"]))
        .order_by(Report.urgency.desc(), Report.scheduled_date.asc(), Report.created_at.asc())
        .all()
    )
    completed = (
        Report.query.filter_by(officer_id=current_user.id, status="completed")
        .order_by(Report.completed_at.desc())
        .limit(5)
        .all()
    )
    return render_template(
        "officer/dashboard.html",
        tasks=tasks,
        completed=completed,
        active_count=len(tasks),
    )


@officer_bp.route("/tasks")
@login_required
@role_required("officer")
def tasks():
    status = request.args.get("status")
    q = Report.query.filter_by(officer_id=current_user.id)
    if status:
        q = q.filter_by(status=status)
    items = q.order_by(Report.updated_at.desc()).all()
    return render_template("officer/tasks.html", tasks=items, status=status)


@officer_bp.route("/tasks/<int:report_id>", methods=["GET", "POST"])
@login_required
@role_required("officer")
def task_detail(report_id):
    report = Report.query.get_or_404(report_id)
    if report.officer_id != current_user.id:
        flash("This task is not assigned to you.", "danger")
        return redirect(url_for("officer.tasks"))

    if request.method == "POST":
        action = request.form.get("action")
        note = (request.form.get("note") or "").strip()
        if action == "start" and report.status in ("assigned", "scheduled"):
            transition_status(report, "in_progress", current_user, note=note or "Collection started")
            db.session.commit()
            flash("Task marked as in progress.", "success")
        elif action == "complete" and report.status in ("assigned", "scheduled", "in_progress"):
            transition_status(
                report, "completed", current_user, note=note or "Collection completed"
            )
            db.session.commit()
            flash("Task completed. Thank you.", "success")
        else:
            flash("Invalid action for current status.", "warning")
        return redirect(url_for("officer.task_detail", report_id=report.id))

    return render_template("officer/task_detail.html", report=report)


@officer_bp.route("/profile", methods=["GET", "POST"])
@login_required
@role_required("officer")
def profile():
    if request.method == "POST":
        current_user.name = (request.form.get("name") or current_user.name).strip()
        current_user.phone = (request.form.get("phone") or "").strip()
        password = request.form.get("password") or ""
        if password:
            if len(password) < 6:
                flash("Password must be at least 6 characters.", "danger")
                return render_template("officer/profile.html")
            current_user.set_password(password)
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("officer.profile"))
    return render_template("officer/profile.html")
