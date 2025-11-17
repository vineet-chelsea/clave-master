# Adding Autoclave Programs to Database

This guide explains how to add all 25 roll category programs to the database.

## Script: `backend/add_all_25_programs.py`

This script adds all 25 predefined roll category programs with their complete step sequences.

## Running the Script

### Option 1: Using Docker (Recommended)

```bash
# Execute the script inside the backend container
docker-compose exec backend python3 add_all_25_programs.py
```

### Option 2: Running Locally

```bash
# Navigate to backend directory
cd backend

# Make sure you have the .env file configured
# Then run the script
python3 add_all_25_programs.py
```

## What the Script Does

1. **Connects to PostgreSQL database** using environment variables:
   - `PG_HOST` (default: localhost)
   - `PG_PORT` (default: 5432)
   - `PG_DATABASE` (default: autoclave)
   - `PG_USER` (default: postgres)
   - `PG_PASSWORD` (from .env)

2. **Adds all 25 roll category programs:**
   - TSL ECL ROLL (NBR)
   - TSL ECL ROLL (EPDM)
   - TSL ECL ROLL (NBR) Qty. 1-3 Roll
   - TSL ECL ROLL (NBR) Qty. 4+ Roll
   - TSL ECL ROLL (EPDM) Qty. 1-3 Roll
   - TSL ECL ROLL (EPDM) Qty. 4+ Roll
   - TSL ECL ROLL (NBR) Qty. 1-3 Roll (Alternative)
   - TSL ECL ROLL (NBR) Qty. 4+ Roll (Alternative)
   - TSL ECL ROLL (EPDM) Qty. 1-3 Roll (Alternative)
   - TSL ECL ROLL (EPDM) Qty. 4+ Roll (Alternative)
   - TSL ECL ROLL (NBR) Qty. 1-3 Roll (Variant)
   - TSL ECL ROLL (NBR) Qty. 4+ Roll (Variant)
   - TSL ECL ROLL (EPDM) Qty. 1-3 Roll (Variant)
   - TSL ECL ROLL (EPDM) Qty. 4+ Roll (Variant)
   - TSL ECL ROLL (NBR) Qty. 1-3 Roll (Special)
   - TSL ECL ROLL (NBR) Qty. 4+ Roll (Special)
   - TSL ECL ROLL (EPDM) Qty. 1-3 Roll (Special)
   - TSL ECL ROLL (EPDM) Qty. 4+ Roll (Special)
   - TSL ECL ROLL (NBR) Qty. 1-3 Roll (Extended)
   - TSL ECL ROLL (NBR) Qty. 4+ Roll (Extended)
   - TSL ECL ROLL (EPDM) Qty. 1-3 Roll (Extended)
   - TSL ECL ROLL (EPDM) Qty. 4+ Roll (Extended)
   - TSL ECL ROLL (NBR) Qty. 1-3 Roll (Final)
   - TSL ECL ROLL (NBR) Qty. 4+ Roll (Final)
   - JSW Roll

3. **Handles quantity-dependent steps:**
   - Programs with "Qty. 1-3" or "Qty. 4+" have different final steps
   - Script automatically structures these as `base_steps` and `quantity_variations`

4. **Prompts for confirmation** before making changes

## Example Output

```
[OK] Connected to PostgreSQL database 'autoclave'

This script will add 25 roll category programs to the database.
Do you want to proceed? (yes/no): yes

[INFO] Adding program: TSL ECL ROLL (NBR) Program
[INFO] Adding program: TSL ECL ROLL (EPDM) Program
...
[SUCCESS] All 25 programs added successfully!
```

## Verifying Programs Were Added

### Using Docker

```bash
# Connect to database
docker-compose exec postgres psql -U postgres -d autoclave

# Check program count
SELECT COUNT(*) FROM autoclave_programs;

# List all programs
SELECT roll_category_name, program_name FROM autoclave_programs ORDER BY roll_category_name;

# View a specific program's steps
SELECT roll_category_name, steps FROM autoclave_programs WHERE roll_category_name = 'JSW Roll';

# Exit
\q
```

### Using psql directly

```bash
psql -U postgres -d autoclave -c "SELECT COUNT(*) FROM autoclave_programs;"
```

## Alternative: Import from Spreadsheet

If you have a spreadsheet with program data:

```bash
# Using Docker
docker-compose exec backend python3 import_programs_from_spreadsheet.py /path/to/programs.xlsx

# Or locally
cd backend
python3 import_programs_from_spreadsheet.py /path/to/programs.xlsx
```

See `backend/SPREADSHEET_IMPORT_GUIDE.md` for spreadsheet format details.

## Troubleshooting

### Database Connection Error

```bash
# Check if database is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Verify environment variables
docker-compose exec backend env | grep PG_
```

### Programs Already Exist

The script will update existing programs. If you want to start fresh:

```bash
# Connect to database
docker-compose exec postgres psql -U postgres -d autoclave

# Delete existing programs (be careful!)
DELETE FROM autoclave_programs;

# Exit
\q

# Then run the script again
docker-compose exec backend python3 add_all_25_programs.py
```

### Permission Errors

```bash
# Make sure script is executable
docker-compose exec backend chmod +x add_all_25_programs.py

# Or run with explicit Python
docker-compose exec backend python3 add_all_25_programs.py
```

## When to Run This Script

- **After initial deployment** - First time setting up the system
- **After database reset** - If database was recreated
- **After pulling updates** - If new programs were added to the script
- **After manual database changes** - To restore standard programs

## Notes

- The script is **idempotent** - safe to run multiple times
- Existing programs will be **updated** if they already exist
- Programs are linked to roll categories via `roll_category_name`
- Quantity-dependent programs use special JSON structure for steps

