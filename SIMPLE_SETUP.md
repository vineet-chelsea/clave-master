# Simple Setup - No Database Required!

## ✅ Easiest Option: Use CSV Storage

I've created a version that stores readings in a CSV file - no database needed!

### How to Run:

```bash
cd backend
python sensor_service_no_db.py
```

### What it does:
- ✅ Reads from PLC every second
- ✅ Displays readings in console
- ✅ Saves to `sensor_readings.csv` file
- ✅ No database setup needed!

### Output File:

Readings are saved to `backend/sensor_readings.csv` with format:

```csv
timestamp,pressure,temperature
2025-10-26T12:30:45,0.0,24.8
2025-10-26T12:30:46,0.0,24.9
```

You can:
- Open in Excel
- Import to any database later
- Parse with Python/PowerShell
- Share the file

## 📊 Alternative: Postgres Setup (If You Want Database)

### Quick Install Option 1: Download

1. Go to: https://www.postgresql.org/download/windows/
2. Download and install
3. Remember the password you set

### Quick Install Option 2: Chocolatey

If you have Chocolatey installed:

```bash
choco install postgresql
```

### After Installing PostgreSQL:

1. **Create database:**
```bash
createdb -U postgres autoclave
```

2. **Create table:**
```bash
psql -U postgres -d autoclave -c "CREATE TABLE sensor_readings (id SERIAL PRIMARY KEY, timestamp TIMESTAMP DEFAULT NOW(), pressure DECIMAL(10,2), temperature DECIMAL(10,2));"
```

3. **Run service:**
```bash
cd backend
python sensor_service.py
```

## 🎯 Recommendation

**Start with the CSV version** - it's simplest and works immediately:

```bash
cd backend
python sensor_service_no_db.py
```

You can always add Postgres later if you need it!

## Current Status

✅ PLC connection works  
✅ Reading registers 69 and 70  
✅ Service ready to run  
⏳ Database: Optional (use CSV for now!)

**Just run `python sensor_service_no_db.py` and you're done!** 🎉

