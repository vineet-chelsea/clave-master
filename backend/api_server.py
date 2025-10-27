"""
REST API Server for Sensor Readings
Provides endpoints for frontend to get latest sensor data
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# PostgreSQL configuration
PG_HOST = os.getenv('PG_HOST', '127.0.0.1')
PG_PORT = os.getenv('PG_PORT', '5432')
PG_DATABASE = os.getenv('PG_DATABASE', 'autoclave')
PG_USER = os.getenv('PG_USER', 'postgres')
PG_PASSWORD = os.getenv('PG_PASSWORD', 'postgres')

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD
    )

@app.route('/api/sensor-readings/latest', methods=['GET'])
def get_latest_reading():
    """Get the latest sensor reading"""
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

@app.route('/api/sensor-readings/recent', methods=['GET'])
def get_recent_readings():
    """Get recent sensor readings"""
    limit = request.args.get('limit', 10, type=int)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT timestamp, pressure, temperature FROM sensor_readings ORDER BY timestamp DESC LIMIT %s",
            (limit,)
        )
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        readings = [
            {
                'timestamp': row[0].isoformat() if row[0] else None,
                'pressure': float(row[1]),
                'temperature': float(row[2])
            }
            for row in rows
        ]
        
        return jsonify(readings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Get all process sessions"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, program_name, status, start_time, end_time, target_pressure, duration_minutes, steps_data FROM process_sessions ORDER BY start_time DESC LIMIT 50"
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
                'end_time': row[4].isoformat() if row[4] else None,
                'target_pressure': float(row[5]) if row[5] else None,
                'duration_minutes': int(row[6]) if row[6] else None,
                'steps_data': row[7] if row[7] else None
            }
            for row in rows
        ]
        
        return jsonify(sessions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<int:session_id>/logs', methods=['GET'])
def get_session_logs(session_id):
    """Get logs for a specific session - includes all sensor readings during session time range"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get session start and end times
        cursor.execute(
            "SELECT start_time, end_time FROM process_sessions WHERE id=%s",
            (session_id,)
        )
        session_row = cursor.fetchone()
        
        if not session_row or not session_row[0]:
            return jsonify({'error': 'Session not found'}), 404
        
        start_time, end_time = session_row
        
        if end_time:
            # Session is completed - get all sensor readings within time range
            cursor.execute(
                """
                SELECT timestamp, pressure, temperature 
                FROM sensor_readings 
                WHERE timestamp >= %s AND timestamp <= %s 
                ORDER BY timestamp ASC
                """,
                (start_time, end_time)
            )
        else:
            # Session is still running - get recent readings
            cursor.execute(
                """
                SELECT timestamp, pressure, temperature 
                FROM sensor_readings 
                WHERE timestamp >= %s
                ORDER BY timestamp DESC
                LIMIT 1000
                """,
                (start_time,)
            )
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Format logs with valve_position and status (use null for historical data)
        logs = [
            {
                'timestamp': row[0].isoformat() if row[0] else None,
                'pressure': float(row[1]),
                'temperature': float(row[2]),
                'valve_position': None,
                'status': 'running'
            }
            for row in rows
        ]
        
        # If we got DESC order (running session), reverse it
        if not end_time and len(logs) > 0:
            logs.reverse()
        
        return jsonify(logs)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/start-control', methods=['POST'])
