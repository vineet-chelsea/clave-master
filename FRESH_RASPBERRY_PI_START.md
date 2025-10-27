# 🍓 Fresh Raspberry Pi Setup - Start Here

## Complete Setup from Scratch

### Prerequisites
- Raspberry Pi 4 (recommended) or Pi 3
- MicroSD card (32GB minimum)
- USB-to-RS485 adapter for Modbus
- Internet connection

---

## Step 1: Flash Raspberry Pi OS

1. Download Raspberry Pi Imager: https://www.raspberrypi.com/software/
2. Flash OS to SD card
3. **Enable SSH** during imaging
4. Insert SD card into Pi and power on

---

## Step 2: Connect and Update System

### Connect via SSH
```bash
# Find Pi IP address
ping raspberrypi.local

# Or check your router for connected devices
# Default IP often starts with 192.168.1.x

# SSH into Pi
ssh pi@<ip-address>
# Default password: raspberry

# You'll be prompted to change password on first login
```

### Update System
```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo reboot
```

**Wait for reboot, then reconnect via SSH.**

---

## Step 3: Install Docker

```bash
# Install Docker (official script)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group (so you don't need sudo)
sudo usermod -aG docker $USER

# Verify Docker works
docker --version

# Log out and back in for group changes
exit
```

**Reconnect via SSH** for group changes to take effect.

---

## Step 4: Install Docker Compose

```bash
# Install via apt (recommended)
sudo apt-get update
sudo apt-get install -y docker-compose-plugin

# Verify
docker compose version
```

---

## Step 5: Clone Repository

```bash
# Create project directory
mkdir -p ~/projects
cd ~/projects

# Clone the repository
git clone https://github.com/vineet-chelsea/clave-master.git
cd clave-master

# Verify files
ls -la
```

You should see:
- `docker-compose.yml`
- `Dockerfile.frontend`
- `Dockerfile.backend`
- `deploy.sh`

---

## Step 6: Connect Modbus Device

```bash
# Plug in USB-to-RS485 adapter

# Check if detected
lsusb

# Find device path
dmesg | grep tty
```

**Common device paths:**
- `/dev/ttyUSB0` - USB adapters
- `/dev/ttyACM0` - Arduino-based adapters
- `/dev/ttyAMA0` - GPIO serial (if using GPIO)

**Note which device you have!**

---

## Step 7: Quick Deploy

```bash
# Make deploy script executable
chmod +x deploy.sh

# Run automated deployment
./deploy.sh
```

The script will:
1. ✅ Check Docker is installed
2. ✅ Check Docker Compose is installed
3. ✅ Create `.env` file with default settings
4. ✅ Fix all serial device permissions
5. ✅ Build Docker images (takes 10-15 minutes)
6. ✅ Start all services
7. ✅ Show you the access URL

**Total time: ~15-20 minutes**

---

## Step 8: Access Application

After deployment completes, access at:

```bash
# Find your Pi's IP address
hostname -I
```

Open browser:
```
http://<pi-ip-address>
```

Example: `http://192.168.1.100`

---

## Step 9: Configure Modbus (if needed)

If your device path is different from `/dev/ttyACM0`:

```bash
# Edit .env file
nano .env

# Change COM_PORT to your device:
# COM_PORT=/dev/ttyUSB0
# or
# COM_PORT=/dev/ttyAMA0

# Save and restart
docker compose restart backend
```

---

## Step 10: Enable Auto-Start

```bash
# Create systemd service
sudo nano /etc/systemd/system/autoclave.service
```

Paste this (adjust path if needed):
```ini
[Unit]
Description=Autoclave Control System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/pi/projects/clave-master
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable autoclave
sudo systemctl start autoclave
sudo systemctl status autoclave
```

---

## Verification

### Check Services
```bash
docker ps
```

Should show 3 containers:
- `autoclave-frontend`
- `autoclave-backend`
- `autoclave-db`

### Test Frontend
Open browser: `http://<pi-ip-address>`

### Test API
```bash
curl http://localhost:5000/api/health
# Should return: {"status":"healthy","database":"connected"}
```

---

## Troubleshooting

### Can't connect via SSH
```bash
# Check if SSH is enabled
sudo systemctl status ssh

# Enable if not running
sudo systemctl enable ssh
sudo systemctl start ssh
```

### Docker permission denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
# Or logout and back in
```

### Serial device not found
```bash
# List USB devices
lsusb

# Check tty devices
ls -l /dev/tty*

# Fix permissions
sudo chmod 666 /dev/ttyACM0
sudo chmod 666 /dev/ttyUSB0
```

### Out of memory during build
```bash
# Add swap
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Change: CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

---

## Summary

✅ **OS flashed**  
✅ **Docker installed**  
✅ **Repository cloned**  
✅ **Services deployed**  
✅ **Auto-start enabled**  

**System ready for production!** 🎉

Access: `http://<pi-ip-address>`

