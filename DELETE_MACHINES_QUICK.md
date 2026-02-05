# Quick Guide: Delete All Machines Except OPCUA-Simulation-Machine

## ✅ Easiest Method: Direct SQL

The table name is `machine` (singular, lowercase), not `machines`.

### Step 1: Connect to Database

```bash
docker-compose exec postgres psql -U pm_user -d pm_db
```

### Step 2: View Current Machines

```sql
SELECT id, name, created_at FROM machine ORDER BY created_at;
```

### Step 3: Delete All Except OPCUA-Simulation-Machine

```sql
DELETE FROM machine WHERE name != 'OPCUA-Simulation-Machine';
```

### Step 4: Verify

```sql
SELECT id, name FROM machine;
```

You should see only:
- `OPCUA-Simulation-Machine`

### Step 5: Exit

```sql
\q
```

## Alternative: One-Line SQL Command

```bash
docker-compose exec -T postgres psql -U pm_user -d pm_db -c "DELETE FROM machine WHERE name != 'OPCUA-Simulation-Machine';"
```

## Using the SQL File

```bash
# Copy SQL file into container and run
docker-compose exec -T postgres psql -U pm_user -d pm_db < delete_machines.sql
```

## What Gets Deleted

When machines are deleted, the following related data is **automatically deleted** (cascade delete):

- ✅ All sensors associated with those machines
- ✅ All sensor data (historical readings)
- ✅ All predictions
- ✅ All alarms
- ✅ All tickets

## Important Notes

⚠️ **Warning**: This operation is **irreversible**. All data associated with deleted machines will be permanently removed.

The table name is `machine` (singular), not `machines` (plural).

## Troubleshooting

### Table Not Found Error

If you get `relation "machines" does not exist`, use `machine` (singular):

```sql
-- Wrong
DELETE FROM machines WHERE name != 'OPCUA-Simulation-Machine';

-- Correct
DELETE FROM machine WHERE name != 'OPCUA-Simulation-Machine';
```

### Check Table Name

To see all tables:

```bash
docker-compose exec postgres psql -U pm_user -d pm_db -c "\dt"
```

Look for `machine` (singular).
