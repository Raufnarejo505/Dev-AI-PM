-- Delete all machines and related data in correct order
-- This handles foreign key constraints by deleting dependent data first

BEGIN;

-- Step 1: Delete all predictions (references machine)
DELETE FROM prediction;

-- Step 2: Delete all alarms (references machine)
DELETE FROM alarm;

-- Step 3: Delete all tickets (references machine)
DELETE FROM ticket;

-- Step 4: Delete all sensor_data (references machine)
DELETE FROM sensor_data;

-- Step 5: Delete all sensors (references machine, will cascade)
DELETE FROM sensor;

-- Step 6: Now delete all machines
DELETE FROM machine;

-- Verify deletion
SELECT COUNT(*) as remaining_machines FROM machine;
SELECT COUNT(*) as remaining_sensors FROM sensor;
SELECT COUNT(*) as remaining_predictions FROM prediction;

COMMIT;
