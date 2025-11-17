# Docker Deployment Guide - Raspberry Pi

This guide covers deploying the latest changes to your Raspberry Pi using Docker.

## Prerequisites

- SSH access to Raspberry Pi
- Docker and Docker Compose installed
- Git installed on Raspberry Pi
- Existing repository cloned on Raspberry Pi

## Step-by-Step Docker Deployment

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
# Create a backup of docker-compose.yml
cp docker-compose.yml docker-compose.yml.backup

# Or create a backup branch
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

### Step 5: Verify Serial Device

```bash
# Check if serial device exists
ls -l /dev/ttyACM0

# If device doesn't exist, check for other USB serial devices
ls -l /dev/ttyUSB* /dev/ttyACM*

# Note the device path - you may need to update docker-compose.yml
```

### Step 6: Update docker-compose.yml (if needed)

If your serial device path is different, update `docker-compose.yml`:

```yaml
volumes:
  - /dev/ttyACM0:/dev/ttyACM0  # Change if your device is different
environment:
  - COM_PORT=/dev/ttyACM0  # Change if your device is different
```

### Step 7: Stop Running Containers

```bash
# Stop all containers
docker-compose down

# Or stop specific services
docker-compose stop backend frontend postgres
```

### Step 8: Remove Old Images (Optional - for clean rebuild)

```bash
# Remove old backend and frontend images
docker-compose rm -f backend frontend

# Or remove all images (more aggressive)
docker rmi $(docker images -q autoclave-backend autoclave-frontend) 2>/dev/null || true
```

### Step 9: Rebuild Docker Images

```bash
# Rebuild all services with no cache (ensures latest dependencies)
docker-compose build --no-cache

# Or rebuild specific service
docker-compose build --no-cache backend
docker-compose build --no-cache frontend
```

**Note:** This step will:
- Install new Python dependencies (reportlab, matplotlib, pytz)
- Install new npm dependencies (date-fns-tz)
- Update all code changes

### Step 10: Start Containers

```bash
# Start all services
docker-compose up -d

# Or start specific services
docker-compose up -d postgres  # Start database first
docker-compose up -d backend   # Then backend
docker-compose up -d frontend  # Finally frontend
```

### Step 11: Check Container Status

```bash
# Check if all containers are running
docker-compose ps

# Should show:
# - autoclave-db (postgres) - Up
# - autoclave-backend - Up
# - autoclave-frontend - Up
```

### Step 12: View Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# View last 100 lines
docker-compose logs --tail=100 backend
```

### Step 13: Verify Deployment

#### Check Backend API

```bash
# Health check
curl http://localhost:5000/api/health

# Latest sensor reading
curl http://localhost:5000/api/sensor-readings/latest

# Should return JSON with pressure and temperature
```

#### Check Frontend

```bash
# Open in browser
# http://<raspberry-pi-ip> or http://localhost

# Or check if nginx is serving
curl http://localhost
```

#### Check Database

```bash
# Connect to database container
docker-compose exec postgres psql -U postgres -d autoclave

# Check roll categories
SELECT * FROM roll_categories WHERE category_name = 'JSW Roll';

# Check if programs exist
SELECT COUNT(*) FROM autoclave_programs;

# Exit
\q
```

### Step 14: Test New Features

1. **PDF Report Generation:**
   - Access frontend
   - Go to Historical Data
   - Select a session
   - Click "Generate PDF Report"
   - Verify PDF downloads

2. **IST Timezone:**
   - Check timestamps in frontend
   - Verify they show IST time (UTC+5:30)

3. **Buzzer Control:**
   - Check backend logs for buzzer messages
   - Start a control session
   - Monitor for buzzer activation

4. **Temperature Adjustment:**
   - Check temperature readings
   - Verify temperatures above 80°C are adjusted

## Quick Deployment Commands

### Full Rebuild and Restart

```bash
# One-liner for complete deployment
cd /path/to/clave-master && \
git pull origin main && \
docker-compose down && \
docker-compose build --no-cache && \
docker-compose up -d && \
docker-compose logs -f
```

### Update Only Backend

```bash
docker-compose stop backend
docker-compose build --no-cache backend
docker-compose up -d backend
docker-compose logs -f backend
```

### Update Only Frontend

```bash
docker-compose stop frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
docker-compose logs -f frontend
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs for errors
docker-compose logs backend

