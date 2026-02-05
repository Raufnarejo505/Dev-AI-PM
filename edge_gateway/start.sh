#!/bin/bash
# Quick start script for OPC UA → MQTT Gateway

set -e

echo "🚀 Starting OPC UA → MQTT Gateway"
echo ""

# Load environment variables from .env if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run the gateway
python main.py
