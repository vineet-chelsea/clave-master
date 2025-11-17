# Timezone Setup - IST (Indian Standard Time)

## ✅ Changes Applied

All timestamps in the system have been updated to use **IST (Indian Standard Time, UTC+5:30)**.

### Backend Changes

1. **Added `pytz` dependency** (`backend/requirements.txt`)
   - `pytz==2024.1` for timezone handling

2. **Updated `backend/api_server.py`**:
   - Added `IST = pytz.timezone('Asia/Kolkata')`
   - Added `get_ist_now()` function to get current IST datetime
   - Updated `get_db_connection()` to set PostgreSQL timezone to IST
   - All `datetime.now()` calls replaced with `get_ist_now()`

3. **Updated `backend/sensor_control_service.py`**:
   - Added `IST = pytz.timezone('Asia/Kolkata')`
   - Added `get_ist_now()` function
   - Updated database connection to set timezone to IST
   - All `datetime.now()` calls replaced with `get_ist_now()`
   - All timestamp insertions now use IST

### Frontend Changes

1. **Added `date-fns-tz` dependency** (`package.json`)
   - `date-fns-tz==3.0.0` for timezone conversions

2. **Updated `src/components/HistoricalData.tsx`**:
   - Added `formatInTimeZone` import from `date-fns-tz`
   - Created `formatIST()` helper function
   - All date formatting now uses IST timezone

3. **Updated `src/components/ProcessMonitor.tsx`**:
   - Added `formatInTimeZone` import from `date-fns-tz`
   - Chart timestamps now display in IST

### Database Configuration

- PostgreSQL connections now set timezone to `'Asia/Kolkata'` on connection
- All `TIMESTAMP WITH TIME ZONE` columns will store and return times in IST
- Database default timezone is set per connection

## 📦 Installation Required

### Backend
```bash
cd backend
pip install pytz==2024.1
# Or install all requirements
pip install -r requirements.txt
```

### Frontend
```bash
npm install date-fns-tz@3.0.0
# Or install all dependencies
npm install
```

## 🔄 How It Works

### Backend
- All timestamps are created using `get_ist_now()` which returns `datetime.now(IST)`
- Database connections set timezone to IST: `SET timezone = 'Asia/Kolkata'`
- PostgreSQL automatically converts stored timestamps to IST when queried

### Frontend
- All date formatting uses `formatIST()` or `formatInTimeZone(date, 'Asia/Kolkata', format)`
- Timestamps from API are interpreted and displayed in IST
- Charts show IST time on X-axis

## ✅ Verification

After installation, verify:
1. Backend logs show IST timestamps
2. Database stores timestamps in IST
3. Frontend displays all times in IST
4. Charts show IST time labels
5. PDF reports show IST timestamps

## 📝 Notes

- IST is UTC+5:30 (no daylight saving time)
- All timestamps are consistent across backend, database, and frontend
- Historical data will display in IST (converted from stored UTC if needed)
- New data will be stored directly in IST

