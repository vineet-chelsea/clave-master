# ✅ Final Setup Complete!

## Current Status

✅ **Python Service** - Reading from PLC, saving to PostgreSQL  
✅ **API Server** - Serving data from PostgreSQL on port 5000  
✅ **Frontend Updated** - Polls API every second  

## How to Start Everything

### Terminal 1: Sensor Service (Reads PLC)
```bash
cd backend
python sensor_service.py
```

You should see:
```
[OK] Connected to PostgreSQL
[OK] Connected to PLC on COM10
[12:30:45] Reading #1 - Pressure: 0.0 PSI, Temperature: 24.8°C [OK]
```

### Terminal 2: API Server (Serves Data)
```bash
cd backend
python api_server.py
```

You should see:
```
============================================================
Sensor Readings API Server
============================================================
PostgreSQL: 127.0.0.1:5432/autoclave
Starting server on http://localhost:5000
============================================================
```

### Terminal 3: Frontend
```bash
npm run dev
```

## How to Verify It's Working

### 1. Check API is responding:
```bash
curl http://localhost:5000/api/sensor-readings/latest
```

### 2. Check database has data:
```bash
psql -U postgres -h 127.0.0.1 -p 5432 -d autoclave -c "SELECT COUNT(*) FROM sensor_readings;"
```

### 3. Open browser:
http://localhost:8080

You should see:
- Current pressure value
- Current temperature value
- Values updating every second!

## Architecture

```
┌──────────┐
│   PLC    │ COM10
│ (Modbus) │
└─────┬────┘
      │ Reads every 1 second
      ↓
┌─────────────────┐
│ sensor_service  │
│     .py         │
└─────┬───────────┘
      │ Saves to
      ↓
┌─────────────────┐
│   PostgreSQL    │
│  (autoclave)    │
└─────┬───────────┘
      │ Serves via
      ↓
┌─────────────────┐
│  api_server.py  │
│  Port 5000      │
└─────┬───────────┘
      │ API calls
      ↓
┌─────────────────┐
│   Frontend      │
│  (React App)    │
└─────────────────┘
  Shows live data!
```

## Files Created

**Backend:**
- `sensor_service.py` - Reads PLC, saves to PostgreSQL
- `api_server.py` - REST API server
- `sensor_service_no_db.py` - CSV version (alternative)
- `.env` - Configuration

**Frontend:**
- `src/pages/Index.tsx` - Updated to poll API
- `src/components/ProcessMonitor.tsx` - Updated to poll API
- `src/integrations/supabase/client.ts` - Added API helper

## Troubleshooting

### "ModuleNotFoundError: No module named 'flask'"
**Solution:** Already installed! ✅

### "API not responding"
- Make sure API server is running
- Check `http://localhost:5000/api/health`

### "No readings in database"
- Check sensor_service.py is running
- Verify PLC connection
- Check PostgreSQL is running

### "UI not updating"
- Make sure all 3 services are running:
  1. sensor_service.py
  2. api_server.py  
  3. Frontend (npm run dev)
- Check browser console for errors

## Quick Commands

### Start sensor service:
```bash
cd backend && python sensor_service.py
```

### Start API server:
```bash
cd backend && python api_server.py
```

### Start frontend:
```bash
npm run dev
```

### Check database:
```bash
psql -U postgres -h 127.0.0.1 -p 5432 -d autoclave -c "SELECT * FROM sensor_readings ORDER BY timestamp DESC LIMIT 5;"
```

## Everything is Ready! 🎉

Your UI will now show real-time pressure and temperature values that update every second!

Just run all 3 services and watch it work! 🚀

