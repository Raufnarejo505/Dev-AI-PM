#!/bin/bash

set -e

echo "🚀 Starting Predictive Maintenance Platform..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Build and start services
echo -e "${BLUE}📦 Building Docker images...${NC}"
docker-compose build

echo -e "${BLUE}🚀 Starting services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 10

# Wait for database
echo -e "${YELLOW}⏳ Waiting for database...${NC}"
until docker-compose exec -T postgres pg_isready -U pm_user > /dev/null 2>&1; do
    sleep 2
done

# Wait for backend
echo -e "${YELLOW}⏳ Waiting for backend...${NC}"
until curl -f http://localhost:8000/health > /dev/null 2>&1; do
    sleep 2
done

# Seed database
echo -e "${BLUE}🌱 Seeding database with demo data...${NC}"
docker-compose exec -T backend python -m app.tasks.seed_demo_data || echo "⚠️  Seed script may have already run"

echo -e "${GREEN}✅ All services are running!${NC}"
echo ""
echo "📍 Access Points:"
echo "   Frontend:    http://localhost:3000"
echo "   Backend API: http://localhost:8000/docs"
echo "   AI Service:  http://localhost:8001/health"
echo ""
echo "👤 Demo Users:"
echo "   Admin:    admin@example.com / admin123"
echo "   Engineer: engineer@example.com / engineer123"
echo "   Viewer:   viewer@example.com / viewer123"
echo ""
echo "📝 Test Login:"
echo "   curl -X POST http://localhost:8000/users/login \\"
echo "     -H 'Content-Type: application/x-www-form-urlencoded' \\"
echo "     -d 'username=admin@example.com&password=admin123'"
echo ""
echo "🔍 View Logs:"
echo "   docker-compose logs -f [service_name]"
echo ""
echo "🛑 Stop Services:"
echo "   docker-compose down"
