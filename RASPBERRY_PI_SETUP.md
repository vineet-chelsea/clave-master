# 🍓 Raspberry Pi Setup Guide

## Complete Setup Instructions

### 1. Install Docker on Raspberry Pi

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt-get install -y python3-pip
sudo pip3 install docker-compose

# Log out and back in for group changes
```

### 2. Install Required Packages

```bash
# For serial communication
sudo apt-get install -y python3-serial

# For database access
sudo apt-get install -y postgresql-client

# Optional: Git
sudo apt-get install -y git
```

### 3. Set Up GPIO/Serial (if needed)

```bash
# Enable serial interface
sudo raspi-config
# Navigate to: Interface Options → Serial Port
# Enable: Serial Interface
# Disable: Serial Console

# Add user to dialout group
sudo usermod -aG dialout $USER

# Reboot
sudo reboot
```

### 4. Find Modbus USB Device

```bash
# List USB devices
lsusb

# Find device
dmesg | grep tty

# Common paths:
# /dev/ttyUSB0 - USB adapter
# /dev/ttyACM0 - Arduino
# /dev/ttyAMA0 - GPIO serial
```

### 5. Clone Repository

```bash
cd /home/pi
git clone <your-repo-url> autoclave
cd autoclave
```

### 6. Configure Environment

```bash
# Copy example env
cp env.example .env

# Edit configuration
nano .env
```

**Modify for your setup:**
```env
COM_PORT=/dev/ttyUSB0    # Your Modbus device
BAUD_RATE=9600
SLAVE_ID=1
```

### 7. Build and Deploy

```bash
# Build Docker images
docker-compose build

# Start all services
docker-compose up -d

# Verify running
docker-compose ps

# View logs
docker-compose logs -f
```

### 8. Access Application

- **Local:** http://raspberrypi.local
- **Network:** http://<pi-ip-address>
- **IP Check:** `hostname -I`

## Hardware Connections

### Modbus USB Adapter
1. Plug USB-to-RS485 adapter into Pi
2. Connect to PLC via RS485 cables
3. Check device path: `ls /dev/ttyUSB*`

### Power Requirements
- Raspberry Pi 4: 5V 3A power supply
- Modbus adapter: Self-powered via USB

## Network Setup

### Enable WiFi (Optional)
```bash
sudo raspi-config
# System Options → S73 Wireless LAN
```

### Static IP (Recommended)
Edit `/etc/dhcpcd.conf`:
```bash
sudo nano /etc/dhcpcd.conf
```

Add:
```
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
```

## Auto-Start on Boot

Create systemd service:

```bash
sudo nano /etc/systemd/system/autoclave.service
```

Paste:
```ini
[Unit]
Description=Autoclave Control System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/pi/autoclave
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0
User=pi
Group=pi

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable autoclave
sudo systemctl start autoclave
```

## Troubleshooting

### Device Not Found
```bash
# Check permissions
ls -l /dev/ttyUSB0

# Fix permissions
sudo chmod 666 /dev/ttyUSB0

# Or add to group
sudo usermod -aG dialout $USER
sudo reboot
```

### Build Errors
```bash
# Clean and rebuild
docker-compose down
docker system prune -a
docker-compose build --no-cache
```

### Low Memory
```bash
# Check memory
free -h

# Enable swap (if needed)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Change CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## Security

### Change Default Passwords
```bash
# Edit .env
nano .env

# Change PostgreSQL password
POSTGRES_PASSWORD=your_secure_password
```

### Firewall Setup
```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # Web
sudo ufw allow 5000/tcp  # API
sudo ufw enable
```

## Maintenance

### Update Application
```bash
cd /home/pi/autoclave
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
```

## Summary

✅ **Docker installed**  
✅ **Services running**  
✅ **Accessible on network**  
✅ **Auto-start enabled**  
✅ **Modbus connected**  

**System ready for production use on Raspberry Pi!** 🎉

