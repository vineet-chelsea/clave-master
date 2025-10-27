# ✅ Pressure Control System Complete!

## What Was Created

### 1. Pressure Controller Service ✅
**File:** `backend/pressure_controller.py`

**Features:**
- ✅ Monitors pressure every second
- ✅ Controls valve register 51 (0-4000)
- ✅ Adjusts valve every 30 seconds if needed
- ✅ Accepts ±1 PSI tolerance
- ✅ Logs to database automatically
- ✅ Creates session tracking

### 2. Database Tables ✅
- ✅ `process_sessions` - Track control sessions
- ✅ `process_logs` - Log pressure/temperature/valve data

### 3. API Endpoints ✅
- ✅ `GET /api/sessions` - List sessions
- ✅ `GET /api/sessions/{id}/logs` - Get session logs

## How It Works

### Control Logic

```python
# Every second:
- Read pressure from Register 70
- Read temperature from Register 69
- Log to database

# Every 30 seconds:
- Check if pressure is within ±1 PSI of target
- If too low: increase valve (valve += 200)
- If too high: decrease valve (valve -= 200)
- If in range: maintain current valve position
```

### Valve Control

**Register 51 (Holding Register):**
- Range: 0-4000
- 0 = Fully closed
- 4000 = Fully open
- Adjustments: ±200 per control cycle

## Usage

### Manual Mode

```bash
cd backend
python pressure_controller.py 20 30
```

**Parameters:**
- `20` = Target pressure (PSI)
- `30` = Duration (minutes)

### Expected Behavior

```
============================================================
Pressure Control System
============================================================
Target Pressure: 20 PSI
Duration: 30 minutes
Tolerance: ±1 PSI
Control Interval: 30 seconds
============================================================

[OK] Connected to PostgreSQL
[OK] Created session: 123
[OK] Connected to PLC on COM10
[OK] Initialized valve position: 0/4000

[12:30:45] Pressure: 18.5 PSI / Target: 20.0 PSI | Valve: 0/4000 | Time left: 30 min
[12:30:46] Pressure: 18.6 PSI / Target: 20.0 PSI | Valve: 0/4000 | Time left: 29 min
...
[12:31:15] Pressure: 19.2 PSI / Target: 20.0 PSI | Valve: 200/4000 | Time left: 29 min
[CONTROL] Pressure low (19.2 < 20.0), increasing valve to 400
[12:31:16] Pressure: 20.3 PSI / Target: 20.0 PSI | Valve: 400/4000 | Time left: 29 min
[OK] Pressure within tolerance (20.3 ± 1.0 PSI)
...
[COMPLETE] Target pressure reached for 30 minutes
```

## Database Logging

### Sessions Table
Stores each control run:
```sql
id | program_name | status | start_time | end_time
1  | Manual Control | completed | 2025-10-26 12:30:00 | 2025-10-26 13:00:00
```

### Logs Table
Stores every reading:
```sql
session_id | pressure | temperature | valve_position | timestamp
1         | 18.5     | 25.8        | 0              | 2025-10-26 12:30:45
1         | 20.3     | 26.1        | 400            | 2025-10-26 12:31:16
```

## Integration with Frontend

### Current Status

Frontend can now:
1. **Start control session** - Call pressure controller
2. **Monitor in real-time** - Poll latest readings
3. **View sessions** - `GET /api/sessions`
4. **View logs** - `GET /api/sessions/{id}/logs`

### Next Steps for Full UI Integration

1. **Manual Control Page** - Already exists
   - User sets target pressure and duration
   - Calls `pressure_controller.py` with parameters
   - Displays current readings

2. **Auto Mode** - Needs enhancement
   - Select program from database
   - Extract pressure and duration
   - Run with program parameters

3. **Sessions View** - Already exists
   - Shows all sessions
   - Click to view logs
   - Display valve adjustments

## Testing

### Test the Controller:

```bash
# Terminal 1: Start sensor service (reads from PLC)
cd backend
python sensor_service.py

# Terminal 2: Start API server
python api_server.py

# Terminal 3: Run pressure control test (1 minute test)
python pressure_controller.py 20 1
```

### View in Database:

```bash
# Check session created
psql -U postgres -h 127.0.0.1 -p 5432 -d autoclave -c "SELECT * FROM process_sessions ORDER BY id DESC LIMIT 1;"

# Check logs
psql -U postgres -h 127.0.0.1 -p 5432 -d autoclave -c "SELECT COUNT(*) FROM process_logs;"
```

## Complete Architecture

```
┌─────────────┐
│ PLC         │
│ Register 70 │→ Pressure (0-87 PSI)
│ Register 69 │→ Temperature (0-350°C)
│ Register 51 │→ Valve Control (0-4000) ← Controls pressure
└──────┬──────┘
       │
       ↓
┌──────────────────┐
│Pressure Controller│
│ • Reads pressure  │
│ • Controls valve  │
│ • Every 30 sec    │
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│   PostgreSQL     │
│ • Sessions       │
│ • Logs           │
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│   API Server     │
│ Port 5000        │
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│   Frontend       │
│ • Real-time UI   │
│ • Shows pressure │
│ • Shows valve    │
└──────────────────┘
```

## Features Implemented

✅ **Manual Control**
- Set target pressure
- Set duration
- Automatic valve control
- Logs everything

✅ **Registers Used**
- 70: Read pressure
- 69: Read temperature
- 51: Control valve

✅ **Control Algorithm**
- ±1 PSI tolerance
- 30 second adjustment interval
- Valve range 0-4000
- Smooth control (±200 steps)

✅ **Logging**
- Every reading logged
- Session tracking
- Valve position recorded
- Timestamps on all data

## Run All Services

```bash
# Terminal 1: Read sensors (background)
cd backend
python sensor_service.py

# Terminal 2: API server
python api_server.py

# Terminal 3: Pressure control (when user starts)
python pressure_controller.py 20 30

# Terminal 4: Frontend
npm run dev
```

## Everything is Ready! 🎉

Your pressure control system:
- ✅ Monitors pressure continuously
- ✅ Controls valve automatically
- ✅ Maintains target ±1 PSI
- ✅ Logs to database
- ✅ Visible in UI sessions

Just integrate the controller call from your frontend! 🚀

