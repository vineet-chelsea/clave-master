# Testing the API

## PowerShell Commands (Windows)

### Test Start Control:
```powershell
Invoke-WebRequest -Uri "http://localhost:5000/api/start-control" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"target_pressure": 20, "duration_minutes": 5}'
```

### Or using curl if installed:
```powershell
curl -X POST http://localhost:5000/api/start-control `
  -H "Content-Type: application/json" `
  -d '{\"target_pressure\": 20, \"duration_minutes\": 5}'
```

### Stop Control:
```powershell
Invoke-WebRequest -Uri "http://localhost:5000/api/stop-control" -Method POST
```

### Get Latest Sensor Reading:
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/sensor-readings/latest" -Method GET
```

### Get All Sessions:
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/sessions" -Method GET
```

## Python Test Script

Create `test_start.py`:
```python
import requests

# Start control
response = requests.post('http://localhost:5000/api/start-control', json={
    'target_pressure': 20,
    'duration_minutes': 5
})

print(response.json())
```

## Manual Browser Test

1. Open browser: http://localhost:5000/api/health
2. Should see: `{"status":"healthy","api":"service_api"}`

## Check Service is Running

Terminal where service_api.py is running should show:
```
[OK] Connected to PostgreSQL
[OK] Connected to PLC on COM10
[INFO] Service ready...
```

## When You Start Control from UI:

You should see in the terminal:
```
[OK] Started control session 123
     Target: 20.0 PSI
     Duration: 5 minutes
     Control thread started
[CONTROL] Control loop started
```

