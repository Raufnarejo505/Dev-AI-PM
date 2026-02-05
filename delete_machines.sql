-- Delete all machines except OPCUA-Simulation-Machine
-- Table name is 'machine' (singular, lowercase) not 'machines'

-- First, let's see what machines exist
SELECT id, name, created_at FROM machine ORDER BY created_at;

-- Delete all machines except OPCUA-Simulation-Machine
-- This will cascade delete related sensors, sensor_data, predictions, alarms, tickets
DELETE FROM machine WHERE name != 'OPCUA-Simulation-Machine';

-- Verify deletion
SELECT id, name, created_at FROM machine;
