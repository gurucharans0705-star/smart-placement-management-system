# ============================================================
# routes/admin.py
# Admin-facing routes.
#
# NOTE: This is currently a placeholder for Step 4 (Authentication)
# so that login redirects work end-to-end. Full dashboard features
# (company management, applicant lists, status updates) will be
# added in the "Admin Dashboard" step.
# ============================================================

from flask import Blueprint, render_template, session, redirect, url_for, flash

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def login_required(f):
    """Simple decorator to protect admin-only routes."""
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.admin_login"))
        return f(*args, **kwargs)
    return wrapper


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    # Placeholder dashboard - will be expanded in a later step.
    return render_template("admin/dashboard.html", name=session.get("admin_name"))
