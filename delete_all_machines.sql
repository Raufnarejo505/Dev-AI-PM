-- Delete ALL machines from the database
-- OPCUA-Simulation-Machine will be created automatically by the OPC UA connector

-- Step 1: View count before deletion
SELECT COUNT(*) as total_machines FROM machine;

-- Step 2: Delete ALL machines
-- This will cascade delete all related sensors, sensor_data, predictions, alarms, tickets
DELETE FROM machine;

-- Step 3: Verify deletion
SELECT COUNT(*) as remaining_machines FROM machine;
SELECT id, name FROM machine;
