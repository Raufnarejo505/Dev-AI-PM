# PowerShell script for local development

Write-Host "🚀 Starting Predictive Maintenance Platform..." -ForegroundColor Cyan

# Build and start services
Write-Host "`n📦 Building Docker images..." -ForegroundColor Blue
docker-compose build

Write-Host "`n🚀 Starting services..." -ForegroundColor Blue
docker-compose up -d

# Wait for services
Write-Host "`n⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Wait for database
Write-Host "⏳ Waiting for database..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
do {
    Start-Sleep -Seconds 2
    $attempt++
    try {
        docker-compose exec -T postgres pg_isready -U pm_user 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { break }
    } catch {}
} while ($attempt -lt $maxAttempts)

# Wait for backend
Write-Host "⏳ Waiting for backend..." -ForegroundColor Yellow
$attempt = 0
do {
    Start-Sleep -Seconds 2
    $attempt++
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) { break }
    } catch {}
} while ($attempt -lt $maxAttempts)

# Seed database
Write-Host "`n🌱 Seeding database with demo data..." -ForegroundColor Blue
docker-compose exec -T backend python -m app.tasks.seed_demo_data 2>&1 | Out-Null

Write-Host "`n✅ All services are running!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Access Points:" -ForegroundColor Cyan
Write-Host "   Frontend:    http://localhost:3000" -ForegroundColor White
Write-Host "   Backend API: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   AI Service:  http://localhost:8001/health" -ForegroundColor White
Write-Host ""
Write-Host "👤 Demo Users:" -ForegroundColor Cyan
Write-Host "   Admin:    admin@example.com / admin123" -ForegroundColor White
Write-Host "   Engineer: engineer@example.com / engineer123" -ForegroundColor White
Write-Host "   Viewer:   viewer@example.com / viewer123" -ForegroundColor White
Write-Host ""
Write-Host "📝 Test Login:" -ForegroundColor Cyan
Write-Host '   $formData = @{username="admin@example.com"; password="admin123"}' -ForegroundColor White
Write-Host '   Invoke-WebRequest -Uri "http://localhost:8000/users/login" -Method POST -Body $formData -ContentType "application/x-www-form-urlencoded"' -ForegroundColor White
Write-Host ""
Write-Host "🛑 Stop Services:" -ForegroundColor Cyan
Write-Host "   docker-compose down" -ForegroundColor White
