# Fix: Container Restarting Issue

## Problems Identified

1. **Missing `requests` module** - Added to requirements.txt ✅
2. **Wrong service starting** - Docker starts sensor_control_service.py but UI needs api_server.py
3. **Need both services** - API server AND sensor service need to run together

## Fixes Applied

### 1. Added requests to requirements.txt
```txt
requests==2.31.0
```

### 2. Created start_backend.sh
Runs both services simultaneously:
- API server (handles frontend requests)
- Sensor control service (reads PLC and controls valve)

### 3. Updated Dockerfile.backend
Now runs `start_backend.sh` which starts both services

## Rebuild Commands

```bash
# Stop everything
docker compose down

# Rebuild with fixes
docker compose build --no-cache backend

# Start services
docker compose up -d

# Check logs
docker compose logs backend
```

## Expected Behavior

After rebuilding, you should see:
- ✅ Both services running in one container
- ✅ API server on port 5000
- ✅ Sensor service reading PLC
- ✅ UI can connect to backend
- ✅ Auto programs load correctly

## Verify

```bash
# Check container isn't restarting
docker compose ps

# Check logs
docker compose logs backend

# Test API
curl http://localhost:5000/api/health
```

**Container should no longer restart!** ✅

