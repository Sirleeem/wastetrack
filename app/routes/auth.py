from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("No account found with that email. Register as a resident, or create admin/officer via /auth/setup.", "danger")
        elif not user.is_active_user:
            flash("This account is inactive. Contact an administrator.", "danger")
        elif not user.check_password(password):
            flash("Incorrect password for that email.", "danger")
        else:
            login_user(user, remember=bool(request.form.get("remember")))
            flash(f"Welcome back, {user.name} ({user.role}).", "success")
            next_url = request.args.get("next")
            if next_url:
                return redirect(next_url)
            # After login go to role workspace (homepage stays public via logo/Home)
            if user.is_admin:
                return redirect(url_for("admin.dashboard"))
            if user.is_officer:
                return redirect(url_for("officer.dashboard"))
            return redirect(url_for("resident.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

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
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "danger")
        else:
            user = User(name=name, email=email, phone=phone, role="resident")
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Account created. You can now submit waste reports.", "success")
            return redirect(url_for("resident.dashboard"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.home"))


@auth_bp.route("/setup", methods=["GET", "POST"])
def setup():
    """Create admin or officer without being logged in.

    Protect with SETUP_SECRET env var (Render → Environment).
    Open: /auth/setup?key=YOUR_SETUP_SECRET
    """
    expected = (current_app.config.get("SETUP_SECRET") or "").strip()
    provided = (
        (request.args.get("key") or request.form.get("setup_key") or "").strip()
    )

    # Allow setup without secret only if there is no admin yet
    has_admin = User.query.filter_by(role="admin").first() is not None
    secret_ok = bool(expected) and provided == expected
    open_bootstrap = not has_admin and not expected

    if has_admin and not secret_ok:
        flash(
            "Setup is locked. Set SETUP_SECRET in Render, then open "
            "/auth/setup?key=YOUR_SECRET",
            "warning",
        )
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        if has_admin and not secret_ok:
            flash("Invalid setup key.", "danger")
            return redirect(url_for("auth.login"))

        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        role = (request.form.get("role") or "admin").strip().lower()
        if role not in ("admin", "officer"):
            role = "admin"

        if not name or not email or not password:
            flash("Name, email and password are required.", "danger")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
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
            flash(
                f"{role.title()} account {action}: {email}. You can sign in now.",
                "success",
            )
            return redirect(url_for("auth.login"))

    return render_template(
        "auth/setup.html",
        needs_key=has_admin or bool(expected),
        open_bootstrap=open_bootstrap,
    )
