# ✅ Final Solution - How It Actually Works

## The Problem

When you start a process from the UI, it tries to start the service but the frontend doesn't have the service instance to call its methods.

## The Solution (Simple)

You need to run **THREE** things, in this order:

### 1. Main Service (Terminal 1)
```bash
cd backend
python sensor_control_service.py
```

Keep this running - it reads sensors every second.

### 2. API Server (Terminal 2)  
```bash
cd backend
python api_server.py
```

This serves data to the frontend.

### 3. Frontend (Terminal 3)
```bash
npm run dev
```

## How the UI Connects

The UI doesn't directly control the service. Instead:

1. **UI makes HTTP requests** to the API server (`api_server.py`)
2. **API server** reads/writes to PostgreSQL database
3. **Main service** reads from PLC and writes to database
4. **Database** is the bridge between them

## Current Flow

```
Frontend (localhost:5173)
    ↓ HTTP requests
API Server (localhost:5000)
    ↓ reads/writes
PostgreSQL Database
    ↓ reads/writes
Main Service (sensor_control_service.py)
    ↓ reads/writes
PLC (COM10)
```

## How to Start Control from UI

The UI needs to:
1. **Create a session in database** (via API)
2. **Start pressure control** (the service monitors and controls automatically)
3. **Read progress** (via API polling database)

## Integration Needed in UI

When user clicks "Start":

```javascript
// In your frontend code
const response = await fetch('http://localhost:5000/api/sessions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    program_name: 'Manual Control',
    target_pressure: userInput.pressure,
    duration_minutes: userInput.duration
  })
});

// Start control by calling backend script
// OR poll database and start control based on session status
```

## Alternative: Direct Python Call

Or, your UI could trigger a Python script:

```javascript
// Start control by running Python script
await fetch('http://localhost:5000/api/run-control', {
  method: 'POST',
  body: JSON.stringify({
    target_pressure: 20,
    duration_minutes: 30
  })
});
```

But you'd need to add this endpoint to your API server.

## Recommended Approach

**Simplest for now:**

1. Run the main service (reads sensors, logs to DB)
2. Run API server (serves data)
3. UI starts a control session by creating database entry
4. Add a script that monitors new sessions and starts pressure control

**OR**

Modify the main service to check for active sessions and start control automatically.

## Check What's Currently Running

Run this to see what services are active:

```powershell
# Check if service is running
Get-Process python

# Check if API is responding
Invoke-RestMethod http://localhost:5000/api/health
```

## Summary

You need **3 terminals** running:
1. `python sensor_control_service.py` - Reads sensors
2. `python api_server.py` - Serves API
3. `npm run dev` - Frontend

Then the UI can make HTTP requests to control pressure!

