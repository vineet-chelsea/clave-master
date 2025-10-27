# How to Apply Database Migration

## Quick Guide

The sensor readings need a database table to store data. Here's how to create it.

## Option 1: Using Local Supabase (Recommended)

If you're using local Supabase:

### Step 1: Start Supabase
```bash
# If using Supabase CLI
supabase start

# Or use Docker
docker-compose up -d
```

### Step 2: Open Supabase Dashboard
Go to: http://127.0.0.1:54323

### Step 3: Run SQL Migration
1. Click **SQL Editor**
2. Paste this SQL:

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

## Option 2: Using Cloud Supabase

If you're using cloud Supabase (app.supabase.com):

1. Go to your Supabase project
2. Navigate to **SQL Editor**
3. Paste the SQL from above
4. Click **Run** ✅

### Update Configuration
Make sure `backend/.env` has your cloud credentials:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=your-anon-key
```

## Option 3: Test Without Database First

You can test the PLC connection without Supabase:

```bash
cd backend
python sensor_service_standalone.py
```

This standalone version will:
- ✅ Connect to PLC
- ✅ Read sensors every second
- ✅ Display readings in console
- ❌ Does NOT save to database (for testing only)

## Verification

After applying the migration, the frontend will automatically:
1. ✅ Connect to sensor_readings table
2. ✅ Display latest readings
3. ✅ Update every second automatically

## Need Help?

- See `SENSOR_INTEGRATION.md` for full documentation
- See `LOCAL_SETUP_COMPLETE.md` for troubleshooting

