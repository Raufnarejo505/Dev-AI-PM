-- Cleanup script to delete all machines except Extruder-SQL and unwanted sensors
-- Run this with: docker-compose exec postgres psql -U pm_user -d pm_db -f /path/to/cleanup_machines.sql

-- First, delete all sensors that belong to machines we're going to delete
DELETE FROM sensor 
WHERE machine_id IN (
    SELECT id FROM machine WHERE name != 'Extruder-SQL'
);

-- Delete all machines except Extruder-SQL
DELETE FROM machine WHERE name != 'Extruder-SQL';

-- Now delete unwanted sensors from Extruder-SQL machine
-- Keep only: ScrewSpeed_rpm, Pressure_bar, Temperaturzonen Zone 1-4
DELETE FROM sensor 
WHERE machine_id IN (SELECT id FROM machine WHERE name = 'Extruder-SQL')
  AND name NOT IN (
    'ScrewSpeed_rpm',
    'Pressure_bar',
    'Temperaturzonen Zone 1',
    'Temperaturzonen Zone 2',
    'Temperaturzonen Zone 3',
    'Temperaturzonen Zone 4'
  );

-- Show remaining machines and sensors
SELECT 'Remaining machines:' as info;
SELECT id, name, location, status FROM machine;

SELECT 'Remaining sensors:' as info;
SELECT s.id, s.name, s.sensor_type, s.unit, m.name as machine_name
FROM sensor s
JOIN machine m ON s.machine_id = m.id
ORDER BY m.name, s.name;
