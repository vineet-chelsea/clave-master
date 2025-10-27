# ⚠️ Multi-Step Backend Implementation Needed

## Current Problem

**Target PSI is not increasing in backend as flow moves on**

The backend currently:
- ✅ Starts with first step's target PSI
- ✅ Controls valve to reach that pressure
- ⚠️ **Never advances to next steps**
- ⚠️ **Never updates target pressure**

## Root Cause

The `sensor_control_service.py` doesn't implement multi-step logic. It only:
1. Reads `target_pressure` from session
2. Controls valve to reach that pressure
3. Waits for duration
4. Completes

**It never checks or processes `steps_data` from the session.**

## What Needs to Be Added

### 1. Read Program Steps from Session

```python
# In control_loop or start_control_session
cursor.execute(
    "SELECT steps_data FROM process_sessions WHERE id=%s",
    (self.session_id,)
)
result = cursor.fetchone()
steps_data = result[0] if result and result[0] else None
```

### 2. Track Current Step

Add state variables:
```python
self.current_step_index = 0
self.step_start_time = None
self.program_steps = []
```

### 3. Check Step Completion

```python
def check_step_completion(self):
    """Check if current step duration has been exceeded"""
    if not self.program_steps or self.current_step_index >= len(self.program_steps):
        return False
    
    current_step = self.program_steps[self.current_step_index]
    step_duration_minutes = current_step['duration_minutes']
    
    elapsed_minutes = (time.time() - self.step_start_time) / 60
    
    if elapsed_minutes >= step_duration_minutes:
        return True
    return False
```

### 4. Advance to Next Step

```python
def advance_to_next_step(self):
    """Move to next program step"""
    self.current_step_index += 1
    
    if self.current_step_index >= len(self.program_steps):
        # All steps complete
        self.complete_session()
        return
    
    # Update target pressure for new step
    new_step = self.program_steps[self.current_step_index]
    target_pressure = self.parse_pressure_range(new_step['psi_range'])
    
    self.target_pressure = target_pressure
    self.step_start_time = time.time()
    
    print(f"[STEP] Advanced to step {self.current_step_index + 1}/{len(self.program_steps)}")
    print(f"[STEP] New target: {target_pressure} PSI")
```

### 5. Parse Pressure Range

```python
def parse_pressure_range(self, psi_range):
    """Parse pressure from range string (e.g., '5-10' -> 7.5)"""
    if '-' in psi_range:
        parts = psi_range.split('-')
        if len(parts) == 2:
            try:
                low = float(parts[0].strip())
                high = float(parts[1].strip())
                return (low + high) / 2  # Median
            except:
                pass
    # Single value or "Steady at X"
    try:
        import re
        numbers = re.findall(r'\d+(?:\.\d+)?', psi_range)
        if numbers:
            return float(numbers[0])
    except:
        pass
    return 0
```

### 6. Update Control Loop

```python
# In control_loop, add step check
if self.check_step_completion():
    self.advance_to_next_step()
```

## Implementation Locations

### File: `backend/sensor_control_service.py`

**Add to `__init__`:**
```python
self.current_step_index = 0
self.step_start_time = None
self.program_steps = []
```

**Add methods:**
- `parse_pressure_range()`
- `load_program_steps()`
- `check_step_completion()`
- `advance_to_next_step()`

**Update `start_control_session()`:**
```python
# Load program steps if this is an auto program
if steps_data:
    self.program_steps = steps_data
    self.current_step_index = 0
    self.step_start_time = time.time()
    # Set target to first step
    first_step = self.program_steps[0]
    self.target_pressure = self.parse_pressure_range(first_step['psi_range'])
```

**Update `control_loop()`:**
```python
# Check if step completed
if self.program_steps and self.current_step_index < len(self.program_steps):
    if self.check_step_completion():
        self.advance_to_next_step()
```

## Expected Behavior After Fix

### Test Program (6 minutes)
1. **Step 1:** Target 7.5 PSI for 1 min
2. **Step 2:** Target 10 PSI for 1 min
3. **Step 3:** Target 22.5 PSI for 1 min
4. **Step 4:** Target 22.5 PSI for 1 min
5. **Step 5:** Target 42.5 PSI for 1 min
6. **Step 6:** Target 42.5 PSI for 1 min
7. **Complete**

### Console Output
```
[STEP] Advanced to step 2/6
[STEP] New target: 10.0 PSI
[CONTROL] Adjusting valve to reach 10.0 PSI
```

## Summary

The backend needs to:
1. ✅ Load `steps_data` from session
2. ✅ Track current step index
3. ✅ Monitor elapsed time per step
4. ✅ Advance to next step when duration exceeded
5. ✅ Update target pressure for each step
6. ✅ Repeat until all steps complete

**This is the missing multi-step logic!** 🎯

