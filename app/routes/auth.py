from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db, limiter
from app.models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

MIN_PASSWORD_LEN = 8


def _dashboard_for(user: User) -> str:
    if user.is_admin:
        return url_for("admin.dashboard")
    if user.is_officer:
        return url_for("officer.dashboard")
    return url_for("resident.dashboard")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(_dashboard_for(current_user))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Invalid email or password.", "danger")
        elif not user.is_active_user:
            flash("This account is inactive.", "danger")
        elif not user.check_password(password):
            flash("Invalid email or password.", "danger")
        else:
            # Session fixation protection
            session.clear()
            session.permanent = True
            login_user(user, remember=bool(request.form.get("remember")))
            flash(f"Welcome back, {user.name}.", "success")
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(_dashboard_for(user))

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(_dashboard_for(current_user))

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        phone = (request.form.get("phone") or "").strip()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""

        if not name or not email or not password:
            flash("Name, email and password are required.", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        elif len(password) < MIN_PASSWORD_LEN:
            flash(f"Password must be at least {MIN_PASSWORD_LEN} characters.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "danger")
        else:
            user = User(name=name, email=email, phone=phone or None, role="resident")
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            session.clear()
            login_user(user)
            flash("Account created. You can now submit waste reports.", "success")
            return redirect(url_for("resident.dashboard"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.home"))


@auth_bp.route("/setup", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def setup():
    """Staff account setup. Always requires SETUP_SECRET in production presentation mode."""
    expected = (current_app.config.get("SETUP_SECRET") or "").strip()
    provided = (request.args.get("key") or request.form.get("setup_key") or "").strip()
    has_admin = User.query.filter_by(role="admin").first() is not None
    secret_ok = bool(expected) and provided == expected

    # Require SETUP_SECRET whenever it is configured; if missing and no admin, allow first admin
    if not expected and has_admin:
        return render_template("auth/setup.html", needs_key=False, setup_blocked=True)
    if expected and not secret_ok and request.method == "GET":
        return render_template(
            "auth/setup.html",
            needs_key=True,
            setup_blocked=False,
            hint_key=True,
        )
    if expected and not secret_ok and request.method == "POST":
        flash("Invalid setup key.", "danger")
        return render_template("auth/setup.html", needs_key=True, setup_blocked=False)

    if request.method == "POST":
        form_key = (request.form.get("setup_key") or "").strip()
        if expected and form_key != expected and provided != expected:
            flash("Invalid setup key.", "danger")
            return render_template("auth/setup.html", needs_key=True, setup_blocked=False)

        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        role = (request.form.get("role") or "admin").strip().lower()
        if role not in ("admin", "officer"):
            role = "admin"

        if not name or not email or not password:
            flash("Name, email and password are required.", "danger")
        elif len(password) < MIN_PASSWORD_LEN:
            flash(f"Password must be at least {MIN_PASSWORD_LEN} characters.", "danger")
        else:
            user = User.query.filter_by(email=email).first()
            if user:
                user.name = name
                user.role = role
                user.is_active_user = True
                user.set_password(password)
                action = "updated"
            else:
                user = User(name=name, email=email, role=role, is_active_user=True)
                user.set_password(password)
                db.session.add(user)
                action = "created"
            db.session.commit()
            flash(f"{role.title()} account {action}: {email}. You can sign in now.", "success")
            return redirect(url_for("auth.login"))

    return render_template(
        "auth/setup.html",
        needs_key=bool(expected),
        setup_blocked=False,
    )
