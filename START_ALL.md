# 🚀 How to Start Everything

## Run These 3 Commands

### Terminal 1: Sensor Service
```bash
cd backend
python sensor_control_service.py
```

**Wait for:**
```
[OK] Connected to PostgreSQL
[OK] Connected to PLC on COM10
[INFO] Service ready...
```

### Terminal 2: API Server
```bash
cd backend
python api_server.py
```

**Wait for:**
```
Starting server on http://localhost:5000
```

### Terminal 3: Frontend
```bash
npm run dev
```

**Wait for:**
```
Local: http://localhost:5173
```

## Test the Setup

### 1. Open browser: http://localhost:5173

### 2. Try starting manual control:
1. Click "MANUAL" button
2. Set target pressure (e.g., 20 PSI)
3. Set duration (e.g., 5 minutes)
4. Click "START MANUAL PROCESS"

### 3. You should see:

**In Terminal 2 (API Server):**
```
POST /api/start-control - 200 OK
```

**In Terminal 1 (Sensor Service):**
```
[OK] Started control session 123
     Target: 20.0 PSI
     Duration: 5 minutes
     Control thread started
[CONTROL] Control loop started
```

**In UI:**
- ✅ No error message
- ✅ Shows ProcessMonitor screen
- ✅ Pressure and temperature updating

## What Each Service Does

- **sensor_control_service.py**: Reads PLC, saves to database, controls valve
- **api_server.py**: HTTP API for UI to call
- **Frontend**: React UI that user interacts with

## Troubleshooting

### "Connection refused"
- Make sure API server (Terminal 2) is running
- Check it says "Starting server on http://localhost:5000"

### "Failed to start session"
- Check Terminal 2 for error messages
- Make sure database tables exist (process_sessions, process_logs, sensor_readings)

### PLC not connected
- Check Terminal 1 for COM port errors
- Make sure sensor_control_service.py is running

## Everything is Ready! ✅

Just run those 3 commands and you're good to go!

