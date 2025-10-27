# Quick Start Guide - Sensor Integration

## 🎯 What Was Added

I've integrated your Modbus PLC sensor readings with the autoclave control system. Here's what's new:

### New Files Created:
- ✅ `backend/sensor_service.py` - Python service to read from PLC
- ✅ `backend/requirements.txt` - Python dependencies
- ✅ `backend/run_sensor_service.bat` - Windows launcher
- ✅ `backend/SETUP.md` - Detailed setup instructions
- ✅ `backend/env_template.txt` - Environment template
- ✅ `SENSOR_INTEGRATION.md` - Complete integration guide

### Files Modified:
- ✅ `supabase/migrations/20250930171000_create_sensor_readings.sql` - Created sensor readings table
- ✅ `src/integrations/supabase/types.ts` - Added sensor_readings types
- ✅ `src/components/ProcessMonitor.tsx` - Now uses real sensor readings
- ✅ `.gitignore` - Added backend exclusions

## 🚀 Quick Setup (3 Steps)

### Step 1: Database Migration (One-Time)

1. Open your Supabase project
2. Go to SQL Editor
3. Run this SQL to create the sensor_readings table:

```sql
-- Create table for realtime sensor readings
CREATE TABLE public.sensor_readings (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  pressure DECIMAL(10, 2) NOT NULL,
  temperature DECIMAL(10, 2) NOT NULL
);

ALTER TABLE public.sensor_readings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view sensor readings" ON public.sensor_readings FOR SELECT USING (true);
CREATE POLICY "Anyone can insert sensor readings" ON public.sensor_readings FOR INSERT WITH CHECK (true);

CREATE INDEX idx_sensor_readings_timestamp ON public.sensor_readings(timestamp DESC);

ALTER PUBLICATION supabase_realtime ADD TABLE public.sensor_readings;
```

### Step 2: Python Backend Setup

Open a terminal in the `backend` folder:

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Create .env file (copy from template)
copy env_template.txt .env

# Edit .env with your Supabase credentials
```

Edit `.env` file:
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=your-anon-key
COM_PORT=COM10
BAUD_RATE=9600
SLAVE_ID=1
```

### Step 3: Start the Service

```bash
python sensor_service.py
```

You should see:
```
✓ Connected to Supabase
✓ Connected to PLC on COM10
[12:30:45] Reading #1 - Pressure: 15.3 PSI, Temperature: 25.8°C ✓
```

## 📊 How It Works

### Sensor Reading Flow:

```
PLC (COM10)
  ↓ Modbus
  Address 70 → Pressure (0-4095 → 0-87 PSI)
  Address 69 → Temperature (0-4095 → 0-350°C)
  ↓ Python Service (reads every 1 second)
  ↓ Supabase
  sensor_readings table
  ↓ Realtime Subscription
  ↓ Frontend
  Live Display (updates automatically)
```

### Frontend Updates:

- **Mode Selection Screen** - Shows current pressure & temperature
- **Program Selection** - Displays live readings
- **Manual Control** - Real-time sensor values
- **Process Monitor** - Live charts with actual data

No refresh needed - updates happen automatically every second!

## 🔧 Configuration

### Change Reading Speed

Edit `backend/sensor_service.py`:
```python
READ_INTERVAL = 2  # Change from 1 to 2 seconds
```

### Change Register Addresses

If your PLC uses different addresses:
```python
PRESSURE_REGISTER = 70      # Change if different
TEMPERATURE_REGISTER = 69   # Change if different
```

### Change Scaling

If sensors have different ranges:
```python
# For pressure (current: 0-87 PSI)
PRESSURE_OUTPUT_MAX = 87  # Change to your max PSI

# For temperature (current: 0-350°C)
TEMPERATURE_OUTPUT_MAX = 350  # Change to your max temp
```

## ✅ Testing

### Test 1: PLC Connection
```bash
python sensor_service.py
# Should see: "✓ Connected to PLC on COM10"
```

### Test 2: Database Connection
# Should see: "✓ Connected to Supabase"
# Should see: "Reading #1 - Pressure: XX PSI, Temperature: XX°C ✓"
```

### Test 3: Frontend
1. Start frontend: `npm run dev`
2. Open browser to `http://localhost:8080`
3. Check Mode Selection screen - should show live readings
4. Readings should update every second

## 🐛 Troubleshooting

### "Failed to connect to PLC"

- **Check COM port**: Look in Device Manager (Windows)
- **Verify cable**: Ensure PLC is connected
- **Check settings**: Baud rate, slave ID must match PLC

### "Failed to initialize Supabase"

- **Check .env**: Verify credentials are correct
- **Test connection**: Visit Supabase dashboard
- **Check network**: Ensure internet is working

### "Frontend shows 0 PSI"

- **Verify Python service**: Check if it's running
- **Check database**: Query `sensor_readings` table
- **Check logs**: Look for errors in console
- **Verify subscription**: Check browser console for realtime errors

### "Readings not updating"

- **Check Python service logs**: Look for errors
- **Verify migration ran**: Table should exist
- **Check RLS policies**: Should allow SELECT
- **Enable realtime**: Table must be in publication

## 📝 What Changed in Frontend

### ProcessMonitor Component

**Before:** Simulated pressure/temperature values
```typescript
setCurrentPressure((prev) => prev + (diff * 0.05)); // Simulated
```

**After:** Real sensor readings from Supabase
```typescript
// Subscribes to sensor_readings table
// Updates automatically when new reading arrives
setCurrentPressure(payload.new.pressure); // Real
```

### Index Component

Already had sensor subscription - no changes needed!

## 🎉 Success Indicators

You'll know it's working when:

1. ✅ Python service shows readings every second
2. ✅ Frontend displays current pressure/temperature
3. ✅ Values change when pressure/temperature actually changes
4. ✅ Charts update in real-time during process monitoring
5. ✅ No errors in browser console

## 📚 Next Steps

1. **Verify Integration**: Watch readings update in real-time
2. **Customize**: Adjust scaling if needed
3. **Monitor**: Check Supabase for historical data
4. **Deploy**: Set up as Windows service for production

For detailed information, see `SENSOR_INTEGRATION.md`.

