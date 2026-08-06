# ============================================================
# config.py
# Central place for all configuration values.
# Keeping config separate makes it easy to change settings
# (e.g. DB password) without touching app logic.
# ============================================================

import os

class Config:
    # Secret key is used by Flask to sign session cookies securely.
    # In production, set this via an environment variable instead.
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-to-a-random-secret-key")

    # ---------------- MySQL Database Settings ----------------
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DB = os.environ.get("MYSQL_DB", "placement_system")

    # ---------------- File Upload Settings ----------------
    UPLOAD_FOLDER = os.path.join("static", "uploads", "resumes")
    ALLOWED_EXTENSIONS = {"pdf"}          # only PDF resumes allowed
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024   # 5 MB max upload size
