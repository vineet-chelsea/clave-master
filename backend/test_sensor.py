"""Quick test to verify sensor service configuration"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Environment Variables Test:")
print("=" * 50)
print(f"VITE_SUPABASE_URL: {os.getenv('VITE_SUPABASE_URL', 'NOT SET')}")
print(f"VITE_SUPABASE_PUBLISHABLE_KEY: {os.getenv('VITE_SUPABASE_PUBLISHABLE_KEY', 'NOT SET')[:50]}...")
print(f"COM_PORT: {os.getenv('COM_PORT', 'NOT SET')}")
print(f"BAUD_RATE: {os.getenv('BAUD_RATE', 'NOT SET')}")
print(f"SLAVE_ID: {os.getenv('SLAVE_ID', 'NOT SET')}")
print("=" * 50)

# Check if Supabase credentials exist
supabase_url = os.getenv('VITE_SUPABASE_URL', '')
supabase_key = os.getenv('VITE_SUPABASE_PUBLISHABLE_KEY', '')

if not supabase_url or not supabase_key:
    print("\n[ERROR] Missing Supabase credentials in .env file!")
    print("Make sure backend/.env contains:")
    print("  VITE_SUPABASE_URL=...")
    print("  VITE_SUPABASE_PUBLISHABLE_KEY=...")
else:
    print("\n[OK] Environment variables loaded successfully!")

