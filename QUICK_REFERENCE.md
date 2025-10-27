# Quick Reference Guide

## 🎯 How to Run Manual Control

### From Command Line:
```bash
cd backend
python pressure_controller.py 20 30
```

Parameters:
- `20` = Target pressure in PSI
- `30` = Duration in minutes

### From Frontend (Integration Needed):
1. User enters target pressure (e.g., 20 PSI)
2. User enters duration (e.g., 30 minutes)
3. Frontend calls: `python pressure_controller.py 20 30`
4. Controller automatically:
   - Monitors pressure
   - Adjusts valve (register 51)
   - Logs to database
   - Displays progress

## 📊 How It Works

### Control Loop (Every 30 seconds):
```
Read current pressure
  ↓
Compare to target (±1 PSI tolerance)
  ↓
If pressure < target - 1:
  → Increase valve (valve += 200)
  
If pressure > target + 1:
  → Decrease valve (valve -= 200)
  
If within tolerance:
  → Maintain valve position
```

### Registers Used:
- **Register 70**: Read current pressure (0-87 PSI)
- **Register 51**: Control valve opening (0-4000)
  - 0 = Closed
  - 4000 = Fully open
  - Adjustments ±200 per cycle

## 🔄 Auto Mode Integration

For auto mode (program selection):
1. Load program from database
2. Extract steps (pressure and duration for each step)
3. For each step, run:
   ```python
   python pressure_controller.py <step_pressure> <step_duration>
   ```

## 📈 Viewing Results

### Database Queries:

**List sessions:**
```bash
psql -U postgres -h 127.0.0.1 -p 5432 -d autoclave -c "SELECT * FROM process_sessions ORDER BY start_time DESC LIMIT 10;"
```

**View logs for a session:**
```bash
psql -U postgres -h 127.0.0.1 -p 5432 -d autoclave -c "SELECT * FROM process_logs WHERE session_id=1 ORDER BY timestamp;"
```

### Via API:

**Get all sessions:**
```bash
curl http://localhost:5000/api/sessions
```

**Get session logs:**
```bash
curl http://localhost:5000/api/sessions/1/logs
```

## 🎮 Services Needed

### For Pressure Control:
1. **sensor_service.py** - Background reading (optional)
2. **pressure_controller.py** - Active control
3. **api_server.py** - Serves data

### For UI Updates:
All 3 services must be running for real-time UI updates.

## ⚙️ Configuration

Current settings in `backend/.env`:
```env
PG_HOST=127.0.0.1
PG_PORT=5432
PG_DATABASE=autoclave
PG_USER=postgres
PG_PASSWORD=postgres

COM_PORT=COM10
BAUD_RATE=9600
SLAVE_ID=1
```

Modbus registers:
- Pressure: 70
- Temperature: 69
- Valve Control: 51

## 🚀 Quick Start

### Test (1 minute):
```bash
cd backend
python pressure_controller.py 20 1
```

### Full Session (30 minutes):
```bash
cd backend
python pressure_controller.py 20 30
```

The controller will:
- ✅ Connect to PLC
- ✅ Monitor pressure every second
- ✅ Adjust valve every 30 seconds
- ✅ Maintain target ±1 PSI
- ✅ Log to database
- ✅ Show progress in console

## Complete! 🎉

Your pressure control system is ready. Integrate from UI and start controlling! 🚀

