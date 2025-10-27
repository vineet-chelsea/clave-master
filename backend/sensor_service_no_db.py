"""
Modbus PLC Sensor Reading Service - No Database Required
Continuously reads pressure and temperature from PLC
Stores readings in CSV file instead of database
"""

import os
import time
import sys
import csv
from datetime import datetime
from pymodbus.client import ModbusSerialClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Modbus configuration
COM_PORT = os.getenv('COM_PORT', 'COM10')
BAUD_RATE = int(os.getenv('BAUD_RATE', '9600'))
SLAVE_ID = int(os.getenv('SLAVE_ID', '1'))
TIMEOUT = 2

# Register addresses
PRESSURE_REGISTER = 68
TEMPERATURE_REGISTER = 69

# Scaling factors
PRESSURE_MIN = 0
PRESSURE_MAX = 4095
PRESSURE_OUTPUT_MIN = 0
PRESSURE_OUTPUT_MAX = 87

TEMPERATURE_MIN = 0
TEMPERATURE_MAX = 4095
TEMPERATURE_OUTPUT_MIN = 0
TEMPERATURE_OUTPUT_MAX = 350

# Reading interval (seconds)
READ_INTERVAL = 1

# CSV file for storing readings
CSV_FILE = 'sensor_readings.csv'


class SensorReader:
    def __init__(self):
        """Initialize Modbus PLC client"""
        self.plc_client = ModbusSerialClient(
            port=COM_PORT,
            baudrate=BAUD_RATE,
            parity='N',
            stopbits=1,
            bytesize=8,
            timeout=TIMEOUT
        )
        self.slave_id = SLAVE_ID
        self.initialize_csv()
    
    def initialize_csv(self):
        """Initialize CSV file with headers"""
        try:
            if not os.path.exists(CSV_FILE):
                with open(CSV_FILE, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['timestamp', 'pressure', 'temperature'])
        except Exception as e:
            print(f"Warning: Could not initialize CSV file: {e}")
    
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
        
        scaled = min_out + (raw_value - min_in) * (max_out - min_out) / (max_in - min_in)
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
                pressure_psi = self.scale_value(
                    raw_value, 
                    PRESSURE_MIN, PRESSURE_MAX,
                    PRESSURE_OUTPUT_MIN, PRESSURE_OUTPUT_MAX
                )
                return pressure_psi
            else:
                return None
        except Exception as e:
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
                temperature = self.scale_value(
                    raw_value, 
                    TEMPERATURE_MIN, TEMPERATURE_MAX,
                    TEMPERATURE_OUTPUT_MIN, TEMPERATURE_OUTPUT_MAX
                )
                return temperature
            else:
                return None
        except Exception as e:
            return None
    
    def save_to_csv(self, pressure, temperature):
        """Save sensor readings to CSV file"""
        try:
            with open(CSV_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    pressure,
                    temperature
                ])
            return True
        except Exception as e:
            return False
    
    def run_continuous(self):
        """Continuously read sensors and save to CSV"""
        print(f"\n{'='*60}")
        print("Starting Sensor Reading Service (CSV Mode)")
        print(f"{'='*60}")
        print(f"Reading interval: {READ_INTERVAL} seconds")
        print(f"Pressure register: {PRESSURE_REGISTER} (0-4095 → 0-87 PSI)")
        print(f"Temperature register: {TEMPERATURE_REGISTER} (0-4095 → 0-350°C)")
        print(f"Data file: {CSV_FILE}")
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
                    # Save to CSV
                    success = self.save_to_csv(pressure, temperature)
                    
                    reading_count += 1
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    status = "[SAVED]" if success else "[DISPLAY ONLY]"
                    print(f"[{timestamp}] Reading #{reading_count} - Pressure: {pressure} PSI, Temperature: {temperature}°C {status}")
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
            print(f"Sensor reading service stopped. Data saved to {CSV_FILE}")


def main():
    """Main entry point"""
    print("="*60)
    print("Modbus PLC Sensor Service (No Database Required)")
    print("="*60)
    print("Readings will be saved to CSV file")
    print(f"Modbus: {COM_PORT}, {BAUD_RATE} baud, Slave ID {SLAVE_ID}")
    print("="*60)
    
    reader = SensorReader()
    reader.run_continuous()


if __name__ == "__main__":
    main()

