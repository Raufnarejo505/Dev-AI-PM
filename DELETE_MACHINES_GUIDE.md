# Delete All Machines Except OPCUA-Simulation-Machine

## Quick Method (Using Script)

### Option 1: Run Script Directly

```bash
# Navigate to backend directory
cd backend

# Run the script
python scripts/delete_machines_except_opcua.py
```

The script will:
1. List all machines in the database
2. Show which machines will be deleted
3. Ask for confirmation
4. Delete all machines except "OPCUA-Simulation-Machine"

### Option 2: Using Docker

```bash
# Run script inside backend container
docker-compose exec backend python scripts/delete_machines_except_opcua.py
```

## What Gets Deleted

When a machine is deleted, the following related data is also deleted (cascade delete):

- ✅ **Sensors** - All sensors associated with the machine
- ✅ **Sensor Data** - All historical sensor readings
- ✅ **Predictions** - All AI predictions for the machine
- ✅ **Alarms** - All alarms triggered for the machine
- ✅ **Tickets** - All maintenance tickets for the machine

## Manual Method (Using SQL)

If you prefer to use SQL directly:

```bash
# Connect to database
docker-compose exec postgres psql -U pm_user -d pm_db

# Delete machines (except OPCUA-Simulation-Machine)
DELETE FROM machines 
WHERE name != 'OPCUA-Simulation-Machine';

# Verify deletion
SELECT id, name, created_at FROM machines;

# Exit
\q
```

## Verification

After running the script, verify the results:

```bash
# Check machines via API (if backend is running)
curl http://localhost:8000/api/machines

# Or check database directly
docker-compose exec postgres psql -U pm_user -d pm_db -c "SELECT id, name FROM machines;"
```

You should see only:
- `OPCUA-Simulation-Machine`

## Safety Notes

⚠️ **Warning**: This operation is **irreversible**. All data associated with deleted machines will be permanently removed.

The script includes:
- ✅ Confirmation prompt before deletion
- ✅ Lists all machines that will be deleted
- ✅ Error handling and rollback on failure
- ✅ Detailed logging

## Troubleshooting

### Script Not Found

If the script doesn't exist, create it manually or run:

```bash
# Create the script file
cat > backend/scripts/delete_machines_except_opcua.py << 'EOF'
# [paste script content]
EOF
```

### Permission Errors

If you get permission errors:

```bash
# Make script executable (Linux/Mac)
chmod +x backend/scripts/delete_machines_except_opcua.py
```

### Database Connection Issues

Ensure the database is running:

```bash
docker-compose ps postgres
```

## Alternative: Using Backend API

You can also delete machines one by one using the API:

```bash
# Get all machines
curl http://localhost:8000/api/machines

# Delete a specific machine (replace {machine_id} with actual UUID)
curl -X DELETE http://localhost:8000/api/machines/{machine_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

But the script is faster for bulk deletion.
