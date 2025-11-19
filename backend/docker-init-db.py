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
        
        # Drop all existing tables in correct order (handle foreign key constraints)
        print("[INFO] Dropping existing tables to create fresh database...")
        
        tables_to_drop = [
            'process_logs',      # Has FK to process_sessions
            'process_sessions',
            'sensor_readings',
            'autoclave_programs',
            'roll_categories'
        ]
        
        for table in tables_to_drop:
            if check_table_exists(cursor, table):
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                print(f"[OK] Dropped {table} table")
        
        # Commit the drops
        conn.commit()
        
        print("[INFO] Creating fresh tables...")
        
        # Create sensor_readings table
        cursor.execute("""
            CREATE TABLE sensor_readings (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
                pressure NUMERIC(6,2) NOT NULL,
                temperature NUMERIC(6,2) NOT NULL
            );
        """)
        
        cursor.execute("""
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
                steps_data JSONB,
                roll_category_name TEXT,
                sub_roll_name TEXT,
                roll_id TEXT,
                operator_name TEXT,
                number_of_rolls INTEGER
            );
        """)
        
        cursor.execute("""
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
        """)
        
        cursor.execute("""
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
                roll_category_name TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        cursor.execute("""
            CREATE INDEX idx_program_number 
            ON autoclave_programs(program_number);
        """)
        
        print("[OK] Created autoclave_programs table")
        
        # Create roll_categories table
        cursor.execute("""
            CREATE TABLE roll_categories (
                id SERIAL PRIMARY KEY,
                category_name TEXT UNIQUE NOT NULL,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        print("[OK] Created roll_categories table")
        
        # Insert 25 predefined roll categories (reference data only)
        roll_categories = [
            "TSL ECL ROLL (NBR)",
            "CGL-2 Alkali Roll (NBR)",
            "TCIL Damming Roll (NBR)",
            "TATA Bluescop Roll",
            "TCIL ECL Roll",
            "PLTCM Tension Lever Roll",
            "XNBR Roll",
            "Pickling-2 (Solid Roll)",
            "Hypalon Roll",
            "Sink Roll 1000 dia. Roll",
            "Deflector Roll 1000 dia. Roll",
            "TSDPL 600 dia. Roll",
            "RSP Sink Roll",
            "KPO Dipping Roll",
            "PLTCM Dryer Support Roll",
            "Snubber Roll",
            "TSL DAM Roll",
            "Pulley",
            "MS Pipe",
            "SLEEVE 20 mm Lining",
            "SLEEVE 40-45 mm Lining",
            "SLEEVE 50-60 mm Lining",
            "Sleeve Mandrel",
            "JSW Roll",
            "Other Roll"
        ]
        
        for category in roll_categories:
            cursor.execute("""
                INSERT INTO roll_categories (category_name)
                VALUES (%s)
            """, (category,))
        
        print(f"[OK] Inserted {len(roll_categories)} roll categories (reference data)")
        
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

