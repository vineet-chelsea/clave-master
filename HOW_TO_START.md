# How to Start the System

## Problem
"Failed to start service when starting process from UI"

## Root Cause
The `control_loop` wasn't being started when control session begins!

## Fixed

Updated `sensor_control_service.py` to:
- ✅ Start control thread when session begins
- ✅ Handle missing end_time
- ✅ Better error messages
- ✅ Proper cleanup

## How to Start

### Terminal 1: Main Service (MUST START FIRST)
```bash
cd backend
python sensor_control_service.py
```

Wait for:
```
[OK] Connected to PostgreSQL
[OK] Connected to PLC on COM10
[INFO] Service ready. Waiting for frontend to start control...
```

### Terminal 2: API Server
```bash
cd backend
python api_server.py
```

### Terminal 3: Frontend
```bash
npm run dev
```

## Testing the Fix

### Start the service first:
```bash
cd backend
python sensor_control_service.py
```

### Then from UI:
1. Click Manual Control
2. Enter target pressure (e.g., 20 PSI)
3. Enter duration (e.g., 5 minutes)
4. Click Start

### Expected Output in Terminal:
```
[OK] Started control session 123
     Target: 20.0 PSI
     Duration: 5 minutes
     Control thread started
[CONTROL] Control loop started
[12:30:45] Reading #1 - Pressure: 18.5 PSI, Temperature: 25.8°C | Target: 20.0 PSI | Valve: 0/4000 | Time: 5 min
...
[CONTROL] Pressure low (19.2 < 20.0), increasing valve to 200
```

## Key Changes Made

1. **Added control thread initialization:**
   ```python
   self.control_thread = threading.Thread(target=self.control_loop, daemon=True)
   self.control_thread.start()
   ```

2. **Added end_time initialization:**
   ```python
   self.end_time = None
   ```

3. **Added safety check:**
   ```python
   if self.end_time and datetime.now().timestamp() >= self.end_time:
   ```

4. **Better error handling:**
   ```python
   import traceback
   traceback.print_exc()
   ```

## Now It Should Work! ✅

The control loop will start automatically when you start a control session from the UI.

