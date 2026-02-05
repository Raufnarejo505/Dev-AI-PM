# Simple Way to Delete ALL Machines

## Quick SQL Method

### Step 1: Connect to Database

```powershell
docker-compose exec postgres psql -U pm_user -d pm_db
```

### Step 2: Run These SQL Commands

Copy and paste these commands one by one:

```sql
BEGIN;

DELETE FROM prediction;
DELETE FROM alarm;
DELETE FROM ticket;
DELETE FROM sensor_data;
DELETE FROM sensor;
DELETE FROM machine;

SELECT COUNT(*) FROM machine;

COMMIT;

\q
```

## Or Use the SQL File

```powershell
docker-compose exec -T postgres psql -U pm_user -d pm_db -f delete_all_now.sql
```

## Verify

After running, you should see:
- `machines_remaining: 0`
- `sensors_remaining: 0`
- `predictions_remaining: 0`

## Then Refresh Browser

1. Hard refresh: `Ctrl + Shift + R`
2. Machines tab should be empty
