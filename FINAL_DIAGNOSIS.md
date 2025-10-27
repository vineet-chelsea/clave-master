# 🔍 Final Diagnosis

## Current Status

Need to see what's actually in the database to understand the issue.

## What to Check

### 1. Database Status
Run this to see active sessions:
```bash
psql -U postgres -h 127.0.0.1 -p 5432 -d autoclave -c "SELECT id, status, target_pressure, duration_minutes FROM process_sessions WHERE status IN ('running', 'paused');"
```

### 2. Browser Console
Press F12 and look for:
- "Active session found" logs
- Any errors in red
- Network tab for API calls

### 3. API Response
Open in browser: http://localhost:5000/api/sessions
Should show active sessions

## Likely Issues

### Issue 1: Session has NULL values
Old sessions created before API fix have NULL target_pressure/duration_minutes
**Fix:** Clean database (already done)

### Issue 2: Multiple sessions
Multiple 'running' sessions causing confusion
**Fix:** Stop all, start fresh

### Issue 3: Backend not running
Sensor service not detecting sessions
**Fix:** Restart sensor service

## Next Steps

1. **Clean database:**
```bash
psql -U postgres -h 127.0.0.1 -p 5432 -d autoclave -c "UPDATE process_sessions SET status='stopped' WHERE status IN ('running', 'paused');"
```

2. **Restart all services**

3. **Start new session**

4. **Check logs in all terminals**

## Need More Info

Share:
- Browser console output
- Database query results  
- What happens when you click START
- Any error messages

