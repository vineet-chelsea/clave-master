# ✅ Fixed Type Error!

## Problem

```
TypeError: unsupported operand type(s) for -: 'float' and 'decimal.Decimal'
```

The database returns `Decimal` type, but code was comparing with `float`.

## Fix Applied

1. **Convert database values to float:**
   ```python
   float(target_pressure)
   int(duration_minutes)
   ```

2. **Convert in control loop:**
   ```python
   pressure_diff = float(pressure) - float(self.target_pressure)
   ```

## What Changed

- ✅ Database Decimal → Float conversion
- ✅ Type safety in control logic
- ✅ Proper error handling

## Try Again!

Refresh and start a session. Should work now! ✅

