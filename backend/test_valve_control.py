"""Test valve control register writing"""
from pymodbus.client import ModbusSerialClient
import time
from dotenv import load_dotenv
import os

load_dotenv()

COM_PORT = os.getenv('COM_PORT', 'COM10')
BAUD_RATE = int(os.getenv('BAUD_RATE', '9600'))
SLAVE_ID = int(os.getenv('SLAVE_ID', '1'))

VALVE_REGISTER = 51

def test_valve_write():
    """Test writing to valve control register"""
    print("="*60)
    print("Valve Control Test")
    print("="*60)
    print(f"COM Port: {COM_PORT}")
    print(f"Baud Rate: {BAUD_RATE}")
    print(f"Slave ID: {SLAVE_ID}")
    print(f"Register: {VALVE_REGISTER}")
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
        print(f"[ERROR] Failed to connect to PLC on {COM_PORT}")
        return
    
    print(f"[OK] Connected to PLC on {COM_PORT}\n")
    
    # Test values
    test_values = [0, 1000, 2000, 3000, 4000]
    
    for value in test_values:
        print(f"Setting valve to {value}/4000...")
        
        # Write
        result = client.write_register(
            VALVE_REGISTER,
            value,
            slave=SLAVE_ID
        )
        
        if result.isError():
            print(f"  [ERROR] Write failed: {result}")
        else:
            print(f"  [OK] Write successful")
        
        time.sleep(0.5)
        
        # Verify by reading back
        read_result = client.read_holding_registers(
            VALVE_REGISTER,
            count=1,
            slave=SLAVE_ID
        )
        
        if read_result and not read_result.isError():
            actual = read_result.registers[0]
            print(f"  [OK] Verified: Register contains {actual}")
        else:
            print(f"  [WARNING] Could not read back")
        
        print()
    
    print("Test complete")
    client.close()

if __name__ == "__main__":
    test_valve_write()

