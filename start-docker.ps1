# Start Predictive Maintenance System with Docker Compose
# This script will build and start all services

Write-Host "🚀 Starting Predictive Maintenance Platform..." -ForegroundColor Cyan
Write-Host ""

# Check if docker-compose.yml exists
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "❌ Error: docker-compose.yml not found!" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory." -ForegroundColor Yellow
    exit 1
}

Write-Host "📦 Building and starting all services..." -ForegroundColor Yellow
Write-Host "This may take a few minutes on first run..." -ForegroundColor Yellow
Write-Host ""

# Start docker-compose in detached mode
docker-compose up --build -d

Write-Host ""
Write-Host "⏳ Waiting for services to initialize (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host ""
Write-Host "📊 Service Status:" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "🔍 Checking service health..." -ForegroundColor Cyan
Write-Host ""

# Check backend health
try {
    $backendHealth = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($backendHealth.StatusCode -eq 200) {
        Write-Host "✅ Backend is healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "⏳ Backend is still starting..." -ForegroundColor Yellow
}

# Check AI service health
try {
    $aiHealth = Invoke-WebRequest -Uri "http://localhost:8001/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($aiHealth.StatusCode -eq 200) {
        Write-Host "✅ AI Service is healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "⏳ AI Service is still starting..." -ForegroundColor Yellow
}

# Check frontend
try {
    $frontend = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($frontend.StatusCode -eq 200) {
        Write-Host "✅ Frontend is accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "⏳ Frontend is still starting..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "🎉 Docker services are starting!" -ForegroundColor Green
Write-Host ""
Write-Host "Access Points:" -ForegroundColor Yellow
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "  AI Service: http://localhost:8001" -ForegroundColor White
Write-Host ""
Write-Host "View logs: docker-compose logs -f" -ForegroundColor Cyan
Write-Host "Stop services: docker-compose down" -ForegroundColor Cyan
Write-Host ""
Write-Host "⏳ Give services 1-2 minutes to fully initialize..." -ForegroundColor Yellow
Write-Host "Then open http://localhost:3000 in your browser!" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan

