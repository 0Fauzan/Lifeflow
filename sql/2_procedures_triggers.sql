-- ============================================================
--  LIFEFLOW BLOOD BANK — Django Edition
--  SQL FILE 2 of 2: STORED PROCEDURES + TRIGGERS
--
--  ⚠️  Run AFTER Django migrations AND 1_views.sql
--  ⚠️  DELIMITER $$ is used — MySQL Workbench handles this fine
-- ============================================================

USE lifeflow_db;

DROP PROCEDURE IF EXISTS approve_donation;
DROP PROCEDURE IF EXISTS fulfill_request;
DROP PROCEDURE IF EXISTS reject_donation;
DROP TRIGGER IF EXISTS low_stock_alert;
DROP TRIGGER IF EXISTS restore_donor_eligibility;

DELIMITER $$

-- ─────────────────────────────────────────────────────────────
-- PROCEDURE 1: Approve Donation
-- Updates inventory + donor stats atomically
-- Usage: CALL approve_donation(1, 1);
-- ─────────────────────────────────────────────────────────────
CREATE PROCEDURE approve_donation(
    IN p_donation_id INT,
    IN p_admin_id    INT
)
BEGIN
    DECLARE v_blood_group VARCHAR(5);
    DECLARE v_units       DECIMAL(4,2);
    DECLARE v_donor_id    INT;

    START TRANSACTION;

    SELECT blood_group, units_donated, donor_id
      INTO v_blood_group, v_units, v_donor_id
      FROM core_donation
     WHERE id = p_donation_id;

    UPDATE core_donation
       SET status       = 'approved',
           approved_by_id = p_admin_id
     WHERE id = p_donation_id;

    UPDATE core_bloodinventory
       SET units_available = units_available + v_units
     WHERE blood_group = v_blood_group;

    UPDATE core_donor
       SET total_donations = total_donations + 1,
           last_donation   = CURDATE(),
           is_eligible     = 0
     WHERE id = v_donor_id;

    COMMIT;
    SELECT 'SUCCESS' AS result;
END$$


-- ─────────────────────────────────────────────────────────────
-- PROCEDURE 2: Fulfill Blood Request
-- Deducts inventory if stock is sufficient
-- Usage: CALL fulfill_request(1, 1);
-- ─────────────────────────────────────────────────────────────
CREATE PROCEDURE fulfill_request(
    IN p_request_id INT,
    IN p_admin_id   INT
)
BEGIN
    DECLARE v_blood_group VARCHAR(5);
    DECLARE v_units       DECIMAL(5,2);
    DECLARE v_available   INT;

    START TRANSACTION;

    SELECT blood_group, units_needed
      INTO v_blood_group, v_units
      FROM core_bloodrequest
     WHERE id = p_request_id;

    SELECT units_available
      INTO v_available
      FROM core_bloodinventory
     WHERE blood_group = v_blood_group;

    IF v_available >= v_units THEN
        UPDATE core_bloodrequest
           SET status         = 'fulfilled',
               fulfilled_date = CURDATE(),
               handled_by_id  = p_admin_id
         WHERE id = p_request_id;

        UPDATE core_bloodinventory
           SET units_available = units_available - v_units
         WHERE blood_group = v_blood_group;

        COMMIT;
        SELECT 'SUCCESS' AS result, v_available AS stock_before, v_units AS deducted;
    ELSE
        ROLLBACK;
        SELECT 'INSUFFICIENT_STOCK' AS result, v_available AS available, v_units AS needed;
    END IF;
END$$


-- ─────────────────────────────────────────────────────────────
-- PROCEDURE 3: Reject Donation
-- Usage: CALL reject_donation(1, 1);
-- ─────────────────────────────────────────────────────────────
CREATE PROCEDURE reject_donation(
    IN p_donation_id INT,
    IN p_admin_id    INT
)
BEGIN
    UPDATE core_donation
       SET status         = 'rejected',
           approved_by_id = p_admin_id
     WHERE id = p_donation_id;
    SELECT 'REJECTED' AS result;
END$$


-- ─────────────────────────────────────────────────────────────
-- TRIGGER 1: Low Stock Alert
-- Auto-notifies all admins when blood drops below 5 units
-- ─────────────────────────────────────────────────────────────
CREATE TRIGGER low_stock_alert
AFTER UPDATE ON core_bloodinventory
FOR EACH ROW
BEGIN
    IF NEW.units_available < 5 AND OLD.units_available >= 5 THEN
        INSERT INTO core_notification (user_id, title, message, is_read, created_at)
        SELECT
            id,
            CONCAT('⚠️ Low Stock: ', NEW.blood_group),
            CONCAT('Blood group ', NEW.blood_group, ' dropped to ', NEW.units_available, ' units. Action needed.'),
            0,
            NOW()
        FROM core_user
        WHERE role = 'admin';
    END IF;
END$$


-- ─────────────────────────────────────────────────────────────
-- TRIGGER 2: Restore Donor Eligibility
-- Auto-marks donor eligible after 90 days
-- ─────────────────────────────────────────────────────────────
CREATE TRIGGER restore_donor_eligibility
AFTER UPDATE ON core_donor
FOR EACH ROW
BEGIN
    IF NEW.last_donation IS NOT NULL THEN
        IF DATEDIFF(CURDATE(), NEW.last_donation) >= 90 THEN
            UPDATE core_donor
               SET is_eligible = 1
             WHERE id = NEW.id;
        END IF;
    END IF;
END$$

DELIMITER ;

-- ============================================================
--  🎉 ALL DONE!
--
--  Django table prefix is "core_" (app name)
--  Tables created by Django migrations:
--    core_user, core_donor, core_hospital
--    core_bloodinventory, core_camp, core_campregistration
--    core_donation, core_bloodrequest, core_notification
--
--  To test procedures:
--    CALL approve_donation(1, 1);
--    CALL fulfill_request(1, 1);
--
--  To view data:
--    SELECT * FROM blood_stock_view;
--    SELECT * FROM eligible_donors_view;
--    SELECT * FROM pending_requests_view;
-- ============================================================
