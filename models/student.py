# ============================================================
# models/student.py
# All database queries related to the Student Dashboard live
# here. Keeping queries out of routes/student.py makes the
# route functions short and easy to read.
#
# NOTE: This file is NEW - it does not touch/replace anything
# used by auth.py, admin.py, or the existing login/registration
# flow.
# ============================================================

from models.db import get_db_connection


# ------------------------------------------------------------
# PROFILE
# ------------------------------------------------------------
def get_student_by_id(student_id):
    """Fetch a single student's full profile as a dict."""
    conn = get_db_connection()
    if conn is None:
        return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
    student = cursor.fetchone()
    cursor.close()
    conn.close()
    return student


def update_resume_path(student_id, resume_path):
    """Save/replace the resume file path for a student."""
    conn = get_db_connection()
    if conn is None:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE students SET resume_path = %s WHERE student_id = %s",
            (resume_path, student_id)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"[DB ERROR] update_resume_path: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def calculate_profile_completion(student):
    """
    Returns profile completion as a percentage (0-100).
    Checks a fixed set of fields; each filled field adds equal weight.
    """
    fields_to_check = [
        student.get("full_name"),
        student.get("email"),
        student.get("department"),
        student.get("cgpa"),
        student.get("passing_year"),
        student.get("resume_path"),
    ]
    filled = sum(1 for f in fields_to_check if f not in (None, "", 0) or f == 0)
    # backlogs = 0 is valid/filled, so count it separately (0 is a real value)
    if student.get("backlogs") is not None:
        filled += 1
    total = len(fields_to_check) + 1  # +1 for backlogs
    percentage = int((filled / total) * 100)
    return percentage


# ------------------------------------------------------------
# ELIGIBILITY (shared helper used by both "eligible companies"
# and "apply" so the rule is defined in exactly one place)
# ------------------------------------------------------------
def _eligibility_sql_condition():
    """
    Returns the SQL WHERE clause (as a string) used to filter
    companies a student is eligible for, based on:
      - CGPA        : company.min_cgpa <= student.cgpa
      - Department   : student's department is in the company's
                        allowed_departments comma-list
      - Backlogs      : student.backlogs <= company.max_backlogs
      - Passing year   : company.eligible_batch_years is empty/NULL
                          (open to all) OR contains the student's
                          passing_year
    """
    return """
        c.is_active = 1
        AND c.min_cgpa <= %(cgpa)s
        AND FIND_IN_SET(%(department)s, c.allowed_departments)
        AND c.max_backlogs >= %(backlogs)s
        AND (
            c.eligible_batch_years IS NULL
            OR c.eligible_batch_years = ''
            OR %(passing_year)s IS NULL
            OR FIND_IN_SET(%(passing_year)s, c.eligible_batch_years)
        )
    """


def get_eligible_companies(student):
    """Return list of companies the student is currently eligible for."""
    conn = get_db_connection()
    if conn is None:
        return []
    cursor = conn.cursor(dictionary=True)

    params = {
        "cgpa": student["cgpa"],
        "department": student["department"],
        "backlogs": student["backlogs"],
        "passing_year": student.get("passing_year"),
    }

    query = f"""
        SELECT c.*
        FROM companies c
        WHERE {_eligibility_sql_condition()}
        ORDER BY c.last_date ASC
    """
    cursor.execute(query, params)
    companies = cursor.fetchall()
    cursor.close()
    conn.close()
    return companies


def is_student_eligible_for_company(student, company_id):
    """Check eligibility for one specific company (used before applying)."""
    conn = get_db_connection()
    if conn is None:
        return False
    cursor = conn.cursor(dictionary=True)

    params = {
        "cgpa": student["cgpa"],
        "department": student["department"],
        "backlogs": student["backlogs"],
        "passing_year": student.get("passing_year"),
        "company_id": company_id,
    }
    query = f"""
        SELECT c.company_id
        FROM companies c
        WHERE c.company_id = %(company_id)s AND {_eligibility_sql_condition()}
    """
    cursor.execute(query, params)
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result is not None


# ------------------------------------------------------------
# PLACEMENT DRIVES (all active companies, with eligibility +
# "already applied" flags attached for display)
# ------------------------------------------------------------
def get_active_drives(student):
    """
    Return every active company/drive, annotated with:
      - is_eligible : bool, whether this student meets criteria
      - has_applied  : bool, whether this student already applied
      - application_status : current status if applied, else None
    """
    conn = get_db_connection()
    if conn is None:
        return []
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM companies WHERE is_active = 1 ORDER BY last_date ASC")
    companies = cursor.fetchall()

    # Get this student's existing applications in one query (avoid N+1)
    cursor.execute(
        "SELECT company_id, status FROM applications WHERE student_id = %s",
        (student["student_id"],)
    )
    applications = {row["company_id"]: row["status"] for row in cursor.fetchall()}
    cursor.close()
    conn.close()

    eligible_ids = {c["company_id"] for c in get_eligible_companies(student)}

    for company in companies:
        company["is_eligible"] = company["company_id"] in eligible_ids
        company["has_applied"] = company["company_id"] in applications
        company["application_status"] = applications.get(company["company_id"])

    return companies


