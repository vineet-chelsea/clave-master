# Sensor Reading Service

This service continuously reads pressure and temperature from a Modbus PLC and stores the readings in Supabase for real-time monitoring in the frontend.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your settings:
- `VITE_SUPABASE_URL`: Your Supabase project URL
- `VITE_SUPABASE_PUBLISHABLE_KEY`: Your Supabase anon/public key
- `COM_PORT`: Modbus COM port (default: COM10)
- `BAUD_RATE`: Baud rate (default: 9600)
- `SLAVE_ID`: Modbus slave ID (default: 1)

### 3. Configure Sensor Register Addresses

The default configuration in `sensor_service.py`:
- **Pressure**: Register 70 (0-4095 raw → 0-87 PSI)
- **Temperature**: Register 69 (0-4095 raw → 0-350°C)

To modify:
- Edit the `PRESSURE_REGISTER` and `TEMPERATURE_REGISTER` constants
- Adjust scaling factors as needed

## Running the Service

### Windows

```bash
# Run directly
python sensor_service.py

# Or use the batch script
run_sensor_service.bat
```

### Linux/Mac

```bash
python sensor_service.py
```

The service will:
1. Connect to the Modbus PLC
2. Read sensor values every second (configurable via `READ_INTERVAL`)
3. Scale the raw values to real units (PSI and °C)
4. Store readings in Supabase `sensor_readings` table
5. Log all readings to console

## Integration with Frontend

The frontend automatically syncs with these readings via Supabase realtime:
- Latest readings appear on Mode Selection and Manual Control screens
- Data updates in real-time every second
- No manual refresh needed

## Troubleshooting

### Connection Issues
- Check COM port is correct and not in use by another program
- Verify baud rate matches PLC settings
- Check Modbus slave ID

### Supabase Issues
- Verify credentials in `.env` file
- Check that `sensor_readings` table exists (run migration)
- Ensure RLS policies allow inserts

### Reading Errors
- Verify register addresses are correct for your PLC
- Check scaling factors match your sensor specifications
- Monitor console output for specific error messages

