from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Report
from app.utils import generate_tracking_code, role_required, save_upload, transition_status

resident_bp = Blueprint("resident", __name__, url_prefix="/resident")


@resident_bp.route("/dashboard")
@login_required
@role_required("resident")
def dashboard():
    reports = (
        Report.query.filter_by(reporter_id=current_user.id)
        .order_by(Report.created_at.desc())
        .limit(10)
        .all()
    )
    total = Report.query.filter_by(reporter_id=current_user.id).count()
    open_count = Report.query.filter(
        Report.reporter_id == current_user.id,
        Report.status.notin_(["completed", "rejected"]),
    ).count()
    completed = Report.query.filter_by(reporter_id=current_user.id, status="completed").count()
    return render_template(
        "resident/dashboard.html",
        reports=reports,
        total=total,
        open_count=open_count,
        completed=completed,
    )


@resident_bp.route("/reports")
@login_required
@role_required("resident")
def reports():
    items = (
        Report.query.filter_by(reporter_id=current_user.id)
        .order_by(Report.created_at.desc())
        .all()
    )
    return render_template("resident/reports.html", reports=items)


@resident_bp.route("/reports/new", methods=["GET", "POST"])
@login_required
@role_required("resident")
def new_report():
    if request.method == "POST":
        category = request.form.get("category") or "other"
        description = (request.form.get("description") or "").strip()
        address = (request.form.get("address") or "").strip()
        urgency = request.form.get("urgency") or "medium"
        try:
            latitude = float(request.form.get("latitude") or 0)
            longitude = float(request.form.get("longitude") or 0)
        except ValueError:
            latitude = longitude = 0

        if category not in Report.CATEGORIES:
            category = "other"
        if urgency not in Report.URGENCIES:
            urgency = "medium"

        if not description:
            flash("Please describe the waste issue.", "danger")
        elif not latitude or not longitude:
            flash("Please set a location on the map.", "danger")
        else:
            image_name = save_upload(request.files.get("image"))
            report = Report(
                tracking_code=generate_tracking_code(),
                category=category,
                description=description,
                address=address or None,
                latitude=latitude,
                longitude=longitude,
                image_filename=image_name,
                urgency=urgency,
                status="submitted",
                reporter_id=current_user.id,
            )
            db.session.add(report)
            db.session.flush()
            transition_status(report, "submitted", current_user, note="Report submitted by resident")
            db.session.commit()
            flash(f"Report submitted. Tracking code: {report.tracking_code}", "success")
            return redirect(url_for("resident.report_detail", report_id=report.id))

    return render_template(
        "resident/new_report.html",
        categories=Report.CATEGORIES,
        urgencies=Report.URGENCIES,
    )


@resident_bp.route("/reports/<int:report_id>")
@login_required
@role_required("resident")
def report_detail(report_id):
    report = Report.query.get_or_404(report_id)
    if report.reporter_id != current_user.id:
        flash("You can only view your own reports.", "danger")
        return redirect(url_for("resident.reports"))
    return render_template("resident/report_detail.html", report=report)


@resident_bp.route("/profile", methods=["GET", "POST"])
@login_required
@role_required("resident")
def profile():
    if request.method == "POST":
        current_user.name = (request.form.get("name") or current_user.name).strip()
        current_user.phone = (request.form.get("phone") or "").strip()
        password = request.form.get("password") or ""
        if password:
            if len(password) < 6:
                flash("Password must be at least 6 characters.", "danger")
                return render_template("resident/profile.html")
            current_user.set_password(password)
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("resident.profile"))
    return render_template("resident/profile.html")
