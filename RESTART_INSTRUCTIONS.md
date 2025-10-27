# 🔄 Need to Restart Services

## The Fix Requires Restart

You need to restart the sensor service for the fix to take effect.

## How to Restart

### 1. Stop the Old Service

Find the terminal running `sensor_control_service.py` and press `Ctrl+C` to stop it.

Or kill all Python processes:
```powershell
Get-Process python | Stop-Process -Force
```

### 2. Start Services Fresh

**Terminal 1: Sensor Service**
```bash
cd backend
python sensor_control_service.py
```

**Terminal 2: API Server**
```bash
cd backend
python api_server.py
```

**Terminal 3: Frontend (if not running)**
```bash
npm run dev
```

## Check It's Fixed

1. Start sensor service - should only read sensors, NOT auto-start control
2. Start API server
3. Open UI
4. Start a session from UI
5. Then control should start

## What Should Happen

### On Service Start:
```
[OK] Connected to PLC on COM10
[INFO] Service ready...
[12:30:45] Reading #1 - Pressure: 18.5 PSI, Temperature: 25.8°C
[12:30:46] Reading #2 - Pressure: 18.6 PSI, Temperature: 25.9°C
```
**NO auto-start of control!**

### After Starting from UI:
```
[NEW SESSION] Detected session X
     Target: 20.0 PSI
     Duration: 5 minutes
[OK] Started control session X
[CONTROL] Control loop started
```

## The Service Must Be Restarted! 🔄

The fix is in the code, but you need to restart the service to apply it.

