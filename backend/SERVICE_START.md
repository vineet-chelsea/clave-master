# Service Starting Guide

## Current Setup

**You have 2 options:**

### Option 1: Run Separate Services (Current)

**Terminal 1:** Sensor reading service
```bash
cd backend
python sensor_service.py
```
- Reads sensors every second
- Saves to database
- Uses COM10

**Terminal 2:** API server
```bash
cd backend
python api_server.py
```
- Serves data to frontend
- Uses port 5000

**Terminal 3:** Pressure control (when needed)
```bash
cd backend
python pressure_controller.py 20 30
```
- Uses COM10 (will conflict with sensor_service!)
- Controls valve
- Logs to database

**Problem:** Can't run sensor_service and pressure_controller at the same time (both use COM10)

### Option 2: Use Integrated Service (Recommended) ✨

**Single service that does everything:**

```bash
cd backend

# Run with sensor reading only
python integrated_service.py

# Run with sensor reading + pressure control
python integrated_service.py --control --pressure 20 --duration 30
```

**Benefits:**
- ✅ Single COM10 connection
- ✅ No conflicts
- ✅ Reads sensors AND controls pressure simultaneously
- ✅ Better resource usage

## Recommended Setup

### Terminal 1: Integrated Service
```bash
cd backend
python integrated_service.py --control --pressure 20 --duration 30
```

This will:
- Connect to PLC once (COM10)
- Read sensors every second
- Save to database
- Control pressure if --control is specified
- Log everything

### Terminal 2: API Server
```bash
cd backend
python api_server.py
```

### Terminal 3: Frontend
```bash
npm run dev
```

## Architecture

### Old Way (Conflicts):
```
sensor_service.py → COM10 (reads)
pressure_controller.py → COM10 (conflicts!)
```

### New Way (Integrated):
```
integrated_service.py → COM10 (reads + controls)
  ├─ Sensor reading thread
  └─ Control thread
```

## Usage

### Just Sensor Reading:
```bash
python integrated_service.py
```

### Sensor Reading + Pressure Control:
```bash
python integrated_service.py --control --pressure 20 --duration 30
```

### Parameters:
- `--control` - Enable pressure control
- `--pressure X` - Target pressure in PSI
- `--duration Y` - Duration in minutes

## Output

```
============================================================
Integrated Sensor & Control Service
============================================================
Reading sensors every 1 second
============================================================

[OK] Connected to PostgreSQL
[OK] Connected to PLC on COM10
[INFO] Starting control: 20.0 PSI for 30 minutes
[OK] Created session: 123
[CONTROL] Starting control loop: 20.0 PSI for 30 min

[12:30:45] Reading #1 - Pressure: 18.5 PSI, Temperature: 25.8°C | Valve: 0/4000 | Target: 20.0 PSI
[12:30:46] Reading #2 - Pressure: 18.6 PSI, Temperature: 25.9°C | Valve: 0/4000 | Target: 20.0 PSI
...
[CONTROL] Pressure low (19.2 < 20.0), increasing valve to 200
[12:31:15] Reading #15 - Pressure: 19.2 PSI, Temperature: 26.1°C | Valve: 200/4000 | Target: 20.0 PSI
```

## Benefits

✅ **Single COM port connection** - No conflicts  
✅ **Both reading and control** - Simultaneously  
✅ **Better resource usage** - One thread  
✅ **Simpler architecture** - One service  
✅ **Auto logging** - Everything to database  

## Stop the Service

Press `Ctrl+C` to stop gracefully.

## Everything is Ready! 🎉

Use `integrated_service.py` for best results!

