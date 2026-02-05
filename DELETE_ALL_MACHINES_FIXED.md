# Delete ALL Machines - Fixed Solution

## Problem
Foreign key constraints prevent direct deletion of machines because:
- `prediction` table references `machine`
- `alarm` table references `machine`
- `ticket` table references `machine`
- `sensor_data` table references `machine`
- `sensor` table references `machine`

## Solution: Delete in Correct Order

### Method 1: Python Script (Recommended)

```powershell
docker-compose exec backend python /app/scripts/delete_all_machines_cascade.py
```

This script:
- Deletes all related data first (predictions, alarms, tickets, sensor_data, sensors)
- Then deletes all machines
- Verifies deletion
- Handles transactions properly

### Method 2: SQL Script

```powershell
# Connect to database
docker-compose exec postgres psql -U pm_user -d pm_db
```

Then run:

```sql
BEGIN;

-- Delete in correct order
DELETE FROM prediction;
DELETE FROM alarm;
DELETE FROM ticket;
DELETE FROM sensor_data;
DELETE FROM sensor;
DELETE FROM machine;

-- Verify
SELECT COUNT(*) FROM machine;
SELECT COUNT(*) FROM sensor;
SELECT COUNT(*) FROM prediction;

COMMIT;

\q
```

### Method 3: One-Line SQL (Using the SQL file)

```powershell
docker-compose exec -T postgres psql -U pm_user -d pm_db < delete_all_machines_cascade.sql
```

## After Deletion

1. **Hard refresh browser**: `Ctrl + Shift + R`
2. **Check Machines tab** - should be empty
3. **When OPC UA starts**, it will create "OPCUA-Simulation-Machine" automatically

## Verify Deletion

```powershell
docker-compose exec postgres psql -U pm_user -d pm_db -c "SELECT COUNT(*) FROM machine; SELECT COUNT(*) FROM sensor; SELECT COUNT(*) FROM prediction;"
```

All counts should be `0`.
