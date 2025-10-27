# Fix: Permission Denied on /dev/ttyACM0

## Error
```
/dev/ttyACM0 permission denied
```

## Solutions

### Quick Fix (Temporary)

```bash
# Grant read/write permissions
sudo chmod 666 /dev/ttyACM0

# Verify
ls -l /dev/ttyACM0
# Should show: crw-rw-rw-

# Test access
cat /dev/ttyACM0
# Should work without error
```

### Permanent Fix (Recommended)

**Option 1: Add user to dialout group**
```bash
# Add user to dialout group
sudo usermod -aG dialout $USER

# Log out and back in, or:
newgrp dialout

# Or reboot
sudo reboot
```

**Option 2: Create udev rule**
```bash
# Create udev rule
sudo nano /etc/udev/rules.d/99-serial-permissions.rules
```

Paste:
```
KERNEL=="ttyACM[0-9]*", MODE="0666"
KERNEL=="ttyUSB[0-9]*", MODE="0666"
KERNEL=="ttyAMA[0-9]*", MODE="0666"
```

Apply:
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Test Access

```bash
# Check permissions
ls -l /dev/ttyACM0

# Should show: crw-rw-rw- or crw-rw----

# Test write access
echo "test" > /dev/ttyACM0
# Should not error
```

### For Docker

If running in Docker, the container needs access:

```yaml
# In docker-compose.yml
volumes:
  - /dev/ttyACM0:/dev/ttyACM0

# May need privileged mode
privileged: true
```

Or ensure host permissions are set first:
```bash
sudo chmod 666 /dev/ttyACM0
```

## Summary

**Quick:** `sudo chmod 666 /dev/ttyACM0`  
**Permanent:** `sudo usermod -aG dialout $USER` + reboot  
**Docker:** Set host permissions before starting container

✅ **Permission denied error fixed!**

