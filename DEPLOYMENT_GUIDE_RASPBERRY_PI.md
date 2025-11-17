# Deployment Guide - Raspberry Pi

This guide covers deploying the latest changes to your Raspberry Pi system.

## Prerequisites

- SSH access to Raspberry Pi
- Git installed on Raspberry Pi
- Python 3.x installed
- Node.js and npm installed (for frontend)
- PostgreSQL running
- Existing repository cloned on Raspberry Pi

## Step-by-Step Deployment

### Step 1: SSH into Raspberry Pi

```bash
ssh pi@<raspberry-pi-ip-address>
# Or use your configured SSH alias
```

### Step 2: Navigate to Project Directory

```bash
cd /path/to/clave-master
# Example: cd ~/clave-master or cd /home/pi/clave-master
```

### Step 3: Backup Current State (Recommended)

```bash
# Create a backup branch
git branch backup-$(date +%Y%m%d-%H%M%S)

# Or backup the entire directory
cp -r /path/to/clave-master /path/to/clave-master-backup-$(date +%Y%m%d)
```

### Step 4: Pull Latest Changes from GitHub

```bash
# Check current branch
git branch

# Ensure you're on main branch
git checkout main

# Fetch latest changes
git fetch origin

# Pull latest changes
git pull origin main
```

### Step 5: Install/Update Backend Dependencies

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment if you're using one
# source venv/bin/activate  # Uncomment if using venv

# Install/update Python dependencies
pip3 install -r requirements.txt

# Or if using system Python
sudo pip3 install -r requirements.txt
```

**New dependencies added:**
- `reportlab==4.0.7` (PDF generation)
- `matplotlib==3.8.2` (Chart generation)
- `pytz==2024.1` (Timezone support)

### Step 6: Install/Update Frontend Dependencies

```bash
# Navigate to project root
cd ..

# Install/update npm packages
npm install

# New dependency: date-fns-tz@3.0.0
```

### Step 7: Database Updates

#### Option A: If using Docker (Recommended)

```bash
# Stop containers
docker-compose down

# Rebuild containers (if Dockerfile changed)
docker-compose build

# Start containers
docker-compose up -d

# Check logs
docker-compose logs -f
```

#### Option B: If using Local PostgreSQL

```bash
# Connect to PostgreSQL
psql -U postgres -d autoclave

# Check if JSW Roll category exists
SELECT * FROM roll_categories WHERE category_name = 'JSW Roll';

# If it doesn't exist, run the init script
# Exit psql first
exit

# Run database initialization (if needed)
python3 backend/docker-init-db.py
```

### Step 8: Update Environment Variables (if needed)

Check `.env` file in backend directory:

```bash
cd backend
cat .env
```

Ensure these are set correctly:
- `COM_PORT` - Serial port (e.g., `/dev/ttyACM0` for Raspberry Pi)
- `BAUD_RATE` - Usually 9600
- `SLAVE_ID` - Modbus slave ID
- `PG_HOST` - PostgreSQL host (usually `127.0.0.1` or `localhost`)
- `PG_PORT` - PostgreSQL port (usually `5432`)
- `PG_DATABASE` - Database name (usually `autoclave`)
- `PG_USER` - PostgreSQL user
- `PG_PASSWORD` - PostgreSQL password

### Step 9: Stop Running Services

```bash
# Find running Python processes
ps aux | grep sensor_control_service
ps aux | grep api_server

# Stop them (replace PID with actual process ID)
kill <PID>

# Or if using systemd services
sudo systemctl stop sensor-control-service
sudo systemctl stop api-server

# Or if using screen/tmux
screen -r  # or tmux attach
# Then Ctrl+C to stop services
```

### Step 10: Verify Serial Port Permissions

```bash
# Check if user has access to serial port
ls -l /dev/ttyACM0

# If permission denied, add user to dialout group
sudo usermod -a -G dialout $USER

# Log out and log back in for changes to take effect
# Or use:
newgrp dialout
```

### Step 11: Start Backend Services

#### Option A: Using Screen (Recommended for testing)

```bash
# Start sensor control service
screen -S sensor-service
cd /path/to/clave-master/backend
python3 sensor_control_service.py
# Press Ctrl+A then D to detach

# Start API server
screen -S api-server
cd /path/to/clave-master/backend
python3 api_server.py
# Press Ctrl+A then D to detach

# View screens
screen -ls
screen -r sensor-service  # To reattach
```

#### Option B: Using systemd (Recommended for production)

Create service files:

**`/etc/systemd/system/sensor-control-service.service`:**
```ini
[Unit]
Description=Sensor Control Service
After=network.target postgresql.service

