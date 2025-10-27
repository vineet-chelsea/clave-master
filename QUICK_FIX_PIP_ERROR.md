# Fix: Externally-Managed-Environment Error

## Problem
```
error: externally-managed-environment
× This environment is externally managed
```

## Cause
Newer Raspberry Pi OS (Debian 12+) uses PEP 668 to prevent system-wide Python package installation.

## Solution: Use Virtual Environment

### Option 1: Quick Fix (Recommended)

```bash
# Create virtual environment
python3 -m venv ~/venv

# Activate it
source ~/venv/bin/activate

# Install docker-compose
pip install docker-compose

# Use docker-compose
docker-compose --version

# Deactivate when done
deactivate
```

### Option 2: Update Docker Compose Command

Use `/home/pi/venv/bin/docker-compose` or activate venv first:

```bash
source ~/venv/bin/activate
docker-compose up -d
```

### Option 3: Add to PATH (Permanent)

```bash
# Add to .bashrc
echo 'source ~/venv/bin/activate' >> ~/.bashrc

# Reload
source ~/.bashrc

# Now docker-compose works directly
docker-compose --version
```

## Updated Systemd Service

When using virtual environment, update service file:

```ini
ExecStart=/usr/bin/bash -c "source /home/pi/venv/bin/activate && docker-compose up -d"
ExecStop=/usr/bin/bash -c "source /home/pi/venv/bin/activate && docker-compose down"
```

## Complete Fix

```bash
# 1. Create venv
python3 -m venv ~/venv

# 2. Activate
source ~/venv/bin/activate

# 3. Install docker-compose
pip install docker-compose

# 4. Add to .bashrc for auto-activation
echo 'source ~/venv/bin/activate' >> ~/.bashrc

# 5. Test
docker-compose --version
```

**Fixed!** ✅