# Check if port is already in use
sudo netstat -tulpn | grep 5000
sudo netstat -tulpn | grep 80

# Check container status
docker ps -a
```

### Serial Device Not Found

```bash
# Check if device exists on host
ls -l /dev/ttyACM0

# Check if device is accessible in container
docker-compose exec backend ls -l /dev/ttyACM0

# If device path changed, update docker-compose.yml and restart
```

### Database Connection Issues

```bash
# Check if postgres container is healthy
docker-compose ps postgres

# Check postgres logs
docker-compose logs postgres

# Test connection from backend container
docker-compose exec backend python3 -c "import psycopg2; psycopg2.connect(host='postgres', port=5432, database='autoclave', user='postgres', password='postgres')"
```

### Permission Issues

```bash
# Check if user is in docker group
groups

# Add user to docker group if needed
sudo usermod -aG docker $USER
# Log out and back in

# Check docker daemon is running
sudo systemctl status docker
```

### Build Failures

```bash
# Check build logs
docker-compose build --no-cache backend 2>&1 | tee build.log

# Check if dependencies are correct
docker-compose exec backend pip3 list | grep -E "reportlab|matplotlib|pytz"
```

### Frontend Not Loading

```bash
# Check frontend logs
docker-compose logs frontend

# Check if nginx is running in container
docker-compose exec frontend ps aux | grep nginx

# Rebuild frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

## Rollback Procedure

If something goes wrong:

```bash
# Stop all containers
docker-compose down

# Rollback to previous commit
git log  # Find previous commit hash
git checkout <previous-commit-hash>

# Rebuild and restart
docker-compose build --no-cache
docker-compose up -d

# Or restore from backup
cp docker-compose.yml.backup docker-compose.yml
docker-compose up -d
```

## Maintenance Commands

### View Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df
```

### Clean Up

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes (be careful!)
docker volume prune

# Full cleanup (removes everything unused)
docker system prune -a
```

### Update Docker Compose

```bash
# Pull latest docker-compose if needed
sudo pip3 install --upgrade docker-compose

# Or if using docker compose (v2)
sudo apt update
sudo apt install docker-compose-plugin
```

## Environment Variables

If you need to change environment variables, edit `docker-compose.yml`:

```yaml
backend:
  environment:
    - COM_PORT=/dev/ttyACM0
    - BAUD_RATE=9600
    - SLAVE_ID=1
    - PG_HOST=postgres
    # ... etc
```

Then restart:
```bash
docker-compose up -d backend
```

## Monitoring

### Continuous Log Monitoring

```bash
# Follow all logs
docker-compose logs -f

# Follow specific service
docker-compose logs -f backend | grep -E "BUZZER|ERROR|WARNING"
```

### Health Checks

```bash
# API health
watch -n 5 'curl -s http://localhost:5000/api/health'

# Container health
watch -n 5 'docker-compose ps'
```

## Post-Deployment Checklist

- [ ] All containers are running (`docker-compose ps`)
- [ ] API health check returns success
- [ ] Frontend is accessible
- [ ] Sensor readings are being logged
- [ ] PDF reports generate correctly
- [ ] Timestamps show IST timezone
- [ ] Database contains all 25 roll categories
- [ ] No errors in logs
- [ ] Serial device is accessible in container

## Notes

- **Serial Device:** On Raspberry Pi, typically `/dev/ttyACM0` or `/dev/ttyUSB0`
- **Privileged Mode:** Backend container uses `privileged: true` for serial device access
- **Data Persistence:** Database data is stored in Docker volume `postgres_data`
- **Ports:** Backend on 5000, Frontend on 80
- **Network:** All containers use `autoclave-network`

## Quick Reference

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# Rebuild
docker-compose build --no-cache

# Logs
docker-compose logs -f

# Status
docker-compose ps

# Execute command in container
docker-compose exec backend <command>
docker-compose exec frontend <command>
docker-compose exec postgres <command>
```

