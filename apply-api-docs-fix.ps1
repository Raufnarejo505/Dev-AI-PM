# PowerShell script to apply API documentation fix
# Run this on your Windows machine if you have SSH access, or copy commands to server

Write-Host "🔧 Applying API Documentation Fix..." -ForegroundColor Cyan
Write-Host ""

# Commands to run on your Netcup server (via SSH or direct access)
Write-Host "📋 Commands to run on your server:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Navigate to project directory:" -ForegroundColor Green
Write-Host "   cd '/root/Predictive Maintenance'" -ForegroundColor White
Write-Host ""
Write-Host "2. Rebuild backend container:" -ForegroundColor Green
Write-Host "   docker compose -f docker-compose.prod.yml build backend" -ForegroundColor White
Write-Host ""
Write-Host "3. Restart backend container:" -ForegroundColor Green
Write-Host "   docker compose -f docker-compose.prod.yml restart backend" -ForegroundColor White
Write-Host ""
Write-Host "4. Wait for backend to start:" -ForegroundColor Green
Write-Host "   sleep 8" -ForegroundColor White
Write-Host ""
Write-Host "5. Check backend status:" -ForegroundColor Green
Write-Host "   docker compose -f docker-compose.prod.yml ps backend" -ForegroundColor White
Write-Host ""
Write-Host "6. Test OpenAPI schema:" -ForegroundColor Green
Write-Host "   curl http://localhost:8000/openapi.json | grep 'openapi'" -ForegroundColor White
Write-Host ""
Write-Host "✅ After running these commands, test:" -ForegroundColor Cyan
Write-Host "   - http://37.120.176.43:3000/api/docs" -ForegroundColor Yellow
Write-Host "   - http://37.120.176.43:3000/api/redoc" -ForegroundColor Yellow
Write-Host ""


