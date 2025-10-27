# Troubleshooting Modbus Connection Issues

## Current Issue
You're getting: "No Response received from the remote slave"

This means:
- ✅ PLC connection works (COM10 is connected)
- ❌ Register addresses 70 and 69 don't exist or are wrong type
- ❌ May be holding registers, not input registers

## Solution Steps

### Step 1: Scan for Correct Registers

I've created a scanner tool to find where your sensor data is:

```bash
cd backend
python register_scan.py
```

This will:
- Scan registers 65-80 (around 69-70)
- Try both input registers and holding registers
- Show you which registers have data

**Example output:**
```
Scanning input registers 65 to 80...
  Register 68: Value = 1234
  Register 70: Value = 2048

Scanning holding registers 65 to 80...
  Register 70: Value = 1500
```

### Step 2: Update Register Addresses

Once you find the correct addresses, update them in `sensor_service.py`:

Edit these lines:
```python
PRESSURE_REGISTER = 70    # Change to your pressure register
TEMPERATURE_REGISTER = 69  # Change to your temperature register
```

### Step 3: Updated Code Already Fixes Some Issues

The code now tries:
1. Input registers first
2. Holding registers if input fails
3. This should work for most PLCs

Try running again:
```bash
python sensor_service.py
```

## Common Issues & Fixes

### Issue: "No response from slave"
**Possible causes:**
1. Wrong register type (input vs holding) - ✅ **FIXED** (code now tries both)
2. Wrong register addresses - Use scanner above
3. Wrong slave ID - Check in PLC manual

### Issue: "Wrong register addresses"
**Solution:**
- Use `register_scan.py` to find correct addresses
- Check PLC manual for register map
- Update `sensor_service.py` with correct addresses

### Issue: "Wrong Slave ID"
**Current setting:** Slave ID = 1 (from .env)

**To change:**
Edit `backend/.env`:
```env
SLAVE_ID=2  # or whatever your PLC uses
```

### Issue: "Wrong baud rate"
**Current setting:** 9600

**To change:**
Edit `backend/.env`:
```env
BAUD_RATE=19200  # or whatever your PLC uses
```

## Quick Test

### 1. Scan for registers
```bash
cd backend
python register_scan.py
```

### 2. Run updated service
```bash
python sensor_service.py
```

The updated code should now automatically try both input and holding registers!

## If Still Not Working

1. **Check PLC documentation** for:
   - Register addresses for pressure/temperature
   - Input vs holding registers
   - Slave ID
   - Baud rate

2. **Test with Modbus scanner software:**
   - Use ModScan or similar
   - Manually find the correct registers
   - Update the code with those addresses

3. **Verify connection:**
   - Check COM port in Device Manager
   - Verify cable is connected
   - Check PLC is powered on
   - Verify PLC is configured for Modbus RTU

## Next Steps

1. Run: `python register_scan.py`
2. Note which registers have values
3. Update `sensor_service.py` if addresses are different
4. Run again: `python sensor_service.py`

Good luck! The updated code should help automatically detect the correct register type.

