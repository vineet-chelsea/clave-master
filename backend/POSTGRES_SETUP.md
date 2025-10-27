# PostgreSQL Setup for Sensor Reading Service

## Installation

### Option 1: Download PostgreSQL

Download and install PostgreSQL from: https://www.postgresql.org/download/windows/

### Option 2: Install with winget

```bash
winget install PostgreSQL.PostgreSQL
```

## Setup Steps

### 1. Install PostgreSQL

Follow the installer and remember the postgres user password (default is `postgres`)

### 2. Create Database

Open psql or pgAdmin and run:

```sql
CREATE DATABASE autoclave;
```

Or use command line:

```bash
psql -U postgres -c "CREATE DATABASE autoclave;"
```

### 3. Run Table Creation Script

```bash
psql -U postgres -d autoclave -f backend/postgres_setup.sql
```

Or copy and run the SQL manually in pgAdmin.

### 4. Update Configuration

The `backend/.env` file is already configured with default values:

```env
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=autoclave
PG_USER=postgres
PG_PASSWORD=postgres  # Change this to your PostgreSQL password
```

### 5. Install Python Driver

```bash
cd backend
pip install psycopg2-binary
```

### 6. Test Connection

```bash
cd backend
python test_modbus_read.py
```

This will test if PostgreSQL connection works.

### 7. Start Sensor Service

```bash
cd backend
python sensor_service.py
```

## Configuration

### Default PostgreSQL Settings:
- Host: localhost
- Port: 5432
- Database: autoclave
- User: postgres
- Password: (set during installation)

### To Change Settings:

Edit `backend/.env`:

```env
PG_HOST=your-postgres-host
PG_PORT=5432
PG_DATABASE=autoclave
PG_USER=postgres
PG_PASSWORD=your_password
```

## Verification

### Check if PostgreSQL is running:
```bash
# Windows
Get-Service postgresql*

# Or check listening port
netstat -an | findstr 5432
```

### Test database connection:
```bash
psql -U postgres -d autoclave
```

### View sensor readings:
```sql
SELECT * FROM sensor_readings ORDER BY timestamp DESC LIMIT 10;
```

## Troubleshooting

### "Connection refused"
- Ensure PostgreSQL is running
- Check port 5432 is not blocked
- Verify host and port in .env

### "Database does not exist"
- Run: `CREATE DATABASE autoclave;`

### "Table does not exist"
- Run the SQL in `backend/postgres_setup.sql`

### "Authentication failed"
- Check username and password in .env
- Verify PostgreSQL user permissions

## Quick Start (If PostgreSQL Already Installed)

1. Create database:
```bash
createdb -U postgres autoclave
```

2. Create table:
```bash
psql -U postgres -d autoclave -c "CREATE TABLE sensor_readings (id SERIAL PRIMARY KEY, timestamp TIMESTAMP DEFAULT NOW(), pressure DECIMAL(10,2), temperature DECIMAL(10,2));"
```

3. Install driver:
```bash
pip install psycopg2-binary
```

4. Run service:
```bash
cd backend
python sensor_service.py
```

Done! ✅

