"""
Add all 25 roll programs to database based on spreadsheet data
Includes quantity-dependent steps for applicable rolls
"""
import os
import sys
import json
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

def ensure_roll_category(cursor, category_name):
    """Ensure a roll category exists in the roll_categories table"""
    cursor.execute("""
        INSERT INTO roll_categories (category_name, is_active)
        VALUES (%s, true)
        ON CONFLICT (category_name) DO UPDATE SET is_active = true
        RETURNING id
    """, (category_name,))
    return cursor.fetchone()[0]

def add_all_programs():
    """Add all 25 roll programs to database"""
    conn = connect_db()
    cur = conn.cursor()
    
    # Define all 25 programs based on images
    programs = [
        {
            'roll_category_name': 'TSL ECL ROLL (NBR)',
            'program_name': 'TSL ECL ROLL (NBR) Program',
            'description': 'Autoclave program for TSL ECL ROLL (NBR)',
            'base_steps': [
                {'psi_range': '0-5', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '5-10', 'duration_minutes': 45, 'action': 'steady'},
                {'psi_range': '10-20', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '20-30', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '30-40', 'duration_minutes': 15, 'action': 'raise'}
           #     {'psi_range': '40-45', 'duration_minutes': 150, 'action': 'steady'}   2 Hrs. 30 Mins.
            ],
            'quantity_variations': {
                '1-3': {
                    'final_step': {'psi_range': '45-45', 'duration_minutes': 150, 'action': 'steady'}  # 2 Hrs. 30 Mins.
                },
                '4+': {
                    'final_step': {'psi_range': '45-45', 'duration_minutes': 180, 'action': 'steady'}  # 3 Hrs.
                }
            }
        },
        {
            'roll_category_name': 'CGL-2 Alkali Roll (NBR)',
            'program_name': 'CGL-2 Alkali Roll (NBR) Program',
            'description': 'Autoclave program for CGL-2 Alkali Roll (NBR)',
            'base_steps': [
                {'psi_range': '0-5', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '5-10', 'duration_minutes': 45, 'action': 'steady'},
                {'psi_range': '10-20', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '20-30', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '30-40', 'duration_minutes': 15, 'action': 'raise'}
  #              {'psi_range': '40-45', 'duration_minutes': 150, 'action': 'steady'}  # 2 Hrs. 30 Mins.
            ],
            'quantity_variations': {
                '1-3': {
                    'final_step': {'psi_range': '45-45', 'duration_minutes': 150, 'action': 'steady'}  # 2 Hrs. 30 Mins.
                },
                '4+': {
                    'final_step': {'psi_range': '45-45', 'duration_minutes': 180, 'action': 'steady'}  # 3 Hrs.
                }
            }
        },
        {
            'roll_category_name': 'TCIL Damming Roll (NBR)',
            'program_name': 'TCIL Damming Roll (NBR) Program',
            'description': 'Autoclave program for TCIL Damming Roll (NBR)',
            'base_steps': [
                {'psi_range': '0-5', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '5-10', 'duration_minutes': 45, 'action': 'steady'},
                {'psi_range': '10-20', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '20-30', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '30-40', 'duration_minutes': 15, 'action': 'raise'}
      #          {'psi_range': '40-45', 'duration_minutes': 150, 'action': 'steady'}  # 2 Hrs. 30 Mins.
            ],
            'quantity_variations': {
                '1-3': {
                    'final_step': {'psi_range': '45-45', 'duration_minutes': 150, 'action': 'steady'}  # 2 Hrs. 30 Mins.
                },
                '4+': {
                    'final_step': {'psi_range': '45-45', 'duration_minutes': 180, 'action': 'steady'}  # 3 Hrs.
                }
            }
        },
        {
            'roll_category_name': 'TATA Bluescop Roll',
            'program_name': 'TATA Bluescop Roll Program',
            'description': 'Autoclave program for TATA Bluescop Roll',
            'base_steps': [
                {'psi_range': '0-5', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '5-10', 'duration_minutes': 45, 'action': 'steady'},
                {'psi_range': '10-20', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '20-30', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '30-40', 'duration_minutes': 15, 'action': 'raise'}
               # {'psi_range': '40-45', 'duration_minutes': 150, 'action': 'steady'}  # 2 Hrs. 30 Mins.
            ],
            'quantity_variations': {
                '1-3': {
                    'final_step': {'psi_range': '45-45', 'duration_minutes': 150, 'action': 'steady'}  # 2 Hrs. 30 Mins.
                },
                '4+': {
                    'final_step': {'psi_range': '45-45', 'duration_minutes': 180, 'action': 'steady'}  # 3 Hrs.
                }
            }
        },
        {
            'roll_category_name': 'TCIL ECL Roll',
            'program_name': 'TCIL ECL Roll Program',
            'description': 'Autoclave program for TCIL ECL Roll',
            'base_steps': [
                {'psi_range': '0-5', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '5-10', 'duration_minutes': 45, 'action': 'steady'},
                {'psi_range': '10-20', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '20-30', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '30-40', 'duration_minutes': 15, 'action': 'raise'}
       #         {'psi_range': '40-45', 'duration_minutes': 150, 'action': 'steady'}  # 2 Hrs. 30 Mins.
            ],
            'quantity_variations': {
                '1-3': {
                    'final_step': {'psi_range': '45-45', 'duration_minutes': 150, 'action': 'steady'}  # 2 Hrs. 30 Mins.
                },
                '4+': {
                    'final_step': {'psi_range': '45-45', 'duration_minutes': 180, 'action': 'steady'}  # 3 Hrs.
                }
            }
        },
        {
            'roll_category_name': 'PLTCM Tension Lever Roll',
            'program_name': 'PLTCM Tension Lever Roll Program',
            'description': 'Autoclave program for PLTCM Tension Lever Roll',
            'base_steps': [
                {'psi_range': '0-5', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '5-10', 'duration_minutes': 45, 'action': 'steady'},
                {'psi_range': '10-20', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '20-30', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '30-40', 'duration_minutes': 15, 'action': 'raise'}
             #   {'psi_range': '40-45', 'duration_minutes': 150, 'action': 'steady'}  # 2 Hrs. 30 Mins.
            ],
            'quantity_variations': {
                '1-3': {
                    'final_step': {'psi_range': '45-45', 'duration_minutes': 150, 'action': 'steady'}  # 2 Hrs. 30 Mins.
                },
                '4+': {
                    'final_step': {'psi_range': '45-45', 'duration_minutes': 180, 'action': 'steady'}  # 3 Hrs.
                }
            }
        },
        {
            'roll_category_name': 'XNBR Roll',
            'program_name': 'XNBR Roll Program',
            'description': 'Autoclave program for XNBR Roll',
            'base_steps': [
                {'psi_range': '5-10', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '10', 'duration_minutes': 20, 'action': 'steady'},  # Raise to 40-451
                {'psi_range': '40-45', 'duration_minutes': 30, 'action': 'raise'},
                 {'psi_range': '40-45', 'duration_minutes': 180, 'action': 'raise'} # Steady at 40-45, 6 Hrs.
            ],
            'quantity_variations': {
              
            }
        },
        {
            'roll_category_name': 'Pickling Line (Solid Roll)',
            'program_name': 'Pickling-2 (Solid Roll) Program',
            'description': 'Autoclave program for Pickling-2 (Solid Roll)',
            'base_steps': [
                {'psi_range': '0-5', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '5', 'duration_minutes': 45, 'action': 'steady'},  # Steady at 5
                {'psi_range': '15', 'duration_minutes': 15, 'action': 'raise'},  # Raise to 15
                {'psi_range': '15', 'duration_minutes': 45, 'action': 'steady'},  # Steady at 15
                {'psi_range': '40', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '40-40', 'duration_minutes': 270, 'action': 'steady'}# Raise to 40
            ],
            'quantity_variations': {
            }
        },
        {
            'roll_category_name': 'Hypalon Roll',
            'program_name': 'Hypalon Roll Program',
            'description': 'Autoclave program for Hypalon Roll',
            'base_steps': [
                {'psi_range': '5-10', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '10', 'duration_minutes': 75, 'action': 'steady'},  # Steady at 10, 1 Hr 15 Mins.
                {'psi_range': '20-25', 'duration_minutes': 15, 'action': 'raise'},  # Raise to 20-25
                {'psi_range': '20-25', 'duration_minutes': 30, 'action': 'steady'},  # Steady at 20-25
                {'psi_range': '40-45', 'duration_minutes': 15, 'action': 'raise'},  # Raise to 40-45
                {'psi_range': '40-45', 'duration_minutes': 120, 'action': 'steady'}  # Steady at 40-45, 2 Hrs.
            ],
            'quantity_variations': {}  # No quantity variations for Hypalon
        },
        {
            'roll_category_name': 'Sink Roll 1000 dia. Roll',
            'program_name': 'Sink Roll 1000 dia. Roll Program',
            'description': 'Autoclave program for Sink Roll 1000 dia. Roll',
            'base_steps': [
                {'psi_range': '0-5', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '5-10', 'duration_minutes': 45, 'action': 'steady'},
                {'psi_range': '10-20', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '20-30', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '30-40', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '40-45', 'duration_minutes': 210, 'action': 'steady'}  # 3 Hrs. 30 Mins.
            ],
            'quantity_variations': {}
        },
        {
            'roll_category_name': 'Deflector Roll 1000 dia. Roll',
            'program_name': 'Deflector Roll 1000 dia. Roll Program',
            'description': 'Autoclave program for Deflector Roll 1000 dia. Roll',
            'base_steps': [
                {'psi_range': '0-5', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '5-10', 'duration_minutes': 45, 'action': 'steady'},
                {'psi_range': '10-20', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '20-30', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '30-40', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '40-45', 'duration_minutes': 210, 'action': 'steady'}  # 3 Hrs. 30 Mins.
            ],
            'quantity_variations': {}
        },
        {
            'roll_category_name': 'TSDPL 600 dia. Roll',
            'program_name': 'TSDPL 600 dia. Roll Program',
            'description': 'Autoclave program for TSDPL 600 dia. Roll',
            'base_steps': [
                {'psi_range': '0-5', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '5-10', 'duration_minutes': 45, 'action': 'steady'},
                {'psi_range': '10-20', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '20-30', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '30-40', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '40-45', 'duration_minutes': 180, 'action': 'steady'}  # 3 Hrs.
            ],
            'quantity_variations': {}
        },
        {
            'roll_category_name': 'RSP Sink Roll',
            'program_name': 'RSP Sink Roll Program',
            'description': 'Autoclave program for RSP Sink Roll',
            'base_steps': [
                {'psi_range': '0-5', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '5-10', 'duration_minutes': 45, 'action': 'steady'},
                {'psi_range': '10-20', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '20-30', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '30-40', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '40-45', 'duration_minutes': 180, 'action': 'steady'}  # 3 Hrs.
            ],
            'quantity_variations': {}
        },
        {
            'roll_category_name': 'KPO Dipping Roll',
            'program_name': 'KPO Dipping Roll Program',
            'description': 'Autoclave program for KPO Dipping Roll',
            'base_steps': [
                {'psi_range': '0-5', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '5-10', 'duration_minutes': 45, 'action': 'steady'},
                {'psi_range': '10-20', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '20-30', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '30-40', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '40-45', 'duration_minutes': 180, 'action': 'steady'}  # 3 Hrs.
            ],
            'quantity_variations': {}
        },
        {
            'roll_category_name': 'PLTCM Dryer Support Roll',
            'program_name': 'PLTCM Dryer Support Roll Program',
            'description': 'Autoclave program for PLTCM Dryer Support Roll',
            'base_steps': [
                {'psi_range': '0-5', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '5-10', 'duration_minutes': 30, 'action': 'steady'},
                {'psi_range': '10-20', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '20-30', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '30-40', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '40-45', 'duration_minutes': 120, 'action': 'steady'}  # 2 Hrs.
            ],
            'quantity_variations': {}
        },
        {
            'roll_category_name': 'Snubber Roll',
            'program_name': 'Snubber Roll Program',
            'description': 'Autoclave program for Snubber Roll',
            'base_steps': [
                {'psi_range': '0-5', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '5-10', 'duration_minutes': 30, 'action': 'steady'},
                {'psi_range': '10-20', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '20-30', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '30-40', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '40-45', 'duration_minutes': 120, 'action': 'steady'}  # 2 Hrs.
            ],
            'quantity_variations': {}
        },
        {
            'roll_category_name': 'TSL DAM Roll',
            'program_name': 'TSL DAM Roll Program',
            'description': 'Autoclave program for TSL DAM Roll',
            'base_steps': [
                {'psi_range': '5-10', 'duration_minutes': 60, 'action': 'raise'},  # 1 Hr.
                {'psi_range': '15-20', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '20-25', 'duration_minutes': 240, 'action': 'steady'}  # 4 Hrs.
            ],
            'quantity_variations': {}
        },
        {
            'roll_category_name': 'Pulley',
            'program_name': 'Pulley Program',
            'description': 'Autoclave program for Pulley',
            'base_steps': [
                {'psi_range': '5-10', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '10', 'duration_minutes': 20, 'action': 'steady'},  # Steady at 10
                {'psi_range': '30-35', 'duration_minutes': 45, 'action': 'raise'},  # Raise to 30-35
                {'psi_range': '40-45', 'duration_minutes': 120, 'action': 'steady'}  # Steady at 40-45, 2 Hrs.
            ],
            'quantity_variations': {}
        },
        {
            'roll_category_name': 'MS Pipe',
            'program_name': 'MS Pipe Program',
            'description': 'Autoclave program for MS Pipe',
            'base_steps': [
                {'psi_range': '5-10', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '10', 'duration_minutes': 20, 'action': 'steady'},  # Steady at 10
                {'psi_range': '30-35', 'duration_minutes': 45, 'action': 'raise'},  # Raise to 30-35
                {'psi_range': '40-45', 'duration_minutes': 120, 'action': 'steady'}  # Steady at 40-45, 2 Hrs.
            ],
            'quantity_variations': {}
        },
        {
            'roll_category_name': 'SLEEVE 20 mm Lining',
            'program_name': 'SLEEVE 20 mm Lining Program',
            'description': 'Autoclave program for SLEEVE 20 mm Lining',
            'base_steps': [
                {'psi_range': '3', 'duration_minutes': 60, 'action': 'steady'},  # 3 phr, 1 Hr.
                {'psi_range': '30', 'duration_minutes': 15, 'action': 'raise'},  # Raise to 30 phr
                {'psi_range': '30', 'duration_minutes': 150, 'action': 'steady'}  # Stay at 30 phr, 2 Hrs. 30 Mins.
            ],
            'quantity_variations': {}
        },
        {
            'roll_category_name': 'SLEEVE 40-45 mm Lining',
            'program_name': 'SLEEVE 40-45 mm Lining Program',
            'description': 'Autoclave program for SLEEVE 40-45 mm Lining',
            'base_steps': [
                {'psi_range': '3', 'duration_minutes': 60, 'action': 'steady'},  # 3 phr, 1 Hr.
                {'psi_range': '30', 'duration_minutes': 15, 'action': 'raise'},  # Raise to 30 phr
                {'psi_range': '30', 'duration_minutes': 300, 'action': 'steady'}  # Stay at 30 phr, 5 Hrs.
            ],
            'quantity_variations': {}
        },
        {
            'roll_category_name': 'SLEEVE 50-60 mm Lining',
            'program_name': 'SLEEVE 50-60 mm Lining Program',
            'description': 'Autoclave program for SLEEVE 50-60 mm Lining',
            'base_steps': [
                {'psi_range': '3', 'duration_minutes': 60, 'action': 'steady'},  # 3 phr, 1 Hr.
                {'psi_range': '30', 'duration_minutes': 15, 'action': 'raise'},  # Raise to 30 phr
                {'psi_range': '30', 'duration_minutes': 360, 'action': 'steady'}  # Stay at 30 phr, 6 Hrs.
            ],
            'quantity_variations': {}
        },
        {
            'roll_category_name': 'Sleeve Mandrel',
            'program_name': 'Sleeve Mandrel Program',
            'description': 'Autoclave program for Sleeve Mandrel',
            'base_steps': [
                {'psi_range': '5-10', 'duration_minutes': 60, 'action': 'raise'},  # 05-Oct (5-10), 1 Hr.
                {'psi_range': '15-20', 'duration_minutes': 30, 'action': 'raise'},
                {'psi_range': '30', 'duration_minutes': 180, 'action': 'steady'}  # 3 Hrs.
            ],
            'quantity_variations': {}
        },
        {
            'roll_category_name': 'JSW Roll',
            'program_name': 'JSW 700 Dia. Roll Program',
            'description': 'Autoclave program for JSW 700 Dia. Roll',
            'base_steps': [
                {'psi_range': '5-10', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '10', 'duration_minutes': 75, 'action': 'steady'},  # Steady at 10, 1 Hr 15 Mins.
                {'psi_range': '20-25', 'duration_minutes': 15, 'action': 'raise'},  # Raise to 20-25
                {'psi_range': '20-25', 'duration_minutes': 30, 'action': 'steady'},  # Steady at 20-25
                {'psi_range': '40-45', 'duration_minutes': 15, 'action': 'raise'},  # Raise to 40-45
                {'psi_range': '40-45', 'duration_minutes': 150, 'action': 'steady'}  # Steady at 40-45, 2 Hrs. 30 Mins.
            ],
            'quantity_variations': {}
        },
        {
            'roll_category_name': 'Other Roll',
            'program_name': 'Other Roll Program',
            'description': 'Autoclave program for Other Roll',
            'base_steps': [
                {'psi_range': '0-5', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '5-10', 'duration_minutes': 45, 'action': 'steady'},
                {'psi_range': '10-20', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '20-30', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '30-40', 'duration_minutes': 15, 'action': 'raise'},
                {'psi_range': '40-45', 'duration_minutes': 150, 'action': 'steady'}  # 2 Hrs. 30 Mins.
            ],
            'quantity_variations': {
                '1-3': {
                    'final_step': {'psi_range': '45-45', 'duration_minutes': 150, 'action': 'steady'}  # 2 Hrs. 30 Mins.
                },
                '4+': {
                    'final_step': {'psi_range': '45-45', 'duration_minutes': 180, 'action': 'steady'}  # 3 Hrs.
                }
            }
        },
        {
            'roll_category_name': 'Test Program',
            'program_name': 'Test Program',
            'description': 'Quick test program - 0.1 minutes at 1 PSI for testing purposes',
            'base_steps': [
                {'psi_range': '1', 'duration_minutes': 0.1, 'action': 'steady'}
            ],
            'quantity_variations': {}  # No quantity variations for test program
        }
    ]
    
    print("="*60)
    print("Adding All 25 Roll Programs + Test Program to Database")
    print("="*60)
    print(f"Total programs to add: {len(programs)}\n")
    
    imported = 0
    updated = 0
    
    for idx, program in enumerate(programs, 1):
        roll_category_name = program['roll_category_name']
        program_name = program['program_name']
        description = program['description']
        base_steps = program['base_steps']
        quantity_variations = program.get('quantity_variations', {})
        
        # Ensure roll category exists in roll_categories table
        ensure_roll_category(cur, roll_category_name)
        
        # Build steps structure
        if quantity_variations:
            steps_structure = {
                'base_steps': base_steps,
                'quantity_variations': quantity_variations
            }
        else:
            steps_structure = base_steps
        
        # Check if program already exists
        cur.execute("""
            SELECT id, program_number FROM autoclave_programs
            WHERE roll_category_name = %s OR program_name = %s
            LIMIT 1
        """, (roll_category_name, program_name))
        
        existing = cur.fetchone()
        
        if existing:
            # Update existing program
            program_id = existing[0]
            program_number = existing[1]
            cur.execute("""
                UPDATE autoclave_programs
                SET program_name = %s,
                    description = %s,
                    steps = %s::jsonb,
                    roll_category_name = %s
                WHERE id = %s
            """, (
                program_name,
                description,
                json.dumps(steps_structure),
                roll_category_name,
                program_id
            ))
            print(f"[{idx:2d}] [UPDATE] {program_name} (P{program_number:02d}, ID: {program_id})")
            print(f"            Base steps: {len(base_steps)}")
            if quantity_variations:
                print(f"            Quantity variations: {', '.join(quantity_variations.keys())}")
            updated += 1
        else:
            # Insert new program
            cur.execute("SELECT COALESCE(MAX(program_number), 0) + 1 FROM autoclave_programs")
            program_number = cur.fetchone()[0]
            
            cur.execute("""
                INSERT INTO autoclave_programs
                (program_number, program_name, description, steps, roll_category_name)
                VALUES (%s, %s, %s, %s::jsonb, %s)
                RETURNING id
            """, (
                program_number,
                program_name,
                description,
                json.dumps(steps_structure),
                roll_category_name
            ))
            
            program_id = cur.fetchone()[0]
            print(f"[{idx:2d}] [ADD] {program_name} (P{program_number:02d}, ID: {program_id})")
            print(f"         Base steps: {len(base_steps)}")
            if quantity_variations:
                print(f"         Quantity variations: {', '.join(quantity_variations.keys())}")
            imported += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("\n" + "="*60)
    print("IMPORT SUMMARY")
    print("="*60)
    print(f"Imported: {imported}")
    print(f"Updated:  {updated}")
    print(f"Total:    {imported + updated}")
    print("="*60)
    
    # Print programs with quantity variations
    print("\nPrograms with Quantity-Dependent Steps:")
    print("-" * 60)
    qty_programs = [p for p in programs if p.get('quantity_variations')]
    for p in qty_programs:
        print(f"  ? {p['roll_category_name']}")
        print(f"    - 1-3 rolls: Final step at {p['quantity_variations']['1-3']['final_step']['psi_range']} PSI for {p['quantity_variations']['1-3']['final_step']['duration_minutes']} min")
        print(f"    - 4+ rolls:  Final step at {p['quantity_variations']['4+']['final_step']['psi_range']} PSI for {p['quantity_variations']['4+']['final_step']['duration_minutes']} min")
    print(f"\nTotal programs with quantity variations: {len(qty_programs)}")
    print(f"Total programs without quantity variations: {len(programs) - len(qty_programs)}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("REVIEW: All 25 Roll Programs")
    print("="*60)
    print("\nThis script will add/update all 25 roll programs to the database.")
    print("Programs with quantity-dependent steps will be stored with")
    print("quantity_variations structure.\n")
    
    # Check if running in non-interactive mode (Docker, CI, etc.)
    import sys
    if sys.stdin.isatty():
        # Interactive mode - ask for confirmation
        response = input("Do you want to proceed? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("\n[INFO] Operation cancelled. No changes made.")
            print("\nTo review the programs before running, check the script file:")
            print("  backend/add_all_25_programs.py")
            sys.exit(0)
    else:
        # Non-interactive mode - proceed automatically
        print("[INFO] Running in non-interactive mode. Proceeding automatically...")
    
    add_all_programs()

