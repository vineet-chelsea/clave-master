# 🐳 Docker Deployment for Raspberry Pi

## Overview

Complete Docker setup for Autoclave Control System on Raspberry Pi with:
- **PostgreSQL** database
- **Python Backend** (sensor service + API)
- **React Frontend** (Nginx)
- **Modbus Communication** via USB

## Prerequisites

### Raspberry Pi Setup
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo pip3 install docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

### Hardware Requirements
- Raspberry Pi 4 (recommended) or Pi 3
- USB-to-RS485 adapter (for Modbus)
- PLC connected to Modbus

## Quick Start

### 1. Clone Repository
```bash
cd /home/pi
git clone <your-repo-url> autoclave
cd autoclave
```

### 2. Update Configuration

Edit `.env` for your Modbus settings:
```bash
nano .env
```

```env
# Modbus Configuration
COM_PORT=/dev/ttyUSB0
BAUD_RATE=9600
PARITY=N
STOP_BITS=1
BYTE_SIZE=8
SLAVE_ID=1

# PostgreSQL (default for Docker)
PG_HOST=postgres
PG_PORT=5432
PG_DATABASE=autoclave
PG_USER=postgres
PG_PASSWORD=postgres
```

### 3. Build and Run
```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Access Application
- **Frontend:**** http://pi-ip-address
- **API:** http://pi-ip-address:5000
- **Database:** localhost:5432

## Docker Services

### PostgreSQL Database
```yaml
- Image: postgres:15-alpine
- Port: 5432
- Data: Persistent volume
- Auto-initialization: Yes
```

### Backend Services
```yaml
- Image: Custom Python 3.11
- Port: 5000
- Includes:
  * Sensor control service
  * API server
  * Modbus communication
- Device: /dev/ttyUSB0
```

### Frontend
```yaml
- Image: Nginx Alpine
- Port: 80
- Built from: React source
- Static files served via Nginx
```

## Project Structure

```
autoclave/
├── docker-compose.yml      # Main orchestration
├── Dockerfile.frontend     # React build
├── Dockerfile.backend      # Python services
├── nginx.conf             # Frontend config
├── .dockerignore          # Build exclusions
├── backend/
│   ├── docker-init-db.py  # DB initialization
│   ├── sensor_control_service.py
│   ├── api_server.py
│   └── requirements.txt
└── src/                   # React source
```

## Database Initialization

The database is automatically initialized with:
1. `sensor_readings` - Sensor data
2. `process_sessions` - Control sessions
3. `process_logs` - Session logs
4. `autoclave_programs` - Auto programs

Run manually if needed:
```bash
docker-compose exec backend python docker-init-db.py
```

## Modbus Device Access

### Finding Your USB Device
```bash
lsusb
# Look for USB-to-Serial adapter

dmesg | grep tty
# Check device path
```

### Common Devices
- `/dev/ttyUSB0` - USB adapter
- `/dev/ttyACM0` - Arduino-based adapters
- `/dev/ttyAMA0` - GPIO serial (Pi 3)

### Grant Permissions
```bash
sudo chmod 666 /dev/ttyUSB0
# Or add user to dialout group
sudo usermod -aG dialout $USER
```

## Environment Variables

Create `.env` file in project root:
```env
# Modbus
COM_PORT=/dev/ttyUSB0
BAUD_RATE=9600
SLAVE_ID=1

# Database
PG_HOST=postgres
PG_PORT=5432
PG_DATABASE=autoclave
PG_USER=postgres
PG_PASSWORD=postgres
```

## Useful Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific
docker-compose restart backend
```

### Access Database
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d autoclave

# Run SQL
docker-compose exec postgres psql -U postgres -d autoclave -c "SELECT * FROM process_sessions;"
```

### Rebuild After Changes
```bash
# Rebuild specific service
docker-compose build backend
docker-compose up -d --no-deps backend

# Rebuild all
docker-compose build --no-cache
docker-compose up -d
```

### Stop and Remove
```bash
# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes data!)
docker-compose down -v
```

## Troubleshooting

### Modbus Connection Issues
```bash
# Check device exists
ls -l /dev/ttyUSB0

# Check permissions
ls -l /dev/ttyUSB0

# Test connection
docker-compose exec backend python -c "from pymodbus.client import ModbusSerialClient; print('OK')"
```

### Database Connection Issues
```bash
# Check database is running
docker-compose ps

# Check logs
docker-compose logs postgres

# Test connection
docker-compose exec backend python -c "import psycopg2; print('OK')"
```

### Frontend Not Loading
```bash
# Check Nginx
docker-compose logs frontend

# Rebuild frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Permission Errors
```bash
# Add user to groups
sudo usermod -aG docker,dialout $USER

# Log out and back in for changes to take effect
```

## Network Configuration

### Find Pi IP Address
```bash
hostname -I
```

### Access from Network
Edit `/etc/dhcpcd.conf`:
```
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
```

### Firewall (if enabled)
```bash
sudo ufw allow 80/tcp
sudo ufw allow 5000/tcp
```

## Backup and Restore

### Backup Database
```bash
docker-compose exec postgres pg_dump -U postgres autoclave > backup.sql
```

### Restore Database
```bash
cat backup.sql | docker-compose exec -T postgres psql -U postgres autoclave
```

## Performance Optimization for Pi

### In `docker-compose.yml`:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
```

### Reduce Memory Usage
```yaml
services:
  postgres:
    command: >
      postgres
      -c shared_buffers=128MB
      -c max_connections=20
```

## Auto-Start on Boot

Create systemd service:
```bash
sudo nano /etc/systemd/system/autoclave.service
```

```ini
[Unit]
Description=Autoclave Docker Services
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/pi/autoclave
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Enable service:
```bash
sudo systemctl enable autoclave
sudo systemctl start autoclave
```

## Summary

✅ **PostgreSQL** - Database with persistent storage  
✅ **Backend** - Python services in one container  
✅ **Frontend** - React app served via Nginx  
✅ **Modbus** - USB device access  
✅ **Auto-restart** - Containers restart on failure  
✅ **Easy deployment** - Single command to start  

## Quick Reference

```bash
# Start everything
docker-compose up -d

# View status
docker-compose ps

# View logs
docker-compose logs -f

# Stop everything
docker-compose down

# Rebuild after code changes
docker-compose build && docker-compose up -d
```

**Ready for Raspberry Pi deployment!** 🚀

