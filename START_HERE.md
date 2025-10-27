# 🚀 Start Here - Sensor Integration Complete!

## ✅ What I've Done For You

I've set up everything needed to integrate real Modbus PLC sensor readings with your autoclave control system.

### Completed Setup ✅

1. **✅ Created Python Backend Service**
   - `backend/sensor_service.py` - Reads from PLC every 1 second
   - Reads address 70 → Pressure (0-87 PSI)
   - Reads address 69 → Temperature (0-350°C)
   - Saves to Supabase automatically

2. **✅ Installed All Dependencies**
   - pymodbus, supabase, python-dotenv
   - Ready to run immediately

3. **✅ Created Configuration**
   - `backend/.env` - Pre-configured with settings
   - Modbus: COM10, 9600 baud, Slave ID 1
   - Supabase: Local instance configured

4. **✅ Updated Frontend**
   - Modified `ProcessMonitor.tsx` to use real sensor readings
   - Updated Supabase types to include sensor_readings table
   - Frontend will automatically update every second

5. **✅ Created Documentation**
   - `SENSOR_INTEGRATION.md` - Complete guide
   - `QUICK_START.md` - Quick reference
   - `MIGRATION_STEPS.md` - Database setup
   - `SETUP_COMPLETE.md` - This summary

## 🎯 What You Need to Do

### ONE Simple Step: Database Migration

Run this SQL in your Supabase dashboard:

1. Go to **Supabase Dashboard** → **SQL Editor**
2. Paste and run this:

```sql
CREATE TABLE public.sensor_readings (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  pressure DECIMAL(10, 2) NOT NULL,
  temperature DECIMAL(10, 2) NOT NULL
);

ALTER TABLE public.sensor_readings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view sensor readings" 
  ON public.sensor_readings FOR SELECT USING (true);

CREATE POLICY "Anyone can insert sensor readings" 
  ON public.sensor_readings FOR INSERT WITH CHECK (true);

CREATE INDEX idx_sensor_readings_timestamp 
  ON public.sensor_readings(timestamp DESC);

ALTER PUBLICATION supabase_realtime ADD TABLE public.sensor_readings;
```

3. Click **Run** ✅

That's it! Just one SQL query.

## 🚀 Start the System

### Terminal 1: Python Sensor Service
```bash
cd backend
python sensor_service.py
```

Expected output:
```
✓ Connected to Supabase
✓ Connected to PLC on COM10
[12:30:45] Reading #1 - Pressure: 15.3 PSI, Temperature: 25.8°C ✓
```

### Terminal 2: Frontend App
```bash
npm run dev
```

Expected output:
```
VITE v5.4.19  ready in 431 ms
➜  Local:   http://localhost:8080/
```

### Browser
Open http://localhost:8080 and see your live sensor readings! 🎉

## 📊 How It Works

```
┌─────────────┐
│   PLC       │ COM10
│  (Modbus)   │ ────┐
└─────────────┘     │
                    │
              Register 70 → Pressure (0-87 PSI)
              Register 69 → Temperature (0-350°C)
                    │
         ┌──────────┴──────────┐
         │                     │
         v                     v
  Python Service        Supabase
  (reads every         (stores &)
  1 second)             broadcasts)
         │                     │
         └──────────┬──────────┘
                    v
              React Frontend
              (updates every
               second auto)
```

## ⚙️ Configuration

Everything is pre-configured, but you can adjust:

### Change COM Port
Edit `backend/.env`:
```env
COM_PORT=COM10  # Change to COM3, COM4, etc.
```

### Change Register Addresses
Edit `backend/sensor_service.py`:
```python
PRESSURE_REGISTER = 70      # Change if different
TEMPERATURE_REGISTER = 69   # Change if different
```

### Change Scaling
```python
# In sensor_service.py
PRESSURE_OUTPUT_MAX = 87        # Max PSI
TEMPERATURE_OUTPUT_MAX = 350    # Max temperature
```

## 🎉 Success Indicators

You'll know it's working when:

1. ✅ Python service shows readings every second
2. ✅ Frontend displays current pressure/temperature
3. ✅ Values update in real-time (no refresh needed)
4. ✅ Charts update during process monitoring

## 📚 Documentation

For more details:
- **Quick Start:** `QUICK_START.md`
- **Full Guide:** `SENSOR_INTEGRATION.md`
- **Database:** `MIGRATION_STEPS.md`

## ⚠️ Troubleshooting

### "Failed to connect to PLC"
- Check if COM10 exists in Device Manager
- Try different COM port if needed
- Verify cable is connected

### "Failed to initialize Supabase"
- Make sure Supabase is running
- Check that database migration was run

### Frontend shows 0 PSI
- Ensure Python service is running
- Check Python logs for errors
- Verify database migration completed

## ✨ That's All!

You're ready to go. Just run the SQL migration and start the services!

The system will:
- ✅ Read from your PLC every second
- ✅ Save to database automatically
- ✅ Update frontend in real-time
- ✅ Show live charts and displays

Enjoy your fully integrated sensor monitoring system! 🎊

