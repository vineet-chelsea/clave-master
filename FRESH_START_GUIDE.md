# 🚀 Fresh Start Guide

## All Processes Stopped ✅

You can now start everything fresh.

## How to Start (In Order)

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
 * Running on http://127.0.0.1:5000
```

### Terminal 3: Frontend
```bash
npm run dev
```

**Wait for:**
```
VITE ready in XXX ms
  ➜  Local:   http://localhost:5173/
```

## Test Process

1. Open browser: http://localhost:5173
2. Click "MANUAL"
3. Set:
   - Target pressure: 20 PSI
   - Duration: **2 minutes** (not 5!)
4. Click "START MANUAL PROCESS"

## What to Check

### Should See:
- ✅ "Manual Control - 20 PSI for 2 min" (NOT 5 min)
- ✅ Charts populate with data
- ✅ Progress increments: "0 / 2 minutes" → "1 / 2 minutes"
- ✅ Pressure reading updates

### Browser Console (F12):
- "Set sessionId to: X"
- "Chart data:" logs every 10 seconds
- No errors

## If Charts Still Empty

Check console for:
- "Chart data:" logs - should show data being added
- Session ID set
- Sensor readings updating

## Good Luck! 🎉

Start fresh and test. Check browser console if issues persist!

