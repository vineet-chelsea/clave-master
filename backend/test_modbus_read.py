"""Quick test to verify Modbus reading works"""
from pymodbus.client import ModbusSerialClient
import os
from dotenv import load_dotenv

load_dotenv()

COM_PORT = os.getenv('COM_PORT', 'COM10')
BAUD_RATE = int(os.getenv('BAUD_RATE', '9600'))
SLAVE_ID = int(os.getenv('SLAVE_ID', '1'))

print("="*60)
print("Testing Modbus Read")
print("="*60)
print(f"COM Port: {COM_PORT}")
print(f"Baud Rate: {BAUD_RATE}")
print(f"Slave ID: {SLAVE_ID}")
print("="*60)

# Create client
client = ModbusSerialClient(
    port=COM_PORT,
    baudrate=BAUD_RATE,
    parity='N',
    stopbits=1,
    bytesize=8,
    timeout=2
)

# Connect
if not client.connect():
    print("[ERROR] Failed to connect to PLC")
    exit(1)

print("[OK] Connected to PLC\n")

# Test reading temperature from register 69
print("Testing Register 69 (Temperature)...")
try:
    result = client.read_input_registers(69, count=1, slave=SLAVE_ID)
    if result and not result.isError():
        print(f"[OK] Register 69: {result.registers[0]}")
    else:
        print(f"[ERROR] Reading register 69: {result}")
except Exception as e:
    print(f"[ERROR] Exception: {e}")

# Test reading pressure from register 70
print("\nTesting Register 70 (Pressure)...")
try:
    result = client.read_input_registers(70, count=1, slave=SLAVE_ID)
    if result and not result.isError():
        print(f"[OK] Register 70: {result.registers[0]}")
    else:
        print(f"[ERROR] Reading register 70: {result}")
except Exception as e:
    print(f"[ERROR] Exception: {e}")

client.close()
print("\n[OK] Test complete")

