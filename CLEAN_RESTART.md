# 🔄 Clean Restart - Complete Reset

## All Processes Stopped ✅

## Start Completely Fresh

### Step 1: Sensor Service
```bash
cd backend
python sensor_control_service.py
```

**Expected Output:**
```
[OK] Connected to PostgreSQL
[OK] Connected to PLC on COM10
[INFO] Service ready...
```

### Step 2: API Server
```bash
cd backend
python api_server.py
```

**Expected Output:**
```
Starting server on http://localhost:5000
```

### Step 3: Frontend
```bash
npm run dev
```

**Expected Output:**
```
VITE ready in XXX ms
Local: http://localhost:5173/
```

## Test Process

1. Open browser: http://localhost:5173
2. Click "MANUAL" button
3. Set:
   - Target pressure: 20 PSI
   - Duration: **1 minute** (start with 1 min for quick test)
4. Click "START MANUAL PROCESS"

## Check Console (F12)

Should see:
- ✅ "ProcessMonitor mounted with: {...}"
- ✅ "Set sessionId to: X"
- ✅ "Chart data:" logs every 10 seconds
- ✅ Progress updating

## If Still Not Working

**Share browser console output:**
1. Press F12 in browser
2. Go to Console tab
3. Copy all logs
4. Share them so I can see what's actually happening

## Database Check

After starting a process, verify data saved:
```bash
psql -U postgres -h 127.0.0.1 -p 5432 -d autoclave -c "SELECT id, target_pressure, duration_minutes FROM process_sessions WHERE status='running';"
```

Should show actual values (not NULL).

## Start Fresh Now! 🚀

All services stopped, ready for clean start.

