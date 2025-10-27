# 🚀 Start These 3 Commands NOW

## ERROR: ERR_CONNECTION_REFUSED

The API server on port 5000 is not running!

## Start in THIS Order:

### Terminal 1: Sensor Service
```bash
cd C:\Users\vemco\clave-master\backend
python sensor_control_service.py
```

**Wait until you see:**
```
[OK] Connected to PostgreSQL
[OK] Connected to PLC on COM10
[INFO] Service ready...
```

### Terminal 2: API Server (MOST IMPORTANT!)
```bash
cd C:\Users\vemco\clave-master\backend
python api_server.py
```

**Wait until you see:**
```
Starting server on http://localhost:5000
 * Serving Flask app 'api_server'
 * Debug mode: on
Running on http://127.0.0.1:5000
```

### Terminal 3: Frontend
```bash
cd C:\Users\vemco\clave-master
npm run dev
```

**Wait until you see:**
```
VITE ready in XXX ms
  ➜  Local:   http://localhost:5173/
```

## Then Test:

1. Open: http://localhost:5173
2. Click "MANUAL"
3. Set pressure and duration
4. Click "START MANUAL PROCESS"

## What You Should See:

**In Terminal 2 (API Server):**
```
127.0.0.1 - - [12:30:45] "POST /api/start-control HTTP/1.1" 200 -
```

**In Terminal 1 (Sensor Service):**
```
[NEW SESSION] Detected session 7
     Target: 20.0 PSI
     Duration: 5 minutes
[OK] Started control session 7
[CONTROL] Control loop started
```

**In Browser Console (F12):**
```
API Response: {success: true, session_id: 7, ...}
```

## ⚠️ Important:

The API server **MUST** be running for the frontend to work!

Check if it's running:
```powershell
netstat -an | findstr :5000
```

Should show:
```
TCP    0.0.0.0:5000           0.0.0.0:0              LISTENING
```

If nothing shows, the API server is NOT running!

