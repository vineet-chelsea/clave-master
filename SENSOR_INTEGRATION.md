# Sensor Integration Guide

This document explains how to integrate real Modbus PLC sensor readings with the autoclave control system.

## Overview

The system consists of three parts:
1. **Python Backend Service** - Reads from PLC and stores in Supabase
2. **Supabase Database** - Stores sensor readings in real-time
3. **React Frontend** - Displays live sensor data

## Architecture

```
PLC (Modbus) → Python Service → Supabase → React Frontend
     ↓                              ↓            ↓
  Register 69                   sensor_       Live Charts
  Register 70                  readings       Real-time
    table                     Updates
```

## Setup Instructions

### Step 1: Database Migration

Run the sensor_readings migration in your Supabase project:

1. Go to Supabase Dashboard → SQL Editor
2. Run the migration file: `supabase/migrations/20250930171000_create_sensor_readings.sql`
3. Verify the table exists with these columns:
   - `id` (UUID)
   - `timestamp` (Timestamp)
   - `pressure` (Decimal)
   - `temperature` (Decimal)

### Step 2: Python Backend Setup

Navigate to the backend directory:

```bash
cd backend
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure environment:

1. Copy `env_template.txt` to `.env`
2. Edit `.env` with your credentials:

```env
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=eyJxxxxx
COM_PORT=COM10
BAUD_RATE=9600
SLAVE_ID=1
```

### Step 3: Configure PLC Register Addresses

Edit `backend/sensor_service.py` to match your PLC:

```python
# Current configuration:
PRESSURE_REGISTER = 70      # Address 70 (0-4095 → 0-87 PSI)
TEMPERATURE_REGISTER = 69   # Address 69 (0-4095 → 0-350°C)
```

To change scaling:

```python
# For example, if pressure ranges from 0-100 PSI:
PRESSURE_OUTPUT_MIN = 0
PRESSURE_OUTPUT_MAX = 100  # Change this

# For temperature in Fahrenheit (0-500°F):
TEMPERATURE_OUTPUT_MIN = 0
TEMPERATURE_OUTPUT_MAX = 500  # Change this
```

### Step 4: Start the Sensor Service

**Windows:**
```bash
python sensor_service.py
```

**Linux/Mac:**
```bash
python3 sensor_service.py
```

You should see output like:
```
============================================================
Starting Continuous Sensor Reading Service
============================================================
Reading interval: 1 seconds
Pressure register: 70 (0-4095 → 0-87 PSI)
Temperature register: 69 (0-4095 → 0-350°C)
============================================================

✓ Connected to PLC on COM10
[12:30:45] Reading #1 - Pressure: 15.3 PSI, Temperature: 25.8°C ✓
[12:30:46] Reading #2 - Pressure: 15.4 PSI, Temperature: 26.1°C ✓
...
```

### Step 5: Verify Frontend Integration

The frontend automatically syncs with sensor readings:

1. **Index Page** - Shows latest pressure/temperature on mode selection
2. **Program Selection** - Displays current readings
3. **Manual Control** - Shows live sensor values
4. **Process Monitor** - Real-time charts and displays

No code changes needed - it uses Supabase realtime subscriptions!

## How It Works

### Python Service Flow

1. Connects to Modbus PLC on specified COM port
2. Every second (configurable):
   - Reads register 70 → scales to 0-87 PSI
   - Reads register 69 → scales to 0-350°C
   - Inserts reading into Supabase
3. Frontend receives updates via Supabase realtime

### Frontend Flow

1. Component subscribes to `sensor_readings` table
2. On new INSERT:
   - Updates pressure state
   - Updates temperature state
   - Adds to chart data (if monitoring)
3. UI updates automatically - no refresh needed

### Example: Reading Address 70

```python
# PLC returns raw value: 2048 (out of 4095)
# Scaling formula: 0 + (2048 - 0) * (87 - 0) / (4095 - 0)
# Result: 43.5 PSI
```

## Customization

### Change Reading Frequency

```python
# In sensor_service.py
READ_INTERVAL = 2  # Read every 2 seconds instead of 1
```

### Add More Sensors

1. Add register address:
```python
MOTOR_SPEED_REGISTER = 71
```

2. Add read function:
```python
def read_motor_speed(self):
    result = self.plc_client.read_input_registers(
        MOTOR_SPEED_REGISTER, count=1, device_id=self.slave_id
    )
    if not result.isError():
        return result.registers[0]
    return None
```

3. Update database schema:
```sql
ALTER TABLE sensor_readings ADD COLUMN motor_speed INTEGER;
```

4. Update Supabase types in `src/integrations/supabase/types.ts`

5. Add to save function:
```python
self.supabase.table('sensor_readings').insert({
    'pressure': pressure,
    'temperature': temperature,
    'motor_speed': motor_speed  # Add this
}).execute()
```

## Troubleshooting

### "Cannot connect to PLC"

**Symptoms:** `Failed to connect to PLC on COM10`

**Solutions:**
- Check COM port in Device Manager (Windows)
- Verify baud rate matches PLC settings
- Ensure no other program is using the port
- Check cable connection

### "Readings stuck at 0"

**Symptoms:** All readings show 0.0

**Solutions:**
- Verify register addresses are correct
- Check that sensors are powered
- Review PLC Modbus configuration
- Look for communication errors in logs

### "Failed to initialize Supabase"

**Symptoms:** `Failed to initialize Supabase`

**Solutions:**
- Verify credentials in `.env` file
- Check internet connection
- Ensure Supabase project is active
- Test connection manually with Supabase CLI

### "Frontend not updating"

**Symptoms:** Readings don't change in browser

**Solutions:**
- Verify `sensor_readings` table exists
- Check RLS policies allow SELECT
- Enable realtime for the table
- Check browser console for errors

### "Temperature in wrong units"

**Symptoms:** Temperature seems incorrect

**Solutions:**
- Check if PLC uses Celsius or Fahrenheit
- Adjust scaling factors accordingly
- Verify maximum temperature range

## Production Deployment

### Windows Service

Use NSSM (Non-Sucking Service Manager):

```bash
nssm install SensorService python
nssm set SensorService AppDirectory C:\Users\vemco\clave-master\backend
nssm set SensorService AppParameters sensor_service.py
nssm start SensorService
```

### Linux systemd

Create `/etc/systemd/system/sensor-service.service`:

```ini
[Unit]
Description=Modbus Sensor Service
After=network.target

[Service]
Type=simple
User=autoclave
WorkingDirectory=/opt/clave-master/backend
ExecStart=/usr/bin/python3 sensor_service.py
Restart=always
Environment="VITE_SUPABASE_URL=xxx"
Environment="VITE_SUPABASE_PUBLISHABLE_KEY=xxx"

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable sensor-service
sudo systemctl start sensor-service
sudo systemctl status sensor-service
```

## Monitoring

### Check Service Status

```bash
# Windows - Check if process is running
tasklist | findstr python

# Linux
ps aux | grep sensor_service
systemctl status sensor-service
```

### View Recent Readings

Query Supabase directly:

```sql
SELECT * FROM sensor_readings 
ORDER BY timestamp DESC 
LIMIT 10;
```

### Check Connection Quality

The Python service logs connection status. Monitor for:
- `✓ Connected to PLC` - Connection successful
- `Error reading pressure` - Communication issues
- Exception messages - Detailed error information

## Support

For issues:
1. Check service logs for errors
2. Verify PLC communication with Modbus scanner
3. Test Supabase connection manually
4. Review browser console for frontend errors

