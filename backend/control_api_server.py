"""
API Server for Frontend to Control Pressure
Provides endpoints for UI to start/stop control
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import os
from dotenv import load_dotenv
import subprocess
import threading
import time

load_dotenv()

app = Flask(__name__)
CORS(app)

# PostgreSQL configuration
PG_HOST = os.getenv('PG_HOST', '127.0.0.1')
PG_PORT = os.getenv('PG_PORT', '5432')
PG_DATABASE = os.getenv('PG_DATABASE', 'autoclave')
PG_USER = os.getenv('PG_USER', 'postgres')
PG_PASSWORD = os.getenv('PG_PASSWORD', 'postgres')

# Global controller process
controller_process = None

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD
    )

@app.route('/api/start-control', methods=['POST'])
def start_control():
    """Start pressure control session"""
    try:
        data = request.json
        target_pressure = float(data.get('target_pressure'))
        duration_minutes = int(data.get('duration_minutes'))
        program_name = data.get('program_name', 'Manual Control')
        
        # Create session in database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO process_sessions (program_name, status, start_time) VALUES (%s, %s, %s) RETURNING id",
            (program_name, 'running', 'now()')
        )
        session_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        # Start controller in background
        global controller_process
        if controller_process and controller_process.poll() is None:
            controller_process.terminate()
        
        controller_process = subprocess.Popen(
            ['python', 'pressure_controller.py', str(target_pressure), str(duration_minutes), '--session-id', str(session_id)],
            cwd='backend'
        )
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'target_pressure': target_pressure,
            'duration_minutes': duration_minutes
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stop-control', methods=['POST'])
def stop_control():
    """Stop current control session"""
    try:
        global controller_process
        if controller_process and controller_process.poll() is None:
            controller_process.terminate()
            controller_process.wait()
        
        # Update session status
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE process_sessions SET status='stopped', end_time=now() WHERE status='running'"
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sensor-readings/latest', methods=['GET'])
def get_latest_reading():
    """Get latest sensor reading"""
    try:
        conn = get_db_connection()
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
        conn = get_db_connection()
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
        conn = get_db_connection()
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
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    print("="*60)
    print("Control API Server")
    print("="*60)
    print(f"PostgreSQL: {PG_HOST}:{PG_PORT}/{PG_DATABASE}")
    print(f"Starting server on http://localhost:5000")
    print("="*60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

