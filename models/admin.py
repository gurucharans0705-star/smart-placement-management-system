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
