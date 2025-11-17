# 📊 Import Programs from Spreadsheet

## Quick Start

1. **Prepare your spreadsheet** (Excel or CSV) with the format shown in your images
2. **Run the import script:**
   ```bash
   cd backend
   python import_programs_from_spreadsheet.py your_file.xlsx
   ```

## Spreadsheet Format

### Required Columns:
- `roll_category` - Name of the roll category (e.g., "TSL ECL ROLL (NBR)", "JSW 700 Dia. Roll")
- `psi` - PSI range or value (see formats below)
- `duration` - Duration (see formats below)

### Optional Columns:
- `action` - Step action: "raise", "steady", or "lower" (auto-detected from PSI if not provided)
- `quantity` - For quantity-dependent steps: "1-3" or "4+"

## PSI Format Examples

The script handles various PSI formats:

- **Ranges**: `"0-5"`, `"5-10"`, `"40-45"` → Stored as range
- **Steady at**: `"Steady at 10"`, `"Steady at 40-45"` → Extracts the value/range
- **Raise to**: `"Raise to 40-45"`, `"Raise to 20-25"` → Extracts the range, action = "raise"
- **Stay at**: `"Stay at 30 phr"` → Extracts the value, action = "steady"
- **Sleeves (phr)**: `"3 phr"`, `"30 phr"` → Converts to PSI value

## Duration Format Examples

The script handles various duration formats:

- `"15 Mins."` → 15 minutes
- `"45 MINS."` → 45 minutes
- `"1 Hr."` → 60 minutes
- `"2 Hrs."` → 120 minutes
- `"1 Hr 15 Mins."` → 75 minutes
- `"2 Hrs. 30 Mins."` → 150 minutes
- `"3 Hrs 15 Mins."` → 195 minutes
- `"6 Hrs."` → 360 minutes
- `"4 Hrs. 30 Mins."` → 270 minutes

## Quantity-Dependent Steps

For rolls that have different final steps based on quantity:

### Method 1: Include in roll_category name
```
roll_category,psi,duration
TSL ECL ROLL (NBR),0-5,15 Mins.
TSL ECL ROLL (NBR),5-10,45 Mins.
TSL ECL ROLL (NBR),10-20,15 Mins.
TSL ECL ROLL (NBR),20-30,15 Mins.
TSL ECL ROLL (NBR),30-40,15 Mins.
TSL ECL ROLL (NBR),40-45,2 Hrs. 30 Mins.
TSL ECL ROLL (NBR) Qty. 1-3 Roll,45-45,2 Hrs. 30 Mins.
TSL ECL ROLL (NBR) Qty. 4 or more Roll,45-45,3 Hrs.
```

### Method 2: Use quantity column
```
roll_category,psi,duration,quantity
TSL ECL ROLL (NBR),0-5,15 Mins.,
TSL ECL ROLL (NBR),5-10,45 Mins.,
TSL ECL ROLL (NBR),40-45,2 Hrs. 30 Mins.,
TSL ECL ROLL (NBR),45-45,2 Hrs. 30 Mins.,1-3
TSL ECL ROLL (NBR),45-45,3 Hrs.,4+
```

## Example Spreadsheet Structure

Based on your images, here's the format:

| roll_category | psi | duration |
|--------------|-----|----------|
| TSL ECL ROLL (NBR) | 0-5 | 15 MINS. |
| TSL ECL ROLL (NBR) | 5-10 | 45 MINS. |
| TSL ECL ROLL (NBR) | 10-20 | 15 MINS. |
| TSL ECL ROLL (NBR) | 20-30 | 15 MINS. |
| TSL ECL ROLL (NBR) | 30-40 | 15 MINS. |
| TSL ECL ROLL (NBR) | 40-45 | 2 Hrs. 30 MINS. |
| TSL ECL ROLL (NBR) Qty. 1-3 Roll | 45-45 | 2 Hrs. 30 Mins. |
| TSL ECL ROLL (NBR) Qty. 4 or more Roll | 45-45 | 3 Hrs. |
| JSW 700 Dia. Roll | 5-10 | 15 Mins. |
| JSW 700 Dia. Roll | Steady at 10 | 1 Hr 15 Mins. |
| JSW 700 Dia. Roll | Raise to 20-25 | 15 Mins. |
| JSW 700 Dia. Roll | Steady at 20-25 | 30 Mins. |
| JSW 700 Dia. Roll | Raise to 40-45 | 15 Mins. |
| JSW 700 Dia. Roll | Steady at 40-45 | 2 Hrs. 30 Mins. |
| SLEEVE 20 mm Lining | 3 phr | 1 Hr. |
| SLEEVE 20 mm Lining | Raise to 30 phr | 15 Mins. |
| SLEEVE 20 mm Lining | Stay at 30 phr | 2 Hrs. 30 Mins. |

