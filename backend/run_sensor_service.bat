@echo off
REM Windows Batch script to run the sensor reading service

echo Starting Modbus Sensor Reading Service...
echo.

REM Load environment variables from .env file if it exists
if exist .env (
    echo Loading environment variables from .env...
    for /f "tokens=*" %%a in ('type .env') do (
        set "%%a"
    )
)

REM Run the Python service
python sensor_service.py

pause

