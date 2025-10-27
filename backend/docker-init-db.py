"""
Initialize PostgreSQL database with tables for Docker deployment
"""

import psycopg2
import os
import sys
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def check_table_exists(cursor, table_name):
    """Check if a table exists in the database"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_name = %s
        );
    """, (table_name,))
    return cursor.fetchone()[0]

def init_database():
    """Initialize database tables"""
    
    # Database connection parameters from environment
    DB_HOST = os.getenv('PG_HOST', 'postgres')
    DB_PORT = os.getenv('PG_PORT', '5432')
    DB_NAME = os.getenv('PG_DATABASE', 'autoclave')
    DB_USER = os.getenv('PG_USER', 'postgres')
    DB_PASSWORD = os.getenv('PG_PASSWORD', 'postgres')
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        cursor = conn.cursor()
        
        print("[OK] Connected to database")
        
        # Check if tables already exist
        tables_exist = (
            check_table_exists(cursor, 'sensor_readings') and
            check_table_exists(cursor, 'process_sessions') and
            check_table_exists(cursor, 'process_logs') and
            check_table_exists(cursor, 'autoclave_programs')
        )
        
        if tables_exist:
            print("[OK] Database tables already exist - skipping initialization")
            cursor.close()
            conn.close()
            return True
        
        print("[INFO] Tables not found - initializing database...")
        
        # Create sensor_readings table
        cursor.execute("""
            CREATE TABLE sensor_readings (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
                pressure NUMERIC(6,2) NOT NULL,
                temperature NUMERIC(6,2) NOT NULL
            );
            
            CREATE INDEX idx_sensor_timestamp 
            ON sensor_readings(timestamp DESC);
        """)
        
        print("[OK] Created sensor_readings table")
        
        # Create process_sessions table
        cursor.execute("""
            CREATE TABLE process_sessions (
                id SERIAL PRIMARY KEY,
                program_name TEXT,
                status TEXT DEFAULT 'running',
                start_time TIMESTAMP DEFAULT NOW(),
                end_time TIMESTAMP,
                target_pressure NUMERIC(6,2),
                duration_minutes INTEGER,
                steps_data JSONB
            );
            
            CREATE INDEX idx_sessions_status 
            ON process_sessions(status);
        """)
        
        print("[OK] Created process_sessions table")
        
        # Create process_logs table
        cursor.execute("""
            CREATE TABLE process_logs (
                id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES process_sessions(id),
                program_name TEXT,
                timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
                pressure NUMERIC(6,2),
                temperature NUMERIC(6,2),
                valve_position INTEGER,
                status TEXT
            );
            
            CREATE INDEX idx_logs_session 
            ON process_logs(session_id, timestamp);
        """)
        
        print("[OK] Created process_logs table")
        
        # Create autoclave_programs table
        cursor.execute("""
            CREATE TABLE autoclave_programs (
                id SERIAL PRIMARY KEY,
                program_number INTEGER NOT NULL UNIQUE,
                program_name VARCHAR(255) NOT NULL,
                description TEXT,
                steps JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            CREATE INDEX idx_program_number 
            ON autoclave_programs(program_number);
        """)
        
        print("[OK] Created autoclave_programs table")
        
        # Commit changes
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n[OK] Database initialization complete!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("="*60)
    print("Database Initialization for Docker")
    print("="*60)
    init_database()

