# ============================================================
# routes/student.py
# Student-facing routes: Dashboard, Resume Upload, Eligible
# Companies, Placement Drives, Apply, Application History,
# Notifications.
#
# NOTE: login_required and the "student.dashboard" endpoint
# name are kept exactly as before (Step 4) so nothing that
# already links to them - e.g. templates/base.html and
# routes/auth.py's redirect after login - breaks.
# ============================================================

import os
from functools import wraps
from flask import (
    Blueprint, render_template, session, redirect, url_for,
    flash, request, current_app
)
from werkzeug.utils import secure_filename

from config import Config
from models.student import (
    get_student_by_id,
    update_resume_path,
    calculate_profile_completion,
    get_eligible_companies,
    get_active_drives,
    has_applied,
    apply_to_company,
    get_applications_for_student,
    get_dashboard_stats,
    get_notifications_for_student,
)

student_bp = Blueprint("student", __name__, url_prefix="/student")


def login_required(f):
    """Simple decorator to protect student-only routes. (Unchanged from Step 4.)"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "student_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.student_login"))
        return f(*args, **kwargs)
    return wrapper


def _allowed_resume_file(filename):
    """Check the uploaded file has a .pdf extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    )


# ------------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------------
@student_bp.route("/dashboard")
@login_required
def dashboard():
    student = get_student_by_id(session["student_id"])
    if not student:
        flash("Student profile not found.", "error")
        return redirect(url_for("auth.logout"))

    profile_completion = calculate_profile_completion(student)
    stats = get_dashboard_stats(student)
    recent_notifications = get_notifications_for_student(student["student_id"], limit=3)

    return render_template(
        "student/dashboard.html",
        student=student,
        profile_completion=profile_completion,
        stats=stats,
        recent_notifications=recent_notifications,
    )


# ------------------------------------------------------------
# RESUME UPLOAD
# ------------------------------------------------------------
@student_bp.route("/resume/upload", methods=["POST"])
@login_required
def upload_resume():
    student_id = session["student_id"]

    if "resume" not in request.files:
        flash("No file selected.", "error")
        return redirect(url_for("student.dashboard"))

    file = request.files["resume"]

    if file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("student.dashboard"))

    if not _allowed_resume_file(file.filename):
        flash("Only PDF files are allowed for resumes.", "error")
        return redirect(url_for("student.dashboard"))

    # Standardize the filename per student (e.g. student_12.pdf).
    # Saving under the SAME name each time automatically replaces
    # the old resume file on disk.
    filename = secure_filename(f"student_{student_id}.pdf")

    # Build the absolute folder path on disk, and make sure it exists.
    upload_folder_abs = os.path.join(current_app.root_path, Config.UPLOAD_FOLDER)
    os.makedirs(upload_folder_abs, exist_ok=True)

    file_path_abs = os.path.join(upload_folder_abs, filename)
    file.save(file_path_abs)

    # Store the path RELATIVE to the static/ folder in the DB so
    # templates can use url_for('static', filename=resume_path).
    relative_path = os.path.join("uploads", "resumes", filename).replace("\\", "/")

    if update_resume_path(student_id, relative_path):
        flash("Resume uploaded successfully!", "success")
    else:
        flash("Resume upload failed. Please try again.", "error")

    return redirect(url_for("student.dashboard"))


# ------------------------------------------------------------
# ELIGIBLE COMPANIES
# ------------------------------------------------------------
@student_bp.route("/companies")
@login_required
def companies():
    student = get_student_by_id(session["student_id"])
    if not student:
        flash("Student profile not found.", "error")
        return redirect(url_for("auth.logout"))

    eligible_companies = get_eligible_companies(student)
    applied_ids = {
        app["company_id"] for app in get_applications_for_student(student["student_id"])
    }

    return render_template(
        "student/companies.html",
        companies=eligible_companies,
        applied_ids=applied_ids,
    )


# ------------------------------------------------------------
# PLACEMENT DRIVES (all active drives, with eligibility shown)
# ------------------------------------------------------------
@student_bp.route("/drives")
@login_required
def drives():
    student = get_student_by_id(session["student_id"])
    if not student:
        flash("Student profile not found.", "error")
        return redirect(url_for("auth.logout"))

    active_drives = get_active_drives(student)
    return render_template("student/drives.html", drives=active_drives)


# ------------------------------------------------------------
# APPLY TO A COMPANY
# ------------------------------------------------------------
@student_bp.route("/apply/<int:company_id>", methods=["POST"])
@login_required
def apply(company_id):
    student_id = session["student_id"]

    if has_applied(student_id, company_id):
        flash("You have already applied to this company.", "error")
        return redirect(url_for("student.drives"))

    success, message = apply_to_company(student_id, company_id)
    flash(message, "success" if success else "error")
    return redirect(url_for("student.drives"))


# ------------------------------------------------------------
# APPLICATION HISTORY
# ------------------------------------------------------------
@student_bp.route("/applications")
@login_required
def applications():
    student_id = session["student_id"]
    application_list = get_applications_for_student(student_id)
    return render_template("student/applications.html", applications=application_list)


# ------------------------------------------------------------
# NOTIFICATIONS
# ------------------------------------------------------------
@student_bp.route("/notifications")
@login_required
def notifications():
    student_id = session["student_id"]
    notification_list = get_notifications_for_student(student_id)
    return render_template("student/notifications.html", notifications=notification_list)
