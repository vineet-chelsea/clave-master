# Debug Chart and Duration Issues

## Problem Summary

From the screenshot:
- ✅ UI shows "Manual Control - 20 PSI for 5 min"
- ❌ Charts are empty (no data)
- ❌ Progress shows "0 / 5 minutes" (not increasing)

## Root Cause Analysis

### 1. Chart Data Issue
Charts are empty because:
- `startProcessSimulation` runs every 1 second
- But it might not be running if `status !== 'running'`
- Or `currentPressure`/`currentTemperature` are 0

### 2. Progress Not Increasing
Progress shows 0 because:
- Progress calculation might be wrong
- Or status is not 'running'

## Console Debug

Check browser console (F12) for:
1. **Chart data logs** - Should see data every 10 seconds
2. **Session ID** - "Set sessionId to: X"
3. **Sensor readings** - Check if values are updating

## What to Check

### In Browser Console:
Look for logs starting with:
- "Chart data:" - Should show data being added
- "Found active session:" - Should show session being restored
- "Setting manual config:" - Should show correct values

### Duration Values:
From database query, recent sessions show:
- ID 28: duration=2, target=20 ✅ (stopped)
- ID 26: duration=1, target=20 ✅ (stopped)
- ID 22: duration=2, target=20 ✅ (stopped)

So values ARE being saved correctly!

## Next Steps

1. Open browser console (F12)
2. Start a new process
3. Check console for:
   - Chart data length
   - Sensor readings
   - Progress updates
4. Share console output if still not working

## Added Debug Logging

Added console.log to chart updates to see what's happening.

