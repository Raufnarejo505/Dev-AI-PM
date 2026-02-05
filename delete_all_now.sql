-- Delete ALL machines and related data
-- Run this in psql

BEGIN;

DELETE FROM prediction;
DELETE FROM alarm;
DELETE FROM ticket;
DELETE FROM sensor_data;
DELETE FROM sensor;
DELETE FROM machine;

SELECT COUNT(*) as machines_remaining FROM machine;
SELECT COUNT(*) as sensors_remaining FROM sensor;
SELECT COUNT(*) as predictions_remaining FROM prediction;

COMMIT;
