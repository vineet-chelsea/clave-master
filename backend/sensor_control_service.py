"""
Main Sensor and Control Service
Run this ONCE before starting the frontend
Handles all PLC communication and control logic
"""

import os
import time
import sys
import subprocess
import re
from datetime import datetime
from pymodbus.client import ModbusSerialClient
from dotenv import load_dotenv
import psycopg2
import threading
import requests
import pytz
try:
    import serial
    import serial.tools.list_ports
except ImportError:
    # Fallback if pyserial is not available
    serial = None

load_dotenv()

# Modbus configuration
COM_PORT = os.getenv('COM_PORT', 'COM10')
BAUD_RATE = int(os.getenv('BAUD_RATE', '9600'))
SLAVE_ID = int(os.getenv('SLAVE_ID', '1'))
TIMEOUT = 2

# Register addresses
PRESSURE_REGISTER = 68
TEMPERATURE_REGISTER = 69
VALVE_CONTROL_REGISTER = 51
BUZZER_COIL_ADDRESS = 0  # Coil address for buzzer control

# Scaling
PRESSURE_MIN = 0
PRESSURE_MAX = 4095
PRESSURE_OUTPUT_MIN = 0
PRESSURE_OUTPUT_MAX = 87

# Control parameters
CONTROL_INTERVAL = 7  # Check every 15 seconds
PRESSURE_TOLERANCE = 1
MAX_VALVE_VALUE = 4000

# Buzzer control parameters
BUZZER_ON_DURATION = 3  # Buzzer on for 3 seconds
BUZZER_OFF_DURATION = 3  # Buzzer off for 3 seconds
BUZZER_CHECK_INTERVAL = 5  # Check pressure every 5 seconds for buzzer
# Buzzer threshold logic:
# - For ranges (e.g., "5-10"): activates when pressure < (lower + 1) = 6
# - For constants (e.g., "10"): activates when pressure < (constant - 2) = 8

# PostgreSQL configuration
PG_HOST = os.getenv('PG_HOST', '127.0.0.1')
PG_PORT = os.getenv('PG_PORT', '5432')
PG_DATABASE = os.getenv('PG_DATABASE', 'autoclave')
PG_USER = os.getenv('PG_USER', 'postgres')
PG_PASSWORD = os.getenv('PG_PASSWORD', 'postgres')

# Sensor reading interval
SENSOR_READ_INTERVAL = 7

# IST timezone (UTC+5:30)
IST = pytz.timezone('Asia/Kolkata')

def get_ist_now():
    """Get current datetime in IST timezone"""
    return datetime.now(IST)


