# PowerShell script to delete all machines except OPCUA-Simulation-Machine
# Run this from the project root directory

Write-Host "=== Machine Deletion Script ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: List all current machines
Write-Host "Current machines in database:" -ForegroundColor Yellow
docker-compose exec -T postgres psql -U pm_user -d pm_db -c "SELECT id, name, created_at FROM machine ORDER BY created_at;"

Write-Host ""
Write-Host "Press Enter to continue with deletion, or Ctrl+C to cancel..."
Read-Host

# Step 2: Delete all machines except OPCUA-Simulation-Machine
Write-Host "Deleting all machines except 'OPCUA-Simulation-Machine'..." -ForegroundColor Yellow

# Use case-insensitive match and handle potential variations
$deleteCommand = @"
DELETE FROM machine 
WHERE LOWER(TRIM(name)) != LOWER('OPCUA-Simulation-Machine');
"@

docker-compose exec -T postgres psql -U pm_user -d pm_db -c $deleteCommand

# Step 3: Verify deletion
Write-Host ""
Write-Host "Remaining machines:" -ForegroundColor Green
docker-compose exec -T postgres psql -U pm_user -d pm_db -c "SELECT id, name FROM machine;"

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
