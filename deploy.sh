#!/bin/bash

# Autoclave Quick Deploy Script for Raspberry Pi
# This script automates the entire deployment process

set -e  # Exit on error

echo "================================================"
echo "  Autoclave Control System - Quick Deploy"
echo "================================================"
echo ""

# Detect user and project directory
PROJECT_DIR=$(pwd)
USER=$(whoami)

echo "Project directory: $PROJECT_DIR"
echo "User: $USER"
echo ""

# Step 1: Check Docker
echo "[1/7] Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker not installed!"
    echo "Run: curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh"
    exit 1
fi
echo "✓ Docker installed"

# Step 2: Check Docker Compose
echo "[2/7] Checking Docker Compose..."
if ! command -v docker compose &> /dev/null; then
    echo "Installing docker-compose-plugin..."
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
fi
echo "✓ Docker Compose installed"

# Step 3: Create .env if not exists
echo "[3/7] Setting up environment..."
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# Modbus Configuration
COM_PORT=/dev/ttyACM0
BAUD_RATE=9600
SLAVE_ID=1

# PostgreSQL Configuration
PG_HOST=postgres
PG_PORT=5432
PG_DATABASE=autoclave
PG_USER=postgres
PG_PASSWORD=postgres
EOF
    echo "✓ Created .env file"
else
    echo "✓ .env file exists"
fi

# Step 4: Fix permissions for serial devices
echo "[4/7] Fixing serial device permissions..."
if ls /dev/ttyACM* &>/dev/null; then
    sudo chmod 666 /dev/ttyACM*
    echo "✓ Fixed permissions for /dev/ttyACM*"
fi
if ls /dev/ttyUSB* &>/dev/null; then
    sudo chmod 666 /dev/ttyUSB*
    echo "✓ Fixed permissions for /dev/ttyUSB*"
fi
if ls /dev/ttyAMA* &>/dev/null; then
    sudo chmod 666 /dev/ttyAMA*
    echo "✓ Fixed permissions for /dev/ttyAMA*"
fi

# Step 5: Build Docker images
echo "[5/7] Building Docker images..."
echo "This may take 10-15 minutes on Raspberry Pi..."
docker compose build
echo "✓ Docker images built"

# Step 6: Start services
echo "[6/7] Starting services..."
docker compose up -d
echo "✓ Services started"

# Step 7: Wait for services and check status
echo "[7/7] Checking service status..."
sleep 5
docker compose ps

echo ""
echo "================================================"
echo "  Deployment Complete!"
echo "================================================"
echo ""
echo "Access the application at:"
echo "  http://$(hostname -I | awk '{print $1}')"
echo ""
echo "Or locally:"
echo "  http://raspberrypi.local"
echo ""
echo "Services:"
echo "  Frontend:  http://$(hostname -I | awk '{print $1}')"
echo "  API:       http://$(hostname -I | awk '{print $1}'):5000"
echo "  Database:  localhost:5432"
echo ""
echo "View logs:"
echo "  docker compose logs -f"
echo ""
echo "Stop services:"
echo "  docker compose down"
echo ""

