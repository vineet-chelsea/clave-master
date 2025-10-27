# 🚀 Start This Before Your UI

## Single Service to Run

### Start the Main Service:

```bash
cd backend
python sensor_control_service.py
```

**This ONE service handles everything:**
- ✅ Reads sensors from PLC (COM10)
- ✅ Saves to PostgreSQL database
- ✅ Ready for frontend to control
- ✅ Can be controlled via API or directly

### Then Start Frontend:

In a **NEW terminal:**
```bash
npm run dev
```

### Also Start API Server (Optional):

```bash
cd backend
python api_server.py
```

## How It Works

```
sensor_control_service.py
    ↓
  Reads PLC every second
  Saves to database
  Ready for control
    ↓
Frontend (npm run dev)
    ↓
  Connects to API
  Sees live sensor data
```

## What to Run

### Before starting frontend:

**Terminal 1:** Main service
```bash
cd backend
python sensor_control_service.py
```

You'll see:
```
[OK] Connected to PostgreSQL
[OK] Connected to PLC on COM10
[INFO] Service ready. Waiting for frontend to start control...
```

### Then start frontend:

**Terminal 2:** Frontend
```bash
npm run dev
```

### Optional - API server:

**Terminal 3:** API server
```bash
cd backend
python api_server.py
```

## Service Output

```
============================================================
Sensor & Control Service
============================================================
COM Port: COM10
Reading sensors every 1 second
Control interval: 30 seconds
============================================================

[OK] Connected to PostgreSQL
[OK] Connected to PLC on COM10

[INFO] Service ready. Waiting for frontend to start control...

[12:30:45] Reading #1 - Pressure: 18.5 PSI, Temperature: 25.8°C
[12:30:46] Reading #2 - Pressure: 18.6 PSI, Temperature: 25.9°C
```

When control is active (from UI):
```
[12:31:00] Reading #16 - Pressure: 19.5 PSI, Temperature: 26.1°C | Target: 20.0 PSI | Valve: 200/4000 | Time: 29 min
[12:31:30] Reading #46 - Pressure: 20.3 PSI, Temperature: 26.5°C | Target: 20.0 PSI | Valve: 200/4000 | Time: 29 min
[OK] Started control session 123
     Target: 20 PSI
     Duration: 30 minutes
```

## This is the ONE Service to Run! ✅

Start `sensor_control_service.py` FIRST, then start your frontend.

Everything else is automatic! 🎉

