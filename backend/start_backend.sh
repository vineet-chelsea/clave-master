#!/bin/bash
# Start both sensor service and API server

echo "======================================"
echo "Autoclave Backend Startup"
echo "======================================"

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
sleep 5

# Initialize database if needed
echo "Initializing database..."
if ! python docker-init-db.py; then
    echo "[ERROR] Database initialization failed!"
    exit 1
fi

echo ""
echo "Starting services..."
echo ""

# Start API server in foreground
python api_server.py &
API_PID=$!

# Wait a moment for API to start
sleep 5

# Start sensor control service in foreground
python sensor_control_service.py &
SENSOR_PID=$!

# Wait for either process to exit
wait -n

# If either process exits, kill the other and exit
kill $API_PID $SENSOR_PID 2>/dev/null
exit 1

