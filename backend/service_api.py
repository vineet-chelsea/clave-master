"""
API Server for Communication with Sensor Control Service
This allows the frontend to communicate with the running service instance
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
import subprocess
import time

load_dotenv()

app = Flask(__name__)
CORS(app)

# Store service instance reference
service_instance = None

def get_service_instance():
    """Get the running service instance"""
    global service_instance
    if service_instance is None:
        from sensor_control_service import SensorControlService
        service_instance = SensorControlService()
        # Start the service in background thread
        import threading
        service_thread = threading.Thread(target=service_instance.run, daemon=True)
        service_thread.start()
        # Wait a bit for initialization
        time.sleep(2)
    return service_instance

@app.route('/api/start-control', methods=['POST'])
def start_control():
    """Start pressure control session"""
    try:
        data = request.json
        target_pressure = float(data.get('target_pressure'))
        duration_minutes = int(data.get('duration_minutes'))
        program_name = data.get('program_name', 'Manual Control')
        
        service = get_service_instance()
        
        if service.start_control_session(target_pressure, duration_minutes, program_name):
            return jsonify({
                'success': True,
                'session_id': service.session_id,
                'target_pressure': target_pressure,
                'duration_minutes': duration_minutes
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to start session'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stop-control', methods=['POST'])
def stop_control():
    """Stop current control session"""
    try:
        service = get_service_instance()
        service.stop_control_session()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sensor-readings/latest', methods=['GET'])
def get_latest_reading():
    """Get latest sensor reading"""
    try:
        import psycopg2
        
        PG_HOST = os.getenv('PG_HOST', '127.0.0.1')
        PG_PORT = os.getenv('PG_PORT', '5432')
        PG_DATABASE = os.getenv('PG_DATABASE', 'autoclave')
        PG_USER = os.getenv('PG_USER', 'postgres')
        PG_PASSWORD = os.getenv('PG_PASSWORD', 'postgres')
        
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD
        )
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT timestamp, pressure, temperature FROM sensor_readings ORDER BY timestamp DESC LIMIT 1"
        )
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            return jsonify({
                'timestamp': row[0].isoformat() if row[0] else None,
                'pressure': float(row[1]),
                'temperature': float(row[2])
            })
        else:
            return jsonify({
                'timestamp': None,
                'pressure': 0,
                'temperature': 25
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Get all process sessions"""
    try:
        import psycopg2
        
        PG_HOST = os.getenv('PG_HOST', '127.0.0.1')
        PG_PORT = os.getenv('PG_PORT', '5432')
        PG_DATABASE = os.getenv('PG_DATABASE', 'autoclave')
        PG_USER = os.getenv('PG_USER', 'postgres')
        PG_PASSWORD = os.getenv('PG_PASSWORD', 'postgres')
        
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD
        )
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, program_name, status, start_time, end_time FROM process_sessions ORDER BY start_time DESC LIMIT 50"
        )
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        sessions = [
            {
                'id': row[0],
                'program_name': row[1],
                'status': row[2],
                'start_time': row[3].isoformat() if row[3] else None,
                'end_time': row[4].isoformat() if row[4] else None
            }
            for row in rows
        ]
        
        return jsonify(sessions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<int:session_id>/logs', methods=['GET'])
def get_session_logs(session_id):
    """Get logs for a specific session"""
    try:
        import psycopg2
        
        PG_HOST = os.getenv('PG_HOST', '127.0.0.1')
        PG_PORT = os.getenv('PG_PORT', '5432')
        PG_DATABASE = os.getenv('PG_DATABASE', 'autoclave')
        PG_USER = os.getenv('PG_USER', 'postgres')
        PG_PASSWORD = os.getenv('PG_PASSWORD', 'postgres')
        
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD
        )
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT timestamp, pressure, temperature, valve_position, status FROM process_logs WHERE session_id=%s ORDER BY timestamp ASC LIMIT 100",
            (session_id,)
        )
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        logs = [
            {
                'timestamp': row[0].isoformat() if row[0] else None,
                'pressure': float(row[1]),
                'temperature': float(row[2]),
                'valve_position': row[3],
                'status': row[4]
            }
            for row in rows
        ]
        
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'api': 'service_api'})

if __name__ == '__main__':
    print("="*60)
    print("Service API Server")
    print("="*60)
    print("This starts the sensor service and provides API")
    print(f"Starting on http://localhost:5000")
    print("="*60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

