"""
Integrated Sensor Reading and Pressure Control Service
Combines sensor monitoring with pressure control in one service
"""

import os
import time
import sys
from datetime import datetime
from pymodbus.client import ModbusSerialClient
from dotenv import load_dotenv
import psycopg2
import threading

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

# PostgreSQL configuration
PG_HOST = os.getenv('PG_HOST', '127.0.0.1')
PG_PORT = os.getenv('PG_PORT', '5432')
PG_DATABASE = os.getenv('PG_DATABASE', 'autoclave')
PG_USER = os.getenv('PG_USER', 'postgres')
PG_PASSWORD = os.getenv('PG_PASSWORD', 'postgres')

# Sensor reading interval
SENSOR_READ_INTERVAL = 1  # Read every second


class IntegratedService:
    def __init__(self):
        """Initialize integrated service"""
        # Initialize PLC client (shared connection)
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
        
        # State
        self.control_active = False
        self.target_pressure = None
        self.valve_position = 0
        self.control_thread = None
        
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
            return False
    
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
    
    def save_process_log(self, session_id, pressure, temperature, valve_position):
        """Save process log to database"""
        if not self.conn:
            return
            
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO process_logs (session_id, program_name, pressure, temperature, valve_position, status) VALUES (%s, %s, %s, %s, %s, %s)",
                (session_id, 'Active Session', pressure, temperature, valve_position, 'running')
            )
            self.conn.commit()
            cursor.close()
        except Exception as e:
            pass
    
    def control_pressure_loop(self, target_pressure, duration_minutes, session_id):
        """Pressure control loop in background thread"""
        end_time = datetime.now().timestamp() + (duration_minutes * 60)
        control_count = 0
        
        print(f"[CONTROL] Starting control loop: {target_pressure} PSI for {duration_minutes} min")
        
        while datetime.now().timestamp() < end_time and self.control_active:
            pressure = self.read_pressure()
            
            if pressure is None:
                time.sleep(1)
                continue
            
            # Control logic every 15 seconds
            control_count += 1
            if control_count >= 30:
                control_count = 0
                
                pressure_diff = pressure - target_pressure
                
                if abs(pressure_diff) > 1:  # Tolerance ±1 PSI
                    if pressure_diff < 0:  # Too low
                        new_valve = min(self.valve_position + 200, 4000)
                        self.set_valve_position(new_valve)
                        print(f"[CONTROL] Pressure low ({pressure:.1f}), increasing valve to {new_valve}")
                    else:  # Too high
                        new_valve = max(self.valve_position - 200, 0)
                        self.set_valve_position(new_valve)
                        print(f"[CONTROL] Pressure high ({pressure:.1f}), decreasing valve to {new_valve}")
            
            time.sleep(1)
        
        print(f"[CONTROL] Control loop completed")
        
        # Mark session as completed
        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "UPDATE process_sessions SET status='completed', end_time=%s WHERE id=%s",
                    (datetime.now(), session_id)
                )
                self.conn.commit()
                cursor.close()
            except:
                pass
    
    def start_control(self, target_pressure, duration_minutes):
        """Start pressure control"""
        if self.control_active:
            print("[WARNING] Control already active")
            return
        
        # Create session
        session_id = None
        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO process_sessions (program_name, status, start_time) VALUES (%s, %s, %s) RETURNING id",
                    ('Manual Control', 'running', datetime.now())
                )
                session_id = cursor.fetchone()[0]
                self.conn.commit()
                cursor.close()
                print(f"[OK] Created session: {session_id}")
            except Exception as e:
                print(f"[ERROR] Failed to create session: {e}")
        
        self.control_active = True
        self.target_pressure = target_pressure
        
        # Start control thread
        self.control_thread = threading.Thread(
            target=self.control_pressure_loop,
            args=(target_pressure, duration_minutes, session_id)
        )
        self.control_thread.daemon = True
        self.control_thread.start()
    
    def stop_control(self):
        """Stop pressure control"""
        self.control_active = False
        print("[OK] Stopping control")
    
    def run(self):
        """Main service loop"""
        print(f"\n{'='*60}")
        print("Integrated Sensor & Control Service")
        print(f"{'='*60}")
        print(f"Reading sensors every {SENSOR_READ_INTERVAL} second")
        print(f"{'='*60}\n")
        
        # Connect to PLC
        if not self.plc_client.connect():
            print(f"[ERROR] Failed to connect to PLC on {COM_PORT}")
            return
        
        print(f"[OK] Connected to PLC on {COM_PORT}\n")
        
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
                    
                    # Display
                    valve_info = f" | Valve: {valve_position}/4000" if valve_position is not None else ""
                    control_info = f" | Target: {self.target_pressure} PSI" if self.control_active else ""
                    
                    print(f"[{timestamp}] Reading #{reading_count} - Pressure: {pressure} PSI, Temperature: {temperature}°C{valve_info}{control_info}")
                
                time.sleep(SENSOR_READ_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n[STOPPED] Service stopped by user")
        finally:
            self.control_active = False
            self.plc_client.close()
            if self.conn:
                self.conn.close()
            print("\n[OK] Service stopped")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Integrated Sensor & Control Service')
    parser.add_argument('--pressure', type=float, help='Target pressure in PSI')
    parser.add_argument('--duration', type=int, help='Duration in minutes')
    parser.add_argument('--control', action='store_true', help='Enable pressure control')
    
    args = parser.parse_args()
    
    service = IntegratedService()
    
    if args.control and args.pressure and args.duration:
        print(f"[INFO] Starting control: {args.pressure} PSI for {args.duration} minutes")
        service.start_control(args.pressure, args.duration)
    
    service.run()


if __name__ == "__main__":
    main()

