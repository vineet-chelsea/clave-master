# ✅ Correct Start Instructions

## The Problem

The UI can't directly call methods on the running service because they're in different processes.

## Solution

Use `service_api.py` which wraps the service and provides API endpoints.

## How to Start (CORRECT WAY)

### Step 1: Start API Server (Runs everything)
```bash
cd backend
python service_api.py
```

This will:
1. Start the sensor service in background
2. Provide API endpoints for UI
3. Handle all control requests

### Step 2: Start Frontend
```bash
npm run dev
```

## What Each File Does

### `sensor_control_service.py`
- The main service that reads sensors and controls valve
- Cannot be called directly from UI (different process)
- Runs continuously

### `service_api.py` ✅ USE THIS
- Wraps the sensor service
- Provides API endpoints
- Can be called from frontend
- Handles all requests

### `api_server.py`
- Old file for basic endpoints
- Doesn't control the service

## Correct Flow

```
Frontend → service_api.py → sensor_control_service.py
                              (RPC via shared instance)
```

## Testing

### Start the API:
```bash
cd backend
python service_api.py
```

### Test from command line:
```bash
curl -X POST http://localhost:5000/api/start-control \
  -H "Content-Type: application/json" \
  -d '{"target_pressure": 20, "duration_minutes": 5}'
```

### Expected Response:
```json
{
  "success": true,
  "session_id": 123,
  "target_pressure": 20,
  "duration_minutes": 5
}
```

## Run This Command

```bash
cd backend
python service_api.py
```

Then open your frontend and try starting a control session.

## Expected Output

```
============================================================
Service API Server
============================================================
Starting on http://localhost:5000
============================================================
[OK] Connected to PostgreSQL
[OK] Connected to PLC on COM10
[INFO] Service ready. Waiting for frontend to start control...
```

When UI sends request:
```
[OK] Started control session 123
     Target: 20 PSI
     Duration: 5 minutes
     Control thread started
[CONTROL] Control loop started
```

## This Should Work! ✅

Use `service_api.py` instead of running the service separately.