class SensorControlService:
    def __init__(self):
        """Initialize service"""
        # Initialize PLC client (connection will be established later)
        self.plc_client = None
        self.slave_id = SLAVE_ID
        self.com_port = COM_PORT
        self.is_connected = False
        self.connection_retry_count = 0
        self.max_retries = 10
        self.usb_reset_enabled = True  # Enable USB reset on persistent failures
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3  # Reset USB after 5 consecutive failures
        
        # Initialize PostgreSQL connection
        self.conn = None
        self.db_connect()
        
        # Control state
        self.control_active = False
        self.target_pressure = None
        self.current_psi_range = None  # Store original psi_range string for buzzer logic
        self.remaining_minutes = 0
        self.valve_position = 0
        self.session_id = None
        self.end_time = None
        self.control_thread = None
        self.last_checked_session_id = None  # Track last session to avoid re-processing
        
        # Buzzer control state
        self.buzzer_active = False
        self.buzzer_thread = None
        self.buzzer_stop_event = threading.Event()
        self.plc_lock = threading.Lock()  # Lock for thread-safe PLC access
        
        # Multi-step program state
        self.program_steps = []
        self.current_step_index = 0
        self.step_start_time = None
        self.step_pause_offset = 0  # Track time spent in pause
        self.paused_time = None  # When step was paused
        
    def check_device_available(self, port_path):
        """Check if serial device exists and is accessible"""
        if sys.platform.startswith('win'):
            # Windows: just check if port exists in list
            try:
                if serial and hasattr(serial.tools, 'list_ports'):
                    ports = serial.tools.list_ports.comports()
                    port_names = [p.device for p in ports]
                    return port_path in port_names
                else:
                    # Fallback: just check if it's a COM port format
                    return port_path.upper().startswith('COM') and len(port_path) <= 5
            except:
                return False
        else:
            # Linux/Unix: check if file exists and is readable
            return os.path.exists(port_path) and os.access(port_path, os.R_OK)
    
    def wait_for_device(self, port_path, max_wait_seconds=30, check_interval=1):
        """Wait for device to become available"""
        elapsed = 0
        while elapsed < max_wait_seconds:
            if self.check_device_available(port_path):
                return True
            time.sleep(check_interval)
            elapsed += check_interval
            if elapsed % 5 == 0:  # Print every 5 seconds
                print(f"[WAIT] Waiting for device {port_path}... ({elapsed}s)")
        return False
    
    def connect_plc(self, retry=True):
        """Connect to PLC with retry logic"""
        if self.is_connected and self.plc_client and self.plc_client.is_socket_open():
            return True
        
        # Check if device is available
        if not self.check_device_available(self.com_port):
            if retry:
                print(f"[WAIT] Device {self.com_port} not available, waiting...")
                if not self.wait_for_device(self.com_port):
                    print(f"[ERROR] Device {self.com_port} not found after waiting")
                    return False
            else:
                print(f"[ERROR] Device {self.com_port} not available")
                return False
        
        # Close existing connection if any
        if self.plc_client:
            try:
                self.plc_client.close()
            except:
                pass
        
        # Create new client
        try:
            self.plc_client = ModbusSerialClient(
                port=self.com_port,
                baudrate=BAUD_RATE,
                parity='N',
                stopbits=1,
                bytesize=8,
                timeout=TIMEOUT
            )
            
            # Attempt connection with exponential backoff
            retry_delay = 1
            for attempt in range(self.max_retries):
                try:
                    if self.plc_client.connect():
                        self.is_connected = True
                        self.connection_retry_count = 0
                        self.consecutive_failures = 0
                        return True
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        print(f"[RETRY] Connection attempt {attempt + 1}/{self.max_retries} failed: {e}")
                        
                        # If we've had multiple consecutive failures, try USB reset
                        if (attempt == self.max_retries // 2 and 
                            self.consecutive_failures >= self.max_consecutive_failures and 
                            self.usb_reset_enabled):
                            print(f"[USB RESET] Multiple connection failures detected, attempting USB reset...")
                            if self.reset_usb_device(self.com_port):
                                print(f"[USB RESET] USB device reset, waiting 3 seconds before retry...")
                                time.sleep(3)
                        
                        print(f"        Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, 10)  # Exponential backoff, max 10s
                    else:
                        print(f"[ERROR] Failed to connect after {self.max_retries} attempts: {e}")
                        self.is_connected = False
                        self.consecutive_failures += 1
                        
                        # Try USB reset as last resort
                        if (self.consecutive_failures >= self.max_consecutive_failures and 
                            self.usb_reset_enabled):
                            print(f"[USB RESET] Persistent failures, attempting USB reset...")
                            if self.reset_usb_device(self.com_port):
                                print(f"[USB RESET] USB reset successful, will retry on next connection attempt")
                                time.sleep(3)
                        
                        return False
            
            self.is_connected = False
            return False
            
        except Exception as e:
            print(f"[ERROR] Failed to create PLC client: {e}")
            self.is_connected = False
            self.consecutive_failures += 1
            
            # Try USB reset if we've had many failures
            if (self.consecutive_failures >= self.max_consecutive_failures and 
                self.usb_reset_enabled):
                print(f"[USB RESET] Persistent failures, attempting USB reset...")
                if self.reset_usb_device(self.com_port):
                    print(f"[USB RESET] USB reset successful")
                    time.sleep(3)
            
            return False
    
    def find_usb_device_path(self, tty_device):
        """Find the USB device path in /sys/bus/usb/devices/ for a given tty device"""
        if sys.platform.startswith('win'):
            return None  # Windows doesn't use this approach
        
        try:
            # Get the device info using udevadm or by checking /sys/class/tty
            # Method 1: Use udevadm to find USB device
            try:
                result = subprocess.run(
                    ['udevadm', 'info', '--name=' + tty_device, '--query=path'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    path = result.stdout.strip()
                    # Extract USB bus/port from path like /devices/pci0000:00/0000:00:14.0/usb1/1-2/1-2.1:1.0/tty/ttyACM0
                    match = re.search(r'/usb\d+/([\d\.-]+):', path)
                    if match:
                        return match.group(1)  # Returns something like "1-2" or "1-2.1"
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Method 2: Check /sys/class/tty directly
            tty_name = os.path.basename(tty_device)
            sys_path = f'/sys/class/tty/{tty_name}/device'
            if os.path.exists(sys_path):
                # Resolve symlink
                real_path = os.path.realpath(sys_path)
                # Look for USB bus pattern
                match = re.search(r'/usb\d+/([\d\.-]+)/', real_path)
                if match:
                    return match.group(1)
            
            return None
        except Exception as e:
            print(f"[DEBUG] Error finding USB device path: {e}")
            return None
    
    def reset_usb_device(self, tty_device):
        """Reset USB device by unbinding and rebinding"""
        if sys.platform.startswith('win'):
            print("[INFO] USB reset not supported on Windows")
            return False
        
        usb_path = self.find_usb_device_path(tty_device)
        if not usb_path:
            print(f"[WARNING] Could not find USB device path for {tty_device}")
            return False
        
        print(f"[USB RESET] Attempting to reset USB device {usb_path} for {tty_device}...")
        
        try:
            # Method 1: Try usbreset tool if available
            try:
                # Find device by vendor/product ID first
                result = subprocess.run(
                    ['lsusb'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    # Try to find usbreset binary
                    usbreset_paths = ['/usr/bin/usbreset', '/usr/local/bin/usbreset', 'usbreset']
                    for usbreset_cmd in usbreset_paths:
                        try:
                            # This would require finding the bus/device numbers
                            # For now, skip this method
                            pass
                        except:
                            pass
            except:
                pass
            
            # Method 2: Unbind and rebind via sysfs (requires root or proper permissions)
            unbind_path = f'/sys/bus/usb/drivers/usb/unbind'
            bind_path = f'/sys/bus/usb/drivers/usb/bind'
            
            # Check if we can write to these paths
            if os.path.exists(unbind_path) and os.access(unbind_path, os.W_OK):
                # Unbind
                try:
                    with open(unbind_path, 'w') as f:
                        f.write(usb_path)
                    print(f"[USB RESET] Unbound USB device {usb_path}")
                    time.sleep(1)  # Wait a moment
                    
                    # Rebind
                    with open(bind_path, 'w') as f:
                        f.write(usb_path)
                    print(f"[USB RESET] Rebound USB device {usb_path}")
                    time.sleep(2)  # Wait for device to reinitialize
                    return True
                except PermissionError:
                    print(f"[USB RESET] Permission denied - need root/sudo access")
                    # Try with sudo if available
                    try:
                        subprocess.run(
                            ['sudo', 'sh', '-c', f'echo {usb_path} > {unbind_path}'],
                            check=True,
                            timeout=2
                        )
                        time.sleep(1)
                        subprocess.run(
                            ['sudo', 'sh', '-c', f'echo {usb_path} > {bind_path}'],
                            check=True,
                            timeout=2
                        )
                        time.sleep(2)
                        print(f"[USB RESET] Reset USB device {usb_path} using sudo")
                        return True
                    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                        print(f"[USB RESET] Could not reset USB device - sudo may not be configured")
                        return False
                except Exception as e:
                    print(f"[USB RESET] Error resetting USB device: {e}")
                    return False
            else:
                print(f"[USB RESET] Cannot access USB reset paths - need proper permissions")
                return False
                
        except Exception as e:
            print(f"[USB RESET] Failed to reset USB device: {e}")
            return False
    
    def ensure_connected(self):
        """Ensure PLC connection is active, reconnect if needed"""
        if not self.is_connected or not self.plc_client or not self.plc_client.is_socket_open():
            print("[RECONNECT] PLC connection lost, attempting to reconnect...")
            return self.connect_plc(retry=True)
        return True
    
    def db_connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(
                host=PG_HOST,
                port=PG_PORT,
                database=PG_DATABASE,
                user=PG_USER,
                password=PG_PASSWORD
            )
            # Set timezone to IST
            cursor = self.conn.cursor()
            cursor.execute("SET timezone = 'Asia/Kolkata'")
            self.conn.commit()
            cursor.close()
            print("[OK] Connected to PostgreSQL")
        except Exception as e:
            print(f"[WARNING] Failed to connect to PostgreSQL: {e}")
            self.conn = None
    
    def scale_pressure(self, raw_value):
        """Scale raw Modbus value to PSI"""
        if raw_value is None:
            return None
        scaled = PRESSURE_OUTPUT_MIN + (raw_value - PRESSURE_MIN) * (PRESSURE_OUTPUT_MAX - PRESSURE_OUTPUT_MIN) / (PRESSURE_MAX - PRESSURE_MIN)
        return round(scaled, 2)
    
    def read_pressure(self):
        """Read current pressure from PLC - Thread-safe"""
        if not self.ensure_connected():
            return None
        try:
            with self.plc_lock:  # Thread-safe access
                result = self.plc_client.read_input_registers(
                    PRESSURE_REGISTER,
                    count=1,
                    slave=self.slave_id
                )
            
            if result and not result.isError():
                raw_value = result.registers[0]
                # Reset failure counter on successful read
                self.consecutive_failures = 0
                if hasattr(self, '_usb_reset_attempted'):
                    delattr(self, '_usb_reset_attempted')
                return self.scale_pressure(raw_value)
            return None
        except Exception as e:
            # Connection may have been lost
            self.is_connected = False
            self.consecutive_failures += 1
            
            # If we've had many failures, try USB reset
            if (self.consecutive_failures >= self.max_consecutive_failures and 
                self.usb_reset_enabled and 
                not hasattr(self, '_usb_reset_attempted')):
                self._usb_reset_attempted = True
                print(f"[USB RESET] Multiple read failures, attempting USB reset...")
                if self.reset_usb_device(self.com_port):
                    print(f"[USB RESET] USB reset successful, will reconnect on next attempt")
                    time.sleep(2)
                    self._usb_reset_attempted = False  # Reset flag after delay
            return None
    
    def read_temperature(self):
        """Read current temperature from PLC - Thread-safe"""
        if not self.ensure_connected():
            return None
        try:
            with self.plc_lock:  # Thread-safe access
                result = self.plc_client.read_input_registers(
                    TEMPERATURE_REGISTER,
                    count=1,
                    slave=self.slave_id
                )
            
            if result and not result.isError():
                raw_value = result.registers[0]
                temperature = 0 + (raw_value - 0) * (350 - 0) / (4095 - 0)
                
                # Apply adjustment formula: temperature + 0.2*(temperature-80) if temperature > 80
                if temperature > 80:
                    temperature = temperature + 0.2 * (temperature - 80)
                
                # Reset failure counter on successful read
                self.consecutive_failures = 0
                if hasattr(self, '_usb_reset_attempted'):
                    delattr(self, '_usb_reset_attempted')
                return round(temperature, 2)
            return None
        except Exception as e:
            # Connection may have been lost
            self.is_connected = False
            self.consecutive_failures += 1
            
            # If we've had many failures, try USB reset
            if (self.consecutive_failures >= self.max_consecutive_failures and 
                self.usb_reset_enabled and 
                not hasattr(self, '_usb_reset_attempted')):
                self._usb_reset_attempted = True
                print(f"[USB RESET] Multiple read failures, attempting USB reset...")
                if self.reset_usb_device(self.com_port):
                    print(f"[USB RESET] USB reset successful, will reconnect on next attempt")
                    time.sleep(2)
                    self._usb_reset_attempted = False  # Reset flag after delay
            return None
    
    def read_valve_position(self):
        """Read current valve position - Thread-safe"""
        if not self.ensure_connected():
            return None
        try:
            with self.plc_lock:  # Thread-safe access
                result = self.plc_client.read_holding_registers(
                    VALVE_CONTROL_REGISTER,
                    count=1,
                    slave=self.slave_id
                )
            
            if result and not result.isError():
                return result.registers[0]
            return None
        except Exception as e:
            # Connection may have been lost
            self.is_connected = False
            self.consecutive_failures += 1
            
            # If we've had many failures, try USB reset
            if (self.consecutive_failures >= self.max_consecutive_failures and 
                self.usb_reset_enabled and 
                not hasattr(self, '_usb_reset_attempted')):
                self._usb_reset_attempted = True
                print(f"[USB RESET] Multiple read failures, attempting USB reset...")
                if self.reset_usb_device(self.com_port):
                    print(f"[USB RESET] USB reset successful, will reconnect on next attempt")
                    time.sleep(2)
                    self._usb_reset_attempted = False  # Reset flag after delay
            return None
    
    def set_valve_position(self, value):
        """Set valve control register (0-4000) - Thread-safe"""
        if not self.ensure_connected():
            return False
        try:
            with self.plc_lock:  # Thread-safe access
                result = self.plc_client.write_register(
                    VALVE_CONTROL_REGISTER,
                    value,
                    slave=self.slave_id
                )
            
            if not result.isError():
                self.valve_position = value
                return True
            return False
        except Exception as e:
            print(f"[ERROR] Writing valve: {e}")
            # Connection may have been lost
            self.is_connected = False
            return False
    
    def set_buzzer(self, state):
        """Set buzzer coil (True=ON, False=OFF) - Thread-safe"""
        if not self.ensure_connected():
            return False
        try:
            with self.plc_lock:  # Thread-safe access to avoid RS485 conflicts
                result = self.plc_client.write_coil(
                    BUZZER_COIL_ADDRESS,
                    state,
                    slave=self.slave_id
                )
            
            if not result.isError():
                return True
            return False
        except Exception as e:
            print(f"[ERROR] Writing buzzer: {e}")
            return False
    
    def buzzer_control_loop(self):
        """Buzzer control loop - runs in separate thread"""
        print("[BUZZER] Buzzer control thread started")
        
        while not self.buzzer_stop_event.is_set():
            try:
                # Check if we have a target pressure and control is active
                if self.target_pressure is None or not self.control_active:
                    time.sleep(BUZZER_CHECK_INTERVAL)
                    continue
                
                # Read current pressure (thread-safe)
                pressure = self.read_pressure()
                
                if pressure is None:
                    time.sleep(BUZZER_CHECK_INTERVAL)
                    continue
                
                # Calculate buzzer threshold based on whether it's a range or constant
                buzzer_threshold = None
                if self.current_psi_range and '-' in self.current_psi_range:
                    # Range: buzzer activates when pressure < (lower + 1)
                    parts = self.current_psi_range.split('-')
                    if len(parts) == 2:
                        try:
                            lower_bound = float(parts[0].strip())
                            buzzer_threshold = lower_bound + 1
                        except:
                            pass
                
                if buzzer_threshold is None:
                    # Constant value: buzzer activates when pressure < (constant - 2)
                    buzzer_threshold = self.target_pressure - 2
                
                # Check if pressure is below threshold (activate buzzer)
                if pressure < buzzer_threshold:
                    if not self.buzzer_active:
                        print(f"[BUZZER] Pressure {pressure:.2f} PSI below threshold ({buzzer_threshold:.2f} PSI), activating buzzer")
                        self.buzzer_active = True
                    
                    # Buzzer cycle: ON for 3 sec, OFF for 3 sec
                    if self.set_buzzer(True):
                        print(f"[BUZZER] ON - Pressure: {pressure:.2f} PSI (Target: {self.target_pressure:.2f} PSI)")
                    
                    # Wait for ON duration, checking stop event
                    for _ in range(BUZZER_ON_DURATION):
                        if self.buzzer_stop_event.is_set():
                            self.set_buzzer(False)
                            return
                        time.sleep(1)
                    
                    if self.set_buzzer(False):
                        print(f"[BUZZER] OFF - Pressure: {pressure:.2f} PSI")
                    
                    # Wait for OFF duration, checking stop event
                    for _ in range(BUZZER_OFF_DURATION):
                        if self.buzzer_stop_event.is_set():
                            return
                        time.sleep(1)
                else:
                    # Pressure above threshold - turn off buzzer if it was on
                    if self.buzzer_active:
                        self.set_buzzer(False)
                        self.buzzer_active = False
                        print(f"[BUZZER] Pressure {pressure:.2f} PSI above threshold ({buzzer_threshold:.2f} PSI), buzzer deactivated")
                    
                    # Wait before next check
                    time.sleep(BUZZER_CHECK_INTERVAL)
                    
            except Exception as e:
                print(f"[ERROR] Buzzer control loop error: {e}")
                time.sleep(BUZZER_CHECK_INTERVAL)
        
        # Ensure buzzer is off when thread stops
        self.set_buzzer(False)
        self.buzzer_active = False
        print("[BUZZER] Buzzer control thread stopped")
    
    def parse_pressure_range(self, psi_range):
        """Parse pressure from range string (e.g., '5-10' -> 7.5, '10' -> 10)"""
        if '-' in psi_range:
            parts = psi_range.split('-')
            if len(parts) == 2:
                try:
                    low = float(parts[0].strip())
                    high = float(parts[1].strip())
                    return (low + high) / 2  # Median
                except:
                    pass
        # Single value or "Steady at X"
        try:
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', psi_range)
            if numbers:
                return float(numbers[0])
        except:
            pass
        return 0
    
    def check_step_completion(self):
        """Check if current step duration has been exceeded"""
        if not self.program_steps or self.current_step_index >= len(self.program_steps):
            return False
        
        current_step = self.program_steps[self.current_step_index]
        step_duration_minutes = current_step['duration_minutes']
        
        if self.step_start_time is None:
            self.step_start_time = time.time()
            return False
        
        # Calculate elapsed time, accounting for pauses
        # step_start_time is the real start time
        # self.paused_time tracks when we were paused
        # self.step_pause_offset accumulates time spent paused
        elapsed_seconds = time.time() - self.step_start_time - self.step_pause_offset
        
        if self.paused_time is not None:
            # Currently paused - add pause time to offset
            pause_duration = time.time() - self.paused_time
            self.step_pause_offset += pause_duration
            self.paused_time = time.time()
        
        elapsed_minutes = elapsed_seconds / 60
        
        if elapsed_minutes >= step_duration_minutes:
            return True
        return False
    
    def mark_paused(self):
        """Mark that the step is now paused"""
        if self.paused_time is None:
            self.paused_time = time.time()
    
    def mark_resumed(self):
        """Mark that the step has resumed"""
        if self.paused_time is not None:
            pause_duration = time.time() - self.paused_time
            self.step_pause_offset += pause_duration
            self.paused_time = None
    
    def advance_to_next_step(self):
        """Move to next program step"""
        self.current_step_index += 1
        
        if self.current_step_index >= len(self.program_steps):
            # All steps complete
            print(f"[COMPLETE] All {len(self.program_steps)} steps completed")
            self.complete_session()
            return
        
        # Update target pressure for new step
        new_step = self.program_steps[self.current_step_index]
        target_pressure = self.parse_pressure_range(new_step['psi_range'])
        
        self.target_pressure = target_pressure
        self.current_psi_range = new_step['psi_range']  # Store original range string for buzzer
        self.step_start_time = time.time()
        self.step_pause_offset = 0  # Reset pause tracking for new step
        self.paused_time = None
        
        print(f"\n[STEP] Advanced to step {self.current_step_index + 1}/{len(self.program_steps)}")
        print(f"[STEP] Target: {target_pressure} PSI ({new_step['psi_range']})")
        print(f"[STEP] Duration: {new_step['duration_minutes']} min")
    
    def save_sensor_reading(self, pressure, temperature):
        """Save sensor reading to database"""
        if not self.conn:
            return
            
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO sensor_readings (pressure, temperature, timestamp) VALUES (%s, %s, %s)",
                (pressure, temperature, get_ist_now())
            )
            self.conn.commit()
            cursor.close()
        except Exception as e:
            pass
    
    def save_process_log(self, pressure, temperature, valve_position):
        """Save process log"""
        if not self.conn or not self.session_id:
            return
            
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO process_logs (session_id, program_name, pressure, temperature, valve_position, status) VALUES (%s, %s, %s, %s, %s, %s)",
                (self.session_id, 'Active Control', pressure, temperature, valve_position, 'running')
            )
            self.conn.commit()
            cursor.close()
        except Exception as e:
            pass
    
    def start_control_session(self, target_pressure, duration_minutes, program_name="Manual Control", steps_data=None, existing_session_id=None):
        """Start a new control session"""
        if not self.conn:
            print("[ERROR] Database not connected")
            return False
        
        # Check if control is already active - prevent duplicate control loops
        if self.control_active:
            # Check if it's for the same session
            if self.session_id:
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT id FROM process_sessions WHERE id=%s AND status='running'",
                    (self.session_id,)
                )
                result = cursor.fetchone()
                cursor.close()
                if result:
                    print(f"[INFO] Control already active for session {self.session_id}, skipping duplicate start")
                    return True
            else:
                print("[INFO] Control already active but no session ID, stopping old control first")
                self.stop_control_session()
        
        try:
            # Convert to proper types
            target_pressure = float(target_pressure)
            duration_minutes = int(duration_minutes)
            
            # If session_id is provided (from API), use it directly
            if existing_session_id:
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT id FROM process_sessions WHERE id=%s AND status='running'",
                    (existing_session_id,)
                )
                result = cursor.fetchone()
                cursor.close()
                if result:
                    self.session_id = existing_session_id
                    print(f"[SESSION] Using provided session {self.session_id}")
                else:
                    print(f"[WARNING] Provided session {existing_session_id} not found or not running, will create new one")
                    existing_session_id = None
            
            # If no session_id provided or session not found, try to find existing or create new
            if not existing_session_id:
                cursor = self.conn.cursor()
                # First, check for ANY running session with target_pressure (most recent)
                cursor.execute(
                    "SELECT id FROM process_sessions WHERE status='running' AND target_pressure IS NOT NULL ORDER BY id DESC LIMIT 1"
                )
                result = cursor.fetchone()
                
                if result:
                    # Use existing session
                    self.session_id = result[0]
                    print(f"[SESSION] Using existing running session {self.session_id}")
                else:
                    # Create new session only if no running session exists
                    cursor.execute(
                        "INSERT INTO process_sessions (program_name, status, start_time) VALUES (%s, %s, %s) RETURNING id",
                        (program_name, 'running', get_ist_now())
                    )
                    self.session_id = cursor.fetchone()[0]
                    print(f"[SESSION] Created new session {self.session_id}")
                
                cursor.close()
            
            # Load program steps if provided (auto program mode)
            if steps_data:
                import json
                if isinstance(steps_data, str):
                    self.program_steps = json.loads(steps_data)
                else:
                    self.program_steps = steps_data
                self.current_step_index = 0
                self.step_start_time = time.time()
                # Set target to first step
                first_step = self.program_steps[0]
                self.target_pressure = self.parse_pressure_range(first_step['psi_range'])
                self.current_psi_range = first_step['psi_range']  # Store original range string for buzzer
                print(f"[PROGRAM] Loaded {len(self.program_steps)} step program")
                print(f"[PROGRAM] Step 1/{len(self.program_steps)}: {self.target_pressure} PSI")
            else:
                # Manual mode - single step (constant value, no range)
                self.program_steps = []
                self.target_pressure = target_pressure
                self.current_psi_range = None  # Manual mode uses constant value
                self.current_step_index = 0
                self.step_start_time = None
            
            self.conn.commit()
            cursor.close()
            
            self.control_active = True
            self.target_pressure = target_pressure
            # For manual mode, current_psi_range is None (will use constant - 2 logic)
            if not self.current_psi_range:
                self.current_psi_range = None
            self.remaining_minutes = duration_minutes
            self.end_time = get_ist_now().timestamp() + (duration_minutes * 60)
            
            # Start control thread only if not already running
            if not hasattr(self, 'control_thread') or not self.control_thread.is_alive():
                self.control_thread = threading.Thread(target=self.control_loop, daemon=True)
                self.control_thread.start()
                print(f"     Control thread started")
            else:
                print(f"     Control thread already running")
            
            # Start buzzer control thread only if not already running
            if not hasattr(self, 'buzzer_thread') or not self.buzzer_thread.is_alive():
                self.buzzer_stop_event.clear()
                self.buzzer_thread = threading.Thread(target=self.buzzer_control_loop, daemon=True)
                self.buzzer_thread.start()
                print(f"     Buzzer control thread started")
            else:
                print(f"     Buzzer control thread already running")
            
            print(f"[OK] Started control session {self.session_id}")
            print(f"     Target: {target_pressure} PSI")
            print(f"     Duration: {duration_minutes} minutes")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to start session: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop_control_session(self):
        """Stop the current control session"""
        print("[STOP] Stopping control session...")
        self.control_active = False
        
        # Stop buzzer thread and turn off buzzer
        if self.buzzer_thread and self.buzzer_thread.is_alive():
            self.buzzer_stop_event.set()
            self.buzzer_thread.join(timeout=2)  # Wait up to 2 seconds for thread to stop
            self.set_buzzer(False)
            print("[STOP] Buzzer thread stopped and buzzer turned off")
        
        # Close valve to safe position
        success = self.set_valve_position(0)
        if success:
            print(f"[SAFETY] Valve closed to 0/4000")
        
        if self.conn and self.session_id:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "UPDATE process_sessions SET status='stopped', end_time=%s WHERE id=%s",
                    (get_ist_now(), self.session_id)
                )
                self.conn.commit()
                cursor.close()
            except Exception as e:
                print(f"[ERROR] Stopping session: {e}")
        
        self.target_pressure = None
        self.session_id = None
        print("[OK] Stopped control session")
    
    def control_loop(self):
        """Main control loop - runs in background thread"""
        control_count = 0
        no_active_session_count = 0
        
        print("[CONTROL] Control loop started")
        
        while self.control_active:
            # Check if session is still active in database
            if self.conn and self.session_id:
                try:
                    cursor = self.conn.cursor()
                    cursor.execute(
                        "SELECT status FROM process_sessions WHERE id=%s",
                        (self.session_id,)
                    )
                    row = cursor.fetchone()
                    cursor.close()
                    
                    if row and row[0] in ('stopped', 'completed'):
                        print(f"[CONTROL] Session status changed to: {row[0]}")
                        if row[0] == 'stopped' or row[0] == 'completed':
                            print("[CONTROL] Session finished, stopping control and closing valve")
                            self.control_active = False
                            # Reset valve to closed position
                            success = self.set_valve_position(0)
                            if success:
                                print(f"[SAFETY] Valve closed to 0/4000")
                            break
                    elif not row or row[0] not in ('running', 'paused'):
                        # Session not found or in unexpected state
                        no_active_session_count += 1
                        if no_active_session_count > 300:  # 5 minutes (300 seconds)
                            print("[SAFETY] No active session for 5 minutes, stopping control")
                            self.control_active = False
                            self.set_valve_position(0)
                            break
                    elif row and row[0] == 'paused':
                        no_active_session_count = 0  # Reset counter
                        # Mark step as paused (if multi-step program)
                        if self.program_steps and self.current_step_index < len(self.program_steps):
                            if self.paused_time is None:
                                print("[CONTROL] Paused - tracking pause time for current step")
                                self.mark_paused()
                        else:
                            print("[CONTROL] Paused")
                        
                        # Wait while paused
                        while self.control_active:
                            cursor = self.conn.cursor()
                            cursor.execute(
                                "SELECT status FROM process_sessions WHERE id=%s",
                                (self.session_id,)
                            )
                            status = cursor.fetchone()[0]
                            cursor.close()
                            if status == 'running':
                                print("[CONTROL] Resumed")
                                # Mark as resumed (if multi-step program)
                                if self.program_steps and self.current_step_index < len(self.program_steps):
                                    self.mark_resumed()
                                    print(f"[CONTROL] Resumed - continuing from step {self.current_step_index + 1}/{len(self.program_steps)}")
                                break
                            elif status == 'stopped':
                                self.control_active = False
                                return
                            time.sleep(1)
                except Exception as e:
                    pass  # Continue if database check fails
            
            if self.end_time and get_ist_now().timestamp() >= self.end_time:
                # Time elapsed
                self.complete_session()
                break
            
            pressure = self.read_pressure()
            temperature = self.read_temperature()
            valve_position = self.read_valve_position()
            
            if pressure is None:
                time.sleep(1)
                continue
            
            # Update remaining time
            self.remaining_minutes = int((self.end_time - get_ist_now().timestamp()) / 60) + 1
            
            # Check for step completion (multi-step programs)
            if self.program_steps and self.current_step_index < len(self.program_steps):
                if self.check_step_completion():
                    self.advance_to_next_step()
            
            # Only control if session status is 'running'
            if self.conn and self.session_id:
                try:
                    cursor = self.conn.cursor()
                    cursor.execute(
                        "SELECT status FROM process_sessions WHERE id=%s",
                        (self.session_id,)
                    )
                    status = cursor.fetchone()[0]
                    cursor.close()
                    
                    if status == 'running':
                        no_active_session_count = 0  # Reset safety counter
                        # Control logic every 15 seconds
                        control_count += 1
                        if control_count >= CONTROL_INTERVAL:
                            control_count = 0
                            
                            pressure_diff = float(pressure) - float(self.target_pressure)
                            
                            if abs(pressure_diff) > PRESSURE_TOLERANCE:
                                if pressure_diff < 0:
             #                                    new_valve = min(self.valve_position - 200, MAX_VALVE_VALUE)
                                    new_valve = max(self.valve_position - 800, 0)
                                    
                                    success = self.set_valve_position(new_valve)
                                    if success:
                                        print(f"[CONTROL] Pressure low ({pressure:.1f}), decreasing valve to {new_valve}")
                                else:
                                    new_valve = min(self.valve_position + 800,MAX_VALVE_VALUE)
                                    success = self.set_valve_position(new_valve)
                                    if success:
            #                                        print(f"[CONTROL] Pressure high ({pressure:.1f}), increasing valve to {new_valve}")										
                                        print(f"[CONTROL] Pressure high ({pressure:.1f}), increasing valve to {new_valve}")
                    elif status == 'paused':
                        no_active_session_count = 0  # Reset counter (paused is valid)
                        print("[CONTROL] Paused - no valve adjustments")
                    else:
                        # Unexpected status - increment safety counter
                        no_active_session_count += 1
                        if no_active_session_count > 300:
                            print("[SAFETY] Session lost, stopping control and closing valve")
                            self.control_active = False
                            self.set_valve_position(0)
                            break
                except Exception as e:
                    pass  # Continue if check fails
            
            # Log to database
            self.save_process_log(pressure, temperature, valve_position)
            
            time.sleep(1)
    
    def complete_session(self):
        """Complete the current control session"""
        if self.conn and self.session_id:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "UPDATE process_sessions SET status='completed', end_time=%s WHERE id=%s",
                    (get_ist_now(), self.session_id)
                )
                self.conn.commit()
                cursor.close()
                print(f"[COMPLETE] Session {self.session_id} completed")
            except Exception as e:
                print(f"[ERROR] Completing session: {e}")
        
        # Stop buzzer thread and turn off buzzer
        if self.buzzer_thread and self.buzzer_thread.is_alive():
            self.buzzer_stop_event.set()
            self.buzzer_thread.join(timeout=2)  # Wait up to 2 seconds for thread to stop
            self.set_buzzer(False)
            print("[COMPLETE] Buzzer thread stopped and buzzer turned off")
        
        # Close valve to safe position
        self.set_valve_position(0)
        print(f"[SAFETY] Valve closed to 0/4000")
        
        self.control_active = False
        self.target_pressure = None
        self.session_id = None
    
    def run(self):
        """Main service loop"""
        print(f"\n{'='*60}")
        print("Sensor & Control Service")
        print(f"{'='*60}")
        print(f"COM Port: {self.com_port}")
        print(f"Reading sensors every {SENSOR_READ_INTERVAL} second")
        print(f"Control interval: {CONTROL_INTERVAL} seconds")
        print(f"{'='*60}\n")
        
        # Connect to PLC with retry logic
        print(f"[INFO] Attempting to connect to PLC on {self.com_port}...")
        if not self.connect_plc(retry=True):
            print(f"[ERROR] Failed to connect to PLC on {self.com_port}")
            print("Check cable connection and ensure PLC is powered")
            print("The service will continue trying to reconnect...")
        else:
            print(f"[OK] Connected to PLC on {self.com_port}\n")
        print("[INFO] Service ready. Waiting for frontend to start control...")
        print("       Or you can start control manually with API endpoints\n")
        print("[SAFETY] Control will auto-stop if no active sessions for 5 minutes\n")
        
        # Initialize valve to 0
        self.set_valve_position(0)
        
        reading_count = 0
        connection_check_counter = 0
        
        try:
            while True:
                # Periodically check connection status (every 10 readings)
                connection_check_counter += 1
                if connection_check_counter >= 10:
                    connection_check_counter = 0
                    if not self.is_connected:
                        print("[INFO] Device not connected, attempting to reconnect...")
                        self.connect_plc(retry=True)
                
                # Read sensors
                pressure = self.read_pressure()
                temperature = self.read_temperature()
                valve_position = self.read_valve_position()
                
                if pressure is not None and temperature is not None:
                    reading_count += 1
                    timestamp = get_ist_now().strftime("%H:%M:%S")
                    
                    # Save to database
                    self.save_sensor_reading(pressure, temperature)
                    
                    # Check for new sessions that need control (only when not already controlling)
                    if not self.control_active and self.conn:
                        try:
                            cursor = self.conn.cursor()
                            # Check for ANY running session (not just new ones)
                            cursor.execute(
                                "SELECT id, target_pressure, duration_minutes, program_name, steps_data FROM process_sessions WHERE status='running' AND target_pressure IS NOT NULL ORDER BY id DESC LIMIT 1"
                            )
                            row = cursor.fetchone()
                            cursor.close()
                            
                            if row:
                                session_id, target_pressure, duration_minutes, program_name, steps_data = row
                                
                                # Only start if this is a different session than we're tracking
                                if session_id != self.last_checked_session_id:
                                    print(f"\n[NEW SESSION] Detected session {session_id}")
                                    print(f"     Target: {float(target_pressure)} PSI")
                                    print(f"     Duration: {duration_minutes} minutes")
                                    if steps_data:
                                        print(f"     Type: Auto Program ({len(steps_data)} steps)")
                                    else:
                                        print(f"     Type: Manual Mode")
                                    self.last_checked_session_id = session_id
                                    # Pass session_id to prevent duplicate session creation
                                    self.start_control_session(float(target_pressure), int(duration_minutes), program_name, steps_data, existing_session_id=session_id)
                        except Exception as e:
                            pass  # Silent fail, continue reading
                    
                    # Display with control info
                    if self.control_active:
                        control_status = f" | Target: {self.target_pressure} PSI | Valve: {self.valve_position}/4000 | Time: {self.remaining_minutes} min"
                        print(f"[{timestamp}] Reading #{reading_count} - Pressure: {pressure} PSI, Temperature: {temperature}°C{control_status}")
                    else:
                        print(f"[{timestamp}] Reading #{reading_count} - Pressure: {pressure} PSI, Temperature: {temperature}°C")
                else:
                    # Connection issue - readings failed
                    if not self.is_connected:
                        timestamp = get_ist_now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] [WARNING] Cannot read sensors - device not connected. Retrying...")
                
                time.sleep(SENSOR_READ_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n\n[STOPPED] Service stopped by user")
        finally:
            if self.control_active:
                self.stop_control_session()
            if self.plc_client:
                try:
                    self.plc_client.close()
                except:
                    pass
            if self.conn:
                self.conn.close()
            print("\n[OK] Service stopped")


def main():
    """Main entry point"""
    print("="*60)
    print("Sensor & Control Service - Start Before Frontend")
    print("="*60)
    print("This service:")
    print("  [OK] Reads sensors from PLC every second")
    print("  [OK] Saves readings to PostgreSQL")
    print("  [OK] Controls valve for pressure control")
    print("  [OK] Logs all actions")
    print("="*60)
    
    service = SensorControlService()
    service.run()


if __name__ == "__main__":
    main()

