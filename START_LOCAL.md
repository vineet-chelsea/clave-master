# Start Local Development - All in One

## Quick Start (Run these 3 commands in separate terminals)

### Terminal 1: Backend Sensor Control Service
```powershell
cd C:\Users\vemco\clave-master\backend
python sensor_control_service.py
```

### Terminal 2: Backend API Server
```powershell
cd C:\Users\vemco\clave-master\backend
python api_server.py
```

### Terminal 3: Frontend
```powershell
cd C:\Users\vemco\clave-master
npm run dev
```

Then open: **http://localhost:8080**

## What You Should See

### Terminal 1 (Sensor Service)
```
Starting Autoclave Backend Services...
[OK] Connected to PLC on COM10
[OK] Connected to PostgreSQL
Reading sensors every 1 second...
[OK] Saved sensor reading: P=0.0 PSI, T=25.0°C
```

### Terminal 2 (API Server)
```
[INFO] Starting Flask API server on http://0.0.0.0:5000
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

### Terminal 3 (Frontend)
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:8080/
  ➜  Network: use --host to expose
```

## First Time Setup

If you haven't run the database initialization yet:
```powershell
cd C:\Users\vemco\clave-master\backend
python init_local_db.py
```

This creates the required database tables.

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'pymodbus'"
```powershell
pip install -r requirements.txt
```

### Error: "could not connect to server"
- Check PostgreSQL is running: `Get-Service postgresql-x64-17`
- Start PostgreSQL: `net start postgresql-x64-17`

### Error: "Access is denied" on COM10
- Close any other programs using COM10
- Check Device Manager for serial port conflicts

### 500 Errors from API
- Make sure you ran `python init_local_db.py` first
- Check both backend services are running
- Check console output for error messages

## Stopping Everything

- Press `Ctrl+C` in each terminal
- Or close the terminal windows

## Next Steps

Once local setup works:
1. Test manual mode
2. Test auto mode with programs
3. Check history section
4. Then deploy to Raspberry Pi with Docker

