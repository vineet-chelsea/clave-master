# 🔍 Enhanced Debug - Session Restoration

## Added Extensive Logging

Added detailed console logs to track what's happening:

### On Page Load:
- `[INDEX] Checking for active sessions...`
- `[INDEX] All sessions:` - Shows all sessions from API
- `[INDEX] Active session:` - Shows if one was found
- `[INDEX] ✓ Restoring` - If restoring
- `[INDEX] ✗ No session` - If not found or incomplete

### While on Selection Screen:
- Checks every 2 seconds for active sessions
- Logs: `🔄 Active session found while on selection...`
- Auto-restores if found

## How to Debug

### 1. Open Browser Console (F12)
Press F12, go to Console tab

### 2. Refresh Page
Look for logs starting with `[INDEX]`

### 3. Check What You See

**If session found:**
```
[INDEX] All sessions: [...]
[INDEX] Active session: {id, status, target_pressure, ...}
[INDEX] ✓ Restoring active session
```

**If session NOT found:**
```
[INDEX] All sessions: [...]
[INDEX] ✗ No active session found
```

### 4. Share Console Output

Copy the console output and share it so I can see:
- Are sessions being fetched?
- Is active session found?
- What's the data structure?
- Any errors?

## Expected Behavior

After refresh with active session:
1. Page loads
2. `[INDEX] Checking...` appears
3. `[INDEX] All sessions: [...]` shows sessions
4. `[INDEX] Active session: {...}` shows the active one
5. UI auto-switches to ProcessMonitor
6. Shows correct duration and pressure

## Debug This! 🔍

Share the browser console output after refreshing!

