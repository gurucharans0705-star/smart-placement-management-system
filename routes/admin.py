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
from datetime import datetime
from flask import Blueprint, render_template, session, redirect, url_for, flash, request

from models.admin import (
    get_dashboard_stats,
    get_recent_students,
    get_recent_companies,
    get_recent_applications,
    get_companies_paginated,
    get_company_by_id,
    create_company,
    update_company,
    delete_company,
    toggle_company_status,
    get_applications_paginated,
    get_application_by_id,
    update_application_status,
    get_all_companies_list,
    APPLICATION_STATUSES,
)

# Departments offered for the "Eligible Departments" checkboxes.
# Kept in one place so Add/Edit forms and validation stay in sync.
DEPARTMENT_OPTIONS = ["CSE", "IT", "ECE", "EEE", "MECH", "CIVIL"]

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
# COMPANY MANAGEMENT (Step 7)
# ------------------------------------------------------------

def _validate_company_form(form):
    """
    Validates the Add/Edit Company form.
    Returns (errors: list[str], cleaned_data: dict | None).
    Keeping this in one place means Add and Edit always apply
    the exact same rules.
    """
    errors = []

    company_name = form.get("company_name", "").strip()
    job_role = form.get("job_role", "").strip()
    location = form.get("location", "").strip()
    package_lpa = form.get("package_lpa", "").strip()
    min_cgpa = form.get("min_cgpa", "").strip()
    max_backlogs = form.get("max_backlogs", "").strip()
    last_date = form.get("last_date", "").strip()
    eligible_batch_years = form.get("eligible_batch_years", "").strip()
    description = form.get("description", "").strip()
    is_active = 1 if form.get("is_active") == "active" else 0
    departments = form.getlist("allowed_departments")  # checkboxes -> list

    # ---- Required text fields ----
    if not company_name:
        errors.append("Company Name is required.")
    if not job_role:
        errors.append("Job Role is required.")
    if not location:
        errors.append("Location is required.")
    if not departments:
        errors.append("Select at least one Eligible Department.")
    elif any(d not in DEPARTMENT_OPTIONS for d in departments):
        errors.append("Invalid department selected.")

    # ---- Numeric fields ----
    package_val = None
    if not package_lpa:
        errors.append("Package is required.")
    else:
        try:
            package_val = float(package_lpa)
            if package_val < 0:
                errors.append("Package cannot be negative.")
        except ValueError:
            errors.append("Package must be a valid number.")

    cgpa_val = None
    if not min_cgpa:
        errors.append("Minimum CGPA is required.")
    else:
        try:
            cgpa_val = float(min_cgpa)
            if not (0 <= cgpa_val <= 10):
                errors.append("Minimum CGPA must be between 0 and 10.")
        except ValueError:
            errors.append("Minimum CGPA must be a valid number.")

    backlogs_val = None
    if max_backlogs == "":
        errors.append("Maximum Backlogs is required.")
    else:
        try:
            backlogs_val = int(max_backlogs)
            if backlogs_val < 0:
                errors.append("Maximum Backlogs cannot be negative.")
        except ValueError:
            errors.append("Maximum Backlogs must be a whole number.")

    # ---- Application Deadline ----
    if not last_date:
        errors.append("Application Deadline is required.")
    else:
        try:
            datetime.strptime(last_date, "%Y-%m-%d")
        except ValueError:
            errors.append("Application Deadline must be a valid date.")

    # ---- Passing Years (optional, comma-separated 4-digit years) ----
    if eligible_batch_years:
        years = [y.strip() for y in eligible_batch_years.split(",") if y.strip()]
        for y in years:
            if not (y.isdigit() and len(y) == 4):
                errors.append("Passing Years must be comma-separated 4-digit years, e.g. 2026,2027.")
                break
        eligible_batch_years = ",".join(years)
    else:
        eligible_batch_years = None

    if errors:
        return errors, None

    cleaned_data = {
        "company_name": company_name,
        "job_role": job_role,
        "location": location,
        "package_lpa": package_val,
        "min_cgpa": cgpa_val,
        "max_backlogs": backlogs_val,
        "allowed_departments": ",".join(departments),
        "eligible_batch_years": eligible_batch_years,
        "last_date": last_date,
        "description": description,
        "is_active": is_active,
    }
    return [], cleaned_data


@admin_bp.route("/companies")
@login_required
def companies():
    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1
    per_page = 10

    company_list, total_count = get_companies_paginated(search=search, page=page, per_page=per_page)
    total_pages = max(1, (total_count + per_page - 1) // per_page)

    return render_template(
        "admin/companies.html",
        companies=company_list,
        search=search,
        page=page,
        total_pages=total_pages,
        total_count=total_count,
    )


@admin_bp.route("/companies/add", methods=["GET", "POST"])
@login_required
def add_company():
    if request.method == "POST":
        errors, data = _validate_company_form(request.form)
        # Normalize the submitted form into a plain dict with
        # allowed_departments as a real list, so the template's
        # department-checkbox logic is identical on GET and POST.
        form_data = request.form.to_dict()
        form_data["allowed_departments"] = request.form.getlist("allowed_departments")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "admin/add_company.html",
                departments=DEPARTMENT_OPTIONS,
                form=form_data,
            )

        success, message = create_company(data)
        flash(message, "success" if success else "error")
        if success:
            return redirect(url_for("admin.companies"))
        return render_template(
            "admin/add_company.html",
            departments=DEPARTMENT_OPTIONS,
            form=form_data,
        )

    return render_template(
        "admin/add_company.html",
        departments=DEPARTMENT_OPTIONS,
        form={"allowed_departments": []},
    )


