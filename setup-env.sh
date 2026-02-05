#!/bin/bash
# Script to configure .env file on Netcup server

# JWT Secret from previous generation
JWT_SECRET="0f3df7be80e40b57e1b2885f892b90876a10dd0bb2bc053e2dd49a0f9ac4fcd2"
POSTGRES_PASSWORD="Netcup2025!StrongPass123"

# Create .env file with proper configuration
cat > backend/.env << 'EOF'
##############################
# Backend / Database
##############################
POSTGRES_USER=pm_user
POSTGRES_PASSWORD=Netcup2025!StrongPass123
POSTGRES_DB=pm_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

##############################
# Authentication
##############################
JWT_SECRET=0f3df7be80e40b57e1b2885f892b90876a10dd0bb2bc053e2dd49a0f9ac4fcd2
JWT_ALGORITHM=HS256
JWT_EXP_MINUTES=60

##############################
# MQTT Broker
##############################
MQTT_BROKER_HOST=mqtt
MQTT_BROKER_PORT=1883
MQTT_TOPICS=factory/#,edge/#

##############################
# AI Service
##############################
AI_SERVICE_URL=http://ai-service:8000

##############################
# Notifications (Gmail SMTP - Optional)
# Configure if you want email notifications
##############################
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=your-email@gmail.com
EMAIL_SMTP_PASS=your-16-char-app-password-here
NOTIFICATION_EMAIL_TO=recipient@example.com

##############################
# Optional Integrations
##############################
SLACK_WEBHOOK_URL=
EOF

echo "✅ .env file created successfully!"
echo ""
echo "Configuration:"
echo "  - JWT_SECRET: Set to generated secret"
echo "  - POSTGRES_PASSWORD: Set to strong password"
echo ""
echo "You can now run: ./deploy-netcup.sh"

