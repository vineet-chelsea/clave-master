"""
REST API Server for Sensor Readings
Provides endpoints for frontend to get latest sensor data
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import psycopg2
import os
import io
from datetime import datetime
from dotenv import load_dotenv
import pytz
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_agg import FigureCanvasAgg

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# PostgreSQL configuration
PG_HOST = os.getenv('PG_HOST', '127.0.0.1')
PG_PORT = os.getenv('PG_PORT', '5432')
PG_DATABASE = os.getenv('PG_DATABASE', 'autoclave')
PG_USER = os.getenv('PG_USER', 'postgres')
PG_PASSWORD = os.getenv('PG_PASSWORD', 'postgres')

# IST timezone (UTC+5:30)
IST = pytz.timezone('Asia/Kolkata')

def get_ist_now():
    """Get current datetime in IST timezone"""
    return datetime.now(IST)

def get_db_connection():
    """Create database connection with IST timezone"""
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD
    )
    # Set timezone to IST
    cursor = conn.cursor()
    cursor.execute("SET timezone = 'Asia/Kolkata'")
    conn.commit()
    cursor.close()
    return conn

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
            # No readings yet - return default values
            return jsonify({
                'timestamp': None,
                'pressure': 0,
                'temperature': 25
            })
    except Exception as e:
        import traceback
        print(f"[ERROR] get_latest_reading: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e), 'detail': traceback.format_exc()}), 500

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
    """Get all process sessions with pagination support"""
    try:
        # Get database connection first
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page_param = request.args.get('per_page', type=int)
        
        # If per_page is not specified or is 0, get all sessions (no pagination)
        if per_page_param is None or per_page_param <= 0:
            # Get all sessions without limit
            cursor.execute("""
                SELECT id, program_name, status, start_time, end_time, target_pressure, duration_minutes, steps_data,
                       roll_category_name, sub_roll_name, roll_id, operator_name, number_of_rolls
                FROM process_sessions 
                ORDER BY start_time DESC
            """)
            rows = cursor.fetchall()
            
            # Get total count
            cursor.execute("SELECT COUNT(*) FROM process_sessions")
            total_count = cursor.fetchone()[0]
            
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
                    'steps_data': row[7] if row[7] else None,
                    'roll_category_name': row[8] if len(row) > 8 else None,
                    'sub_roll_name': row[9] if len(row) > 9 else None,
                    'roll_id': row[10] if len(row) > 10 else None,
                    'operator_name': row[11] if len(row) > 11 else None,
                    'number_of_rolls': int(row[12]) if len(row) > 12 and row[12] else None
                }
                for row in rows
            ]
            
            # Deduplicate (same logic as below)
            seen_sessions = {}
            deduplicated = []
            
            for session in sessions:
                if session['roll_category_name']:
                    key = f"{session['start_time']}_{session['program_name']}_{session['roll_category_name']}"
                else:
                    key = f"{session['start_time']}_{session['program_name']}"
                
                if key not in seen_sessions:
                    seen_sessions[key] = session
                    deduplicated.append(session)
                else:
                    existing = seen_sessions[key]
                    if session['roll_category_name'] and not existing['roll_category_name']:
                        deduplicated.remove(existing)
                        deduplicated.append(session)
                        seen_sessions[key] = session
                    elif session['roll_category_name'] == existing['roll_category_name']:
                        session_fields = sum(1 for v in [session.get('roll_category_name'), session.get('sub_roll_name'), 
                                                         session.get('roll_id'), session.get('operator_name'), 
                                                         session.get('number_of_rolls')] if v is not None)
                        existing_fields = sum(1 for v in [existing.get('roll_category_name'), existing.get('sub_roll_name'),
                                                           existing.get('roll_id'), existing.get('operator_name'),
                                                           existing.get('number_of_rolls')] if v is not None)
                        if session_fields > existing_fields:
                            deduplicated.remove(existing)
                            deduplicated.append(session)
                            seen_sessions[key] = session
            
            return jsonify({
                'sessions': deduplicated,
                'pagination': {
                    'page': 1,
                    'per_page': len(deduplicated),
                    'total': total_count,
                    'total_pages': 1,
                    'has_next': False,
                    'has_prev': False
                }
            })
        
        # Validate parameters for pagination
        page = max(1, page)  # Page must be at least 1
        per_page = min(max(1, per_page_param), 1000)  # Between 1 and 1000
        
        offset = (page - 1) * per_page
        
        # Get total count for pagination
        cursor.execute("SELECT COUNT(*) FROM process_sessions")
        total_count = cursor.fetchone()[0]
        
        # Get paginated sessions
        cursor.execute("""
            SELECT id, program_name, status, start_time, end_time, target_pressure, duration_minutes, steps_data,
                   roll_category_name, sub_roll_name, roll_id, operator_name, number_of_rolls
            FROM process_sessions 
            ORDER BY start_time DESC 
            LIMIT %s OFFSET %s
        """, (per_page, offset))
        
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
                'steps_data': row[7] if row[7] else None,
                'roll_category_name': row[8] if len(row) > 8 else None,
                'sub_roll_name': row[9] if len(row) > 9 else None,
                'roll_id': row[10] if len(row) > 10 else None,
                'operator_name': row[11] if len(row) > 11 else None,
                'number_of_rolls': int(row[12]) if len(row) > 12 and row[12] else None
            }
            for row in rows
        ]
        
        # Deduplicate sessions: If multiple sessions have same start_time, program_name, and roll_category_name,
        # keep only the one with roll details (roll_category_name is not null) or the one with more details
        seen_sessions = {}
        deduplicated = []
        
        for session in sessions:
            # Create a key based on start_time, program_name, and roll_category_name
            # For auto programs, use roll_category_name as part of the key
            if session['roll_category_name']:
                key = f"{session['start_time']}_{session['program_name']}_{session['roll_category_name']}"
            else:
                key = f"{session['start_time']}_{session['program_name']}"
            
            if key not in seen_sessions:
                # First time seeing this key - add it
                seen_sessions[key] = session
                deduplicated.append(session)
            else:
                # Duplicate found - keep the one with more details (roll_category_name, etc.)
                existing = seen_sessions[key]
                
                # Prefer session with roll_category_name over one without
                if session['roll_category_name'] and not existing['roll_category_name']:
                    # Replace with the one that has roll details
                    deduplicated.remove(existing)
                    deduplicated.append(session)
                    seen_sessions[key] = session
                elif session['roll_category_name'] == existing['roll_category_name']:
                    # Both have same roll_category_name - prefer the one with more non-null fields
                    session_fields = sum(1 for v in [session.get('roll_category_name'), session.get('sub_roll_name'), 
                                                     session.get('roll_id'), session.get('operator_name'), 
                                                     session.get('number_of_rolls')] if v is not None)
                    existing_fields = sum(1 for v in [existing.get('roll_category_name'), existing.get('sub_roll_name'),
                                                       existing.get('roll_id'), existing.get('operator_name'),
                                                       existing.get('number_of_rolls')] if v is not None)
                    
                    if session_fields > existing_fields:
                        deduplicated.remove(existing)
                        deduplicated.append(session)
                        seen_sessions[key] = session
                # Otherwise keep the existing one
        
        # Calculate pagination metadata
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        
        return jsonify({
            'sessions': deduplicated,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        })
    except Exception as e:
        import traceback
        print(f"[ERROR] get_sessions: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e), 'detail': traceback.format_exc()}), 500

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

@app.route('/api/sessions/<int:session_id>/pdf', methods=['GET'])
def generate_pdf_report(session_id):
    """Generate 2-page PDF report for a session"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get session details
        cursor.execute("""
            SELECT id, program_name, status, start_time, end_time, target_pressure, duration_minutes,
                   roll_category_name, sub_roll_name, roll_id, operator_name, number_of_rolls
            FROM process_sessions 
            WHERE id=%s
        """, (session_id,))
        
        session_row = cursor.fetchone()
        if not session_row:
            return jsonify({'error': 'Session not found'}), 404
        
        session_id_db, program_name, status, start_time, end_time, target_pressure, duration_minutes, \
        roll_category_name, sub_roll_name, roll_id, operator_name, number_of_rolls = session_row
        
        # Get sensor readings for the session
        if end_time:
            cursor.execute("""
                SELECT timestamp, pressure, temperature 
                FROM sensor_readings 
                WHERE timestamp >= %s AND timestamp <= %s 
                ORDER BY timestamp ASC
            """, (start_time, end_time))
        else:
            cursor.execute("""
                SELECT timestamp, pressure, temperature 
                FROM sensor_readings 
                WHERE timestamp >= %s
                ORDER BY timestamp ASC
                LIMIT 1000
            """, (start_time,))
        
        readings = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not readings:
            return jsonify({'error': 'No sensor readings found for this session'}), 404
        
        # Create PDF in memory - A4 size for printing
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            topMargin=0.75*inch, 
            bottomMargin=0.75*inch,
            leftMargin=0.75*inch,
            rightMargin=0.75*inch
        )
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles - optimized for A4 printing
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=14,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=10,
            alignment=TA_CENTER,
            leading=16
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            spaceAfter=5,
            leading=13
        )
        
        # PAGE 1: Title and Charts
        # Title section
        story.append(Paragraph("AUTOCLAVE PROCESS REPORT", title_style))
        story.append(Spacer(1, 0.1*inch))
        
        # Session Information Table
        info_data = []
        
        # Roll Category Name - always show
        if roll_category_name:
            info_data.append(['Roll Category Name:', roll_category_name])
        elif program_name:
            info_data.append(['Program Name:', program_name])
        else:
            info_data.append(['Program Name:', f'Session {session_id}'])
        
        # Roll Name (Sub-Roll Name) - always show
        if sub_roll_name:
            info_data.append(['Roll Name:', sub_roll_name])
        elif roll_category_name:
            info_data.append(['Roll Name:', roll_category_name])
        else:
            info_data.append(['Roll Name:', 'N/A'])
        
        # Quantity - always show
        if number_of_rolls:
            info_data.append(['Quantity:', str(number_of_rolls)])
        else:
            info_data.append(['Quantity:', 'N/A'])
        
        # Operator Name - always show
        if operator_name:
            info_data.append(['Operator Name:', operator_name])
        else:
            info_data.append(['Operator Name:', 'N/A'])
        
        # Roll ID - always show
        if roll_id:
            info_data.append(['Roll ID:', roll_id])
        else:
            info_data.append(['Roll ID:', 'N/A'])
        
        # Session timing
        if start_time:
            info_data.append(['Start Time:', start_time.strftime('%Y-%m-%d %H:%M:%S')])
        if end_time:
            info_data.append(['End Time:', end_time.strftime('%Y-%m-%d %H:%M:%S')])
        if duration_minutes:
            info_data.append(['Duration:', f'{duration_minutes} minutes'])
        
        # Report generation timestamp
        info_data.append(['Report Generated:', get_ist_now().strftime('%Y-%m-%d %H:%M:%S')])
        
        # Create information table
        if info_data:
            info_table = Table(info_data, colWidths=[2.2*inch, 4.3*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('LEADING', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))
            story.append(info_table)
        
        story.append(Spacer(1, 0.2*inch))
        
        # Prepare data for charts - use ALL readings for entire session
        timestamps = [r[0] for r in readings]
        pressures = [float(r[1]) for r in readings]
        temperatures = [float(r[2]) for r in readings]
        
        # Ensure we have data
        if not timestamps or not pressures or not temperatures:
            return jsonify({'error': 'No valid sensor data found for charts'}), 404
        
        # Create pressure chart - sized for A4, showing ENTIRE session
        fig_pressure = plt.figure(figsize=(6.5, 2.8))
        ax_pressure = fig_pressure.add_subplot(111)
        
        # Plot ALL data points for entire session
        ax_pressure.plot(timestamps, pressures, color='#2563eb', linewidth=1.5)
        
        # Set x-axis to show full time range from start to end
        if len(timestamps) > 0:
            ax_pressure.set_xlim([timestamps[0], timestamps[-1]])
        
        # Set y-axis scale: 5 to 60 PSI with sequential ticks (5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60)
        ax_pressure.set_ylim([5, 60])
        pressure_ticks = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
        ax_pressure.set_yticks(pressure_ticks)
        ax_pressure.set_yticklabels([str(tick) for tick in pressure_ticks])  # Explicitly set labels to ensure correct display
        
        # Format x-axis to show time range clearly
        ax_pressure.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        ax_pressure.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=8))
        
        ax_pressure.set_xlabel('Time', fontsize=9)
        ax_pressure.set_ylabel('Pressure (PSI)', fontsize=9, color='#2563eb')
        ax_pressure.tick_params(axis='y', labelcolor='#2563eb')
        ax_pressure.grid(True, alpha=0.3)
        ax_pressure.set_title('Pressure Chart - Entire Session', fontsize=11, fontweight='bold')
        plt.xticks(rotation=45, fontsize=8)
        plt.tight_layout()
        
        # Save pressure chart to buffer
        img_buffer_pressure = io.BytesIO()
        fig_pressure.savefig(img_buffer_pressure, format='png', dpi=100, bbox_inches='tight')
        img_buffer_pressure.seek(0)
        img_pressure = Image(img_buffer_pressure, width=6.2*inch, height=2.6*inch)
        story.append(img_pressure)
        plt.close(fig_pressure)
        
        story.append(Spacer(1, 0.15*inch))
        
        # Create temperature chart - sized for A4, showing ENTIRE session
        fig_temp = plt.figure(figsize=(6.5, 2.8))
        ax_temp = fig_temp.add_subplot(111)
        
        # Plot ALL data points for entire session
        ax_temp.plot(timestamps, temperatures, color='#dc2626', linewidth=1.5)
        
        # Set x-axis to show full time range from start to end
        if len(timestamps) > 0:
            ax_temp.set_xlim([timestamps[0], timestamps[-1]])
        
        # Set y-axis scale: 20 to 160 °C with specified ticks (20, 40, 60, 80, 100, 120, 140, 160)
        ax_temp.set_ylim([20, 160])
        temp_ticks = [20, 40, 60, 80, 100, 120, 140, 160]
        ax_temp.set_yticks(temp_ticks)
        ax_temp.set_yticklabels([str(tick) for tick in temp_ticks])  # Explicitly set labels to ensure correct display
        
        # Format x-axis to show time range clearly
        ax_temp.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        ax_temp.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=8))
        
        ax_temp.set_xlabel('Time', fontsize=9)
        ax_temp.set_ylabel('Temperature (°C)', fontsize=9, color='#dc2626')
        ax_temp.tick_params(axis='y', labelcolor='#dc2626')
        ax_temp.grid(True, alpha=0.3)
        ax_temp.set_title('Temperature Chart - Entire Session', fontsize=11, fontweight='bold')
        plt.xticks(rotation=45, fontsize=8)
        plt.tight_layout()
        
        # Save temperature chart to buffer
        img_buffer_temp = io.BytesIO()
        fig_temp.savefig(img_buffer_temp, format='png', dpi=100, bbox_inches='tight')
        img_buffer_temp.seek(0)
        img_temp = Image(img_buffer_temp, width=6.2*inch, height=2.6*inch)
        story.append(img_temp)
        plt.close(fig_temp)
        
        # No page break - continue on same page (page 2)
        story.append(Spacer(1, 0.2*inch))
        
        # PAGE 2: Combined Data Table
        story.append(Paragraph("Sensor Readings Data", title_style))
        story.append(Spacer(1, 0.15*inch))
        
        # Sample 72 records evenly across time range
        max_records = min(72, len(readings))
        
        # Calculate step size to evenly sample across all readings
        if len(readings) > max_records:
            step_size = len(readings) / max_records
        else:
            step_size = 1
        
        # Sample indices evenly across the time range
        sampled_indices = []
        for i in range(max_records):
            idx = int(i * step_size)
            if idx < len(readings):
                sampled_indices.append(idx)
        
        # Ensure we have first and last records
        if len(readings) > 1:
            if 0 not in sampled_indices:
                sampled_indices[0] = 0
            if (len(readings) - 1) not in sampled_indices:
                sampled_indices[-1] = len(readings) - 1
            sampled_indices = sorted(list(set(sampled_indices)))[:max_records]
        
        # Combined table with Timestamp, Pressure, and Temperature
        combined_data = [['Timestamp', 'Pressure (PSI)', 'Temperature (°C)']]
        for idx in sampled_indices:
            if idx < len(readings):
                ts = readings[idx][0]
                pressure = readings[idx][1]
                temperature = readings[idx][2]
                combined_data.append([
                    ts.strftime('%Y-%m-%d %H:%M:%S') if isinstance(ts, datetime) else str(ts),
                    f"{float(pressure):.2f}",
                    f"{float(temperature):.2f}"
                ])
        
        # Create combined table with 3 columns
        combined_table = Table(combined_data, colWidths=[2.5*inch, 1.8*inch, 1.8*inch])
        combined_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (2, -1), 'CENTER'),  # Center align pressure and temperature values
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('LEADING', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        story.append(Paragraph("Sensor Readings (72 equally spaced values)", heading_style))
        story.append(combined_table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        # Generate filename
        roll_name = roll_category_name or program_name or 'Session'
        filename = f"Report_{roll_name.replace(' ', '_')}_{session_id}_{get_ist_now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        import traceback
        print(f"[ERROR] PDF generation failed: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'detail': traceback.format_exc()}), 500

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
        
        # CRITICAL: Stop all old running/paused sessions before starting new one
        cursor.execute("""
            UPDATE process_sessions 
            SET status='stopped', end_time=%s 
            WHERE status IN ('running', 'paused')
        """, (get_ist_now(),))
        old_sessions_stopped = cursor.rowcount
        if old_sessions_stopped > 0:
            print(f"[API] Stopped {old_sessions_stopped} old running/paused session(s) before starting new manual control")
        
        # Store control parameters in session metadata
        cursor.execute(
            "INSERT INTO process_sessions (program_name, status, start_time, target_pressure, duration_minutes) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (program_name, 'running', get_ist_now(), float(target_pressure), int(duration_minutes))
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
        
        # Get session_id from request body if provided
        session_id = None
        if request.is_json:
            data = request.get_json()
            session_id = data.get('session_id') if data else None
        
        # If session_id is provided, update that specific session
        if session_id:
            try:
                session_id = int(session_id)
            except (ValueError, TypeError):
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'error': 'Invalid session_id'}), 400
            
            # Check if session exists and is not already completed
            cursor.execute(
                "SELECT status FROM process_sessions WHERE id=%s",
                (session_id,)
            )
            session = cursor.fetchone()
            
            if not session:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'error': 'Session not found'}), 404
            
            current_status = session[0]
            
            # Don't update if already completed
            if current_status == 'completed':
                cursor.close()
                conn.close()
                return jsonify({'success': True, 'rows_affected': 0, 'message': 'Session already completed'})
            
            # Update to stopped if running or paused
            cursor.execute(
                "UPDATE process_sessions SET status='stopped', end_time=%s WHERE id=%s AND status IN ('running', 'paused')",
                (get_ist_now(), session_id)
            )
            rows_affected = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'rows_affected': rows_affected
            })
        
        # Fallback: Update most recent running or paused session
        # Use subquery to get the most recent session ID first, then update it
        cursor.execute("""
            UPDATE process_sessions 
            SET status='stopped', end_time=%s 
            WHERE id = (
                SELECT id FROM process_sessions 
                WHERE status IN ('running', 'paused') 
                ORDER BY id DESC 
                LIMIT 1
            )
        """, (get_ist_now(),))
        rows_affected = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'rows_affected': rows_affected
        })
    except Exception as e:
        print(f"[ERROR] Failed to stop: {e}")
        import traceback
        traceback.print_exc()
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

