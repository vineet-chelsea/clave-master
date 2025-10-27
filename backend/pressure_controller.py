"""
Pressure Controller Service
Monitors pressure and controls valve to maintain target pressure
"""

import os
import time
import sys
from datetime import datetime
from pymodbus.client import ModbusSerialClient
from dotenv import load_dotenv
import psycopg2

load_dotenv()

# Modbus configuration
COM_PORT = os.getenv('COM_PORT', 'COM10')
BAUD_RATE = int(os.getenv('BAUD_RATE', '9600'))
SLAVE_ID = int(os.getenv('SLAVE_ID', '1'))
TIMEOUT = 2

# Register addresses
PRESSURE_REGISTER = 70      # Read current pressure (0-4095 → 0-87 PSI)
TEMPERATURE_REGISTER = 69   # Read current temperature
VALVE_CONTROL_REGISTER = 51  # Control valve opening (0-4000)

# Scaling
PRESSURE_MIN = 0
PRESSURE_MAX = 4095
PRESSURE_OUTPUT_MIN = 0
PRESSURE_OUTPUT_MAX = 87

# Control parameters
CONTROL_INTERVAL = 15  # Check and adjust every 15 seconds
PRESSURE_TOLERANCE = 1  # +/- 1 PSI acceptable
MAX_VALVE_VALUE = 4000  # Maximum valve opening

# PostgreSQL configuration
PG_HOST = os.getenv('PG_HOST', '127.0.0.1')
PG_PORT = os.getenv('PG_PORT', '5432')
PG_DATABASE = os.getenv('PG_DATABASE', 'autoclave')
PG_USER = os.getenv('PG_USER', 'postgres')
PG_PASSWORD = os.getenv('PG_PASSWORD', 'postgres')


