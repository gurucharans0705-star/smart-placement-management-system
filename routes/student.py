# ============================================================
# routes/student.py
# Student-facing routes.
#
# NOTE: This is currently a placeholder for Step 4 (Authentication)
# so that login redirects work end-to-end. Full dashboard features
# (eligible companies, apply, resume upload, application status)
# will be added in the "Student Dashboard" step.
# ============================================================

from flask import Blueprint, render_template, session, redirect, url_for, flash

student_bp = Blueprint("student", __name__, url_prefix="/student")


def login_required(f):
    """Simple decorator to protect student-only routes."""
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        if "student_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.student_login"))
        return f(*args, **kwargs)
    return wrapper


@student_bp.route("/dashboard")
@login_required
def dashboard():
    # Placeholder dashboard - will be expanded in a later step.
    return render_template("student/dashboard.html", name=session.get("student_name"))
