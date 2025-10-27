# Supabase Setup Options

Your PLC readings are working! ✅ But you're getting a Supabase connection error.

## Quick Fix Options

### Option 1: Run Without Supabase (Easiest)

The service is now updated to work WITHOUT Supabase. It will:
- ✅ Read from PLC every second
- ✅ Display readings in console
- ❌ Will NOT save to database (but that's OK for testing!)

**Just run:**
```bash
cd backend
python sensor_service.py
```

You'll see readings like:
```
[12:30:45] Reading #1 - Pressure: 0.0 PSI, Temperature: 24.8°C [OK]
[12:30:46] Reading #2 - Pressure: 0.0 PSI, Temperature: 24.9°C [OK]
```

### Option 2: Set Up Local Supabase

If you want to save readings to database:

**Step 1: Install Supabase CLI**
```bash
npm install -g supabase
```

**Step 2: Initialize Supabase**
```bash
cd C:\Users\vemco\clave-master
supabase init
```

**Step 3: Start Supabase**
```bash
supabase start
```

This will:
- Start local database
- Show you the connection details
- Make it available at http://127.0.0.1:54321

**Step 4: Run Database Migration**

See `MIGRATION_STEPS.md` or run the SQL in Supabase Studio:
http://127.0.0.1:54323 (SQL Editor)

### Option 3: Use Cloud Supabase (Free)

1. Go to https://app.supabase.com
2. Create a free project
3. Get your credentials:
   - Project URL
   - Anon key
4. Update `backend/.env`:
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=your-anon-key
```
5. Run the migration (see `APPLY_MIGRATION.md`)

## Current Status

✅ **Working:**
- PLC connection
- Reading registers 69 (temp) and 70 (pressure)
- Displaying readings in console

❌ **Not Working:**
- Supabase connection (but this is now optional!)

## Recommendation

For now, just run the service WITHOUT Supabase. It will read your sensors and display them. You can add Supabase later if you need database storage.

```bash
cd backend
python sensor_service.py
```

Enjoy your working sensor readings! 🎉