# ------------------------------------------------------------
# APPLICATIONS
# ------------------------------------------------------------
def has_applied(student_id, company_id):
    conn = get_db_connection()
    if conn is None:
        return False
    cursor = conn.cursor()
    cursor.execute(
        "SELECT application_id FROM applications WHERE student_id = %s AND company_id = %s",
        (student_id, company_id)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result is not None


def apply_to_company(student_id, company_id):
    """
    Insert a new application row.
    Returns (success: bool, message: str).
    """
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."

    cursor = conn.cursor(dictionary=True)
    try:
        # Re-check the drive is still active & deadline hasn't passed
        cursor.execute(
            "SELECT company_name, job_role, is_active, last_date FROM companies WHERE company_id = %s",
            (company_id,)
        )
        company = cursor.fetchone()
        if not company:
            return False, "Company not found."
        if not company["is_active"]:
            return False, "This placement drive is no longer active."
        if company["last_date"] and company["last_date"] < __import__("datetime").date.today():
            return False, "The application deadline for this drive has passed."

        cursor.execute(
            "INSERT INTO applications (student_id, company_id, status) VALUES (%s, %s, 'Applied')",
            (student_id, company_id)
        )
        conn.commit()

        # Create a confirmation notification for the student
        _create_notification(
            cursor, conn, student_id,
            f"You have successfully applied to {company['company_name']} for the {company['job_role']} role."
        )
        return True, f"Application submitted to {company['company_name']}!"

    except Exception as e:
        conn.rollback()
        # Most likely cause: UNIQUE constraint (student already applied)
        if "Duplicate entry" in str(e):
            return False, "You have already applied to this company."
        print(f"[DB ERROR] apply_to_company: {e}")
        return False, "Something went wrong while submitting your application."
    finally:
        cursor.close()
        conn.close()


def get_applications_for_student(student_id):
    """Return full application history for a student, newest first."""
    conn = get_db_connection()
    if conn is None:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT a.application_id, a.status, a.applied_at,
               c.company_id, c.company_name, c.job_role, c.package_lpa, c.location
        FROM applications a
        JOIN companies c ON a.company_id = c.company_id
        WHERE a.student_id = %s
        ORDER BY a.applied_at DESC
        """,
        (student_id,)
    )
    applications = cursor.fetchall()
    cursor.close()
    conn.close()
    return applications


# ------------------------------------------------------------
# DASHBOARD STATISTICS
# ------------------------------------------------------------
def get_dashboard_stats(student):
    """Return counts used in the dashboard's stat cards."""
    conn = get_db_connection()
    if conn is None:
        return {"eligible": 0, "applied": 0, "shortlisted": 0, "selected": 0}

    cursor = conn.cursor(dictionary=True)

    eligible_count = len(get_eligible_companies(student))

    cursor.execute(
        "SELECT status, COUNT(*) AS cnt FROM applications WHERE student_id = %s GROUP BY status",
        (student["student_id"],)
    )
    status_counts = {row["status"]: row["cnt"] for row in cursor.fetchall()}
    cursor.close()
    conn.close()

    applied_total = sum(status_counts.values())

    return {
        "eligible": eligible_count,
        "applied": applied_total,
        "shortlisted": status_counts.get("Shortlisted", 0) + status_counts.get("Interview Scheduled", 0),
        "selected": status_counts.get("Selected", 0),
    }


# ------------------------------------------------------------
# NOTIFICATIONS
# ------------------------------------------------------------
def _create_notification(cursor, conn, student_id, message):
    """Internal helper: insert a notification using an existing cursor/conn."""
    try:
        cursor.execute(
            "INSERT INTO notifications (student_id, message) VALUES (%s, %s)",
            (student_id, message)
        )
        conn.commit()
    except Exception as e:
        print(f"[DB ERROR] _create_notification: {e}")


def get_notifications_for_student(student_id, limit=None):
    """Return notifications for a student, newest first."""
    conn = get_db_connection()
    if conn is None:
        return []
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM notifications WHERE student_id = %s ORDER BY created_at DESC"
    if limit:
        query += f" LIMIT {int(limit)}"
    cursor.execute(query, (student_id,))
    notifications = cursor.fetchall()
    cursor.close()
    conn.close()
    return notifications