## How It Works

1. **Reads spreadsheet** - Supports CSV, XLSX, and XLS formats
2. **Groups by roll_category** - Each unique roll_category becomes one program
3. **Detects quantity-dependent steps** - Looks for "Qty. 1-3" or "Qty. 4 or more" in roll_category or quantity column
4. **Builds program structure**:
   - **Base steps**: All regular steps (not quantity-dependent)
   - **Quantity variations**: Final steps that differ by quantity
5. **Stores in database**:
   - If quantity variations exist: Uses `quantity_variations` structure
   - If no quantity variations: Stores as simple steps array
6. **Inserts/Updates**:
   - If program exists: **Updates** it
   - If program doesn't exist: **Creates** new program

## Program Structure in Database

### With Quantity Variations:
```json
{
  "base_steps": [
    {"psi_range": "0-5", "duration_minutes": 15, "action": "raise"},
    {"psi_range": "5-10", "duration_minutes": 45, "action": "steady"},
    {"psi_range": "10-20", "duration_minutes": 15, "action": "raise"},
    {"psi_range": "20-30", "duration_minutes": 15, "action": "raise"},
    {"psi_range": "30-40", "duration_minutes": 15, "action": "raise"},
    {"psi_range": "40-45", "duration_minutes": 150, "action": "steady"}
  ],
  "quantity_variations": {
    "1-3": {
      "final_step": {"psi_range": "45-45", "duration_minutes": 150, "action": "steady"}
    },
    "4+": {
      "final_step": {"psi_range": "45-45", "duration_minutes": 180, "action": "steady"}
    }
  }
}
```

### Without Quantity Variations:
```json
[
  {"psi_range": "5-10", "duration_minutes": 15, "action": "raise"},
  {"psi_range": "10", "duration_minutes": 75, "action": "steady"},
  {"psi_range": "20-25", "duration_minutes": 15, "action": "raise"},
  {"psi_range": "20-25", "duration_minutes": 30, "action": "steady"},
  {"psi_range": "40-45", "duration_minutes": 15, "action": "raise"},
  {"psi_range": "40-45", "duration_minutes": 120, "action": "steady"}
]
```

## Installation

Install required packages:
```bash
pip install pandas openpyxl
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

## Troubleshooting

### "Missing required columns"
- Make sure your spreadsheet has columns: `roll_category`, `psi`, `duration`
- Column names are case-insensitive
- Extra spaces are automatically trimmed

### "No base steps found"
- Make sure each roll_category has at least one regular step (not quantity-dependent)
- Quantity-dependent steps are stored separately

### Duration not parsed correctly
- Check the format matches the examples above
- The script extracts hours and minutes using regex
- If it fails, it tries to extract just numbers

### Quantity variations not detected
- Make sure quantity-dependent rows have "Qty. 1-3" or "Qty. 4 or more" in roll_category name
- Or use a separate `quantity` column with values "1-3" or "4+"

## Output Example

```
============================================================
Import Programs from Spreadsheet
============================================================
Reading file: programs.xlsx

[OK] Read 150 rows from spreadsheet

[OK] Parsed 25 programs

[ADD] TSL ECL ROLL (NBR) Program (P01, ID: 1)
      Base steps: 6
      Quantity variations: 1-3, 4+
[ADD] JSW 700 Dia. Roll Program (P02, ID: 2)
      Base steps: 6
[ADD] SLEEVE 20 mm Lining Program (P03, ID: 3)
      Base steps: 3
...

============================================================
IMPORT SUMMARY
============================================================
Imported: 25
Updated:  0
Skipped:  0
Total:    25
============================================================
```

## Notes

- Programs are grouped by `roll_category`
- Quantity-dependent steps are automatically detected and stored in `quantity_variations`
- The API will automatically calculate the correct steps based on `number_of_rolls` when starting a session
- All 25 roll categories (including "JSW Roll") are already in the database
- If you import the same program twice, it will **update** the existing one