def start_control():
    """Start pressure control session"""
    try:
        data = request.json
        target_pressure = float(data.get('target_pressure'))
        duration_minutes = int(data.get('duration_minutes'))
        program_name = data.get('program_name', 'Manual Control')
        
        # Create session in database with control parameters
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Store control parameters in session metadata
        cursor.execute(
            "INSERT INTO process_sessions (program_name, status, start_time, target_pressure, duration_minutes) VALUES (%s, %s, NOW(), %s, %s) RETURNING id",
            (program_name, 'running', float(target_pressure), int(duration_minutes))
        )
        print(f"[API] Created session with target={target_pressure}, duration={duration_minutes}")
        session_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        # Note: The sensor_service.py should monitor for sessions with status='running' 
        # and start pressure control automatically when detected
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'target_pressure': target_pressure,
            'duration_minutes': duration_minutes,
            'message': 'Session created. Pressure control will start automatically.'
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stop-control', methods=['POST'])
def stop_control():
    """Stop current control session"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Stop both 'running' and 'paused' sessions
        cursor.execute(
            "UPDATE process_sessions SET status='stopped', end_time=NOW() WHERE status IN ('running', 'paused')"
        )
        rows_affected = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"[API] Stopped {rows_affected} session(s)")
        
        return jsonify({'success': True, 'rows_affected': rows_affected})
    except Exception as e:
        print(f"[ERROR] Failed to stop: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/pause-control', methods=['POST'])
def pause_control():
    """Pause current control session"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE process_sessions SET status='paused' WHERE status='running'"
        )
        rows_affected = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"[API] Paused {rows_affected} session(s)")
        
        return jsonify({'success': True, 'rows_affected': rows_affected})
    except Exception as e:
        print(f"[ERROR] Failed to pause: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/resume-control', methods=['POST'])
def resume_control():
    """Resume paused control session"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE process_sessions SET status='running' WHERE status='paused'"
        )
        rows_affected = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"[API] Resumed {rows_affected} session(s)")
        
        return jsonify({'success': True, 'rows_affected': rows_affected})
    except Exception as e:
        print(f"[ERROR] Failed to resume: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/programs', methods=['GET'])
def get_programs():
    """Get all auto programs"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, program_number, program_name, description, steps
            FROM autoclave_programs
            ORDER BY program_number
        """)
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        programs = [
            {
                'id': row[0],
                'program_number': row[1],
                'program_name': row[2],
                'description': row[3] or '',
                'steps': row[4]  # JSONB already parsed by psycopg2
            }
            for row in rows
        ]
        
        return jsonify(programs)
    except Exception as e:
        print(f"[ERROR] Failed to get programs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/start-auto-program', methods=['POST'])
def start_auto_program():
    """Start an auto program with multiple steps"""
    try:
        data = request.json
        program_name = data.get('program_name', 'Auto Program')
        steps = data.get('steps', [])
        total_duration = data.get('total_duration', 60)
        
        if not steps:
            return jsonify({'success': False, 'error': 'No steps provided'}), 400
        
        # Parse pressure from range (e.g., "5-10" -> 7.5, "40-45" -> 42.5)
        def parse_pressure(psi_range):
            if '-' in psi_range:
                parts = psi_range.split('-')
                if len(parts) == 2:
                    try:
                        low = float(parts[0].strip())
                        high = float(parts[1].strip())
                        return (low + high) / 2  # Median
                    except:
                        pass
            # Single value or "Steady at X"
            try:
                # Extract number from string
                import re
                numbers = re.findall(r'\d+(?:\.\d+)?', psi_range)
                if numbers:
                    return float(numbers[0])
            except:
                pass
            return 0
        
        # Get the first step's target pressure
        first_step = steps[0]
        target_pressure = parse_pressure(first_step.get('psi_range', '0'))
        
        # For now, start with just the first step (backend will need multi-step logic)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Store program steps in session
        cursor.execute("""
            INSERT INTO process_sessions 
            (program_name, target_pressure, duration_minutes, status, steps_data)
            VALUES (%s, %s, %s, 'running', %s::jsonb)
            RETURNING id
        """, (
            program_name,
            target_pressure,
            total_duration,
            str(steps).replace("'", '"')
        ))
        
        session_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"[API] Started auto program: {program_name} (Session {session_id})")
        print(f"[API] First step: {target_pressure} PSI for {steps[0].get('duration_minutes')} min")
        print(f"[API] Total steps: {len(steps)}")
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'target_pressure': target_pressure,
            'duration_minutes': total_duration,
            'steps': len(steps),
            'message': f'{program_name} started with {len(steps)} steps'
        })
    except Exception as e:
        print(f"[ERROR] Failed to start auto program: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
    print("Sensor Readings API Server")
    print("="*60)
    print(f"PostgreSQL: {PG_HOST}:{PG_PORT}/{PG_DATABASE}")
    print(f"Starting server on http://localhost:5000")
    print("="*60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