class PressureController:
    def __init__(self, target_pressure, duration_minutes, session_name="Manual Control", plc_client=None):
        self.target_pressure = target_pressure
        self.duration_minutes = duration_minutes
        self.session_name = session_name
        self.start_time = datetime.now()
        
        # Use provided PLC client or create new one
        if plc_client:
            self.plc_client = plc_client
            print("[INFO] Using existing PLC connection")
        else:
            self.plc_client = ModbusSerialClient(
                port=COM_PORT,
                baudrate=BAUD_RATE,
                parity='N',
                stopbits=1,
                bytesize=8,
                timeout=TIMEOUT
            )
        
        self.slave_id = SLAVE_ID
        self.owns_connection = plc_client is None
        
        # Initialize PostgreSQL connection
        self.conn = None
        self.session_id = None
        self.db_connect()
        
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
            self.create_session()
        except Exception as e:
            print(f"[WARNING] Failed to connect to PostgreSQL: {e}")
            
    def create_session(self):
        """Create a new process session in database"""
        if not self.conn:
            return
            
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO process_sessions (program_name, status, start_time) VALUES (%s, %s, %s) RETURNING id",
                (self.session_name, 'running', datetime.now())
            )
            self.session_id = cursor.fetchone()[0]
            self.conn.commit()
            cursor.close()
            print(f"[OK] Created session: {self.session_id}")
        except Exception as e:
            print(f"[ERROR] Failed to create session: {e}")
    
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
                pressure_psi = self.scale_pressure(raw_value)
                return pressure_psi
            return None
        except Exception as e:
            print(f"[ERROR] Reading pressure: {e}")
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
                # Scale from 0-4095 to 0-350
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
            if result.isError():
                print(f"[ERROR] Writing valve control: {result}")
                return False
            print(f"[OK] Set valve to {value}/4000")
            return True
        except Exception as e:
            print(f"[ERROR] Writing valve control: {e}")
            return False
    
    def log_reading(self, pressure, temperature, valve_position):
        """Log sensor reading to database"""
        if not self.conn:
            return
            
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO process_logs (session_id, program_name, pressure, temperature, valve_position, status) VALUES (%s, %s, %s, %s, %s, %s)",
                (self.session_id, self.session_name, pressure, temperature, valve_position, 'running')
            )
            self.conn.commit()
            cursor.close()
        except Exception as e:
            pass  # Silent fail
    
    def control_pressure(self):
        """Main control loop"""
        print(f"\n{'='*60}")
        print("Pressure Control System")
        print(f"{'='*60}")
        print(f"Target Pressure: {self.target_pressure} PSI")
        print(f"Duration: {self.duration_minutes} minutes")
        print(f"Tolerance: ±{PRESSURE_TOLERANCE} PSI")
        print(f"Control Interval: {CONTROL_INTERVAL} seconds")
        print(f"{'='*60}\n")
        
        # Connect to PLC
        if not self.plc_client.connect():
            print(f"[ERROR] Failed to connect to PLC on {COM_PORT}")
            return
        
        print(f"[OK] Connected to PLC on {COM_PORT}")
        
        # Initialize valve
        valve_position = 0
        if not self.set_valve_position(valve_position):
            print("[WARNING] Could not initialize valve")
        
        print(f"[OK] Initialized valve position: {valve_position}/4000\n")
        
        end_time = datetime.now().timestamp() + (self.duration_minutes * 60)
        control_count = 0
        
        try:
            while datetime.now().timestamp() < end_time:
                # Read current sensors
                pressure = self.read_pressure()
                temperature = self.read_temperature()
                valve_read = self.read_valve_position()
                
                if pressure is None:
                    time.sleep(1)
                    continue
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                remaining_minutes = int((end_time - datetime.now().timestamp()) / 60)
                
                # Display current status
                print(f"[{timestamp}] Pressure: {pressure} PSI / Target: {self.target_pressure} PSI | Valve: {valve_read}/4000 | Time left: {remaining_minutes} min")
                
                # Log to database
                self.log_reading(pressure, temperature, valve_position)
                
                # Check if adjustment needed (every 15 seconds)
                control_count += 1
                if control_count >= CONTROL_INTERVAL:
                    control_count = 0
                    
                    pressure_diff = pressure - self.target_pressure
                    
                    if abs(pressure_diff) > PRESSURE_TOLERANCE:
                        # Adjust valve
                        if pressure_diff < 0:  # Too low, increase valve
                            valve_position = min(valve_position + 200, MAX_VALVE_VALUE)
                            print(f"[CONTROL] Pressure low ({pressure:.1f} < {self.target_pressure:.1f}), increasing valve to {valve_position}")
                        else:  # Too high, decrease valve
                            valve_position = max(valve_position - 200, 0)
                            print(f"[CONTROL] Pressure high ({pressure:.1f} > {self.target_pressure:.1f}), decreasing valve to {valve_position}")
                        
                        self.set_valve_position(valve_position)
                    else:
                        print(f"[OK] Pressure within tolerance ({pressure:.1f} ± {PRESSURE_TOLERANCE} PSI)")
                
                time.sleep(1)  # Read every second, control every 15 seconds
            
            # Process complete
            print(f"\n[COMPLETE] Target pressure reached for {self.duration_minutes} minutes")
            
            if self.conn:
                cursor = self.conn.cursor()
                cursor.execute(
                    "UPDATE process_sessions SET status='completed', end_time=%s WHERE id=%s",
                    (datetime.now(), self.session_id)
                )
                self.conn.commit()
                cursor.close()
            
        except KeyboardInterrupt:
            print("\n[STOPPED] Process terminated by user")
            
            if self.conn:
                cursor = self.conn.cursor()
                cursor.execute(
                    "UPDATE process_sessions SET status='stopped', end_time=%s WHERE id=%s",
                    (datetime.now(), self.session_id)
                )
                self.conn.commit()
                cursor.close()
        except Exception as e:
            print(f"[ERROR] Control loop error: {e}")
            raise
        finally:
            # Only close connection if we own it
            if self.owns_connection:
                self.plc_client.close()
                print("\n[OK] Disconnected from PLC")
            if self.conn:
                self.conn.close()


def main():
    if len(sys.argv) < 3:
        print("Usage: python pressure_controller.py <target_pressure> <duration_minutes>")
        print("Example: python pressure_controller.py 20 30")
        sys.exit(1)
    
    target_pressure = float(sys.argv[1])
    duration_minutes = int(sys.argv[2])
    
    controller = PressureController(target_pressure, duration_minutes)
    controller.control_pressure()


if __name__ == "__main__":
    main()

