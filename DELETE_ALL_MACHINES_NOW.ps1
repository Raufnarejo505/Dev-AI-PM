# PowerShell script to delete ALL machines and refresh frontend

Write-Host "=== Deleting ALL Machines ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Force delete all machines using Python script
Write-Host "Step 1: Deleting all machines from database..." -ForegroundColor Yellow
docker-compose exec backend python /app/scripts/force_delete_all_machines.py

Write-Host ""
Write-Host "Step 2: Verifying deletion..." -ForegroundColor Yellow
docker-compose exec postgres psql -U pm_user -d pm_db -c "SELECT COUNT(*) as total_machines FROM machine;"

Write-Host ""
Write-Host "Step 3: Restarting backend to clear cache..." -ForegroundColor Yellow
docker-compose restart backend

Write-Host ""
Write-Host "Step 4: Restarting frontend to clear cache..." -ForegroundColor Yellow
docker-compose restart frontend

Write-Host ""
Write-Host "✅ Done! Please:" -ForegroundColor Green
Write-Host "   1. Wait 10-15 seconds for services to restart" -ForegroundColor Yellow
Write-Host "   2. Hard refresh your browser (Ctrl+Shift+R)" -ForegroundColor Yellow
Write-Host "   3. Check the Machines tab - it should be empty" -ForegroundColor Yellow
Write-Host ""
