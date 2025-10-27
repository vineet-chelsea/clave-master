"""
Main Sensor and Control Service
Run this ONCE before starting the frontend
Handles all PLC communication and control logic
"""

import os
import time
import sys
from datetime import datetime
from pymodbus.client import ModbusSerialClient
from dotenv import load_dotenv
import psycopg2
import threading
import requests

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

# Scaling
PRESSURE_MIN = 0
PRESSURE_MAX = 4095
PRESSURE_OUTPUT_MIN = 0
PRESSURE_OUTPUT_MAX = 87

# Control parameters
CONTROL_INTERVAL = 15  # Check every 15 seconds
PRESSURE_TOLERANCE = 1
MAX_VALVE_VALUE = 4000

# PostgreSQL configuration
PG_HOST = os.getenv('PG_HOST', '127.0.0.1')
PG_PORT = os.getenv('PG_PORT', '5432')
PG_DATABASE = os.getenv('PG_DATABASE', 'autoclave')
PG_USER = os.getenv('PG_USER', 'postgres')
PG_PASSWORD = os.getenv('PG_PASSWORD', 'postgres')

# Sensor reading interval
SENSOR_READ_INTERVAL = 1


class SensorControlService:
    def __init__(self):
        """Initialize service"""
        # Initialize PLC client
        self.plc_client = ModbusSerialClient(
            port=COM_PORT,
            baudrate=BAUD_RATE,
            parity='N',
            stopbits=1,
            bytesize=8,
            timeout=TIMEOUT
        )
        self.slave_id = SLAVE_ID
        
        # Initialize PostgreSQL connection
        self.conn = None
        self.db_connect()
        
        # Control state
        self.control_active = False
        self.target_pressure = None
        self.remaining_minutes = 0
        self.valve_position = 0
        self.session_id = None
        self.end_time = None
        self.control_thread = None
        self.last_checked_session_id = None  # Track last session to avoid re-processing
        
        # Multi-step program state
        self.program_steps = []
        self.current_step_index = 0
        self.step_start_time = None
        self.step_pause_offset = 0  # Track time spent in pause
        self.paused_time = None  # When step was paused
        
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
        """Read current pressure from PLC"""
        try:
            result = self.plc_client.read_input_registers(
                PRESSURE_REGISTER,
                count=1,
                slave=self.slave_id
            )
            
            if result and not result.isError():
                raw_value = result.registers[0]
                return self.scale_pressure(raw_value)
            return None
        except Exception as e:
            return None
    
    def read_temperature(self):
        """Read current temperature from PLC"""
        try:
            result = self.plc_client.read_input_registers(
                TEMPERATURE_REGISTER,
                count=1,
                slave=self.slave_id
            )
            
            if result and not result.isError():
                raw_value = result.registers[0]
                temperature = 0 + (raw_value - 0) * (350 - 0) / (4095 - 0)
                return round(temperature, 2)
            return None
        except Exception as e:
            return None
    
    def read_valve_position(self):
        """Read current valve position"""
        try:
            result = self.plc_client.read_holding_registers(
                VALVE_CONTROL_REGISTER,
                count=1,
                slave=self.slave_id
            )
            
            if result and not result.isError():
                return result.registers[0]
            return None
        except Exception as e:
            return None
    
    def set_valve_position(self, value):
        """Set valve control register (0-4000)"""
        try:
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
            return False
    
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
                (pressure, temperature, datetime.now())
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
    
    def start_control_session(self, target_pressure, duration_minutes, program_name="Manual Control", steps_data=None):
        """Start a new control session"""
        if not self.conn:
            print("[ERROR] Database not connected")
            return False
        
        try:
            # Convert to proper types
            target_pressure = float(target_pressure)
            duration_minutes = int(duration_minutes)
            
            # Get existing session ID if session already exists (from API)
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id FROM process_sessions WHERE status='running' AND program_name=%s ORDER BY id DESC LIMIT 1",
                (program_name,)
            )
            result = cursor.fetchone()
            
            if result:
                # Use existing session
                self.session_id = result[0]
                print(f"[SESSION] Using existing session {self.session_id}")
            else:
                # Create new session
                cursor.execute(
                    "INSERT INTO process_sessions (program_name, status, start_time) VALUES (%s, %s, %s) RETURNING id",
                    (program_name, 'running', datetime.now())
                )
                self.session_id = cursor.fetchone()[0]
                print(f"[SESSION] Created new session {self.session_id}")
            
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
                print(f"[PROGRAM] Loaded {len(self.program_steps)} step program")
                print(f"[PROGRAM] Step 1/{len(self.program_steps)}: {self.target_pressure} PSI")
            else:
                # Manual mode - single step
                self.program_steps = []
                self.target_pressure = target_pressure
                self.current_step_index = 0
                self.step_start_time = None
            
            self.conn.commit()
            cursor.close()
            
            self.control_active = True
            self.target_pressure = target_pressure
            self.remaining_minutes = duration_minutes
            self.end_time = datetime.now().timestamp() + (duration_minutes * 60)
            
            # Start control thread
            self.control_thread = threading.Thread(target=self.control_loop, daemon=True)
            self.control_thread.start()
            
            print(f"[OK] Started control session {self.session_id}")
            print(f"     Target: {target_pressure} PSI")
            print(f"     Duration: {duration_minutes} minutes")
            print(f"     Control thread started")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to start session: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop_control_session(self):
        """Stop the current control session"""
        self.control_active = False
        
        # Close valve to safe position
        success = self.set_valve_position(0)
        if success:
            print(f"[SAFETY] Valve closed to 0/4000")
        
        if self.conn and self.session_id:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "UPDATE process_sessions SET status='stopped', end_time=%s WHERE id=%s",
                    (datetime.now(), self.session_id)
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
            
            if self.end_time and datetime.now().timestamp() >= self.end_time:
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
            self.remaining_minutes = int((self.end_time - datetime.now().timestamp()) / 60) + 1
            
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
                                    new_valve = min(self.valve_position + 200, MAX_VALVE_VALUE)
                                    success = self.set_valve_position(new_valve)
                                    if success:
                                        print(f"[CONTROL] Pressure low ({pressure:.1f}), increasing valve to {new_valve}")
                                else:
                                    new_valve = max(self.valve_position - 200, 0)
                                    success = self.set_valve_position(new_valve)
                                    if success:
                                        print(f"[CONTROL] Pressure high ({pressure:.1f}), decreasing valve to {new_valve}")
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
                    (datetime.now(), self.session_id)
                )
                self.conn.commit()
                cursor.close()
                print(f"[COMPLETE] Session {self.session_id} completed")
            except Exception as e:
                print(f"[ERROR] Completing session: {e}")
        
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
        print(f"COM Port: {COM_PORT}")
        print(f"Reading sensors every {SENSOR_READ_INTERVAL} second")
        print(f"Control interval: {CONTROL_INTERVAL} seconds")
        print(f"{'='*60}\n")
        
        # Connect to PLC
        if not self.plc_client.connect():
            print(f"[ERROR] Failed to connect to PLC on {COM_PORT}")
            print("Check cable connection and ensure PLC is powered")
            return
        
        print(f"[OK] Connected to PLC on {COM_PORT}\n")
        print("[INFO] Service ready. Waiting for frontend to start control...")
        print("       Or you can start control manually with API endpoints\n")
        print("[SAFETY] Control will auto-stop if no active sessions for 5 minutes\n")
        
        # Initialize valve to 0
        self.set_valve_position(0)
        
        reading_count = 0
        
        try:
            while True:
                # Read sensors
                pressure = self.read_pressure()
                temperature = self.read_temperature()
                valve_position = self.read_valve_position()
                
                if pressure is not None and temperature is not None:
                    reading_count += 1
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
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
                                    self.start_control_session(float(target_pressure), int(duration_minutes), program_name, steps_data)
                        except Exception as e:
                            pass  # Silent fail, continue reading
                    
                    # Display with control info
                    if self.control_active:
                        control_status = f" | Target: {self.target_pressure} PSI | Valve: {self.valve_position}/4000 | Time: {self.remaining_minutes} min"
                        print(f"[{timestamp}] Reading #{reading_count} - Pressure: {pressure} PSI, Temperature: {temperature}°C{control_status}")
                    else:
                        print(f"[{timestamp}] Reading #{reading_count} - Pressure: {pressure} PSI, Temperature: {temperature}°C")
                
                time.sleep(SENSOR_READ_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n\n[STOPPED] Service stopped by user")
        finally:
            if self.control_active:
                self.stop_control_session()
            self.plc_client.close()
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

