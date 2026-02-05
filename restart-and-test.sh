#!/bin/bash
# Script to restart services and run health checks
# Usage: ./restart-and-test.sh

set -e

echo "🔄 Restarting Predictive Maintenance Platform..."
echo ""

# Stop all services
echo "⏹️  Step 1: Stopping all services..."
docker compose down

echo ""
echo "🏗️  Step 2: Rebuilding containers (if needed)..."
docker compose build --no-cache backend

echo ""
echo "🚀 Step 3: Starting all services..."
docker compose up -d

echo ""
echo "⏳ Step 4: Waiting for services to start (30 seconds)..."
sleep 30

echo ""
echo "📊 Step 5: Checking service status..."
docker compose ps

echo ""
echo "🧪 Step 6: Testing health endpoints..."
echo ""

# Test backend health
echo "🔍 Testing Backend Health:"
echo "  - Basic health:"
curl -s http://localhost:8000/health | jq '.' || curl -s http://localhost:8000/health
echo ""
echo "  - Liveness probe:"
curl -s http://localhost:8000/health/live | jq '.' || curl -s http://localhost:8000/health/live
echo ""
echo "  - Readiness probe:"
curl -s http://localhost:8000/health/ready | jq '.' || curl -s http://localhost:8000/health/ready
echo ""

# Test frontend
echo "🔍 Testing Frontend:"
echo "  - Frontend accessible:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:3000 || echo "⚠️  Frontend not responding"
echo ""

# Test API docs
echo "🔍 Testing API Documentation:"
echo "  - OpenAPI schema:"
curl -s http://localhost:8000/openapi.json | grep -o '"openapi": "[^"]*"' | head -1 || echo "⚠️  Could not fetch OpenAPI schema"
echo "  - Swagger UI: http://localhost:3000/api/docs"
echo ""

# Test root endpoint
echo "🔍 Testing Root Endpoint:"
curl -s http://localhost:8000/ | jq '.' || curl -s http://localhost:8000/
echo ""

# Check container health
echo "📋 Container Health Status:"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "✅ Restart and test complete!"
echo ""
echo "🌐 Access Points:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:3000/api/docs"
echo "  - Health: http://localhost:8000/health"
echo ""


