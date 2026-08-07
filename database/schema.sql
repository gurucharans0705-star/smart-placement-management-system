-- ============================================================
-- Smart Placement Management System - Database Schema
-- ============================================================
-- Run this file in MySQL to create the database and tables:
--   mysql -u root -p < schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS placement_system;
USE placement_system;

-- ------------------------------------------------------------
-- Table: students
-- Stores student registration/login details + academic info
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS students (
    student_id      INT AUTO_INCREMENT PRIMARY KEY,
    full_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(100) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,      -- hashed password (never store plain text)
    department      VARCHAR(50)  NOT NULL,      -- e.g. CSE, ECE, MECH
    passing_year    INT DEFAULT NULL,            -- e.g. 2026 (graduation year)
    cgpa            DECIMAL(4,2) NOT NULL,       -- e.g. 8.75
    backlogs        INT DEFAULT 0,               -- number of active backlogs
    resume_path     VARCHAR(255) DEFAULT NULL,   -- path to uploaded PDF resume
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Table: admins
-- Stores admin/placement-officer login details
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admins (
    admin_id        INT AUTO_INCREMENT PRIMARY KEY,
    full_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(100) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Table: companies
-- Companies added by Admin for placement drives
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS companies (
    company_id        INT AUTO_INCREMENT PRIMARY KEY,
    company_name       VARCHAR(100) NOT NULL,
    job_role            VARCHAR(100) NOT NULL,
    package_lpa          DECIMAL(6,2) DEFAULT NULL,   -- salary package in LPA (CTC)
    location              VARCHAR(100) DEFAULT NULL,   -- job location
    min_cgpa             DECIMAL(4,2) NOT NULL,       -- eligibility: minimum CGPA
    allowed_departments  VARCHAR(255) NOT NULL,       -- comma-separated e.g. "CSE,ECE"
    eligible_batch_years VARCHAR(100) DEFAULT NULL,   -- comma-separated e.g. "2026,2027"; NULL = open to all
    max_backlogs         INT DEFAULT 0,                -- eligibility: max backlogs allowed
    is_active              TINYINT(1) DEFAULT 1,        -- whether the drive is currently open
    description          TEXT,
    drive_date            DATE DEFAULT NULL,            -- date of the placement drive
    last_date              DATE DEFAULT NULL,            -- application deadline
    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Table: applications
-- Tracks which student applied to which company + status
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS applications (
    application_id   INT AUTO_INCREMENT PRIMARY KEY,
    student_id        INT NOT NULL,
    company_id        INT NOT NULL,
    status             ENUM('Applied', 'Shortlisted', 'Interview Scheduled', 'Rejected', 'Selected') DEFAULT 'Applied',
    applied_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE,
    UNIQUE KEY unique_application (student_id, company_id)  -- prevent duplicate applications
);

-- ------------------------------------------------------------
-- Table: notifications
-- Simple notification system for students (e.g. status updates)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS notifications (
    notification_id   INT AUTO_INCREMENT PRIMARY KEY,
    student_id          INT NOT NULL,
    message              VARCHAR(255) NOT NULL,
    is_read               BOOLEAN DEFAULT FALSE,
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Seed data: one default admin account
-- Email: admin@placement.com | Password: admin123
-- (password_hash below corresponds to 'admin123' using Werkzeug's
--  generate_password_hash - we will insert this via Python instead,
--  see create_admin.py script in Step 4)
-- ------------------------------------------------------------
