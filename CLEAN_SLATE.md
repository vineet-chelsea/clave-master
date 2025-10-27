# 🔄 Clean Slate - Fresh Start

## All Services Stopped ✅

## Old Sessions Cleaned ✅

All old 'running' and 'paused' sessions have been marked as 'stopped' in the database.

## How to Start Fresh

### Terminal 1: Sensor Service
```bash
cd backend
python sensor_control_service.py
```

Wait for:
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

Wait for:
```
Starting server on http://localhost:5000
```

### Terminal 3: Frontend
```bash
npm run dev
```

Wait for:
```
VITE ready
Local: http://localhost:5173
```

## Test Process

1. Open browser: http://localhost:5173
2. Click "MANUAL"
3. Set:
   - Target pressure: 20 PSI
   - Duration: 1 minute
4. Click "START MANUAL PROCESS"

## What Should Work

✅ **New session creates** - Gets new ID from database  
✅ **Service detects it** - Starts control automatically  
✅ **UI shows progress** - Charts update, time counts  
✅ **Can stop** - Stops properly and returns to selection  
✅ **Can start new** - After stopping, can start again  

## If Still Not Working

Check browser console (F12):
- Any errors?
- Session ID logged?
- API calls successful?

## Everything Ready! 🎉

Start all 3 services and test fresh!