@admin_bp.route("/companies/edit/<int:company_id>", methods=["GET", "POST"])
@login_required
def edit_company(company_id):
    company = get_company_by_id(company_id)
    if not company:
        flash("Company not found.", "error")
        return redirect(url_for("admin.companies"))

    if request.method == "POST":
        errors, data = _validate_company_form(request.form)
        form_data = request.form.to_dict()
        form_data["allowed_departments"] = request.form.getlist("allowed_departments")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template(
                "admin/edit_company.html",
                departments=DEPARTMENT_OPTIONS,
                company=company,
                form=form_data,
            )

        success, message = update_company(company_id, data)
        flash(message, "success" if success else "error")
        if success:
            return redirect(url_for("admin.companies"))
        return render_template(
            "admin/edit_company.html",
            departments=DEPARTMENT_OPTIONS,
            company=company,
            form=form_data,
        )

    # GET: pre-fill the form with existing company data.
    # allowed_departments is stored as "CSE,IT" - split it into a list
    # so the template can check the right boxes.
    form = dict(company)
    form["allowed_departments"] = (company["allowed_departments"] or "").split(",")
    # Format dates as YYYY-MM-DD for <input type="date">
    if company.get("last_date"):
        form["last_date"] = company["last_date"].strftime("%Y-%m-%d")

    return render_template(
        "admin/edit_company.html",
        departments=DEPARTMENT_OPTIONS,
        company=company,
        form=form,
    )


@admin_bp.route("/companies/delete/<int:company_id>", methods=["POST"])
@login_required
def delete_company_route(company_id):
    success, message = delete_company(company_id)
    flash(message, "success" if success else "error")
    return redirect(url_for("admin.companies"))


@admin_bp.route("/companies/toggle/<int:company_id>", methods=["POST"])
@login_required
def toggle_company_status_route(company_id):
    success, message = toggle_company_status(company_id)
    flash(message, "success" if success else "error")
    return redirect(url_for("admin.companies"))


# ------------------------------------------------------------
# PLACEHOLDER PAGES (nav menu targets - full features arrive in
# their own upcoming steps: Placement Drives management,
# Applications management, Students list, Notifications composer)
# ------------------------------------------------------------
@admin_bp.route("/drives")
@login_required
def drives():
    return render_template("admin/drives.html")


# ------------------------------------------------------------
# APPLICATIONS MANAGEMENT (Step 8)
# ------------------------------------------------------------
@admin_bp.route("/applications")
@login_required
def applications():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    company_id = request.args.get("company_id", type=int)
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1
    per_page = 10

    application_list, total_count = get_applications_paginated(
        search=search, status=status, company_id=company_id, page=page, per_page=per_page
    )
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    company_options = get_all_companies_list()

    return render_template(
        "admin/applications.html",
        applications=application_list,
        statuses=APPLICATION_STATUSES,
        company_options=company_options,
        search=search,
        status=status,
        company_id=company_id,
        page=page,
        total_pages=total_pages,
        total_count=total_count,
    )


@admin_bp.route("/applications/<int:application_id>")
@login_required
def view_application(application_id):
    application = get_application_by_id(application_id)
    if not application:
        flash("Application not found.", "error")
        return redirect(url_for("admin.applications"))

    return render_template(
        "admin/view_application.html",
        application=application,
        statuses=APPLICATION_STATUSES,
    )


@admin_bp.route("/applications/<int:application_id>/update-status", methods=["POST"])
@login_required
def update_application_status_route(application_id):
    new_status = request.form.get("status", "").strip()

    success, message = update_application_status(application_id, new_status)
    flash(message, "success" if success else "error")

    # Preserve whatever search/filter/page the admin was on, so
    # updating a status doesn't reset their place in the list.
    # These are passed as hidden fields in the status-update form.
    redirect_args = {
        "search": request.form.get("search", ""),
        "status": request.form.get("filter_status", ""),
        "page": request.form.get("page", 1),
    }
    company_id = request.form.get("company_id", "")
    if company_id:
        redirect_args["company_id"] = company_id

    # If this update came from the details page, go back there instead.
    if request.form.get("return_to") == "details":
        return redirect(url_for("admin.view_application", application_id=application_id))

    return redirect(url_for("admin.applications", **redirect_args))


@admin_bp.route("/students")
@login_required
def students():
    return render_template("admin/students.html")


@admin_bp.route("/notifications")
@login_required
def notifications():
    return render_template("admin/notifications.html")
