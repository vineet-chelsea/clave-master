# Pressure Control System Documentation

## Overview

The pressure control system monitors and regulates pressure using Modbus PLC control.

## Registers

- **Register 70**: Current Pressure (input, read-only, 0-4095 → 0-87 PSI)
- **Register 69**: Current Temperature (input, read-only)
- **Register 51**: Valve Control (holding, writable, 0-4000)

## Control Logic

1. **Target Pressure**: Set by user (e.g., 20 PSI)
2. **Tolerance**: ±1 PSI acceptable range
3. **Control Interval**: Adjusts valve every 15 seconds if needed
4. **Valve Range**: 0-4000 (0 = closed, 4000 = fully open)

## How It Works

```python
# Control loop every 15 seconds:
if current_pressure < target_pressure - 1:
    # Too low, open valve more
    valve_position += 200
    
elif current_pressure > target_pressure + 1:
    # Too high, close valve more
    valve_position -= 200
    
else:
    # Within tolerance, maintain current valve position
    pass
```

## Usage

### Manual Control

```bash
cd backend
python pressure_controller.py 20 30
```

**Parameters:**
- `20` = Target pressure in PSI
- `30` = Duration in minutes

### Auto Mode

Run with program from database:

```python
controller = PressureController(
    target_pressure=program.target_pressure,
    duration_minutes=program.duration,
    session_name=program.name
)
controller.control_pressure()
```

## Database Tables

### `process_sessions`
- `id`: Session ID
- `program_name`: Program or "Manual Control"
- `status`: running/completed/stopped
- `start_time`: Session start
- `end_time`: Session end

### `process_logs`
- `id`: Log entry ID
- `session_id`: Link to session
- `program_name`: Program name
- `pressure`: Current pressure (PSI)
- `temperature`: Current temperature (°C)
- `valve_position`: Valve opening (0-4000)
- `status`: running/paused/stopped
- `timestamp`: Log time

## Integration with Frontend

### Start Session

Frontend calls pressure controller with:
- Target pressure
- Duration
- Session name

### Monitor Progress

Frontend polls API:
- `GET /api/sensor-readings/latest` - Current pressure/temperature
- `GET /api/sessions` - List of sessions
- `GET /api/sessions/{id}/logs` - Session logs

### Stop Session

Send interrupt (Ctrl+C) to controller or call stop API endpoint.

## Control Behavior

**Every 1 second:**
- Read pressure and temperature
- Log to database
- Display status

**Every 15 seconds:**
- Check if pressure is within tolerance
- Adjust valve if needed
- Log adjustment

**Example Output:**

```
[12:30:45] Pressure: 18.5 PSI / Target: 20.0 PSI | Valve: 1500/4000 | Time left: 29 min
[12:31:00] Pressure: 19.2 PSI / Target: 20.0 PSI | Valve: 1700/4000 | Time left: 29 min
[CONTROL] Pressure low (19.2 < 20.0), increasing valve to 1900
[12:31:15] Pressure: 20.3 PSI / Target: 20.0 PSI | Valve: 1900/4000 | Time left: 28 min
[OK] Pressure within tolerance (20.3 ± 1.0 PSI)
```

## Safety

- Maximum pressure: 87 PSI (register max = 4095)
- Valve never exceeds 0-4000 range
- Stops automatically after duration
- Logs all actions for traceability

## Next Steps

1. Integrate with frontend UI
2. Add start/stop/pause controls
3. Display valve position in UI
4. Show control adjustments in real-time
5. Add alarm thresholds

