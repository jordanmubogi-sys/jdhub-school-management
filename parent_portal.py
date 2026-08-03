"""
Parent/Student Portal Web Server
LAN-only PWA for parents and students to view reports, fees, and announcements
"""

from flask import Flask, render_template_string, request, redirect, session, jsonify, send_file
from werkzeug.security import check_password_hash
import sqlite3
import hashlib
import os
from datetime import datetime
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'school_portal_secret_key_2024'

DB_PATH = os.path.join(os.path.dirname(__file__), 'school_data.db')


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def get_school_settings():
    """Get school settings"""
    db = get_db()
    settings = db.execute("SELECT * FROM school_settings WHERE id = 1").fetchone()
    db.close()
    return dict(settings) if settings else {}


# HTML Templates
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Parent Portal - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            width: 400px;
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo h1 {
            color: #2563eb;
            font-size: 24px;
        }
        .logo p {
            color: #64748b;
            font-size: 14px;
            margin-top: 5px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            color: #0f172a;
            font-weight: 500;
            margin-bottom: 8px;
        }
        input {
            width: 100%;
            padding: 15px;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus {
            outline: none;
            border-color: #2563eb;
        }
        .btn {
            width: 100%;
            padding: 15px;
            background: #2563eb;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
        }
        .btn:hover {
            background: #1d4ed8;
        }
        .help {
            text-align: center;
            margin-top: 20px;
            color: #64748b;
            font-size: 13px;
        }
        .error {
            background: #fee2e2;
            color: #dc2626;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
        .school-header {
            background: #2563eb;
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="school-header">
            <h1>{{ school_name }}</h1>
            <p>Parent & Student Portal</p>
        </div>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        <form method="POST">
            <div class="form-group">
                <label>Student ID (e.g., SCH/2026/001)</label>
                <input type="text" name="student_id" placeholder="Enter Student ID" required>
            </div>
            <div class="form-group">
                <label>Password (Parent's Phone Number)</label>
                <input type="password" name="password" placeholder="Enter Password" required>
            </div>
            <button type="submit" class="btn">Sign In</button>
        </form>
        
        <div class="help">
            <p>Username: Student ID | Password: Parent's registered phone number</p>
        </div>
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Parent Portal - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f8fafc;
        }
        .header {
            background: #2563eb;
            color: white;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { font-size: 20px; }
        .header a { color: white; text-decoration: none; }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 30px;
        }
        .welcome {
            background: white;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .welcome h2 { color: #0f172a; margin-bottom: 10px; }
        .welcome p { color: #64748b; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .card h3 {
            color: #0f172a;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .card h3 span { font-size: 24px; }
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #e2e8f0;
        }
        .info-row:last-child { border-bottom: none; }
        .info-label { color: #64748b; }
        .info-value { color: #0f172a; font-weight: 500; }
        .balance { color: #dc2626; font-weight: 600; }
        .success { color: #16a34a; }
        .table {
            width: 100%;
            border-collapse: collapse;
        }
        .table th, .table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }
        .table th { color: #64748b; font-weight: 500; }
        .grade-a { color: #16a34a; font-weight: 600; }
        .grade-b { color: #2563eb; font-weight: 600; }
        .grade-c { color: #ca8a04; font-weight: 600; }
        .grade-f { color: #dc2626; font-weight: 600; }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .tab {
            padding: 10px 20px;
            background: #e2e8f0;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
        }
        .tab.active {
            background: #2563eb;
            color: white;
        }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .announcement {
            background: #eff6ff;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            border-left: 4px solid #2563eb;
        }
        .announcement h4 { color: #0f172a; margin-bottom: 5px; }
        .announcement p { color: #64748b; font-size: 14px; }
        .announcement small { color: #94a3b8; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ school_name }}</h1>
        <a href="/logout">Logout</a>
    </div>
    
    <div class="container">
        <div class="welcome">
            <h2>Welcome, {{ parent_name }}</h2>
            <p>Student: <strong>{{ student_name }}</strong> | Class: <strong>{{ stream_name }}</strong></p>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="showTab('overview')">Overview</button>
            <button class="tab" onclick="showTab('reports')">Report Cards</button>
            <button class="tab" onclick="showTab('fees')">Fees</button>
            <button class="tab" onclick="showTab('attendance')">Attendance</button>
            <button class="tab" onclick="showTab('announcements')">Announcements</button>
        </div>
        
        <div id="overview" class="tab-content active">
            <div class="grid">
                <div class="card">
                    <h3><span>📊</span> Fee Balance</h3>
                    <div class="info-row">
                        <span class="info-label">Total Fees</span>
                        <span class="info-value">KES {{ total_fees|default(0)|int|comma }}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Amount Paid</span>
                        <span class="info-value success">KES {{ total_paid|default(0)|int|comma }}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Balance</span>
                        <span class="info-value balance">KES {{ balance|default(0)|int|comma }}</span>
                    </div>
                </div>
                
                <div class="card">
                    <h3><span>📅</span> Current Term</h3>
                    <div class="info-row">
                        <span class="info-label">Term</span>
                        <span class="info-value">{{ current_term }}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Average Score</span>
                        <span class="info-value">{{ avg_score|default('N/A') }}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Class Position</span>
                        <span class="info-value">{{ position|default('N/A') }}</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="reports" class="tab-content">
            <div class="card">
                <h3><span>📝</span> Term Reports</h3>
                {% if reports %}
                <table class="table">
                    <thead>
                        <tr>
                            <th>Term</th>
                            <th>Average</th>
                            <th>Position</th>
                            <th>Grade</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for report in reports %}
                        <tr>
                            <td>{{ report.term }}</td>
                            <td>{{ report.avg|default('N/A') }}</td>
                            <td>{{ report.position|default('N/A') }}</td>
                            <td><span class="grade-{{ report.grade|lower }}">{{ report.grade|default('N/A') }}</span></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <p style="color: #64748b;">No reports available yet.</p>
                {% endif %}
            </div>
        </div>
        
        <div id="fees" class="tab-content">
            <div class="card">
                <h3><span>💰</span> Payment History</h3>
                {% if payments %}
                <table class="table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Receipt No.</th>
                            <th>Amount</th>
                            <th>Term</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for payment in payments %}
                        <tr>
                            <td>{{ payment.date }}</td>
                            <td>{{ payment.receipt }}</td>
                            <td>KES {{ payment.amount|int|comma }}</td>
                            <td>{{ payment.term }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <p style="color: #64748b;">No payment history available.</p>
                {% endif %}
            </div>
        </div>
        
        <div id="attendance" class="tab-content">
            <div class="card">
                <h3><span>📅</span> Attendance Summary</h3>
                <div class="info-row">
                    <span class="info-label">Days Present</span>
                    <span class="info-value success">{{ attendance.days_present|default(0) }}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Days Absent</span>
                    <span class="info-value" style="color: #dc2626;">{{ attendance.days_absent|default(0) }}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Days Late</span>
                    <span class="info-value">{{ attendance.days_late|default(0) }}</span>
                </div>
            </div>
        </div>
        
        <div id="announcements" class="tab-content">
            {% for ann in announcements %}
            <div class="announcement">
                <h4>{{ ann.title }}</h4>
                <p>{{ ann.content }}</p>
                <small>{{ ann.date }}</small>
            </div>
            {% else %}
            <p style="color: #64748b;">No announcements.</p>
            {% endfor %}
        </div>
    </div>
    
    <script>
        function showTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
        }
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Landing page / Login"""
    if 'student_id' in session:
        return redirect('/dashboard')
    
    school = get_school_settings()
    return render_template_string(
        LOGIN_TEMPLATE,
        school_name=school.get('school_name', 'School'),
        error=request.args.get('error', '')
    )


@app.route('/login', methods=['POST'])
def login():
    """Handle login"""
    student_id = request.form.get('student_id', '').strip()
    password = request.form.get('password', '').strip()
    
    if not student_id or not password:
        return redirect('/?error=Please enter credentials')
    
    db = get_db()
    
    # Verify student
    student = db.execute(
        "SELECT s.*, st.stream_name FROM students s LEFT JOIN streams st ON s.stream_id = st.id WHERE s.student_id = ?",
        (student_id,)
    ).fetchone()
    
    if not student:
        db.close()
        return redirect('/?error=Student not found')
    
    # Verify parent password (phone number)
    parent = db.execute(
        "SELECT * FROM parents WHERE student_id = ? AND is_primary = 1",
        (student_id,)
    ).fetchone()
    
    if not parent:
        db.close()
        return redirect('/?error=Parent not registered')
    
    # Check password
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if parent['primary_phone'] != password:
        db.close()
        return redirect('/?error=Invalid password')
    
    session['student_id'] = student_id
    session['parent_name'] = parent['parent_name']
    session['student_name'] = f"{student['first_name']} {student['last_name']}"
    session['stream_name'] = student['stream_name'] or 'N/A'
    
    db.close()
    return redirect('/dashboard')


@app.route('/dashboard')
def dashboard():
    """Dashboard view"""
    if 'student_id' not in session:
        return redirect('/')
    
    student_id = session['student_id']
    db = get_db()
    school = get_school_settings()
    
    # Get current term
    current_term = db.execute(
        "SELECT * FROM academic_terms WHERE is_current = 1 LIMIT 1"
    ).fetchone()
    
    # Get fee summary
    fee_summary = db.execute("""
        SELECT 
            COALESCE(SUM(fs.amount), 0) as total,
            (SELECT COALESCE(SUM(amount_paid), 0) FROM fee_payments WHERE student_id = ?) as paid
        FROM fee_structure fs
        WHERE fs.stream_id = (SELECT stream_id FROM students WHERE student_id = ?)
    """, (student_id, student_id)).fetchone()
    
    # Get marks
    if current_term:
        marks = db.execute("""
            SELECT m.*, sub.subject_name 
            FROM marks m 
            JOIN subjects sub ON m.subject_id = sub.id
            WHERE m.student_id = ? AND m.term_id = ?
            ORDER BY sub.subject_name
        """, (student_id, current_term['id'])).fetchall()
        
        avg_score = sum(m['total_score'] or 0 for m in marks) / len(marks) if marks else 0
        position = db.execute("""
            SELECT COUNT(*) + 1 as pos FROM marks 
            WHERE term_id = ? AND total_score > ?
        """, (current_term['id'], avg_score)).fetchone() if avg_score else None
    else:
        marks = []
        avg_score = 0
        position = None
    
    # Get attendance
    attendance = db.execute("""
        SELECT * FROM attendance WHERE student_id = ? AND term_id = ?
    """, (student_id, current_term['id'] if current_term else None)).fetchone() if current_term else None
    
    # Get payments
    payments = db.execute("""
        SELECT fp.*, at.term_name
        FROM fee_payments fp
        LEFT JOIN academic_terms at ON fp.term_id = at.id
        WHERE fp.student_id = ?
        ORDER BY fp.payment_date DESC
        LIMIT 10
    """, (student_id,)).fetchall()
    
    # Get announcements
    announcements = db.execute("""
        SELECT * FROM announcements 
        WHERE is_active = 1 
        ORDER BY created_at DESC 
        LIMIT 10
    """).fetchall()
    
    db.close()
    
    # Jinja filters
    def comma(value):
        return f"{value:,}" if value else "0"
    
    template = DASHBOARD_TEMPLATE.replace('{{ total_fees|default(0)|int|comma }}', str(fee_summary['total'] if fee_summary else 0))
    template = template.replace('{{ total_paid|default(0)|int|comma }}', str(fee_summary['paid'] if fee_summary else 0))
    template = template.replace('{{ balance|default(0)|int|comma }}', str((fee_summary['total'] - fee_summary['paid']) if fee_summary else 0))
    template = template.replace('|int|comma', '')
    template = template.replace('|default(0)', '')
    
    return render_template_string(
        template,
        school_name=school.get('school_name', 'School'),
        student_name=session['student_name'],
        stream_name=session['stream_name'],
        parent_name=session['parent_name'],
        current_term=f"{current_term['term_name']} {current_term['academic_year']}" if current_term else "N/A",
        total_fees=fee_summary['total'] if fee_summary else 0,
        total_paid=fee_summary['paid'] if fee_summary else 0,
        balance=(fee_summary['total'] - fee_summary['paid']) if fee_summary else 0,
        avg_score=f"{avg_score:.1f}" if avg_score else "N/A",
        position=position['pos'] if position else "N/A",
        attendance=dict(attendance) if attendance else {'days_present': 0, 'days_absent': 0, 'days_late': 0},
        payments=[dict(p) for p in payments],
        announcements=[dict(a) for a in announcements],
        reports=[],  # Simplified for now
    )


@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect('/')


def run_server(host='0.0.0.0', port=8000):
    """Run the portal server"""
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == '__main__':
    run_server()
