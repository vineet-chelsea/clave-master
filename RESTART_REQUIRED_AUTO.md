# 🔄 Restart Required for Auto Mode

## Changes Made

### 1. New Table: `autoclave_programs`
✅ Added program storage  
✅ "Hypalon Polymers" loaded  

### 2. Updated Table: `process_sessions`  
✅ Added `steps_data` column (JSONB)  
✅ Stores program steps for multi-step execution  

### 3. New API Endpoint: `/api/programs`
✅ Returns all auto programs  

### 4. New API Endpoint: `/api/start-auto-program`
✅ Starts auto program with steps  
✅ Calculates median pressure from ranges  
✅ Stores steps in session  

### 5. Updated Frontend
✅ `ProgramSelection.tsx` - Now uses API  
✅ `Index.tsx` - Updated auto program handler  
✅ ProcessMonitor - Ready for multi-step  

## Restart Instructions

### Stop All Running Services

```powershell
# Find running processes
Get-Process python | Where-Object {$_.MainWindowTitle -like "*sensor*" -or $_.MainWindowTitle -like "*api*"}

# Stop them
Stop-Process -Id <PID> -Force
```

### Start Services in Order

#### Terminal 1: Sensor Control Service
```powershell
cd C:\Users\vemco\clave-master\backend
python sensor_control_service.py
```

#### Terminal 2: API Server
```powershell
cd C:\Users\vemco\clave-master\backend
python api_server.py
```

#### Terminal 3: Frontend
```powershell
cd C:\Users\vemco\clave-master
npm run dev
```

## Test Auto Mode

1. Navigate to UI (http://localhost:5173)
2. Click **"Auto"** mode
3. Select **"Hypalon Polymers"**
4. Click **"START PROGRAM"**
5. Watch the multi-step execution

## What's Working

✅ Program loads from database  
✅ Steps display correctly  
✅ API creates session with steps  
✅ Median pressure calculated  
✅ UI shows all 6 steps  

## What Needs Backend Update

⚠️ Currently only first step executes  
⚠️ Backend needs multi-step logic  
⚠️ Step advancement not implemented  

See `AUTO_MODE_READY.md` for backend implementation details.

