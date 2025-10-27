# ✅ UI Integration Complete!

## What Was Fixed

The UI was **NOT calling the backend** to start control sessions.

### Before:
```javascript
// Just changed UI mode - no backend call
const handleManualStart = (targetPressure, duration) => {
  setManualConfig({ targetPressure, duration });
  setMode('manual-running');  // Only UI change!
}
```

### After:
```javascript
// Now calls backend API
const handleManualStart = async (targetPressure, duration) => {
  const response = await fetch('http://localhost:5000/api/start-control', {
    method: 'POST',
    body: JSON.stringify({
      target_pressure: targetPressure,
      duration_minutes: duration
    })
  });
  // ... handle response
}
```

## Changes Made

### 1. Manual Control (`src/pages/Index.tsx`)
- ✅ Now calls `/api/start-control` endpoint
- ✅ Passes target pressure and duration
- ✅ Shows error toast if API call fails

### 2. Auto Program (`src/pages/Index.tsx`)
- ✅ Also calls `/api/start-control` endpoint
- ✅ Extracts pressure and duration from program
- ✅ Shows error if fails

## What Happens Now

### When User Clicks Start:

1. **UI makes API call** → `POST /api/start-control`
2. **API creates database session** → `process_sessions` table
3. **Service reads the database** → Control logic activates
4. **Valve controls automatically** → Maintains target pressure
5. **UI shows progress** → Polls sensor readings

## How to Test

### Start Services:

```bash
# Terminal 1 - Main service
cd backend
python sensor_control_service.py

# Terminal 2 - API server  
cd backend
python api_server.py

# Terminal 3 - Frontend
npm run dev
```

### Test from UI:

1. Click "Manual" mode
2. Set target pressure (e.g., 20 PSI)
3. Set duration (e.g., 5 minutes)
4. Click "START MANUAL PROCESS"

### Expected Output:

**In Terminal 1 (service):**
```
[OK] Started control session 123
     Target: 20.0 PSI
     Duration: 5 minutes
     Control thread started
[CONTROL] Control loop started
[12:30:45] Reading #1 - Pressure: 18.5 PSI, Temperature: 25.8°C | Target: 20.0 PSI | Valve: 0/4000 | Time: 5 min
```

**In UI:**
- ✅ No "failed to start session" error
- ✅ Shows ProcessMonitor screen
- ✅ Displays current pressure and temperature
- ✅ Updates in real-time

## Error Handling

If the API is not running:
```javascript
toast({
  title: "Failed to Start",
  description: "Could not start pressure control",
  variant: "destructive"
});
```

If database connection fails:
```javascript
toast({
  title: "Failed to Start",
  description: result.error,
  variant: "destructive"
});
```

## Complete Flow

```
User clicks "START" in UI
    ↓
handleManualStart() called
    ↓
fetch('http://localhost:5000/api/start-control')
    ↓
API server receives request
    ↓
Creates session in PostgreSQL
    ↓
Returns session_id to UI
    ↓
UI changes to ProcessMonitor view
    ↓
Service reads database and starts control
    ↓
Valve adjusts automatically every 30 seconds
    ↓
Pressure maintained at target ±1 PSI
```

## Everything is Connected! 🎉

The UI now properly starts control sessions through the API!

