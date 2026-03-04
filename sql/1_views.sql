-- ============================================================
--  LIFEFLOW BLOOD BANK — Django Edition
--  SQL FILE 1 of 2: VIEWS
--
--  ⚠️  Run AFTER Django migrations:
--      python manage.py migrate
--  Then open MySQL Workbench and run this file.
-- ============================================================

USE lifeflow_db;

-- ─────────────────────────────────────────────────────────────
-- VIEW 1: Blood Stock with status labels
-- ─────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW blood_stock_view AS
SELECT
    blood_group,
    units_available,
    CASE
        WHEN units_available = 0  THEN 'Out of Stock'
        WHEN units_available < 5  THEN 'Critical'
        WHEN units_available < 20 THEN 'Low'
        ELSE 'Adequate'
    END AS stock_status,
    last_updated
FROM core_bloodinventory;

-- ─────────────────────────────────────────────────────────────
-- VIEW 2: Eligible Donors
-- ─────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW eligible_donors_view AS
SELECT
    d.id          AS donor_id,
    u.first_name,
    u.last_name,
    u.email,
    u.city,
    d.blood_group,
    d.last_donation,
    d.total_donations
FROM core_donor d
JOIN core_user u ON d.user_id = u.id
WHERE d.is_eligible = 1
  AND u.is_active   = 1;

-- ─────────────────────────────────────────────────────────────
-- VIEW 3: Pending Blood Requests sorted by urgency
-- ─────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW pending_requests_view AS
SELECT
    br.id           AS request_id,
    u.first_name,
    h.hospital_name,
    br.patient_name,
    br.blood_group,
    br.units_needed,
    br.urgency,
    br.request_date
FROM core_bloodrequest br
JOIN core_user     u ON br.requester_id = u.id
JOIN core_hospital h ON h.user_id       = u.id
WHERE br.status = 'pending'
ORDER BY FIELD(br.urgency, 'critical', 'high', 'medium', 'low');

-- ─────────────────────────────────────────────────────────────
-- VIEW 4: Donor Donation Summary
-- ─────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW donor_summary_view AS
SELECT
    CONCAT(u.first_name, ' ', u.last_name) AS donor_name,
    u.city,
    d.blood_group,
    d.total_donations,
    COALESCE(SUM(dn.units_donated), 0)     AS total_units_donated,
    d.last_donation,
    d.is_eligible
FROM core_donor d
JOIN core_user u ON d.user_id = u.id
LEFT JOIN core_donation dn ON dn.donor_id = d.id AND dn.status = 'approved'
GROUP BY d.id;

-- ✅ Done with Views. Run 2_procedures_triggers.sql next.
