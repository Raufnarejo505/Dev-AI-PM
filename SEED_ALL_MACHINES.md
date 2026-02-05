# How to Seed All 4 Machines

The simulator publishes data for 4 machines, but the database only has 2 machines. Follow these steps to add all 4 machines:

## Option 1: Run Seed Script (Recommended)

### On the Server:

```bash
# Connect to backend container
docker compose -f docker-compose.prod.yml exec backend bash

# Run seed script
python -m app.tasks.seed_demo_data

# Or run directly
python app/tasks/seed_demo_data.py
```

## Option 2: Run via Docker Exec

```bash
# Run seed script directly
docker compose -f docker-compose.prod.yml exec backend python -m app.tasks.seed_demo_data
```

## Expected Output

You should see:
```
🌱 Seeding demo data...
✓ Created machine: Pump-01
  ✓ Created 4 sensors for Pump-01
✓ Created machine: Motor-02
  ✓ Created 4 sensors for Motor-02
✓ Created machine: Compressor-A
  ✓ Created 4 sensors for Compressor-A
✓ Created machine: Conveyor-B2
  ✓ Created 4 sensors for Conveyor-B2
✅ Seeding complete!
```

## Verify Machines Created

```bash
# Check machines in database
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db -c "SELECT name, location, status FROM machines;"
```

You should see all 4 machines:
- Pump-01
- Motor-02
- Compressor-A
- Conveyor-B2

## After Seeding

1. **Restart backend** (optional, but recommended):
   ```bash
   docker compose -f docker-compose.prod.yml restart backend
   ```

2. **Start simulator** (if not running):
   ```bash
   docker compose -f docker-compose.prod.yml up -d simulator
   ```

3. **Check dashboard**: Go to http://37.120.176.43:3000/machines
   - You should now see all 4 machines

4. **Wait 1-2 minutes** for simulator data to populate
   - Check Sensors page for live data
   - Check Predictions page for AI predictions

## Troubleshooting

### If machines already exist:
The script checks for existing machines by name, so it won't create duplicates. If you want to recreate them:

```bash
# Delete existing machines (be careful!)
docker compose -f docker-compose.prod.yml exec postgres psql -U pm_user -d pm_db -c "DELETE FROM sensors; DELETE FROM machines;"

# Then run seed script again
docker compose -f docker-compose.prod.yml exec backend python -m app.tasks.seed_demo_data
```

### If seed script fails:
Check backend logs:
```bash
docker compose -f docker-compose.prod.yml logs backend | tail -50
```



