# Sensor Service Setup Instructions

## Quick Start

### 1. Install Python Dependencies

Open a terminal in the `backend` directory and run:

```bash
pip install -r requirements.txt
```

This installs:
- `pymodbus` - For Modbus communication
- `supabase` - For database storage
- `python-dotenv` - For environment variables

### 2. Configure Environment Variables

Create a `.env` file in the `backend` directory with the following content:

```env
# Supabase Configuration
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=your-supabase-anon-key

# Modbus Configuration
COM_PORT=COM10
BAUD_RATE=9600
SLAVE_ID=1
```

**To get your Supabase credentials:**
1. Go to your Supabase project dashboard
2. Navigate to Settings → API
3. Copy the "Project URL" for `VITE_SUPABASE_URL`
4. Copy the "anon public" key for `VITE_SUPABASE_PUBLISHABLE_KEY`

### 3. Run the Database Migration

Make sure the `sensor_readings` table exists in your Supabase database. If you haven't run the migration yet:

1. Go to your Supabase project
2. Navigate to SQL Editor
3. Run the migration file: `supabase/migrations/20250930171000_create_sensor_readings.sql`

### 4. Start the Sensor Service

#### Windows:
```bash
python sensor_service.py
```

Or use the batch script:
```bash
run_sensor_service.bat
```

#### Linux/Mac:
```bash
python3 sensor_service.py
```

## How It Works

The service:
1. **Connects to PLC** via Modbus RTU on the specified COM port
2. **Reads every second:**
   - Register 70 → Pressure (scaled 0-4095 → 0-87 PSI)
   - Register 69 → Temperature (scaled 0-4095 → 0-350°C)
3. **Stores readings** in Supabase `sensor_readings` table
4. **Frontend syncs** automatically via Supabase realtime subscriptions

## Customization

### Change Reading Frequency

Edit `READ_INTERVAL` in `sensor_service.py`:
```python
READ_INTERVAL = 2  # Read every 2 seconds instead of 1
```

### Change Register Addresses

Edit these constants in `sensor_service.py`:
```python
PRESSURE_REGISTER = 70  # Change this to your PLC address
TEMPERATURE_REGISTER = 69  # Change this to your PLC address
```

### Adjust Scaling

If your sensors use different ranges, modify the scaling factors:
```python
# Current: 0-4095 → 0-87 PSI
PRESSURE_MIN = 0
PRESSURE_MAX = 4095
PRESSURE_OUTPUT_MIN = 0
PRESSURE_OUTPUT_MAX = 87  # Change max PSI here
```

## Troubleshooting

### "Failed to connect to PLC"
- Check COM port is correct (Device Manager on Windows)
- Ensure no other program is using the COM port
- Verify baud rate matches PLC settings
- Check cable connection

### "Failed to initialize Supabase"
- Verify credentials in `.env` file
- Check internet connection
- Ensure Supabase project is active

### "Exception reading sensors"
- Verify register addresses are correct
- Check that sensors are powered and connected
- Look for Modbus communication errors in PLC logs

### Readings stuck at 0 or not updating
- Check that the migration created the `sensor_readings` table
- Verify RLS policies allow inserts
- Check console for specific error messages

## Running as a Background Service

### Windows (using Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., "When I log on")
4. Action: Start a program
5. Program: `python`
6. Arguments: `C:\Users\vemco\clave-master\backend\sensor_service.py`
7. Start in: `C:\Users\vemco\clave-master\backend`

### Linux (using systemd)
Create `/etc/systemd/system/sensor-service.service`:
```ini
[Unit]
Description=Modbus Sensor Reading Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/clave-master/backend
ExecStart=/usr/bin/python3 sensor_service.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then enable and start:
```bash
sudo systemctl enable sensor-service
sudo systemctl start sensor-service
```

