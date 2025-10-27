# Data Persistence Fix - Historical Data & Auto Programs

## Problem Fixed
Historical data and auto programs were being deleted on every restart because:
- `docker-init-db.py` was dropping and recreating tables
- `add_auto_programs.py` was deleting existing programs

## Solution Implemented

### 1. Database Initialization (`docker-init-db.py`)
- ✅ Now checks if tables exist before initializing
- ✅ Skips initialization if tables already present
- ✅ Only creates tables on first run

### 2. Auto Programs (`add_auto_programs.py`)
- ✅ Now checks if programs exist before adding
- ✅ Skips addition if programs already present
- ✅ Preserves existing programs

### 3. Data Persistence
- ✅ PostgreSQL volume (`postgres_data`) persists across restarts
- ✅ Data survives container restarts and reboots

## How It Works Now

### First Run (Fresh Database)
```
1. Check tables → Don't exist
2. Create tables
3. Add auto programs
4. Start services
```

### Subsequent Runs (Existing Database)
```
1. Check tables → Already exist → SKIP
2. Check programs → Already exist → SKIP
3. Start services (data preserved)
```

## What's Preserved Across Restarts

- ✅ **Historical Sessions** - All past process sessions
- ✅ **Sensor Readings** - All historical sensor data
- ✅ **Auto Programs** - All 9 pre-loaded programs
- ✅ **Process Logs** - Complete session logs

## Verify On Raspberry Pi

### Pull Latest Changes
```bash
cd ~/clave-master
git pull
```

### Rebuild Backend (to get updated scripts)
```bash
docker compose build backend
docker compose up -d
```

### Check Logs
```bash
docker compose logs backend | grep -i "database\|program"
```

You should see:
```
[OK] Database tables already exist - skipping initialization
[OK] Found 9 existing programs - skipping addition
```

## Test Data Persistence

### 1. Start a session
- Go to Manual or Auto mode
- Start a process
- Let it run for a minute

### 2. Check history
- Go to History
- Verify session appears

### 3. Reboot Raspberry Pi
```bash
sudo reboot
```

### 4. After reboot
- Wait for services to start (~30 seconds)
- Access web interface
- Go to History → Session should still be there
- Go to Auto mode → All 9 programs should be visible

## Status: ✅ DATA NOW PERSISTS ACROSS RESTARTS

All historical data and auto programs will now survive:
- Container restarts
- System reboots
- Docker service restarts

