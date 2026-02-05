#!/bin/bash
# Script to apply the API documentation fix
# Run this on your Netcup server

set -e

echo "🔧 Applying API Documentation Fix..."
echo ""

# Navigate to project directory (adjust path if needed)
cd "/root/Predictive Maintenance" || cd "$(dirname "$0")"

echo "📦 Step 1: Rebuilding backend container..."
docker compose -f docker-compose.prod.yml build backend

echo ""
echo "🔄 Step 2: Restarting backend container..."
docker compose -f docker-compose.prod.yml restart backend

echo ""
echo "⏳ Step 3: Waiting for backend to start..."
sleep 8

echo ""
echo "✅ Step 4: Checking backend status..."
docker compose -f docker-compose.prod.yml ps backend

echo ""
echo "🧪 Step 5: Testing OpenAPI schema..."
echo "Checking OpenAPI version..."
curl -s http://localhost:8000/openapi.json | grep -o '"openapi": "[^"]*"' | head -1 || echo "⚠️  Could not fetch OpenAPI schema (backend might still be starting)"

echo ""
echo "🧪 Step 6: Testing health endpoint..."
curl -s http://localhost:8000/health | head -20 || echo "⚠️  Backend not responding yet"

echo ""
echo "📋 Summary:"
echo "  - Backend container rebuilt"
echo "  - Backend container restarted"
echo ""
echo "🌐 Access API Documentation:"
echo "  - Swagger UI: http://37.120.176.43:3000/api/docs"
echo "  - ReDoc: http://37.120.176.43:3000/api/redoc"
echo "  - OpenAPI JSON: http://37.120.176.43:3000/api/openapi.json"
echo ""
echo "✅ Fix applied! Please test the API docs in your browser."