[Service]
Type=simple
User=pi
WorkingDirectory=/path/to/clave-master/backend
ExecStart=/usr/bin/python3 /path/to/clave-master/backend/sensor_control_service.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**`/etc/systemd/system/api-server.service`:**
```ini
[Unit]
Description=API Server
After=network.target postgresql.service

[Service]
Type=simple
User=pi
WorkingDirectory=/path/to/clave-master/backend
ExecStart=/usr/bin/python3 /path/to/clave-master/backend/api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable sensor-control-service
sudo systemctl enable api-server

# Start services
sudo systemctl start sensor-control-service
sudo systemctl start api-server

# Check status
sudo systemctl status sensor-control-service
sudo systemctl status api-server

# View logs
sudo journalctl -u sensor-control-service -f
sudo journalctl -u api-server -f
```

### Step 12: Start Frontend (if running on Pi)

```bash
# Navigate to project root
cd /path/to/clave-master

# Build frontend
npm run build

# If using a web server (nginx/apache), copy build files
# Or run dev server (not recommended for production)
npm run dev
```

### Step 13: Verify Deployment

#### Check Backend Services

```bash
# Check if services are running
ps aux | grep python

# Check API server
curl http://localhost:5000/api/health

# Check sensor readings
curl http://localhost:5000/api/sensor-readings/latest
```

#### Check Logs

```bash
# If using screen
screen -r sensor-service
# Check for any errors

# If using systemd
sudo journalctl -u sensor-control-service -n 50
sudo journalctl -u api-server -n 50
```

#### Test Features

1. **PDF Report Generation:**
   - Access historical data in frontend
   - Select a session
   - Click "Generate PDF Report"
   - Verify PDF downloads correctly

2. **IST Timezone:**
   - Check timestamps in frontend
   - Verify they show IST time (UTC+5:30)

3. **Buzzer Control:**
   - Start a control session
   - Monitor logs for buzzer activation messages
   - Verify buzzer activates when pressure is below threshold

4. **Temperature Adjustment:**
   - Check temperature readings
   - Verify temperatures above 80°C are adjusted

### Step 14: Troubleshooting

#### Serial Port Issues

```bash
# Check if device is connected
ls -l /dev/ttyACM*

# Check dmesg for USB device
dmesg | tail -20

# Test serial port access
python3 -c "import serial; print(serial.tools.list_ports.comports())"
```

#### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -U postgres -d autoclave -c "SELECT 1;"

# Check PostgreSQL is running
sudo systemctl status postgresql
```

#### Permission Issues

```bash
# Check file permissions
ls -l backend/sensor_control_service.py
ls -l backend/api_server.py

# Make scripts executable if needed
chmod +x backend/sensor_control_service.py
chmod +x backend/api_server.py
```

#### Missing Dependencies

```bash
# Verify Python packages
pip3 list | grep -E "reportlab|matplotlib|pytz|pymodbus|psycopg2"

# Verify npm packages
npm list | grep date-fns-tz
```

### Step 15: Rollback (if needed)

If something goes wrong:

```bash
# Stop services
sudo systemctl stop sensor-control-service
sudo systemctl stop api-server

# Rollback to previous commit
git log  # Find previous commit hash
git checkout <previous-commit-hash>

# Or restore from backup
cd /path/to/clave-master-backup-<date>
# Copy files back

# Restart services
sudo systemctl start sensor-control-service
sudo systemctl start api-server
```

## Quick Deployment Script

You can create a deployment script:

**`deploy.sh`:**
```bash
#!/bin/bash
set -e

echo "Starting deployment..."

# Navigate to project
cd /path/to/clave-master

# Pull latest
git pull origin main

# Update backend dependencies
cd backend
pip3 install -r requirements.txt

# Update frontend dependencies
cd ..
npm install

# Restart services
sudo systemctl restart sensor-control-service
sudo systemctl restart api-server

echo "Deployment complete!"
```

Make it executable:
```bash
chmod +x deploy.sh
```

Run it:
```bash
./deploy.sh
```

## Post-Deployment Checklist

- [ ] Services are running without errors
- [ ] API health check returns success
- [ ] Sensor readings are being logged
- [ ] Frontend can connect to API
- [ ] PDF reports generate correctly
- [ ] Timestamps show IST timezone
- [ ] Buzzer activates when pressure is low
- [ ] Temperature readings are adjusted above 80°C
- [ ] All 25 roll categories are available
- [ ] Database contains all programs

## Notes

- **Serial Port:** On Raspberry Pi, the RS485-to-USB converter typically appears as `/dev/ttyACM0` or `/dev/ttyUSB0`
- **Timezone:** Ensure Raspberry Pi system timezone is set correctly (though code uses IST internally)
- **Permissions:** User must be in `dialout` group for serial port access
- **Firewall:** Ensure port 5000 (API) and frontend port are accessible
- **Logs:** Monitor logs for first few minutes after deployment

## Support

If you encounter issues:
1. Check service logs
2. Verify all dependencies are installed
3. Check serial port permissions
4. Verify database connection
5. Review error messages in logs

