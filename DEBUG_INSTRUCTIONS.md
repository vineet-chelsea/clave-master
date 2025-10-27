# 🔍 Debug Instructions

## I Need Console Output

Without seeing what's happening in the browser, I can't diagnose the issue.

## How to Share Debug Info

### 1. Open Browser Console (F12)
Press F12 in your browser, go to Console tab

### 2. Take Screenshot or Copy
- Take screenshot of console
- Or copy all the text
- Or describe what errors you see

### 3. What to Look For

**Errors?** Red text - what does it say?

**Logs?** Any of these:
- "ProcessMonitor mounted with: ..."
- "Chart data: ..."
- "Set sessionId to: ..."

**Data?** Check:
- Is pressure reading showing (15.8 PSI in your screenshot)?
- Is temperature showing (28.8 °C)?

### 4. Check Network Tab (F12)
- Click Network tab
- Refresh page
- Look for:
  - `/api/sensor-readings/latest` - Is it returning data?
  - `/api/sessions` - What does it return?
  - Any failed requests (red)?

## Quick Tests

### Test 1: API Working?
Open browser: http://localhost:5000/api/health
Should return JSON

### Test 2: Sensor Data?
Open browser: http://localhost:5000/api/sensor-readings/latest
Should return pressure and temperature

### Test 3: Sessions?
Open browser: http://localhost:5000/api/sessions
Should return list of sessions

## Share This Info

1. Browser console output (screenshot or text)
2. What errors appear (if any)
3. What the network tab shows
4. Results of the 3 test URLs above

Without this info, I can't fix the specific issue you're seeing!
