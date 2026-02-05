# PowerShell script to restart and test services
# Usage: .\restart-and-test.ps1

Write-Host "🔄 Restarting Predictive Maintenance Platform..." -ForegroundColor Cyan
Write-Host ""

# Stop all services
Write-Host "⏹️  Step 1: Stopping all services..." -ForegroundColor Yellow
docker compose down

Write-Host ""
Write-Host "🏗️  Step 2: Rebuilding containers (if needed)..." -ForegroundColor Yellow
docker compose build --no-cache backend

Write-Host ""
Write-Host "🚀 Step 3: Starting all services..." -ForegroundColor Yellow
docker compose up -d

Write-Host ""
Write-Host "⏳ Step 4: Waiting for services to start (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host ""
Write-Host "📊 Step 5: Checking service status..." -ForegroundColor Yellow
docker compose ps

Write-Host ""
Write-Host "🧪 Step 6: Testing health endpoints..." -ForegroundColor Yellow
Write-Host ""

# Test backend health
Write-Host "🔍 Testing Backend Health:" -ForegroundColor Green
Write-Host "  - Basic health:" -ForegroundColor White
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
    $response.Content | ConvertFrom-Json | ConvertTo-Json
} catch {
    Write-Host "  ⚠️  Backend not responding: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "  - Liveness probe:" -ForegroundColor White
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health/live" -UseBasicParsing
    $response.Content | ConvertFrom-Json | ConvertTo-Json
} catch {
    Write-Host "  ⚠️  Liveness check failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "  - Readiness probe:" -ForegroundColor White
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health/ready" -UseBasicParsing
    $response.Content | ConvertFrom-Json | ConvertTo-Json
} catch {
    Write-Host "  ⚠️  Readiness check failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test frontend
Write-Host "🔍 Testing Frontend:" -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing
    Write-Host "  ✅ Frontend accessible (HTTP $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Frontend not responding: $_" -ForegroundColor Red
}

Write-Host ""

# Test API docs
Write-Host "🔍 Testing API Documentation:" -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/openapi.json" -UseBasicParsing
    $json = $response.Content | ConvertFrom-Json
    Write-Host "  ✅ OpenAPI version: $($json.openapi)" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Could not fetch OpenAPI schema: $_" -ForegroundColor Red
}
Write-Host "  - Swagger UI: http://localhost:3000/api/docs" -ForegroundColor Cyan

Write-Host ""

# Test root endpoint
Write-Host "🔍 Testing Root Endpoint:" -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing
    $response.Content | ConvertFrom-Json | ConvertTo-Json
} catch {
    Write-Host "  ⚠️  Root endpoint failed: $_" -ForegroundColor Red
}

Write-Host ""

# Check container health
Write-Host "📋 Container Health Status:" -ForegroundColor Yellow
docker compose ps

Write-Host ""
Write-Host "✅ Restart and test complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Access Points:" -ForegroundColor Cyan
Write-Host "  - Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  - Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "  - API Docs: http://localhost:3000/api/docs" -ForegroundColor White
Write-Host "  - Health: http://localhost:8000/health" -ForegroundColor White
Write-Host ""


