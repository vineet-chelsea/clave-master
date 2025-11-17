"""
Import autoclave programs from Excel/CSV spreadsheet
Handles quantity-dependent steps and various duration/PSI formats
"""
import os
import sys
import json
import re
from dotenv import load_dotenv
import psycopg2

# Try to import pandas for Excel support
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("[ERROR] pandas is required. Install with: pip install pandas openpyxl")
    sys.exit(1)

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

def parse_duration_to_minutes(duration_str):
    """Parse duration string to minutes (handles various formats)"""
    if pd.isna(duration_str) or not duration_str:
        return 0
    
    duration_str = str(duration_str).strip()
    
    # Extract hours and minutes using regex
    hours = 0
    minutes = 0
    
    # Match patterns like "2 Hrs. 30 Mins.", "1 Hr 15 Mins.", "3 Hrs", "45 Mins."
    hour_pattern = r'(\d+)\s*(?:hr|hrs?|hour|hours)\.?'
    minute_pattern = r'(\d+)\s*(?:min|mins?|minute|minutes)\.?'
    
    hour_match = re.search(hour_pattern, duration_str, re.IGNORECASE)
    minute_match = re.search(minute_pattern, duration_str, re.IGNORECASE)
    
    if hour_match:
        hours = int(hour_match.group(1))
    if minute_match:
        minutes = int(minute_match.group(1))
    
    # If no match found, try to extract just numbers
    if hours == 0 and minutes == 0:
        numbers = re.findall(r'\d+', duration_str)
        if numbers:
            # Assume it's minutes if just one number
            if len(numbers) == 1:
                minutes = int(numbers[0])
            else:
                # First number is hours, second is minutes
                hours = int(numbers[0])
                minutes = int(numbers[1]) if len(numbers) > 1 else 0
    
    total_minutes = (hours * 60) + minutes
    return total_minutes

