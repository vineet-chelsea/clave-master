# 🍓 Deploy to Raspberry Pi - Step by Step

## Complete Deployment Guide

### Prerequisites
- Raspberry Pi 4 (recommended) or Pi 3
- USB-to-RS485 adapter for Modbus
- MicroSD card (32GB minimum)
- Internet connection

---

## Step 1: Flash Raspberry Pi OS

1. Download Raspberry Pi Imager from: https://www.raspberrypi.com/software/
2. Flash OS to SD card
3. Enable SSH during imaging
4. Insert SD card into Pi

---

## Step 2: Initial Setup

### Connect to Pi
```bash
# Find Pi IP address
ping raspberrypi.local

# SSH into Pi
ssh pi@<pi-ip-address>
# Default password: raspberry
```

### Update System
```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo reboot
```

---

## Step 3: Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Verify installation
sudo docker --version

# Add user to docker group (to run without sudo)
sudo usermod -aG docker $USER

# Log out and back in for group changes
logout
```

---

## Step 4: Install Docker Compose

**Easiest Method - Use Standalone Binary:**

```bash
# Download and install docker compose plugin
sudo apt-get update
sudo apt-get install -y docker-compose-plugin

# Verify installation
docker compose version
```

**Alternative - Install via pip (if needed):**

```bash
# Install build dependencies
sudo apt-get install -y python3-pip python3-venv python3-dev build-essential

# Create virtual environment
python3 -m venv ~/venv

# Activate virtual environment
source ~/venv/bin/activate

# Install docker-compose
pip install docker-compose

# Add to .bashrc for persistence
echo 'source ~/venv/bin/activate' >> ~/.bashrc

# Verify
docker-compose --version
```

---

## Step 5: Clone Repository

```bash
# Clone the repository
cd /home/pi
git clone https://github.com/vineet-chelsea/clave-master.git
cd clave-master

# Verify files
ls -la
```

You should see:
- `docker-compose.yml`
- `Dockerfile.frontend`
- `Dockerfile.backend`
- `nginx.conf`
- `src/` directory
- `backend/` directory

---

## Step 6: Connect Modbus USB Adapter

```bash
# Plug in USB-to-RS485 adapter
# Check if detected
lsusb

# Find device path
dmesg | grep tty
# Look for: /dev/ttyUSB0 or /dev/ttyACM0

# Check permissions
ls -l /dev/ttyUSB0

# Grant permissions
sudo chmod 666 /dev/ttyUSB0

# Or add user to dialout group
sudo usermod -aG dialout $USER
```

**Note:** Remember the device path for Step 7!

---

## Step 7: Configure Environment

```bash
# Create .env file
nano .env
```

Paste this content:
```env
# Modbus Configuration
COM_PORT=/dev/ttyUSB0
BAUD_RATE=9600
PARITY=N
STOP_BITS=1
BYTE_SIZE=8
SLAVE_ID=1

# PostgreSQL Configuration (for Docker)
PG_HOST=postgres
PG_PORT=5432
PG_DATABASE=autoclave
PG_USER=postgres
PG_PASSWORD=postgres
```

**Important:** Change `COM_PORT` if your device is different!

Save and exit: `Ctrl+X`, `Y`, `Enter`

---

## Step 8: Build Docker Images

```bash
# Build all services (this may take 10-15 minutes)
docker-compose build

# If you encounter memory issues, add swap:
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Change: CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

---

## Step 9: Start Services

```bash
# Start all services in background
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

You should see:
- ✅ Frontend running on port 80
- ✅ Backend running on port 5000
- ✅ Database running on port 5432

---

## Step 10: Verify Deployment

### Check Services
```bash
# List running containers
docker ps

# Should show:
# - autoclave-frontend
# - autoclave-backend
# - autoclave-db
```

### Access Web Interface
Open browser on your computer or phone:
```
http://<pi-ip-address>
```

### Find Pi IP Address
```bash
hostname -I
```

---

## Step 11: Enable Auto-Start on Boot

### Create Systemd Service

```bash
sudo nano /etc/systemd/system/autoclave.service
```

Paste this:
```ini
[Unit]
Description=Autoclave Control System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/pi/clave-master
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0
User=pi

[Install]
WantedBy=multi-user.target
```

Save: `Ctrl+X`, `Y`, `Enter`

### Enable Service
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable autoclave service
sudo systemctl enable autoclave

# Start service
sudo systemctl start autoclave

# Check status
sudo systemctl status autoclave
```

---

## Step 12: Configure Static IP (Optional but Recommended)

Edit network configuration:
```bash
sudo nano /etc/dhcpcd.conf
```

Add at end:
```
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8
```

**Change IP to match your network!**

Reboot:
```bash
sudo reboot
```

---

## Verification Checklist

### ✅ Services Running
```bash
docker ps
# Should show 3 containers running
```

### ✅ Frontend Accessible
- Open: `http://<pi-ip-address>`
- Should see autoclave interface

### ✅ API Working
```bash
curl http://localhost:5000/api/health
# Should return: {"status":"healthy","database":"connected"}
```

### ✅ Database Working
```bash
docker-compose exec postgres psql -U postgres -d autoclave -c "SELECT version();"
```

### ✅ Auto-Start Enabled
```bash
# Test by rebooting
sudo reboot

# After reboot, check services
docker ps
```

---

## Troubleshooting

### Service Not Starting
```bash
# Check logs
docker-compose logs backend

# Restart specific service
docker-compose restart backend
```

### Can't Find USB Device
```bash
# Check device
ls -l /dev/ttyUSB*

# Add to docker-compose.yml
# Change: - /dev/ttyUSB0:/dev/ttyUSB0
# To actual device path
```

### Out of Memory
```bash
# Check memory
free -h

# Enable swap (see Step 8)
```

### Frontend Not Loading
```bash
# Rebuild frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

---

## Next Steps

### 1. Add Auto Programs to Database
```bash
# Connect to database
docker-compose exec backend python add_auto_programs.py
```

### 2. Configure PLC Connection
- Verify USB adapter is connected
- Check COM_PORT in `.env` matches device
- Test Modbus communication

### 3. Test System
- Start a test program
- Verify valve control works
- Check sensor readings update

---

## Maintenance Commands

### Update Application
```bash
cd /home/pi/clave-master
git pull
docker-compose build
docker-compose up -d
```

### Backup Database
```bash
docker-compose exec postgres pg_dump -U postgres autoclave > backup_$(date +%Y%m%d).sql
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Stop Everything
```bash
docker-compose down
```

### Rebuild Everything
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

---

## Summary

✅ **Docker installed**  
✅ **Repository cloned**  
✅ **Services built**  
✅ **Auto-start enabled**  
✅ **System ready for production**  

**Access:** `http://<pi-ip-address>`

Your autoclave control system is now deployed on Raspberry Pi! 🎉

---

## Quick Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild after changes
docker-compose build && docker-compose up -d

# Check status
docker-compose ps

# Access database
docker-compose exec postgres psql -U postgres -d autoclave
```

