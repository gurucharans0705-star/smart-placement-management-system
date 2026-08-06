# ============================================================
# create_admin.py
# One-time utility script to create an Admin account.
# Admins don't self-register through the website (for security),
# so run this script once from the terminal to create the first
# admin login:
#
#     python create_admin.py
#
# ============================================================

from werkzeug.security import generate_password_hash
from models.db import get_db_connection

def create_admin(full_name, email, password):
    password_hash = generate_password_hash(password)

    conn = get_db_connection()
    if conn is None:
        print("Could not connect to database. Check config.py settings.")
        return

    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO admins (full_name, email, password_hash) VALUES (%s, %s, %s)",
            (full_name, email, password_hash)
        )
        conn.commit()
        print(f"Admin account created successfully for {email}")
    except Exception as e:
        print(f"Failed to create admin: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # Edit these values, or change to input() prompts if you prefer
    create_admin(
        full_name="Placement Officer",
        email="admin@placement.com",
        password="admin123"
    )
