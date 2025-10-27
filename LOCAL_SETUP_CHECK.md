# Local Setup Check - 500 Error Fix

## Problem
Frontend is getting 500 errors from backend API:
- `GET http://localhost:5000/api/sensor-readings/latest 500 (INTERNAL SERVER ERROR)`
- `GET http://localhost:5000/api/sessions 500 (INTERNAL SERVER ERROR)`

## Root Cause
The backend API server cannot connect to the PostgreSQL database or the tables don't exist.

## Quick Fix Steps

### Step 1: Check if PostgreSQL is Running
```bash
# Windows PowerShell
Get-Service -Name "postgresql*"

# If not running, start it
net start postgresql-x64-15  # or your version
```

### Step 2: Check if Database Exists
```bash
psql -U postgres -h 127.0.0.1 -p 5432 -c "\l"
```

Look for `autoclave` database. If it doesn't exist, create it:
```bash
psql -U postgres -h 127.0.0.1 -p 5432 -c "CREATE DATABASE autoclave;"
```

### Step 3: Run Database Initialization
```bash
cd backend
python docker-init-db.py
```

This will create all necessary tables:
- `sensor_readings`
- `process_sessions`
- `process_logs`
- `autoclave_programs`

### Step 4: Start Backend Services
```bash
# Terminal 1: Start sensor control service
cd backend
python sensor_control_service.py

# Terminal 2: Start API server
python api_server.py
```

The API server should now respond without errors.

### Step 5: Start Frontend
```bash
# Terminal 3: Start frontend
npm run dev
```

Open `http://localhost:8080` - it should now work without 500 errors.

## Verify Setup

### Check Database Tables
```bash
psql -U postgres -h 127.0.0.1 -p 5432 -d autoclave -c "\dt"
```

You should see:
- `autoclave_programs`
- `process_sessions`
- `process_logs`
- `sensor_readings`

### Test API Endpoints
```bash
# Test sensor readings endpoint
curl http://localhost:5000/api/sensor-readings/latest

# Test sessions endpoint
curl http://localhost:5000/api/sessions

# Test programs endpoint
curl http://localhost:5000/api/programs
```

All should return JSON data, not errors.

## Environment Variables

Make sure `backend/.env` exists with:
```env
# PostgreSQL Configuration
PG_HOST=127.0.0.1
PG_PORT=5432
PG_DATABASE=autoclave
PG_USER=postgres
PG_PASSWORD=postgres

# Modbus Configuration
COM_PORT=COM10
BAUD_RATE=9600
SLAVE_ID=1
```

## Summary
The 500 errors are due to database connection issues. After running `docker-init-db.py` to create the tables, everything should work.

