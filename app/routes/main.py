from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for("admin.dashboard"))
        if current_user.is_officer:
            return redirect(url_for("officer.dashboard"))
        return redirect(url_for("resident.dashboard"))
    return render_template("main/home.html")


@main_bp.route("/about")
def about():
    return render_template("main/about.html")
