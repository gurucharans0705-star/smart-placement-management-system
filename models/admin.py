# ============================================================
# models/admin.py
# All database queries related to the Admin Dashboard live here,
# keeping routes/admin.py short and readable.
#
# NOTE: This file is NEW - it does not touch anything used by
# auth.py, models/student.py, or the existing student flow.
# ============================================================

from models.db import get_db_connection


# ------------------------------------------------------------
# DASHBOARD STATISTICS
# ------------------------------------------------------------
def get_dashboard_stats():
    """
    Returns counts for the 4 summary cards:
      - total_students
      - total_companies
      - active_companies
      - total_applications
    """
    conn = get_db_connection()
    if conn is None:
        return {
            "total_students": 0,
            "total_companies": 0,
            "active_companies": 0,
            "total_applications": 0,
        }

    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS cnt FROM students")
    total_students = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) AS cnt FROM companies")
    total_companies = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) AS cnt FROM companies WHERE is_active = 1")
    active_companies = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) AS cnt FROM applications")
    total_applications = cursor.fetchone()["cnt"]

    cursor.close()
    conn.close()

    return {
        "total_students": total_students,
        "total_companies": total_companies,
        "active_companies": active_companies,
        "total_applications": total_applications,
    }


# ------------------------------------------------------------
# RECENT ACTIVITY
# ------------------------------------------------------------
def get_recent_students(limit=5):
    """Latest registered students, newest first."""
    conn = get_db_connection()
    if conn is None:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT student_id, full_name, email, department, cgpa, created_at
        FROM students
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (limit,)
    )
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return students


def get_recent_companies(limit=5):
    """Most recently added companies/drives, newest first."""
    conn = get_db_connection()
    if conn is None:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT company_id, company_name, job_role, package_lpa, is_active, created_at
        FROM companies
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (limit,)
    )
    companies = cursor.fetchall()
    cursor.close()
    conn.close()
    return companies


def get_recent_applications(limit=5):
    """Latest applications submitted by students, newest first."""
    conn = get_db_connection()
    if conn is None:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT a.application_id, a.status, a.applied_at,
               s.full_name AS student_name, s.department,
               c.company_name, c.job_role
        FROM applications a
        JOIN students s ON a.student_id = s.student_id
        JOIN companies c ON a.company_id = c.company_id
        ORDER BY a.applied_at DESC
        LIMIT %s
        """,
        (limit,)
    )
    applications = cursor.fetchall()
    cursor.close()
    conn.close()
    return applications


# ------------------------------------------------------------
# COMPANY MANAGEMENT (Step 7)
# All queries for Add / View / Edit / Delete / Toggle Status.
# ------------------------------------------------------------

def get_companies_paginated(search="", page=1, per_page=10):
    """
    Return (companies, total_count) for the company list page.
    - search: matches against company_name or job_role (case-insensitive)
    - page/per_page: standard offset-based pagination
    """
    conn = get_db_connection()
    if conn is None:
        return [], 0

    cursor = conn.cursor(dictionary=True)

    where_clause = ""
    params = []
    if search:
        where_clause = "WHERE company_name LIKE %s OR job_role LIKE %s"
        like_term = f"%{search}%"
        params = [like_term, like_term]

    # Total count (for pagination controls)
    cursor.execute(f"SELECT COUNT(*) AS cnt FROM companies {where_clause}", params)
    total_count = cursor.fetchone()["cnt"]

    # Page of results
    offset = (page - 1) * per_page
    query = f"""
        SELECT * FROM companies
        {where_clause}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    """
    cursor.execute(query, params + [per_page, offset])
    companies = cursor.fetchall()

    cursor.close()
    conn.close()
    return companies, total_count


def get_company_by_id(company_id):
    """Fetch a single company's full details (used by the Edit form)."""
    conn = get_db_connection()
    if conn is None:
        return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM companies WHERE company_id = %s", (company_id,))
    company = cursor.fetchone()
    cursor.close()
    conn.close()
    return company


def create_company(data):
    """
    Insert a new company row.
    `data` is a dict of already-validated, cleaned values
    (validation happens in routes/admin.py).
    Returns (success: bool, message: str).
    """
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO companies
                (company_name, job_role, package_lpa, location, min_cgpa,
                 allowed_departments, eligible_batch_years, max_backlogs,
                 is_active, description, last_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                data["company_name"], data["job_role"], data["package_lpa"],
                data["location"], data["min_cgpa"], data["allowed_departments"],
                data["eligible_batch_years"], data["max_backlogs"],
                data["is_active"], data["description"], data["last_date"],
            )
        )
        conn.commit()
        return True, "Company added successfully!"
    except Exception as e:
        conn.rollback()
        print(f"[DB ERROR] create_company: {e}")
        return False, "Failed to add company. Please check the details and try again."
    finally:
        cursor.close()
        conn.close()


