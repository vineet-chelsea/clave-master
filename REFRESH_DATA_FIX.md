# ✅ Refresh Data Fix

## Problem

On refresh, UI shows:
- "Manual control 20 PSI for 5 min" (default)
- "0/5 minutes" progress
- Wrong data from old session

## Root Cause

Session restoration was using sessions without `target_pressure` and `duration_minutes` values, defaulting to 20 PSI / 5 min.

## Fix Applied

Now **only restores session if BOTH values exist**:

```typescript
if (activeSession && activeSession.target_pressure && activeSession.duration_minutes) {
  // Valid session - restore it
} else {
  // Session incomplete - don't restore
}
```

## What's Fixed

✅ **Only restores with valid data** - Won't use incomplete sessions  
✅ **Correct duration** - Shows actual duration from database  
✅ **Correct pressure** - Shows actual pressure from database  
✅ **No defaults** - Won't assume 20 PSI / 5 min  

## Result

- If session has complete data → Restore with correct values
- If session incomplete → Don't restore, stay on selection screen
- Prevents showing wrong "5 min" from incomplete data

## Everything Fixed! 🎉

Refresh will now show correct duration and pressure from session data!

