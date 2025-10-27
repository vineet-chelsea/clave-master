# ✅ Session Restore Fix - Manual and Auto Mode

## Problem

On page refresh, UI didn't detect if session was manual or auto mode, causing:
- "Start New Session" button shown incorrectly
- Couldn't determine correct mode
- Session data lost on refresh

## Root Cause

Session restoration logic only checked for `target_pressure` and `duration_minutes`, which didn't distinguish between:
- Manual mode (single step)
- Auto mode (multi-step with `steps_data`)

## Fix Applied

### 1. Frontend (`Index.tsx`)
✅ Added `steps_data` check to distinguish auto vs manual  
✅ Restores auto programs with `selectedProgram` and `setMode('auto-running')`  
✅ Restores manual sessions with `manualConfig` and `setMode('manual-running')`  
✅ Updated both initial load AND continuous session check  

### 2. Backend (`api_server.py`)
✅ Added `steps_data` column to `/api/sessions` response  
✅ Returns `steps_data` from `process_sessions` table  

## How It Works

### Detection Logic
```typescript
if (activeSession.steps_data && Array.isArray(activeSession.steps_data)) {
  // AUTO MODE - Has multiple steps
  setSelectedProgram(program);
  setMode('auto-running');
} else if (activeSession.target_pressure && activeSession.duration_minutes) {
  // MANUAL MODE - Single step
  setManualConfig({ targetPressure, duration });
  setMode('manual-running');
}
```

### Auto Mode Detection
- Checks for `steps_data` array in session
- Restores complete program with steps
- Shows ProcessMonitor with multi-step progress

### Manual Mode Detection
- Checks for `target_pressure` and `duration_minutes`
- Restores manual config
- Shows ProcessMonitor with single step

## What's Fixed

✅ **Auto mode refresh** - Restores with program and steps  
✅ **Manual mode refresh** - Restores with pressure/duration  
✅ **Continuous monitoring** - Detects sessions while on selection screen  
✅ **Mode distinction** - Correctly identifies manual vs auto  
✅ **Session persistence** - Works after refresh or page load  

## Testing

### Test Auto Mode
1. Start auto program (Hypalon Polymers)
2. Wait a few seconds
3. Refresh page (F5)
4. ✅ Should show active session with program name
5. ✅ Should display all 6 steps
6. ✅ Should show current step progress

### Test Manual Mode
1. Start manual session (e.g., 20 PSI for 30 min)
2. Wait a few seconds  
3. Refresh page (F5)
4. ✅ Should show active session with pressure
5. ✅ Should display single step
6. ✅ Should show progress bar

### Test Both
1. Start auto program
2. Refresh page - should restore auto mode
3. Stop program
4. Start manual session
5. Refresh page - should restore manual mode

## API Response Example

### Auto Program Session
```json
{
  "id": 123,
  "program_name": "Hypalon Polymers",
  "status": "running",
  "target_pressure": 7.5,
  "duration_minutes": 270,
  "steps_data": [
    {"psi_range": "5-10", "duration_minutes": 15, "action": "raise"},
    {"psi_range": "10", "duration_minutes": 75, "action": "steady"},
    ...
  ]
}
```

### Manual Session
```json
{
  "id": 124,
  "program_name": "Manual Control",
  "status": "running",
  "target_pressure": 20.0,
  "duration_minutes": 30,
  "steps_data": null
}
```

## Summary

The UI now correctly:
- ✅ Detects active sessions on refresh
- ✅ Distinguishes between manual and auto mode
- ✅ Restores correct mode type
- ✅ Shows appropriate UI components
- ✅ Maintains session data
- ✅ Prevents duplicate "Start" buttons

Both manual and auto mode now persist correctly! 🎉
