#!/bin/bash
# Netcup Deployment Script
# Run this script on your Netcup server after uploading the project

set -e  # Exit on error

echo "🚀 Starting Predictive Maintenance Platform Deployment on Netcup..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Check if Docker Compose is installed
if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Installing..."
    apt update
    apt install -y docker-compose-plugin
fi

# Navigate to project directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "📁 Project directory: $SCRIPT_DIR"

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  backend/.env not found. Creating from example..."
    cp backend/env.example backend/.env
    echo "✅ Created backend/.env - Please edit it with your configuration!"
    echo "   Important: Set JWT_SECRET and POSTGRES_PASSWORD"
    read -p "Press Enter after editing backend/.env to continue..."
fi

# Generate JWT secret if not set
if grep -q "change-me" backend/.env || grep -q "JWT_SECRET=$" backend/.env; then
    echo "🔐 Generating JWT secret..."
    JWT_SECRET=$(openssl rand -hex 32)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" backend/.env
    else
        # Linux
        sed -i "s/JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" backend/.env
    fi
    echo "✅ JWT secret generated and set"
fi

# Build Docker images
echo "🔨 Building Docker images..."
docker compose -f docker-compose.prod.yml build

# Start services
echo "🚀 Starting services..."
docker compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to initialize (30 seconds)..."
sleep 30

# Check service status
echo "📊 Checking service status..."
docker compose -f docker-compose.prod.yml ps

# Check backend health
echo "🏥 Checking backend health..."
for i in {1..10}; do
    if curl -f http://localhost/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy!"
        break
    else
        echo "⏳ Waiting for backend... ($i/10)"
        sleep 5
    fi
done

# Seed demo data
echo "🌱 Seeding demo data..."
docker compose -f docker-compose.prod.yml exec -T backend python -m app.tasks.seed_demo_data || echo "⚠️  Demo data seeding failed (may already exist)"

# Final status
echo ""
echo "✅ Deployment Complete!"
echo ""
echo "📋 Service URLs:"
echo "   Frontend: http://$(hostname -I | awk '{print $1}')"
echo "   Backend API: http://$(hostname -I | awk '{print $1}')/api"
echo "   API Docs: http://$(hostname -I | awk '{print $1}')/api/docs"
echo ""
echo "👤 Demo Login:"
echo "   Admin: admin@example.com / admin123"
echo "   Engineer: engineer@example.com / engineer123"
echo "   Viewer: viewer@example.com / viewer123"
echo ""
echo "📝 Useful Commands:"
echo "   View logs: docker compose -f docker-compose.prod.yml logs -f"
echo "   Restart: docker compose -f docker-compose.prod.yml restart"
echo "   Stop: docker compose -f docker-compose.prod.yml stop"
echo ""

