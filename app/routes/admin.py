from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, or_

from app.extensions import db
from app.models import OptimizationRun, Report, User
from app.services.optimization import manual_path_distance, order_reports
from app.utils import role_required, transition_status

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@login_required
@role_required("admin")
def dashboard():
    total = Report.query.count()
    submitted = Report.query.filter_by(status="submitted").count()
    open_reports = Report.query.filter(
        Report.status.notin_(["completed", "rejected"])
    ).count()
    completed = Report.query.filter_by(status="completed").count()
    high = Report.query.filter(
        Report.urgency == "high", Report.status.notin_(["completed", "rejected"])
    ).count()
    recent = Report.query.order_by(Report.created_at.desc()).limit(8).all()
    map_reports = (
        Report.query.filter(Report.status.notin_(["completed", "rejected"]))
        .order_by(Report.created_at.desc())
        .limit(100)
        .all()
    )
    return render_template(
        "admin/dashboard.html",
        total=total,
        submitted=submitted,
        open_reports=open_reports,
        completed=completed,
        high=high,
        recent=recent,
        map_reports=map_reports,
    )


@admin_bp.route("/reports")
@login_required
@role_required("admin")
def reports():
    status = request.args.get("status")
    category = request.args.get("category")
    urgency = request.args.get("urgency")
    q = request.args.get("q", "").strip()

    query = Report.query
    if status:
        query = query.filter_by(status=status)
    if category:
        query = query.filter_by(category=category)
    if urgency:
        query = query.filter_by(urgency=urgency)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Report.tracking_code.ilike(like),
                Report.description.ilike(like),
                Report.address.ilike(like),
            )
        )
    items = query.order_by(Report.created_at.desc()).all()
    return render_template(
        "admin/reports.html",
        reports=items,
        statuses=Report.STATUSES,
        categories=Report.CATEGORIES,
        urgencies=Report.URGENCIES,
        filters={"status": status, "category": category, "urgency": urgency, "q": q},
    )


@admin_bp.route("/reports/<int:report_id>", methods=["GET", "POST"])
@login_required
@role_required("admin")
def report_detail(report_id):
    report = Report.query.get_or_404(report_id)
    officers = User.query.filter_by(role="officer", is_active_user=True).order_by(User.name).all()

    if request.method == "POST":
        action = request.form.get("action")
        note = (request.form.get("note") or "").strip()
        urgency = request.form.get("urgency")
        officer_id = request.form.get("officer_id")
        scheduled_date = request.form.get("scheduled_date")

        if urgency in Report.URGENCIES:
            report.urgency = urgency

        if action == "verify" and report.status == "submitted":
            transition_status(report, "verified", current_user, note=note or "Verified by admin")
            flash("Report verified.", "success")
        elif action == "reject" and report.status in ("submitted", "verified"):
            transition_status(report, "rejected", current_user, note=note or "Rejected by admin")
            flash("Report rejected.", "warning")
        elif action == "assign":
            if not officer_id:
                flash("Select a collection officer.", "danger")
            else:
                report.officer_id = int(officer_id)
                report.assigned_by_id = current_user.id
                if report.status in ("submitted", "verified", "assigned", "scheduled"):
                    transition_status(
                        report,
                        "assigned",
                        current_user,
                        note=note or f"Assigned to officer #{officer_id}",
                    )
                flash("Officer assigned.", "success")
        elif action == "schedule":
            if scheduled_date:
                try:
                    report.scheduled_date = datetime.strptime(scheduled_date, "%Y-%m-%d").date()
                except ValueError:
                    flash("Invalid date format.", "danger")
                    return redirect(url_for("admin.report_detail", report_id=report.id))
            if report.status in ("submitted", "verified", "assigned", "scheduled"):
                if report.status == "submitted":
                    transition_status(report, "verified", current_user, note="Auto-verified for schedule")
                transition_status(
                    report,
                    "scheduled",
                    current_user,
                    note=note or f"Scheduled for {report.scheduled_date}",
                )
            flash("Report scheduled.", "success")
        elif action == "note":
            report.admin_notes = note
            if note:
                transition_status(report, report.status, current_user, note=note)
            flash("Note saved.", "success")
        elif action == "reopen" and report.status in ("rejected", "completed"):
            transition_status(report, "submitted", current_user, note=note or "Reopened by admin")
            flash("Report reopened.", "info")
        else:
            flash("No valid action applied.", "warning")

        db.session.commit()
        return redirect(url_for("admin.report_detail", report_id=report.id))

    return render_template("admin/report_detail.html", report=report, officers=officers)


@admin_bp.route("/schedule")
@login_required
@role_required("admin")
def schedule():
    date_str = request.args.get("date")
    query = Report.query.filter(
        Report.status.in_(["assigned", "scheduled", "in_progress"]),
        Report.scheduled_date.isnot(None),
    )
    if date_str:
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
            query = query.filter(Report.scheduled_date == d)
        except ValueError:
            flash("Invalid date filter.", "warning")
    items = query.order_by(
        Report.scheduled_date.asc(),
        Report.collection_order.asc(),
        Report.created_at.asc(),
    ).all()
    return render_template("admin/schedule.html", reports=items, date_str=date_str or "")


