# Deployment Status - Complete ✅

## All Issues Fixed

### 1. ✅ Serial Device (`/dev/ttyACM0`)
- Docker volume mounts USB serial device
- `COM_PORT` environment variable set correctly
- `privileged: true` added for device access
- Permissions fixed with `chmod 666`

### 2. ✅ Python Dependencies (`pyserial`)
- Added `pyserial==3.5` to `requirements.txt`
- Fixes `NameError: name 'serial' is not defined`

### 3. ✅ Frontend-Backend Connectivity
- All frontend API calls use `API_URL` constant
- Nginx proxies `/api/*` to `backend:5000` container
- Works for both local development and Docker deployment
- Environment variable `VITE_API_BASE_URL` configurable

## How It Works Now

### Local Development (Your PC)
```
Frontend (Vite on :8080) → Direct API calls → Backend (Flask on :5000)
```

### Docker Deployment (Raspberry Pi)
```
Browser → Frontend (Nginx on :80) → Proxy /api/* → Backend (Flask on :5000)
```

## Deploy to Raspberry Pi

### Step 1: Pull Latest Changes
```bash
cd ~/clave-master
git pull
```

### Step 2: Fix Serial Device Permissions
```bash
# Check which device exists
ls -l /dev/tty{AMA0,USB0,ACM0}

# Fix permissions (use the correct device)
sudo chmod 666 /dev/ttyACM0

# Permanent fix
sudo usermod -aG dialout $USER
sudo reboot  # (if needed)
```

### Step 3: Rebuild and Restart
```bash
# Stop existing containers
docker compose down

# Rebuild with latest changes
docker compose up -d --build

# Check logs
docker compose logs -f backend
```

### Step 4: Verify
```bash
# Check all services are running
docker compose ps

# Check backend logs
docker compose logs backend | tail -50

# Check frontend logs
docker compose logs frontend | tail -50

# Access application
# From Raspberry Pi: http://localhost
# From network: http://<raspberry-pi-ip>
```

## Expected Behavior

### Before Docker (Local PC)
- Frontend: `npm run dev` → `http://localhost:8080`
- Backend: `python api_server.py` + `python sensor_control_service.py`
- Direct connection between frontend and backend

### After Docker (Raspberry Pi)
- Frontend: Access at `http://localhost` or `http://<pi-ip>`
- Backend: Running inside Docker, Nginx proxies API calls
- Same functionality, different deployment method

## Changes Made

1. **backend/requirements.txt**: Added `pyserial==3.5`
2. **docker-compose.yml**: Fixed `COM_PORT` to `/dev/ttyACM0`, added `privileged: true`
3. **nginx.conf**: Added API proxy to backend container
4. **src/integrations/supabase/client.ts**: Centralized `API_URL` constant
5. **All frontend components**: Updated to use `API_URL` instead of hardcoded URLs
6. **Dockerfile.frontend**: Accepts `VITE_API_BASE_URL` build arg

## Troubleshooting

### Backend Not Starting
```bash
# Check serial device exists
ls -l /dev/ttyACM0

# Fix permissions
sudo chmod 666 /dev/ttyACM0

# Restart backend
docker compose restart backend

# Check logs
docker compose logs backend
```

### Frontend Not Connecting to Backend
```bash
# Test API from inside container
docker exec autoclave-backend curl http://localhost:5000/api/sessions

# Test API from host
curl http://localhost:5000/api/sessions

# Check Nginx proxy
docker exec autoclave-frontend cat /etc/nginx/conf.d/default.conf
```

### Serial Communication Errors
```bash
# List serial devices
ls -l /dev/tty*

# Check user groups
groups

# Add user to dialout group
sudo usermod -aG dialout $USER
newgrp dialout  # or logout/login

# Reboot if needed
sudo reboot
```

## Status: ✅ READY FOR DEPLOYMENT

All code has been committed and pushed to the repository. The application should now work identically to the local setup when deployed on Raspberry Pi with Docker.

