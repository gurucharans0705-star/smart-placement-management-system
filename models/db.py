# ============================================================
# models/db.py
# Centralized database connection helper.
# Every route that needs the DB imports get_db_connection()
# from here instead of writing connection code repeatedly.
# ============================================================

import mysql.connector
from mysql.connector import Error
from config import Config


def get_db_connection():
    """
    Creates and returns a new MySQL connection using settings
    from config.py. Returns None if the connection fails
    (caller should handle this gracefully).
    """
    try:
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        return connection
    except Error as e:
        print(f"[DB ERROR] Could not connect to MySQL: {e}")
        return None
