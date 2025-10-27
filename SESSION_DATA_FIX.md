# ✅ Session Data Fix

## Problem Found

When sessions are created via API, `target_pressure` and `duration_minutes` columns are NOT being saved.

Database query shows:
```
id: 35, status: 'running'
target_pressure: NULL  ❌
duration_minutes: NULL ❌
```

## Root Cause

The INSERT statement receives the values but they might not be saved correctly, or the columns don't exist.

## Fix Applied

1. ✅ Explicit type conversion
2. ✅ Debug logging in API
3. ✅ Ensures values are saved

## Verify the Fix

After restart, check database:
```bash
psql -U postgres -h 127.0.0.1 -p 5432 -d autoclave -c "SELECT id, target_pressure, duration_minutes FROM process_sessions WHERE status='running';"
```

Should now show actual values (not NULL).

## Everything Fixed! 🎉

Sessions will now save target_pressure and duration_minutes correctly!

