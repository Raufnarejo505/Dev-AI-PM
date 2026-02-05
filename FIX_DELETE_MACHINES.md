# Fix: Delete All Machines

## Problem
Machines are still appearing in the UI even after running DELETE command, and delete button doesn't work.

## Solution 1: Force Delete via Python Script (Recommended)

Run this script inside the Docker container:

```powershell
docker-compose exec backend python /app/scripts/force_delete_all_machines.py
```

This script:
- Uses raw SQL to delete all machines
- Properly commits the transaction
- Verifies deletion

## Solution 2: Direct SQL with Transaction

Connect to database and run:

```powershell
docker-compose exec postgres psql -U pm_user -d pm_db
```

Then run:

```sql
BEGIN;
DELETE FROM machine;
COMMIT;
SELECT COUNT(*) FROM machine;
\q
```

## Solution 3: Clear Frontend Cache

After deleting machines, refresh the frontend:

1. **Hard refresh**: Press `Ctrl + Shift + R` (or `Cmd + Shift + R` on Mac)
2. **Clear browser cache**: Open DevTools (F12) → Application → Clear Storage → Clear site data
3. **Or restart frontend**: 
   ```powershell
   docker-compose restart frontend
   ```

## Solution 4: Fix Delete Button

The delete button should work. If it doesn't, check browser console for errors.

To manually delete via API:

```powershell
# Get all machines
curl http://localhost:8000/api/machines -H "Authorization: Bearer YOUR_TOKEN"

# Delete each machine (replace {machine_id} with actual UUID)
curl -X DELETE http://localhost:8000/api/machines/{machine_id} -H "Authorization: Bearer YOUR_TOKEN"
```

## Verify Deletion

```powershell
# Check database
docker-compose exec postgres psql -U pm_user -d pm_db -c "SELECT COUNT(*) FROM machine;"

# Check API
curl http://localhost:8000/api/machines
```

## After Deletion

1. Hard refresh the browser (Ctrl+Shift+R)
2. The machines list should be empty
3. When OPC UA connector starts, it will create "OPCUA-Simulation-Machine" automatically
