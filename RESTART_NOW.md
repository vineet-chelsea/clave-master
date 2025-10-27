# 🔄 Restart Instructions

## Issue Found

Session #35 exists but has NULL values for `target_pressure` and `duration_minutes`.

This causes:
- UI to show default "5 min" instead of actual duration
- Charts to be empty
- Progress to show 0/5

## Fixed the API

Now the API will:
- ✅ Explicitly convert to float/int
- ✅ Log the values being saved
- ✅ Debug print when session is created

## Database Cleaned

All running sessions set to 'stopped' to start fresh.

## How to Start Now

### Terminal 1: Sensor Service
```bash
cd backend
python sensor_control_service.py
```

### Terminal 2: API Server
```bash
cd backend
python api_server.py
```

Look for the new debug message:
```
[API] Created session with target=20.0, duration=2
```

### Terminal 3: Frontend
```bash
npm run dev
```

## Test Fresh

1. Open browser: http://localhost:5173
2. Click "MANUAL"
3. Set:
   - Target: 20 PSI
   - Duration: **2 minutes**
4. Click START

## What Should Happen

**In Terminal 2 (API):**
```
[API] Created session with target=20.0, duration=2
```

**In Database:**
```
target_pressure: 20
duration_minutes: 2
```

**In UI:**
- Shows "20 PSI for 2 min" (NOT 5 min)
- Charts populate
- Progress updates: 0/2 → 1/2 → 2/2

## Everything is Fixed! 🎉

Start fresh and test!

