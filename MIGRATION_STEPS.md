# Database Migration Steps

## ✅ Completed Setup

All files have been created and dependencies installed. Here's what's done:

### 1. ✅ Python Backend Service
- **Created:** `backend/sensor_service.py` - Reads Modbus PLC every 1 second
- **Created:** `backend/.env` - Configured with local Supabase settings
- **Installed:** All Python dependencies (pymodbus, supabase, python-dotenv)
- **Status:** Ready to run

### 2. ✅ Frontend Integration
- **Updated:** `src/components/ProcessMonitor.tsx` - Now subscribes to real sensor readings
- **Updated:** `src/integrations/supabase/types.ts` - Added sensor_readings table types
- **Status:** Will automatically sync with sensor readings

### 3. ✅ Configuration
- **Created:** `backend/.env` with default settings:
  - Modbus: COM10, 9600 baud, Slave ID 1
  - Supabase: Local instance (http://127.0.0.1:54321)
- **Status:** Configured

## 🔨 Remaining Step: Database Migration

You need to run the database migration to create the `sensor_readings` table.

### Option 1: Using Supabase Dashboard (Recommended)

1. **Go to your Supabase project**
   - If using local Supabase: http://127.0.0.1:54323
   - If using cloud: https://app.supabase.com → Your Project

2. **Navigate to SQL Editor**

3. **Run this SQL:**
   ```sql
   -- Create table for realtime sensor readings
   CREATE TABLE public.sensor_readings (
     id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
     timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
     pressure DECIMAL(10, 2) NOT NULL,
     temperature DECIMAL(10, 2) NOT NULL
   );

   -- Enable Row Level Security
   ALTER TABLE public.sensor_readings ENABLE ROW LEVEL SECURITY;

   -- Create policies for public access
   CREATE POLICY "Anyone can view sensor readings" 
     ON public.sensor_readings FOR SELECT USING (true);
   
   CREATE POLICY "Anyone can insert sensor readings" 
     ON public.sensor_readings FOR INSERT WITH CHECK (true);

   -- Create index for performance
   CREATE INDEX idx_sensor_readings_timestamp 
     ON public.sensor_readings(timestamp DESC);

   -- Enable realtime for sensor readings
   ALTER PUBLICATION supabase_realtime ADD TABLE public.sensor_readings;
   ```

### Option 2: Using Supabase CLI

If you have Supabase CLI installed:

```bash
# Apply the migration
supabase db push supabase/migrations/20250930171000_create_sensor_readings.sql
```

## 🚀 Testing the Integration

### Step 1: Start the Sensor Service

Open a terminal in the `backend` folder:

```bash
cd backend
python sensor_service.py
```

**Expected output:**
```
✓ Connected to Supabase
✓ Connected to PLC on COM10
[12:30:45] Reading #1 - Pressure: 15.3 PSI, Temperature: 25.8°C ✓
```

### Step 2: Start the Frontend

Open another terminal in the project root:

```bash
npm run dev
```

**Expected:** The application starts on http://localhost:8080

### Step 3: Verify Integration

1. **Open the app** in your browser
2. **Check the Mode Selection screen** - Should show current pressure and temperature
3. **Values should update every second** as the Python service reads from PLC

## 🐛 Troubleshooting

### "Failed to connect to PLC"
- Check if COM10 exists (Device Manager)
- Verify baud rate (9600) matches PLC
- Check cable connection
- Try a different COM port if needed

### "Failed to initialize Supabase"
- Ensure Supabase is running
- For local: Start with `supabase start`
- Check that credentials in `.env` are correct

### "Table sensor_readings does not exist"
- Run the SQL migration (see above)
- Verify the table exists in Supabase dashboard → Table Editor

### Frontend shows 0 PSI
- Make sure Python service is running
- Check Python service logs for errors
- Verify database migration was applied

## 📋 Current Configuration

### Modbus Settings
- **COM Port:** COM10
- **Baud Rate:** 9600
- **Slave ID:** 1
- **Pressure Register:** 70 (0-4095 → 0-87 PSI)
- **Temperature Register:** 69 (0-4095 → 0-350°C)
- **Reading Frequency:** 1 second

### Supabase Settings
- **URL:** http://127.0.0.1:54321 (local)
- **Database:** PostgreSQL
- **Realtime:** Enabled for sensor_readings table

## ✨ What Happens Next

Once everything is running:

1. **Python service** reads PLC every second
2. **Scales values** from 0-4095 to actual units (PSI, °C)
3. **Saves to database** → sensor_readings table
4. **Frontend receives** updates via Supabase realtime subscription
5. **UI updates** automatically every second - no refresh needed!

The whole process is automated and real-time. 🎉

