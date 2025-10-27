# Fix Serial Device Connection

## Problem
The backend is trying to connect to `/dev/ttyUSB0`, but the Docker container doesn't have access to the serial device.

## Solution 1: Check Which Device Exists

Run this command on your Raspberry Pi to check which serial device exists:

```bash
ls -l /dev/tty* | grep -E "(AMA0|USB0|ACM0)"
```

Common devices:
- `/dev/ttyAMA0` - Raspberry Pi GPIO serial port
- `/dev/ttyUSB0` - USB-to-serial adapter
- `/dev/ttyACM0` - USB device connected as serial

## Solution 2: Update docker-compose.yml Based on Your Device

### If using `/dev/ttyAMA0` (GPIO serial):

```yaml
backend:
  environment:
    - COM_PORT=/dev/ttyAMA0
  volumes:
    - /dev/ttyAMA0:/dev/ttyAMA0
    - /dev/gpiomem:/dev/gpiomem  # May be needed for GPIO access
  privileged: true  # May be needed for serial device access
```

### If using `/dev/ttyUSB0` (USB-to-serial):

```yaml
backend:
  environment:
    - COM_PORT=/dev/ttyUSB0
  volumes:
    - /dev/ttyUSB0:/dev/ttyUSB0
  privileged: true  # May be needed for serial device access
```

### If using `/dev/ttyACM0`:

```yaml
backend:
  environment:
    - COM_PORT=/dev/ttyACM0
  volumes:
    - /dev/ttyACM0:/dev/ttyACM0
  privileged: true  # May be needed for serial device access
```

## Solution 3: Check Device Permissions

Even with the correct device, you may get permission errors. Fix them:

```bash
# Temporary fix (until reboot)
sudo chmod 666 /dev/ttyAMA0

# OR for USB
sudo chmod 666 /dev/ttyUSB0

# Permanent fix
sudo usermod -aG dialout $USER
sudo reboot
```

## Quick Fix Command

Run this on your Raspberry Pi to automatically detect and configure:

```bash
# Detect serial device
DEVICE=$(ls /dev/tty{AMA0,USB0,ACM0} 2>/dev/null | head -1)

if [ -z "$DEVICE" ]; then
    echo "No serial device found!"
    exit 1
fi

echo "Found device: $DEVICE"

# Fix permissions
sudo chmod 666 $DEVICE

# Show current docker-compose.yml configuration
cat docker-compose.yml | grep -A 5 "volumes:" | grep "$DEVICE"

# If device is in docker-compose.yml, restart services
docker compose down
docker compose up -d --build
```

## Update Configuration

After identifying your device, update `docker-compose.yml`:

1. Find which device exists: `ls -l /dev/tty* | grep -E "(AMA0|USB0|ACM0)"`
2. Update `docker-compose.yml` to use that device
3. Update the `COM_PORT` environment variable to match
4. Rebuild and restart:

```bash
docker compose down
docker compose up -d --build
```

