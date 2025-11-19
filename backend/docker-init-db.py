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
            print("[OK] Core database tables already exist")
            print("[INFO] Verifying and migrating schema if needed...")
        else:
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
            CREATE TABLE IF NOT EXISTS process_sessions (
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
            
            CREATE INDEX IF NOT EXISTS idx_sessions_status 
            ON process_sessions(status);
        """)
        
        print("[OK] Created/verified process_sessions table")
        
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
            CREATE TABLE IF NOT EXISTS autoclave_programs (
                id SERIAL PRIMARY KEY,
                program_number INTEGER NOT NULL UNIQUE,
                program_name VARCHAR(255) NOT NULL,
                description TEXT,
                steps JSONB NOT NULL,
                roll_category_name TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_program_number 
            ON autoclave_programs(program_number);
        """)
        
        print("[OK] Created/verified autoclave_programs table")
        
        # Add roll_category_name column if it doesn't exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'autoclave_programs' 
            AND column_name = 'roll_category_name'
        """)
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE autoclave_programs ADD COLUMN roll_category_name TEXT")
            print("[OK] Added roll_category_name to autoclave_programs")
        
        # Create roll_categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roll_categories (
                id SERIAL PRIMARY KEY,
                category_name TEXT UNIQUE NOT NULL,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        print("[OK] Created/verified roll_categories table")
        
        # Insert 25 predefined roll categories
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
                ON CONFLICT (category_name) DO NOTHING
            """, (category,))
        
        print(f"[OK] Inserted {len(roll_categories)} roll categories")
        
        # Always check and add missing columns to process_sessions (migration)
        print("[INFO] Checking and adding missing columns to process_sessions...")
        new_columns = [
            ('roll_category_name', 'TEXT'),
            ('sub_roll_name', 'TEXT'),
            ('roll_id', 'TEXT'),
            ('operator_name', 'TEXT'),
            ('number_of_rolls', 'INTEGER')
        ]
        
        for col_name, col_type in new_columns:
            try:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'process_sessions' 
                    AND column_name = %s
                """, (col_name,))
                if cursor.fetchone() is None:
                    cursor.execute(f"ALTER TABLE process_sessions ADD COLUMN {col_name} {col_type}")
                    conn.commit()  # Commit immediately after each column addition
                    print(f"[OK] Added {col_name} to process_sessions")
                else:
                    print(f"[OK] Column {col_name} already exists in process_sessions")
            except Exception as e:
                print(f"[ERROR] Failed to add column {col_name}: {e}")
                raise  # Re-raise to fail the initialization
        
        # Always check and add missing columns to autoclave_programs (migration)
        print("[INFO] Checking and adding missing columns to autoclave_programs...")
        try:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'autoclave_programs' 
                AND column_name = 'roll_category_name'
            """)
            if cursor.fetchone() is None:
                cursor.execute("ALTER TABLE autoclave_programs ADD COLUMN roll_category_name TEXT")
                conn.commit()  # Commit immediately
                print("[OK] Added roll_category_name to autoclave_programs")
            else:
                print("[OK] Column roll_category_name already exists in autoclave_programs")
        except Exception as e:
            print(f"[ERROR] Failed to add roll_category_name to autoclave_programs: {e}")
            raise  # Re-raise to fail the initialization
        
        # Commit changes
        conn.commit()
        
        # Verify all required columns exist in process_sessions
        print("[INFO] Verifying all columns exist in process_sessions...")
        required_columns = ['roll_category_name', 'sub_roll_name', 'roll_id', 'operator_name', 'number_of_rolls']
        for col_name in required_columns:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'process_sessions' 
                AND column_name = %s
            """, (col_name,))
            if cursor.fetchone() is None:
                print(f"[ERROR] Column {col_name} is missing from process_sessions after migration!")
                cursor.close()
                conn.close()
                return False
            else:
                print(f"[OK] Verified column {col_name} exists")
        
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
    success = init_database()
    if not success:
        print("\n[FATAL] Database initialization failed. Exiting...")
        sys.exit(1)
    sys.exit(0)

