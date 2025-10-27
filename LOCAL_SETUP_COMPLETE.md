# ✅ Local Setup Complete!

## All Issues Fixed! 🎉

### What Was Fixed:
1. ✅ Python dependencies installed for Python 3.13
2. ✅ .env file loading configured (using python-dotenv)
3. ✅ Unicode characters replaced with ASCII for Windows console
4. ✅ Environment variables loading correctly

### Current Configuration:
```env
VITE_SUPABASE_URL=http://127.0.0.1:54321
VITE_SUPABASE_PUBLISHABLE_KEY=eyJ... (supabase demo key)
COM_PORT=COM10
BAUD_RATE=9600
SLAVE_ID=1
```

## 🚀 How to Run

### Start the Sensor Service:

```bash
cd backend
python sensor_service.py
```

**Expected Output:**
```
[OK] Connected to Supabase
[ERROR] Failed to connect to PLC on COM10
```

**Note:** The "[ERROR]" message is normal if:
- Your PLC is not connected yet, OR
- The COM port is different (not COM10), OR
- Your PLC is not powered on

### What the Service Will Do:

1. ✅ Connect to Supabase (localhost)
2. ❌ Try to connect to PLC (will fail if not connected)
3. ⏸️ Wait for PLC connection

Once you connect your PLC:
- ✅ Will read Register 70 every second → Pressure (0-87 PSI)
- ✅ Will read Register 69 every second → Temperature (0-350°C)
- ✅ Will save to Supabase automatically
- ✅ Frontend will update every second

## ⚙️ Next Steps

### 1. Connect Your PLC
- Connect to COM10 (or change in `.env` to correct port)
- Ensure PLC is powered on
- Verify baud rate is 9600

### 2. Run Database Migration
Run this SQL in Supabase SQL Editor:

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

### 3. Change COM Port if Needed

If your PLC is on a different COM port (e.g., COM3, COM4):

**Option A:** Edit `backend/.env`:
```env
COM_PORT=COM3  # Change to your port
```

**Option B:** Set environment variable:
```bash
$env:COM_PORT="COM3"
python sensor_service.py
```

### 4. Start the Frontend

In another terminal:
```bash
npm run dev
```

Open browser to: http://localhost:8080

## 📊 When Everything is Connected:

You'll see output like this:
```
============================================================
Starting Continuous Sensor Reading Service
============================================================
Reading interval: 1 seconds
Pressure register: 70 (0-4095 → 0-87 PSI)
Temperature register: 69 (0-4095 → 0-350°C)
============================================================

[OK] Connected to Supabase
[OK] Connected to PLC on COM10
[12:30:45] Reading #1 - Pressure: 15.3 PSI, Temperature: 25.8°C [OK]
[12:30:46] Reading #2 - Pressure: 15.4 PSI, Temperature: 26.1°C [OK]
[12:30:47] Reading #3 - Pressure: 15.5 PSI, Temperature: 26.3°C [OK]
...
```

## 🎯 Success Indicators

✅ **Service Running:**
- "[OK] Connected to Supabase" message
- Service continues running (doesn't exit)

✅ **PLC Connected:**
- "[OK] Connected to PLC" message
- Readings appear every second

✅ **Frontend:**
- Shows current pressure and temperature
- Updates automatically every second
- Charts update in real-time

## 🔧 Troubleshooting

### "Failed to connect to PLC"
**Solutions:**
- Check cable is connected
- Verify COM port in Device Manager
- Update `.env` if wrong port
- Ensure PLC is powered on
- Check baud rate matches (9600)

### "Failed to connect to Supabase"
**Solutions:**
- Ensure Supabase is running locally
- Check URL in `.env` file
- Verify Supabase is accessible at http://127.0.0.1:54321

### "Frontend shows 0 PSI"
**Solutions:**
- Make sure sensor service is running
- Check database migration was applied
- Verify Python service is reading successfully

## 📚 Files to Reference

- `SENSOR_INTEGRATION.md` - Complete integration guide
- `QUICK_START.md` - Quick start instructions
- `MIGRATION_STEPS.md` - Database setup
- `backend/README.md` - Backend documentation

## ✨ You're All Set!

The system is ready. Just:
1. Connect your PLC
2. Run the database migration
3. Start the service
4. Start the frontend
5. Watch it work! 🎉

