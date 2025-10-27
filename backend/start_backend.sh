#!/bin/bash
# Start both sensor service and API server

echo "Starting Autoclave Backend Services..."
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

