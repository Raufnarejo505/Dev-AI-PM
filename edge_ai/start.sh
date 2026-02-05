#!/bin/bash
# Quick start script for Edge / AI Application

set -e

echo "🚀 Starting Edge / AI Application"
echo ""

# Load environment variables from .env if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run the application
python main.py
