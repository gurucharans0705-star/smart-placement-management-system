# ============================================================
# routes/auth.py
# Handles:
#   - Student registration
#   - Student login / logout
#   - Admin login / logout
#
# Security notes:
#   - Passwords are NEVER stored in plain text. We use
#     werkzeug.security to hash them before saving, and to
#     verify them on login.
#   - Logged-in users are tracked using Flask's `session`
#     (a secure, signed cookie) - we store only IDs in it,
#     never passwords.
# ============================================================

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models.db import get_db_connection

# Create a Blueprint named "auth". All routes here will be
# accessible as auth.<function_name> (e.g. auth.student_login)
auth_bp = Blueprint("auth", __name__)


# ------------------------------------------------------------
# STUDENT REGISTRATION
# ------------------------------------------------------------
@auth_bp.route("/student/register", methods=["GET", "POST"])
def student_register():
    if request.method == "POST":
        # 1. Read form data submitted by the student
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        department = request.form.get("department", "").strip()
        cgpa = request.form.get("cgpa", "")
        backlogs = request.form.get("backlogs", "0")

        # 2. Basic server-side validation
        if not full_name or not email or not password or not department or not cgpa:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("auth.student_register"))

        try:
            cgpa = float(cgpa)
            backlogs = int(backlogs)
        except ValueError:
            flash("CGPA and Backlogs must be numeric values.", "error")
            return redirect(url_for("auth.student_register"))

        # 3. Hash the password before storing (never store raw password!)
        password_hash = generate_password_hash(password)

        # 4. Insert into database
        conn = get_db_connection()
        if conn is None:
            flash("Database connection failed. Please try again later.", "error")
            return redirect(url_for("auth.student_register"))

        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO students
                   (full_name, email, password_hash, department, cgpa, backlogs)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (full_name, email, password_hash, department, cgpa, backlogs)
            )
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("auth.student_login"))
        except Exception as e:
            # Most common error here: duplicate email (UNIQUE constraint)
            conn.rollback()
            flash("Registration failed. This email may already be registered.", "error")
            return redirect(url_for("auth.student_register"))
        finally:
            cursor.close()
            conn.close()

    # GET request -> just show the registration form
    return render_template("student/register.html")


# ------------------------------------------------------------
# STUDENT LOGIN
# ------------------------------------------------------------
@auth_bp.route("/student/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()
        if conn is None:
            flash("Database connection failed. Please try again later.", "error")
            return redirect(url_for("auth.student_login"))

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students WHERE email = %s", (email,))
        student = cursor.fetchone()
        cursor.close()
        conn.close()

        # Verify the hashed password matches what was entered
        if student and check_password_hash(student["password_hash"], password):
            # Store only non-sensitive identifying info in the session
            session["student_id"] = student["student_id"]
            session["student_name"] = student["full_name"]
            flash(f"Welcome back, {student['full_name']}!", "success")
            return redirect(url_for("student.dashboard"))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for("auth.student_login"))

    return render_template("student/login.html")


# ------------------------------------------------------------
# ADMIN LOGIN
# ------------------------------------------------------------
@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()
        if conn is None:
            flash("Database connection failed. Please try again later.", "error")
            return redirect(url_for("auth.admin_login"))

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admins WHERE email = %s", (email,))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_id"] = admin["admin_id"]
            session["admin_name"] = admin["full_name"]
            flash(f"Welcome, {admin['full_name']}!", "success")
            return redirect(url_for("admin.dashboard"))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for("auth.admin_login"))

    return render_template("admin/login.html")


# ------------------------------------------------------------
# LOGOUT (works for both student & admin)
# ------------------------------------------------------------
@auth_bp.route("/logout")
def logout():
    # session.clear() removes all session data (student_id, admin_id, etc.)
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))
