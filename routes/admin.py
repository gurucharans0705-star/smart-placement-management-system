# ============================================================
# routes/admin.py
# Admin-facing routes.
#
# This step (Admin Dashboard) fully implements the dashboard
# route. The nav menu also links to Companies, Placement Drives,
# Applications, Students, and Notifications - those are wired up
# here as lightweight placeholder pages so the navigation works
# end-to-end today. Each will be fully built out in its own
# upcoming step (Company Management, etc.) without needing any
# changes to this login_required decorator or the routes already
# built.
# ============================================================

from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for, flash

from models.admin import (
    get_dashboard_stats,
    get_recent_students,
    get_recent_companies,
    get_recent_applications,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def login_required(f):
    """Simple decorator to protect admin-only routes. (Unchanged from Step 4.)"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.admin_login"))
        return f(*args, **kwargs)
    return wrapper


# ------------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------------
@admin_bp.route("/dashboard")
@login_required
def dashboard():
    stats = get_dashboard_stats()
    recent_students = get_recent_students(limit=5)
    recent_companies = get_recent_companies(limit=5)
    recent_applications = get_recent_applications(limit=5)

    return render_template(
        "admin/dashboard.html",
        name=session.get("admin_name"),
        stats=stats,
        recent_students=recent_students,
        recent_companies=recent_companies,
        recent_applications=recent_applications,
    )


# ------------------------------------------------------------
# PLACEHOLDER PAGES (nav menu targets - full features arrive in
# their own upcoming steps: Company Management, Placement Drives
# management, Applications management, Students list,
# Notifications composer)
# ------------------------------------------------------------
@admin_bp.route("/companies")
@login_required
def companies():
    return render_template("admin/companies.html")


@admin_bp.route("/drives")
@login_required
def drives():
    return render_template("admin/drives.html")


@admin_bp.route("/applications")
@login_required
def applications():
    return render_template("admin/applications.html")


@admin_bp.route("/students")
@login_required
def students():
    return render_template("admin/students.html")


@admin_bp.route("/notifications")
@login_required
def notifications():
    return render_template("admin/notifications.html")
