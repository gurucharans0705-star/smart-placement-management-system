-- ============================================================
-- database/migration_step5.sql
-- Adds new columns required for the Student Dashboard (Step 5).
-- This is SAFE to run on your existing database - it only ADDS
-- columns, it does NOT drop or modify any existing data.
--
-- Run it with:
--   mysql -u root -p placement_system < database/migration_step5.sql
-- ============================================================

USE placement_system;

-- ------------------------------------------------------------
-- students: add passing_year (optional field, used for
-- eligibility + profile completion). NULL is allowed so
-- existing student rows are unaffected.
-- ------------------------------------------------------------
ALTER TABLE students
    ADD COLUMN IF NOT EXISTS passing_year INT DEFAULT NULL AFTER department;

-- ------------------------------------------------------------
-- companies: add fields needed for full placement-drive display
-- and eligibility checks.
--   location             - job location shown to students
--   last_date             - application deadline
--   eligible_batch_years  - comma separated list e.g. "2025,2026"
--                           (NULL/empty = open to all batches)
--   is_active              - whether the drive is currently open
-- ------------------------------------------------------------
ALTER TABLE companies
    ADD COLUMN IF NOT EXISTS location VARCHAR(100) DEFAULT NULL AFTER package_lpa,
    ADD COLUMN IF NOT EXISTS last_date DATE DEFAULT NULL AFTER drive_date,
    ADD COLUMN IF NOT EXISTS eligible_batch_years VARCHAR(100) DEFAULT NULL AFTER allowed_departments,
    ADD COLUMN IF NOT EXISTS is_active TINYINT(1) DEFAULT 1 AFTER eligible_batch_years;

-- ------------------------------------------------------------
-- applications: add "Interview Scheduled" as a valid status
-- (existing rows with Applied/Shortlisted/Rejected/Selected
-- are unaffected by this change).
-- ------------------------------------------------------------
ALTER TABLE applications
    MODIFY COLUMN status ENUM('Applied', 'Shortlisted', 'Interview Scheduled', 'Rejected', 'Selected')
    DEFAULT 'Applied';

-- ------------------------------------------------------------
-- OPTIONAL: sample companies for testing the Student Dashboard
-- (only needed if you don't have Admin > Company Management
-- built yet). Safe to skip or delete these lines.
-- ------------------------------------------------------------
INSERT INTO companies
    (company_name, job_role, package_lpa, location, min_cgpa, allowed_departments,
     eligible_batch_years, max_backlogs, description, drive_date, last_date, is_active)
VALUES
    ('TechNova Solutions', 'Software Engineer', 6.50, 'Bengaluru', 7.00, 'CSE,IT',
     '2026', 0, 'Product-based company hiring for backend roles.', '2026-09-10', '2026-08-25', 1),
    ('DataWorks Analytics', 'Data Analyst', 5.50, 'Hyderabad', 6.50, 'CSE,IT,ECE',
     '2026', 1, 'Analytics firm working with large-scale data pipelines.', '2026-09-15', '2026-08-30', 1),
    ('CoreElectro Systems', 'Embedded Engineer', 4.80, 'Chennai', 6.00, 'ECE,EEE',
     '2026', 2, 'Hardware and embedded systems company.', '2026-09-20', '2026-09-05', 1)
;
