# ✅ Sensor Service Ready to Start!

## Database Setup Complete! ✅

- ✅ PostgreSQL connected
- ✅ Database `autoclave` created
- ✅ Table `sensor_readings` created
- ✅ Index created for performance

## Start the Service Now!

```bash
cd backend
python sensor_service.py
```

## Expected Output:

```
============================================================
Starting Continuous Sensor Reading Service
============================================================
Reading interval: 1 seconds
Pressure register: 70 (0-4095 → 0-87 PSI)
Temperature register: 69 (0-4095 → 0-350°C)
============================================================

[OK] Connected to PostgreSQL
[OK] Connected to PLC on COM10
[12:30:45] Reading #1 - Pressure: 0.0 PSI, Temperature: 24.8°C [OK]
[12:30:46] Reading #2 - Pressure: 0.0 PSI, Temperature: 24.9°C [OK]
```

## What's Happening:

1. **Connects to PostgreSQL** - stores readings
2. **Connects to PLC** on COM10
3. **Reads every second:**
   - Register 69 → Temperature (currently showing 334 raw value)
   - Register 70 → Pressure (currently 0)
4. **Saves to database** automatically
5. **Displays in console** with timestamps

## View Stored Readings:

```bash
psql -U postgres -h 127.0.0.1 -p 5432 -d autoclave -c "SELECT * FROM sensor_readings ORDER BY timestamp DESC LIMIT 10;"
```

## Alternative: CSV Version (No Database)

If you prefer simple CSV storage:

```bash
cd backend
python sensor_service_no_db.py
```

This saves to `sensor_readings.csv` - no database needed!

## Configuration

Current settings in `backend/.env`:

```env
PG_HOST=127.0.0.1
PG_PORT=5432
PG_DATABASE=autoclave
PG_USER=postgres
PG_PASSWORD=postgres  # Change if needed

COM_PORT=COM10
BAUD_RATE=9600
SLAVE_ID=1
```

## That's It!

Just run: `python sensor_service.py` and your sensors will be read and stored every second! 🎉