@app.route('/api/roll-categories', methods=['GET'])
def get_roll_categories():
    """Get all roll categories"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, category_name, is_active
            FROM roll_categories
            WHERE is_active = true
            ORDER BY id
        """)
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        categories = [
            {
                'id': row[0],
                'category_name': row[1],
                'is_active': row[2]
            }
            for row in rows
        ]
        
        return jsonify(categories)
    except Exception as e:
        print(f"[ERROR] Failed to get roll categories: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/programs', methods=['GET'])
def get_programs():
    """Get all auto programs"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, program_number, program_name, description, steps, roll_category_name
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
                'steps': row[4],  # JSONB already parsed by psycopg2
                'roll_category_name': row[5]
            }
            for row in rows
        ]
        
        return jsonify(programs)
    except Exception as e:
        print(f"[ERROR] Failed to get programs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/programs/by-category', methods=['GET'])
def get_program_by_category():
    """Get program for roll category + quantity"""
    try:
        roll_category_name = request.args.get('roll_category_name')
        number_of_rolls = request.args.get('number_of_rolls', type=int)
        
        if not roll_category_name or not number_of_rolls:
            return jsonify({'error': 'roll_category_name and number_of_rolls are required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Find program by roll category name
        cursor.execute("""
            SELECT id, program_number, program_name, description, steps
            FROM autoclave_programs
            WHERE roll_category_name = %s
            LIMIT 1
        """, (roll_category_name,))
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not row:
            return jsonify({'error': f'No program found for roll category: {roll_category_name}'}), 404
        
        program_id, program_number, program_name, description, steps = row
        
        # Calculate steps based on quantity
        # Determine quantity range (1-3 or 4+)
        quantity_range = "1-3" if number_of_rolls <= 3 else "4+"
        
        # If steps has quantity_variations structure, apply it
        if isinstance(steps, dict) and 'base_steps' in steps and 'quantity_variations' in steps:
            base_steps = steps['base_steps']
            quantity_variations = steps['quantity_variations']
            
            # Get final step variation for this quantity
            final_step = None
            if quantity_range in quantity_variations:
                final_step = quantity_variations[quantity_range].get('final_step')
            
            # Combine base steps with final step
            calculated_steps = base_steps.copy()
            if final_step:
                calculated_steps.append(final_step)
            
            steps = calculated_steps
        
        return jsonify({
            'id': program_id,
            'program_number': program_number,
            'program_name': program_name,
            'description': description or '',
            'steps': steps,
            'quantity_range': quantity_range,
            'number_of_rolls': number_of_rolls
        })
    except Exception as e:
        print(f"[ERROR] Failed to get program by category: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/start-auto-program', methods=['POST'])
def start_auto_program():
    """Start an auto program with multiple steps"""
    try:
        data = request.json
        
        # New fields for roll category system
        roll_category_name = data.get('roll_category_name')
        number_of_rolls = data.get('number_of_rolls')
        sub_roll_name = data.get('sub_roll_name')
        roll_id = data.get('roll_id')
        operator_name = data.get('operator_name')
        
        # Legacy support - if roll_category_name is provided, use new system
        if roll_category_name and number_of_rolls:
            # Get program by category and quantity directly from database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Find program by roll category name
            cursor.execute("""
                SELECT id, program_number, program_name, description, steps
                FROM autoclave_programs
                WHERE roll_category_name = %s
                LIMIT 1
            """, (roll_category_name,))
            
            row = cursor.fetchone()
            
            if not row:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'error': f'No program found for roll category: {roll_category_name}'}), 404
            
            program_id, program_number, program_name, description, steps = row
            
            # Calculate steps based on quantity
            # Determine quantity range (1-3 or 4+)
            quantity_range = "1-3" if number_of_rolls <= 3 else "4+"
            
            # If steps has quantity_variations structure, apply it
            if isinstance(steps, dict) and 'base_steps' in steps and 'quantity_variations' in steps:
                base_steps = steps['base_steps']
                quantity_variations = steps['quantity_variations']
                
                # Get final step variation for this quantity
                final_step = None
                if quantity_range in quantity_variations:
                    final_step = quantity_variations[quantity_range].get('final_step')
                
                # Combine base steps with final step
                calculated_steps = base_steps.copy()
                if final_step:
                    calculated_steps.append(final_step)
                
                steps = calculated_steps
            
            cursor.close()
            conn.close()
            
            # Default sub_roll_name to roll_category_name if not provided
            if not sub_roll_name:
                sub_roll_name = roll_category_name
        else:
            # Legacy mode - use provided steps directly
            program_name = data.get('program_name', 'Auto Program')
            steps = data.get('steps', [])
            if not steps:
                return jsonify({'success': False, 'error': 'No steps provided'}), 400
        
        # Calculate total duration
        total_duration = sum(step.get('duration_minutes', 0) for step in steps)
        
        # Parse pressure from range (e.g., "5-10" -> 7.5, "40-45" -> 42.5)
        def parse_pressure(psi_range):
            if '-' in str(psi_range):
                parts = str(psi_range).split('-')
                if len(parts) == 2:
                    try:
                        low = float(parts[0].strip())
                        high = float(parts[1].strip())
                        return (high-1)  # Median
                    except:
                        pass
            # Single value or "Steady at X"
            try:
                # Extract number from string
                import re
                numbers = re.findall(r'\d+(?:\.\d+)?', str(psi_range))
                if numbers:
                    return float(numbers[0])
            except:
                pass
            return 0
        
        # Get the first step's target pressure
        if steps:
            first_step = steps[0]
            target_pressure = parse_pressure(first_step.get('psi_range', '0'))
        else:
            target_pressure = 0
        
        # Store program steps in session
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # CRITICAL: Stop all old running/paused sessions before starting new one
        # This ensures only one process runs at a time
        cursor.execute("""
            UPDATE process_sessions 
            SET status='stopped', end_time=%s 
            WHERE status IN ('running', 'paused')
        """, (get_ist_now(),))
        old_sessions_stopped = cursor.rowcount
        if old_sessions_stopped > 0:
            print(f"[API] Stopped {old_sessions_stopped} old running/paused session(s) before starting new process")
        
        # Convert steps to JSON string for storage
        import json
        steps_json = json.dumps(steps)
        
        # Insert session with all new fields - original logic: always create new session with all details
        cursor.execute("""
            INSERT INTO process_sessions 
            (program_name, target_pressure, duration_minutes, status, steps_data,
             roll_category_name, sub_roll_name, roll_id, operator_name, number_of_rolls, start_time)
            VALUES (%s, %s, %s, 'running', %s::jsonb, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            program_name,
            target_pressure,
            total_duration,
            steps_json,
            roll_category_name,
            sub_roll_name,
            roll_id,
            operator_name,
            number_of_rolls,
            get_ist_now()  # Use IST for start_time to match end_time timezone
        ))
        
        session_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"[API] Started auto program: {program_name} (Session {session_id})")
        if steps:
            print(f"[API] First step: {target_pressure} PSI for {steps[0].get('duration_minutes')} min")
        print(f"[API] Total steps: {len(steps)}")
        if roll_category_name:
            print(f"[API] Roll Category: {roll_category_name}, Quantity: {number_of_rolls}")
        
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
        import traceback
        traceback.print_exc()
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

