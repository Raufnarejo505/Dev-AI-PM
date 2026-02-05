-- Direct SQL to delete all machines except OPCUA-Simulation-Machine
-- This handles case-insensitive matching and trims whitespace

-- Step 1: View all machines first
SELECT id, name, created_at FROM machine ORDER BY created_at;

-- Step 2: Delete all machines except OPCUA-Simulation-Machine
-- Using case-insensitive comparison and trimming whitespace
DELETE FROM machine 
WHERE LOWER(TRIM(name)) != LOWER('OPCUA-Simulation-Machine');

-- Step 3: Verify deletion
SELECT id, name, created_at FROM machine;
