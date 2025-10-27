# Fix 500 Errors on Raspberry Pi

## Problem
Frontend shows 500 errors:
- `GET http://localhost:5000/api/sensor-readings/latest 500`
- `GET http://localhost:5000/api/sessions 500`
- Error: `column "target_pressure" of relation "process_sessions" does not exist`

## Root Cause
The database schema on Raspberry Pi is outdated - it's missing columns like `target_pressure`, `duration_minutes`, and `steps_data`.

## Solution: Rebuild Database with Correct Schema

### Step 1: SSH into Raspberry Pi
```bash
ssh vemcon@<raspberry-pi-ip>
```

### Step 2: Pull Latest Changes
```bash
cd ~/clave-master
git pull
```

### Step 3: Stop All Containers
```bash
docker compose down
```

### Step 4: Remove Old Database Volume (to force recreation)
```bash
docker volume rm autoclave_postgres_data
```

### Step 5: Rebuild Everything
```bash
# Rebuild with latest database initialization
docker compose build --no-cache

# Start services
docker compose up -d

# Check logs
docker compose logs backend
```

### Step 6: Verify Database Tables
```bash
# Connect to database
docker exec -it autoclave-backend python

# Then in Python:
import psycopg2
conn = psycopg2.connect(
    host='postgres',
    database='autoclave',
    user='postgres',
    password='postgres'
)
cursor = conn.cursor()
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='process_sessions';")
print(cursor.fetchall())
cursor.close()
exit()
```

You should see `target_pressure`, `duration_minutes`, and `steps_data` in the output.

### Step 7: Add Auto Programs
```bash
docker exec autoclave-backend python add_auto_programs.py
```

### Step 8: Verify Everything Works
```bash
# Check API is responding
curl http://localhost:5000/api/sessions

# Should return JSON, not errors
```

## Alternative: Manual Database Fix

If you can't rebuild, manually fix the schema:

```bash
# Connect to database container
docker exec -it autoclave-db psql -U postgres -d autoclave

# Then run these SQL commands:
ALTER TABLE process_sessions ADD COLUMN IF NOT EXISTS target_pressure NUMERIC(6,2);
ALTER TABLE process_sessions ADD COLUMN IF NOT EXISTS duration_minutes INTEGER;
ALTER TABLE process_sessions ADD COLUMN IF NOT EXISTS steps_data JSONB;

# Exit PostgreSQL
\q

# Restart backend
docker compose restart backend
```

## Verify Fix

1. Check API endpoints return data:
```bash
curl http://localhost:5000/api/sensor-readings/latest
curl http://localhost:5000/api/sessions
curl http://localhost:5000/api/programs
```

2. Open frontend in browser:
```bash
# From Raspberry Pi
curl http://localhost

# From network
http://<raspberry-pi-ip>
```

Should work without 500 errors!

## Summary

The fix ensures:
- ✅ Correct database schema with all required columns
- ✅ Auto programs added to database
- ✅ Frontend and backend communicate properly
- ✅ No more 500 errors

