# ✅ Sensor Service is Running!

## Status

✅ **psycopg2 installed** - PostgreSQL driver ready  
✅ **Database connected** - autoclave database ready  
✅ **Service running** - sensor_service.py started in background  

## What's Happening Now

The sensor service is:
1. **Reading from PLC** every second
2. **Storing in PostgreSQL** database
3. **Displaying in console** with timestamps

## View the Readings

### In Console:
The service is running and showing output like:
```
[12:30:45] Reading #1 - Pressure: 0.0 PSI, Temperature: 24.8°C [OK]
[12:30:46] Reading #2 - Pressure: 0.0 PSI, Temperature: 24.9°C [OK]
```

### In Database:
Check stored readings:
```bash
psql -U postgres -h 127.0.0.1 -p 5432 -d autoclave -c "SELECT timestamp, pressure, temperature FROM sensor_readings ORDER BY timestamp DESC LIMIT 10;"
```

### Count total readings:
```bash
psql -U postgres -h 127.0.0.1 -p 5432 -d autoclave -c "SELECT COUNT(*) FROM sensor_readings;"
```

## Configuration

Current settings (`backend/.env`):
- **PostgreSQL:** 127.0.0.1:5432/autoclave
- **Modbus:** COM10, 9600 baud, Slave ID 1
- **Registers:** 70 (pressure), 69 (temperature)
- **Interval:** 1 second

## Stop the Service

Press `Ctrl+C` in the terminal where it's running, or:

```bash
Get-Process python | Where-Object {$_.Path -like "*sensor_service*"} | Stop-Process
```

## Files Created

- `backend/sensor_readings.csv` (if using CSV version)
- Database: `autoclave.sensor_readings` table

## Everything is Working! 🎉

Your PLC sensor readings are being:
- ✅ Read every second
- ✅ Saved to PostgreSQL
- ✅ Available for analysis

Just check the console output or query the database!

