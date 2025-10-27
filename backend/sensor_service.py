"""
Modbus PLC Sensor Reading Service
Continuously reads pressure and temperature from PLC and stores in PostgreSQL
"""

import os
import time
import sys
from datetime import datetime
from pymodbus.client import ModbusSerialClient
from dotenv import load_dotenv
import psycopg2

# Load environment variables from .env file
load_dotenv()

# PostgreSQL configuration
PG_HOST = os.getenv('PG_HOST', 'localhost')
PG_PORT = os.getenv('PG_PORT', '5432')
PG_DATABASE = os.getenv('PG_DATABASE', 'autoclave')
PG_USER = os.getenv('PG_USER', 'postgres')
PG_PASSWORD = os.getenv('PG_PASSWORD', 'postgres')

# Modbus configuration
COM_PORT = os.getenv('COM_PORT', 'COM10')
BAUD_RATE = int(os.getenv('BAUD_RATE', '9600'))
SLAVE_ID = int(os.getenv('SLAVE_ID', '1'))
TIMEOUT = 2

# Register addresses
PRESSURE_REGISTER = 68 # Address for pressure reading
TEMPERATURE_REGISTER = 69  # Address for temperature reading

# Scaling factors
PRESSURE_MIN = 0  # Minimum raw value
PRESSURE_MAX = 4095  # Maximum raw value
PRESSURE_OUTPUT_MIN = 0  # Minimum output in PSI
PRESSURE_OUTPUT_MAX = 87  # Maximum output in PSI

TEMPERATURE_MIN = 0  # Minimum raw value
TEMPERATURE_MAX = 4095  # Maximum raw value
TEMPERATURE_OUTPUT_MIN = 0  # Minimum output in degrees
TEMPERATURE_OUTPUT_MAX = 350  # Maximum output in degrees

# Reading interval (seconds)
READ_INTERVAL = 5  # Read every 1 second


class SensorReader:
    def __init__(self):
        """Initialize Modbus PLC client and Supabase client"""
        # Initialize Modbus client (matching your working configuration)
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
            print("[INFO] Will continue reading sensors but won't save to database")
            self.conn = None
    
    def connect_plc(self):
        """Establish connection with PLC"""
        try:
            if self.plc_client.connect():
                print(f"[OK] Connected to PLC on {COM_PORT}")
                return True
            else:
                print(f"[ERROR] Failed to connect to PLC on {COM_PORT}")
                return False
        except Exception as e:
            print(f"[ERROR] Exception connecting to PLC: {e}")
            return False
    
    def disconnect_plc(self):
        """Close PLC connection"""
        try:
            self.plc_client.close()
            print("[OK] Disconnected from PLC")
        except Exception as e:
            print(f"Error disconnecting from PLC: {e}")
    
    def scale_value(self, raw_value, min_in, max_in, min_out, max_out):
        """Scale raw value from input range to output range"""
        if raw_value is None:
            return None
        
        # Linear scaling: output = min_out + (raw - min_in) * (max_out - min_out) / (max_in - min_in)
        scaled = min_out + (raw_value - min_in) * (max_out - min_out) / (max_in - min_in)
        
        # Clamp to output range
        scaled = max(min_out, min(scaled, max_out))
        
        return round(scaled, 2)
    
    def read_pressure(self):
        """Read pressure from PLC register 70"""
        try:
            result = self.plc_client.read_input_registers(
                PRESSURE_REGISTER, 
                count=1,
                slave=self.slave_id
            )
            
            if result and not result.isError():
                raw_value = result.registers[0]
                # Scale from 0-4095 to 0-87 PSI
                pressure_psi = self.scale_value(
                    raw_value, 
                    PRESSURE_MIN, PRESSURE_MAX,
                    PRESSURE_OUTPUT_MIN, PRESSURE_OUTPUT_MAX
                )
                return pressure_psi
            else:
                if result:
                    print(f"Error reading pressure register {PRESSURE_REGISTER}: {result}")
                return None
        except Exception as e:
            print(f"Exception reading pressure: {e}")
            return None
    
    def read_temperature(self):
        """Read temperature from PLC register 69"""
        try:
            result = self.plc_client.read_input_registers(
                TEMPERATURE_REGISTER, 
                count=1,
                slave=self.slave_id
            )
            
            if result and not result.isError():
                raw_value = result.registers[0]
                # Scale from 0-4095 to 0-350 degrees
                temperature = self.scale_value(
                    raw_value, 
                    TEMPERATURE_MIN, TEMPERATURE_MAX,
                    TEMPERATURE_OUTPUT_MIN, TEMPERATURE_OUTPUT_MAX
                )
                return temperature
            else:
                if result:
                    print(f"Error reading temperature register {TEMPERATURE_REGISTER}: {result}")
                return None
        except Exception as e:
            print(f"Exception reading temperature: {e}")
            return None
    
    def save_to_postgres(self, pressure, temperature):
        """Save sensor readings to PostgreSQL"""
        if not self.conn:
            return False
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO sensor_readings (pressure, temperature, timestamp) VALUES (%s, %s, %s)",
                (pressure, temperature, datetime.now())
            )
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            # Silently fail - PostgreSQL not available
            return False
    
    def run_continuous(self):
        """Continuously read sensors and save to database"""
        print(f"\n{'='*60}")
        print("Starting Continuous Sensor Reading Service")
        print(f"{'='*60}")
        print(f"Reading interval: {READ_INTERVAL} seconds")
        print(f"Pressure register: {PRESSURE_REGISTER} (0-4095 → 0-87 PSI)")
        print(f"Temperature register: {TEMPERATURE_REGISTER} (0-4095 → 0-350°C)")
        print(f"{'='*60}\n")
        
        if not self.connect_plc():
            print("Failed to connect to PLC. Exiting.")
            return
        
        reading_count = 0
        
        try:
            while True:
                # Read sensors
                pressure = self.read_pressure()
                temperature = self.read_temperature()
                
                if pressure is not None and temperature is not None:
                    # Save to PostgreSQL
                    success = self.save_to_postgres(pressure, temperature)
                    
                    if success:
                        reading_count += 1
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] Reading #{reading_count} - Pressure: {pressure} PSI, Temperature: {temperature}°C [OK]")
                    else:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Failed to save reading")
                else:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] Failed to read sensors")
                
                # Wait before next reading
                time.sleep(READ_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n\nStopping sensor reading service...")
        except Exception as e:
            print(f"\nFatal error in continuous loop: {e}")
        finally:
            self.disconnect_plc()
            print("Sensor reading service stopped.")


def main():
    """Main entry point"""
    print("="*60)
    print("Modbus PLC Sensor Service")
    print("="*60)
    print(f"PostgreSQL: {PG_HOST}:{PG_PORT}/{PG_DATABASE}")
    print(f"Modbus: {COM_PORT}, {BAUD_RATE} baud, Slave ID {SLAVE_ID}")
    print("="*60)
    
    # Create and run sensor reader
    reader = SensorReader()
    reader.run_continuous()


if __name__ == "__main__":
    main()

