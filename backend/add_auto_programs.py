"""
Script to add auto programs to the database
"""
import os
import sys
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

# Database connection parameters
DB_HOST = os.getenv('PG_HOST', 'localhost')
DB_PORT = os.getenv('PG_PORT', '5432')
DB_NAME = os.getenv('PG_DATABASE', 'autoclave')
DB_USER = os.getenv('PG_USER', 'postgres')
DB_PASSWORD = os.getenv('PG_PASSWORD', '')

def connect_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print(f"[OK] Connected to PostgreSQL database '{DB_NAME}'")
        return conn
    except Exception as e:
        print(f"[ERROR] Failed to connect to database: {e}")
        sys.exit(1)

def add_programs():
    """Add auto programs to the database"""
    conn = connect_db()
    cur = conn.cursor()
    
    try:
        # Check if programs already exist
        cur.execute("SELECT COUNT(*) FROM autoclave_programs")
        count = cur.fetchone()[0]
        
        if count > 0:
            print(f"[OK] Found {count} existing programs - skipping addition")
            conn.close()
            return
        
        print("[INFO] No programs found - adding programs...")
        
        # Define programs
        programs = [
            {
                'program_number': 1,
                'program_name': 'Hypalon Polymers',
                'description': 'Standard curing process for Hypalon polymers',
                'steps': [
                    {'psi_range': '5-10', 'duration_minutes': 15, 'action': 'raise'},
                    {'psi_range': '10', 'duration_minutes': 75, 'action': 'steady'},
                    {'psi_range': '20-25', 'duration_minutes': 15, 'action': 'raise'},
                    {'psi_range': '20-25', 'duration_minutes': 30, 'action': 'steady'},
                    {'psi_range': '40-45', 'duration_minutes': 15, 'action': 'raise'},
                    {'psi_range': '40-45', 'duration_minutes': 120, 'action': 'steady'}
                ]
            },
            {
                'program_number': 2,
                'program_name': 'Test Program',
                'description': 'Quick 6-minute test program for validation',
                'steps': [
                    {'psi_range': '5-10', 'duration_minutes': 1, 'action': 'raise'},
                    {'psi_range': '10', 'duration_minutes': 1, 'action': 'steady'},
                    {'psi_range': '20-25', 'duration_minutes': 1, 'action': 'raise'},
                    {'psi_range': '20-25', 'duration_minutes': 1, 'action': 'steady'},
                    {'psi_range': '40-45', 'duration_minutes': 1, 'action': 'raise'},
                    {'psi_range': '40-45', 'duration_minutes': 1, 'action': 'steady'}
                ]
            },
            {
                'program_number': 3,
                'program_name': 'SBR (Solid Roll) Pickling-2 Rolls',
                'description': 'Pickling process for SBR solid rolls',
                'steps': [
                    {'psi_range': '0-5', 'duration_minutes': 15, 'action': 'raise'},
                    {'psi_range': '5', 'duration_minutes': 45, 'action': 'steady'},
                    {'psi_range': '15', 'duration_minutes': 15, 'action': 'raise'},
                    {'psi_range': '15', 'duration_minutes': 45, 'action': 'steady'},
                    {'psi_range': '40', 'duration_minutes': 15, 'action': 'raise'},
                    {'psi_range': '40', 'duration_minutes': 270, 'action': 'steady'}
                ]
            },
            {
                'program_number': 4,
                'program_name': 'PLTCM STL Roll (XNBR)',
                'description': 'Processing for PLTCM STL rolls using XNBR',
                'steps': [
                    {'psi_range': '5-10', 'duration_minutes': 15, 'action': 'raise'},
                    {'psi_range': '10', 'duration_minutes': 20, 'action': 'steady'},
                    {'psi_range': '40-45', 'duration_minutes': 30, 'action': 'raise'},
                    {'psi_range': '40-45', 'duration_minutes': 360, 'action': 'steady'}
                ]
            },
            {
                'program_number': 5,
                'program_name': 'Neoprene Polymers Rolls',
                'description': 'Processing for Neoprene polymers',
                'steps': [
                    {'psi_range': '5-10', 'duration_minutes': 15, 'action': 'raise'},
                    {'psi_range': '10', 'duration_minutes': 75, 'action': 'steady'},
                    {'psi_range': '20-25', 'duration_minutes': 15, 'action': 'raise'},
                    {'psi_range': '25', 'duration_minutes': 30, 'action': 'steady'},
                    {'psi_range': '40-45', 'duration_minutes': 15, 'action': 'raise'},
                    {'psi_range': '40-45', 'duration_minutes': 150, 'action': 'steady'}
                ]
            },
            {
                'program_number': 6,
                'program_name': 'Sleeve - 20mm Thickness',
                'description': 'Sleeve processing for 20mm thickness',
                'steps': [
                    {'psi_range': '3', 'duration_minutes': 60, 'action': 'steady'},
                    {'psi_range': '30', 'duration_minutes': 15, 'action': 'raise'},
                    {'psi_range': '30', 'duration_minutes': 150, 'action': 'steady'}
                ]
            },
            {
                'program_number': 7,
                'program_name': 'Sleeve - 50-60mm Thickness',
                'description': 'Sleeve processing for 50-60mm thickness',
                'steps': [
                    {'psi_range': '3', 'duration_minutes': 60, 'action': 'steady'},
                    {'psi_range': '30', 'duration_minutes': 15, 'action': 'raise'},
                    {'psi_range': '30', 'duration_minutes': 360, 'action': 'steady'}
                ]
            },
            {
                'program_number': 8,
                'program_name': 'NBR/SBR Polymers - 1-3 Rolls',
                'description': 'Processing for 1-3 rolls of NBR/SBR polymers',
                'steps': [
                    {'psi_range': '0-5', 'duration_minutes': 15, 'action': 'raise'},
                    {'psi_range': '5-10', 'duration_minutes': 45, 'action': 'steady'},
                    {'psi_range': '10-20', 'duration_minutes': 15, 'action': 'raise'},
                    {'psi_range': '20-30', 'duration_minutes': 15, 'action': 'raise'},
                    {'psi_range': '30-40', 'duration_minutes': 15, 'action': 'raise'},
                    {'psi_range': '45', 'duration_minutes': 150, 'action': 'steady'}
                ]
            },
            {
                'program_number': 9,
                'program_name': 'NBR/SBR Polymers - 4+ Rolls',
                'description': 'Processing for 4 or more rolls of NBR/SBR polymers',
                'steps': [
                    {'psi_range': '0-5', 'duration_minutes': 15, 'action': 'raise'},
                    {'psi_range': '5-10', 'duration_minutes': 45, 'action': 'steady'},
                    {'psi_range': '10-20', 'duration_minutes': 15, 'action': 'raise'},
                    {'psi_range': '20-30', 'duration_minutes': 15, 'action': 'raise'},
                    {'psi_range': '30-40', 'duration_minutes': 15, 'action': 'raise'},
                    {'psi_range': '45', 'duration_minutes': 180, 'action': 'steady'}
                ]
            }
        ]
        
        # Insert all programs
        for program_data in programs:
            cur.execute("""
                INSERT INTO autoclave_programs 
                (program_number, program_name, description, steps)
                VALUES (%s, %s, %s, %s::jsonb)
                RETURNING id
            """, (
                program_data['program_number'],
                program_data['program_name'],
                program_data['description'],
                str(program_data['steps']).replace("'", '"')
            ))
            
            program_id = cur.fetchone()[0]
            print(f"[OK] Added program: {program_data['program_name']}")
            print(f"     Program ID: {program_id}")
            print(f"     Total steps: {len(program_data['steps'])}")
            print()
        
        conn.commit()
        
        # Summary
        print("="*60)
        print("PROGRAM SUMMARY:")
        print("="*60)
        for program_data in programs:
            print(f"\n{program_data['program_name']} (P{program_data['program_number']:02d})")
            print("-" * 60)
            for i, step in enumerate(program_data['steps'], 1):
                print(f"{i}. {step['psi_range']} PSI - {step['duration_minutes']} min ({step['action']})")
        print("="*60)
        
    except Exception as e:
        print(f"[ERROR] Failed to add programs: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    add_programs()
    print("\n[OK] Auto programs setup complete!")