@admin_bp.route("/optimize", methods=["GET", "POST"])
@login_required
@role_required("admin")
def optimize():
    candidates = (
        Report.query.filter(Report.status.in_(["verified", "assigned", "scheduled"]))
        .order_by(Report.created_at.asc())
        .all()
    )

    result = None
    manual_distance = None
    selected_ids = []

    if request.method == "POST":
        selected_ids = [int(x) for x in request.form.getlist("report_ids")]
        selected = Report.query.filter(Report.id.in_(selected_ids)).all() if selected_ids else []
        if len(selected) < 1:
            flash("Select at least one report to optimize.", "warning")
        else:
            # Manual baseline: current order by id / created_at
            manual_order = sorted(selected, key=lambda r: r.created_at or datetime.min)
            manual_distance = manual_path_distance(manual_order)
            ordered, distance = order_reports(selected)
            for idx, r in enumerate(ordered, start=1):
                r.collection_order = idx
            run = OptimizationRun(
                created_by_id=current_user.id,
                report_ids=",".join(str(r.id) for r in ordered),
                estimated_distance_km=distance,
                notes=f"Optimized {len(ordered)} stops",
            )
            db.session.add(run)
            apply_schedule = request.form.get("apply_schedule")
            schedule_date = request.form.get("schedule_date")
            if apply_schedule and schedule_date:
                try:
                    d = datetime.strptime(schedule_date, "%Y-%m-%d").date()
                    for r in ordered:
                        r.scheduled_date = d
                        if r.status in ("verified", "assigned", "scheduled"):
                            transition_status(
                                r,
                                "scheduled",
                                current_user,
                                note=f"Scheduled via optimization for {d}",
                            )
                except ValueError:
                    flash("Invalid schedule date; order saved without scheduling.", "warning")
            db.session.commit()
            result = {"ordered": ordered, "distance": distance, "manual_distance": manual_distance}
            flash(
                f"Optimization complete. Estimated path: {distance} km "
                f"(manual order: {manual_distance} km).",
                "success",
            )

    recent_runs = OptimizationRun.query.order_by(OptimizationRun.created_at.desc()).limit(5).all()
    return render_template(
        "admin/optimize.html",
        candidates=candidates,
        result=result,
        selected_ids=selected_ids,
        recent_runs=recent_runs,
    )


@admin_bp.route("/analytics")
@login_required
@role_required("admin")
def analytics():
    by_status = (
        db.session.query(Report.status, func.count(Report.id)).group_by(Report.status).all()
    )
    by_category = (
        db.session.query(Report.category, func.count(Report.id)).group_by(Report.category).all()
    )
    by_urgency = (
        db.session.query(Report.urgency, func.count(Report.id)).group_by(Report.urgency).all()
    )

    completed = Report.query.filter(
        Report.status == "completed", Report.completed_at.isnot(None)
    ).all()
    response_hours = []
    for r in completed:
        if r.created_at and r.completed_at:
            delta = (r.completed_at - r.created_at).total_seconds() / 3600.0
            response_hours.append(delta)
    avg_response = round(sum(response_hours) / len(response_hours), 2) if response_hours else None

    with_location = Report.query.filter(
        Report.latitude.isnot(None), Report.longitude.isnot(None)
    ).all()
    complete_fields = 0
    for r in with_location:
        if r.category and r.description and r.status:
            complete_fields += 1
    data_completeness = (
        round(100.0 * complete_fields / len(with_location), 1) if with_location else 0
    )

    hotspot_reports = (
        Report.query.filter(Report.status.notin_(["rejected"]))
        .order_by(Report.created_at.desc())
        .limit(200)
        .all()
    )

    return render_template(
        "admin/analytics.html",
        by_status=by_status,
        by_category=by_category,
        by_urgency=by_urgency,
        avg_response=avg_response,
        completed_count=len(completed),
        data_completeness=data_completeness,
        total=Report.query.count(),
        hotspot_reports=hotspot_reports,
    )


@admin_bp.route("/officers", methods=["GET", "POST"])
@login_required
@role_required("admin")
def officers():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        phone = (request.form.get("phone") or "").strip()
        password = request.form.get("password") or "officer123"
        if not name or not email:
            flash("Name and email are required.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("Email already in use.", "danger")
        else:
            user = User(name=name, email=email, phone=phone, role="officer")
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash(f"Officer {name} created. Temporary password: {password}", "success")
        return redirect(url_for("admin.officers"))

    officers_list = User.query.filter_by(role="officer").order_by(User.name).all()
    return render_template("admin/officers.html", officers=officers_list)


@admin_bp.route("/officers/<int:user_id>/toggle", methods=["POST"])
@login_required
@role_required("admin")
def toggle_officer(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != "officer":
        flash("Not an officer account.", "danger")
    else:
        user.is_active_user = not user.is_active_user
        db.session.commit()
        flash(f"{user.name} is now {'active' if user.is_active_user else 'inactive'}.", "info")
    return redirect(url_for("admin.officers"))
