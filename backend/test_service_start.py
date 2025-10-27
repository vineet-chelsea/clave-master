"""
Test script to verify service can start control sessions
"""

import requests
import time

API_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{API_URL}/api/health", timeout=5)
        print(f"Health check: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_start_control():
    """Test starting control"""
    try:
        response = requests.post(
            f"{API_URL}/api/start-control",
            json={
                'target_pressure': 20,
                'duration_minutes': 5
            },
            timeout=10
        )
        print(f"Start control: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Start control failed: {e}")
        return False

def main():
    print("="*60)
    print("Testing Service API")
    print("="*60)
    
    # Wait a bit for service to start
    print("\nWaiting 5 seconds for service to be ready...")
    time.sleep(5)
    
    # Test health
    print("\n1. Testing health endpoint...")
    if not test_health():
        print("Service not responding!")
        return
    
    # Test start control
    print("\n2. Testing start control...")
    if not test_start_control():
        print("Failed to start control!")
        return
    
    print("\n" + "="*60)
    print("All tests passed!")
    print("="*60)

if __name__ == "__main__":
    main()