def parse_psi_range(psi_str):
    """Parse PSI range string (handles various formats)"""
    if pd.isna(psi_str) or not psi_str:
        return "0"
    
    psi_str = str(psi_str).strip()
    
    # Handle "Steady at X" format -> extract X
    if 'steady at' in psi_str.lower():
        match = re.search(r'steady\s+at\s+(\d+(?:\.\d+)?)', psi_str, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            return str(int(value)) if value.is_integer() else str(value)
    
    # Handle "Raise to X-Y" format -> return range
    if 'raise to' in psi_str.lower():
        match = re.search(r'raise\s+to\s+(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)', psi_str, re.IGNORECASE)
        if match:
            return f"{match.group(1)}-{match.group(2)}"
        # Single value
        match = re.search(r'raise\s+to\s+(\d+(?:\.\d+)?)', psi_str, re.IGNORECASE)
        if match:
            return match.group(1)
    
    # Handle "Stay at X" format
    if 'stay at' in psi_str.lower():
        match = re.search(r'stay\s+at\s+(\d+(?:\.\d+)?)', psi_str, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            return str(int(value)) if value.is_integer() else str(value)
    
    # Handle "X phr" format (for sleeves) -> treat as PSI
    if 'phr' in psi_str.lower():
        match = re.search(r'(\d+(?:\.\d+)?)\s*phr', psi_str, re.IGNORECASE)
        if match:
            return match.group(1)
    
    # Handle range format "X-Y"
    if '-' in psi_str:
        parts = psi_str.split('-')
        if len(parts) == 2:
            try:
                low = float(parts[0].strip())
                high = float(parts[1].strip())
                return f"{int(low) if low.is_integer() else low}-{int(high) if high.is_integer() else high}"
            except:
                return psi_str
    
    # Handle single number
    try:
        value = float(psi_str)
        return str(int(value) if value.is_integer() else value)
    except:
        return psi_str

def parse_action(psi_str, action_str=None):
    """Parse action from PSI string or action column"""
    if action_str and not pd.isna(action_str):
        action_str = str(action_str).strip().lower()
        if 'raise' in action_str or 'increase' in action_str:
            return 'raise'
        elif 'lower' in action_str or 'decrease' in action_str:
            return 'lower'
        else:
            return 'steady'
    
    # Infer from PSI string
    if pd.isna(psi_str) or not psi_str:
        return 'steady'
    
    psi_str = str(psi_str).strip().lower()
    
    if 'raise' in psi_str:
        return 'raise'
    elif 'lower' in psi_str or 'decrease' in psi_str:
        return 'lower'
    elif 'steady' in psi_str or 'stay' in psi_str:
        return 'steady'
    else:
        return 'steady'

def read_spreadsheet(file_path):
    """Read spreadsheet file (Excel or CSV)"""
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.csv':
        df = pd.read_csv(file_path)
    elif file_ext in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path)
    else:
        print(f"[ERROR] Unsupported file format: {file_ext}")
        print("        Supported formats: .csv, .xlsx, .xls")
        sys.exit(1)
    
    return df

def import_programs(file_path):
    """Import programs from spreadsheet"""
    print("="*60)
    print("Import Programs from Spreadsheet")
    print("="*60)
    print(f"Reading file: {file_path}\n")
    
    # Read spreadsheet
    df = read_spreadsheet(file_path)
    
    print(f"[OK] Read {len(df)} rows from spreadsheet\n")
    
    # Normalize column names (lowercase, strip spaces)
    df.columns = [col.strip().lower() for col in df.columns]
    
    # Check for required columns
    required_columns = ['roll_category', 'psi']
    missing = [col for col in required_columns if col not in df.columns]
    
    if missing:
        print(f"[ERROR] Missing required columns: {', '.join(missing)}")
        print(f"        Found columns: {', '.join(df.columns)}")
        sys.exit(1)
    
    # Connect to database
    conn = connect_db()
    cur = conn.cursor()
    
    # Group by roll_category to build programs
    programs = {}
    
    for idx, row in df.iterrows():
        roll_category = str(row['roll_category']).strip() if not pd.isna(row['roll_category']) else None
        psi = row.get('psi', '')
        duration = row.get('duration', '')
        
        if not roll_category or pd.isna(psi):
            continue
        
        # Initialize program if not exists
        if roll_category not in programs:
            programs[roll_category] = {
                'roll_category_name': roll_category,
                'program_name': f"{roll_category} Program",
                'description': f"Autoclave program for {roll_category}",
                'base_steps': [],
                'quantity_variations': {}
            }
        
        # Check if this is a quantity-dependent step
        is_qty_step = False
        qty_range = None
        
        # Check for quantity indicators in roll_category or separate column
        if 'qty' in str(row.get('roll_category', '')).lower() or 'quantity' in str(row.get('roll_category', '')).lower():
            # Extract quantity range
            qty_str = str(row.get('roll_category', '')).lower()
            if '1-3' in qty_str or '1 to 3' in qty_str:
                qty_range = "1-3"
                is_qty_step = True
            elif '4' in qty_str and ('more' in qty_str or '+' in qty_str or 'or more' in qty_str):
                qty_range = "4+"
                is_qty_step = True
        
        # Check for quantity column
        if not is_qty_step and 'quantity' in df.columns:
            qty_val = row.get('quantity', '')
            if not pd.isna(qty_val):
                qty_str = str(qty_val).lower()
                if '1-3' in qty_str or '1 to 3' in qty_str:
                    qty_range = "1-3"
                    is_qty_step = True
                elif '4' in qty_str and ('more' in qty_str or '+' in qty_str):
                    qty_range = "4+"
                    is_qty_step = True
        
        # Parse step data
        psi_range = parse_psi_range(psi)
        duration_minutes = parse_duration_to_minutes(duration)
        action = parse_action(psi, row.get('action', ''))
        
        if is_qty_step and qty_range:
            # This is a quantity-dependent final step
            if qty_range not in programs[roll_category]['quantity_variations']:
                programs[roll_category]['quantity_variations'][qty_range] = {}
            
            programs[roll_category]['quantity_variations'][qty_range]['final_step'] = {
                'psi_range': psi_range,
                'duration_minutes': duration_minutes,
                'action': action
            }
        else:
            # Regular step
            programs[roll_category]['base_steps'].append({
                'psi_range': psi_range,
                'duration_minutes': duration_minutes,
                'action': action
            })
    
    print(f"[OK] Parsed {len(programs)} programs\n")
    
    # Insert or update programs
    imported = 0
    updated = 0
    skipped = 0
    
    for roll_category, program in programs.items():
        roll_category_name = program['roll_category_name']
        program_name = program['program_name']
        description = program['description']
        base_steps = program['base_steps']
        quantity_variations = program['quantity_variations']
        
        if not base_steps:
            print(f"[SKIP] {program_name} - No base steps found")
            skipped += 1
            continue
        
        # Build steps structure
        if quantity_variations:
            # Use quantity_variations structure
            steps_structure = {
                'base_steps': base_steps,
                'quantity_variations': quantity_variations
            }
        else:
            # Just use base steps as array
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
            print(f"[UPDATE] {program_name} (ID: {program_id})")
            print(f"         Base steps: {len(base_steps)}")
            if quantity_variations:
                print(f"         Quantity variations: {', '.join(quantity_variations.keys())}")
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
            print(f"[ADD] {program_name} (P{program_number:02d}, ID: {program_id})")
            print(f"      Base steps: {len(base_steps)}")
            if quantity_variations:
                print(f"      Quantity variations: {', '.join(quantity_variations.keys())}")
            imported += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("\n" + "="*60)
    print("IMPORT SUMMARY")
    print("="*60)
    print(f"Imported: {imported}")
    print(f"Updated:  {updated}")
    print(f"Skipped:  {skipped}")
    print(f"Total:    {imported + updated + skipped}")
    print("="*60)

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python import_programs_from_spreadsheet.py <spreadsheet_file>")
        print("\nSupported formats:")
        print("  - CSV (.csv)")
        print("  - Excel (.xlsx, .xls)")
        print("\nExpected columns:")
        print("  Required:")
        print("    - roll_category: Name of the roll category")
        print("    - psi: PSI range or value (e.g., '5-10', 'Steady at 10', 'Raise to 40-45', '3 phr')")
        print("    - duration: Duration (e.g., '15 Mins.', '2 Hrs. 30 Mins.', '1 Hr 15 Mins.')")
        print("  Optional:")
        print("    - action: 'raise', 'steady', or 'lower' (auto-detected from PSI if not provided)")
        print("    - quantity: '1-3' or '4+' for quantity-dependent steps")
        print("\nExample spreadsheet structure:")
        print("  roll_category,psi,duration")
        print("  TSL ECL ROLL (NBR),0-5,15 Mins.")
        print("  TSL ECL ROLL (NBR),5-10,45 Mins.")
        print("  TSL ECL ROLL (NBR),40-45,2 Hrs. 30 Mins.")
        print("  TSL ECL ROLL (NBR) Qty. 1-3 Roll,45-45,2 Hrs. 30 Mins.")
        print("  TSL ECL ROLL (NBR) Qty. 4 or more Roll,45-45,3 Hrs.")
        print("\nDuration formats supported:")
        print("  - '15 Mins.', '45 MINS.', '1 Hr.', '2 Hrs.'")
        print("  - '1 Hr 15 Mins.', '2 Hrs. 30 Mins.', '3 Hrs 15 Mins.'")
        print("  - '6 Hrs.', '4 Hrs. 30 Mins.'")
        print("\nPSI formats supported:")
        print("  - Ranges: '0-5', '5-10', '40-45'")
        print("  - Steady: 'Steady at 10', 'Steady at 40-45'")
        print("  - Raise: 'Raise to 40-45', 'Raise to 20-25'")
        print("  - Sleeves: '3 phr', '30 phr'")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        sys.exit(1)
    
    import_programs(file_path)

if __name__ == "__main__":
    main()