def update_company(company_id, data):
    """
    Update every field of an existing company.
    Returns (success: bool, message: str).
    """
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE companies
            SET company_name = %s, job_role = %s, package_lpa = %s, location = %s,
                min_cgpa = %s, allowed_departments = %s, eligible_batch_years = %s,
                max_backlogs = %s, is_active = %s, description = %s, last_date = %s
            WHERE company_id = %s
            """,
            (
                data["company_name"], data["job_role"], data["package_lpa"],
                data["location"], data["min_cgpa"], data["allowed_departments"],
                data["eligible_batch_years"], data["max_backlogs"],
                data["is_active"], data["description"], data["last_date"],
                company_id,
            )
        )
        conn.commit()
        return True, "Company updated successfully!"
    except Exception as e:
        conn.rollback()
        print(f"[DB ERROR] update_company: {e}")
        return False, "Failed to update company. Please check the details and try again."
    finally:
        cursor.close()
        conn.close()


def delete_company(company_id):
    """
    Delete a company. Applications referencing it are removed too
    (applications.company_id has ON DELETE CASCADE in schema.sql).
    Returns (success: bool, message: str).
    """
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."

    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM companies WHERE company_id = %s", (company_id,))
        conn.commit()
        return True, "Company deleted successfully!"
    except Exception as e:
        conn.rollback()
        print(f"[DB ERROR] delete_company: {e}")
        return False, "Failed to delete company."
    finally:
        cursor.close()
        conn.close()


def toggle_company_status(company_id):
    """
    Flip a company's is_active flag (Active <-> Inactive).
    Returns (success: bool, message: str).
    """
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT is_active FROM companies WHERE company_id = %s", (company_id,))
        row = cursor.fetchone()
        if not row:
            return False, "Company not found."

        new_status = 0 if row["is_active"] else 1
        cursor.execute(
            "UPDATE companies SET is_active = %s WHERE company_id = %s",
            (new_status, company_id)
        )
        conn.commit()
        status_text = "activated" if new_status else "deactivated"
        return True, f"Company {status_text} successfully!"
    except Exception as e:
        conn.rollback()
        print(f"[DB ERROR] toggle_company_status: {e}")
        return False, "Failed to update company status."
    finally:
        cursor.close()
        conn.close()


# ------------------------------------------------------------
# APPLICATIONS MANAGEMENT (Step 8)
# Reuses the existing `applications` table exactly as-is
# (student_id, company_id, status, applied_at) - no schema
# changes needed. Status values match the existing ENUM:
# Applied, Shortlisted, Interview Scheduled, Rejected, Selected.
# ------------------------------------------------------------

# Valid statuses, in the exact casing the DB ENUM uses.
# Defined once here so routes/admin.py and templates always
# agree with the database on what's a legal status.
APPLICATION_STATUSES = ["Applied", "Shortlisted", "Interview Scheduled", "Rejected", "Selected"]


def get_all_companies_list():
    """Lightweight list of (company_id, company_name) for the filter dropdown."""
    conn = get_db_connection()
    if conn is None:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT company_id, company_name FROM companies ORDER BY company_name ASC")
    companies = cursor.fetchall()
    cursor.close()
    conn.close()
    return companies


def get_applications_paginated(search="", status="", company_id=None, page=1, per_page=10):
    """
    Return (applications, total_count) for the admin Applications page.
      - search: matches student name/email or company name/job role
      - status: exact match against the status ENUM (empty/'' = all)
      - company_id: filter to one company (None = all)
    All filters combine with AND, and all values are passed as
    parameterized query arguments (never string-formatted into SQL).
    """
    conn = get_db_connection()
    if conn is None:
        return [], 0

    cursor = conn.cursor(dictionary=True)

    where_clauses = []
    params = []

    if search:
        where_clauses.append(
            "(s.full_name LIKE %s OR s.email LIKE %s OR c.company_name LIKE %s OR c.job_role LIKE %s)"
        )
        like_term = f"%{search}%"
        params.extend([like_term, like_term, like_term, like_term])

    if status and status in APPLICATION_STATUSES:
        where_clauses.append("a.status = %s")
        params.append(status)

    if company_id:
        where_clauses.append("c.company_id = %s")
        params.append(company_id)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    base_from = """
        FROM applications a
        JOIN students s ON a.student_id = s.student_id
        JOIN companies c ON a.company_id = c.company_id
        {where_sql}
    """.format(where_sql=where_sql)

    # Total count for pagination
    cursor.execute(f"SELECT COUNT(*) AS cnt {base_from}", params)
    total_count = cursor.fetchone()["cnt"]

    # Page of results
    offset = (page - 1) * per_page
    query = f"""
        SELECT a.application_id, a.status, a.applied_at,
               s.student_id, s.full_name, s.email, s.department, s.cgpa,
               c.company_id, c.company_name, c.job_role, c.package_lpa
        {base_from}
        ORDER BY a.applied_at DESC
        LIMIT %s OFFSET %s
    """
    cursor.execute(query, params + [per_page, offset])
    applications = cursor.fetchall()

    cursor.close()
    conn.close()
    return applications, total_count


def get_application_by_id(application_id):
    """
    Full details for the 'View Application' page: student profile,
    company/job info, and application status/date.
    """
    conn = get_db_connection()
    if conn is None:
        return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT a.application_id, a.status, a.applied_at,
               s.student_id, s.full_name, s.email, s.department, s.passing_year,
               s.cgpa, s.backlogs, s.resume_path,
               c.company_id, c.company_name, c.job_role, c.package_lpa,
               c.location, c.description AS company_description
        FROM applications a
        JOIN students s ON a.student_id = s.student_id
        JOIN companies c ON a.company_id = c.company_id
        WHERE a.application_id = %s
        """,
        (application_id,)
    )
    application = cursor.fetchone()
    cursor.close()
    conn.close()
    return application


def update_application_status(application_id, new_status):
    """
    Update the status of a single application.
    Returns (success: bool, message: str).
    """
    if new_status not in APPLICATION_STATUSES:
        return False, "Invalid status value."

    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."

    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE applications SET status = %s WHERE application_id = %s",
            (new_status, application_id)
        )
        if cursor.rowcount == 0:
            conn.rollback()
            return False, "Application not found."
        conn.commit()
        return True, f"Application status updated to '{new_status}'."
    except Exception as e:
        conn.rollback()
        print(f"[DB ERROR] update_application_status: {e}")
        return False, "Failed to update application status."
    finally:
        cursor.close()
        conn.close()
