# Delete ALL Machines

## Quick Command

Run this single command to delete ALL machines:

```powershell
docker-compose exec postgres psql -U pm_user -d pm_db -c "DELETE FROM machine;"
```

## Verify Deletion

```powershell
docker-compose exec postgres psql -U pm_user -d pm_db -c "SELECT COUNT(*) as total_machines FROM machine;"
```

Should return: `total_machines: 0`

## What Gets Deleted

When machines are deleted, the following related data is **automatically deleted** (cascade delete):

- ✅ All sensors associated with those machines
- ✅ All sensor data (historical readings)
- ✅ All predictions
- ✅ All alarms
- ✅ All tickets

## After Deletion

Once all machines are deleted:
- The OPC UA connector will automatically create "OPCUA-Simulation-Machine" when it starts ingesting data
- The dashboard will be empty until OPC UA data starts flowing
- All old dummy/test data will be removed
