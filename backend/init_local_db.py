"""
Initialize local database for Autoclave system
Run this once to set up the database
"""

import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

# PostgreSQL configuration
DB_HOST = os.getenv('PG_HOST', '127.0.0.1')
DB_PORT = os.getenv('PG_PORT', '5432')
DB_NAME = os.getenv('PG_DATABASE', 'autoclave')
DB_USER = os.getenv('PG_USER', 'postgres')
DB_PASSWORD = os.getenv('PG_PASSWORD', 'postgres')

def init_database():
    """Initialize database tables"""
    print("=" * 60)
    print("Database Initialization for Local Setup")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        
        print("[OK] Connected to PostgreSQL")
        
        # Create sensor_readings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
                pressure NUMERIC(6,2) NOT NULL,
                temperature NUMERIC(6,2) NOT NULL
            );
            
            CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp 
            ON sensor_readings(timestamp DESC);
        """)
        
        print("[OK] Created sensor_readings table")
        
        # Create process_sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS process_sessions (
                id SERIAL PRIMARY KEY,
                program_name TEXT,
                status TEXT DEFAULT 'running',
                start_time TIMESTAMP DEFAULT NOW(),
                end_time TIMESTAMP,
                target_pressure NUMERIC(6,2),
                duration_minutes INTEGER,
                steps_data JSONB
            );
            
            CREATE INDEX IF NOT EXISTS idx_sessions_status 
            ON process_sessions(status);
        """)
        
        print("[OK] Created process_sessions table")
        
        # Create process_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS process_logs (
                id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES process_sessions(id),
                program_name TEXT,
                timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
                pressure NUMERIC(6,2),
                temperature NUMERIC(6,2),
                valve_position INTEGER,
                status TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_logs_session 
            ON process_logs(session_id, timestamp);
        """)
        
        print("[OK] Created process_logs table")
        
        # Create autoclave_programs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS autoclave_programs (
                id SERIAL PRIMARY KEY,
                program_number INTEGER NOT NULL UNIQUE,
                program_name VARCHAR(255) NOT NULL,
                description TEXT,
                steps JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_program_number 
            ON autoclave_programs(program_number);
        """)
        
        print("[OK] Created autoclave_programs table")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n[OK] Database initialization complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False
    
    return True

if __name__ == "__main__":
    success = init_database()
    if success:
        print("\nYou can now start the backend services:")
        print("  Terminal 1: python sensor_control_service.py")
        print("  Terminal 2: python api_server.py")
    else:
        print("\nFailed to initialize database. Check the error above.")
        exit(1)

