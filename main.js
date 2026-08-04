const { app, BrowserWindow, ipcMain, dialog, Menu, Tray, nativeImage } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');
const crypto = require('crypto');
const http = require('http');
const { v4: uuidv4 } = require('uuid');

// Data storage paths
const USER_DATA_PATH = app.getPath('userData');
const LICENSE_FILE = path.join(USER_DATA_PATH, 'license.json');
const DATABASE_FILE = path.join(USER_DATA_PATH, 'school_data.json');
const CONFIG_FILE = path.join(USER_DATA_PATH, 'config.json');
const BACKUP_DIR = path.join(USER_DATA_PATH, 'backups');
const AUDIT_LOG_FILE = path.join(USER_DATA_PATH, 'audit.log');

// Ensure directories exist
if (!fs.existsSync(BACKUP_DIR)) fs.mkdirSync(BACKUP_DIR, { recursive: true });

// ============== HARDWARE FINGERPRINTING ==============
function getMachineId() {
    try {
        const uuid = require('uuid').v4;
        const hostname = os.hostname();
        const platform = os.platform();
        const arch = os.arch();
        const cpus = os.cpus()[0];
        const cpuId = cpus ? `${cpus.model}-${cpus.speed}` : 'unknown';
        const totalMem = os.totalmem();
        const mac = getMacAddress();
        
        const raw = `${hostname}|${platform}|${arch}|${cpuId}|${totalMem}|${mac}|${uuid()}`;
        const hash = crypto.createHash('sha256').update(raw).digest('hex').substring(0, 32).toUpperCase();
        return `JD-${hash.substring(0, 4)}-${hash.substring(4, 8)}-${hash.substring(8, 12)}-${hash.substring(12, 16)}`;
    } catch (e) {
        return 'JD-DEMO-MACH-INEID';
    }
}

function getMacAddress() {
    const interfaces = os.networkInterfaces();
    for (const name of Object.keys(interfaces)) {
        for (const iface of interfaces[name]) {
            if (!iface.internal && iface.mac !== '00:00:00:00:00:00') {
                return iface.mac;
            }
        }
    }
    return '00:00:00:00:00:00';
}

function getLocalIP() {
    const interfaces = os.networkInterfaces();
    for (const name of Object.keys(interfaces)) {
        for (const iface of interfaces[name]) {
            if (iface.family === 'IPv4' && !iface.internal) {
                return iface.address;
            }
        }
    }
    return '127.0.0.1';
}

// ============== LICENSE MANAGEMENT ==============
function validateLicense(licenseKey, machineId) {
    // Demo key always works
    if (licenseKey === 'JD-DEMO-2024-ENTERPRISE') return { valid: true, type: 'demo' };
    
    // Generate expected key from machine ID
    const parts = machineId.replace('JD-', '').split('-');
    if (parts.length !== 4) return { valid: false };
    
    const expectedKey = `JD-${parts[0]}-${parts[1]}-${parts[2]}-${parts[3]}`;
    if (licenseKey === expectedKey) {
        return { valid: true, type: 'full' };
    }
    
    return { valid: false };
}

function saveLicense(licenseData) {
    fs.writeFileSync(LICENSE_FILE, JSON.stringify(licenseData, null, 2));
}

function loadLicense() {
    try {
        if (fs.existsSync(LICENSE_FILE)) {
            return JSON.parse(fs.readFileSync(LICENSE_FILE, 'utf8'));
        }
    } catch (e) {}
    return null;
}

// ============== DATABASE OPERATIONS ==============
function getDatabase() {
    try {
        if (fs.existsSync(DATABASE_FILE)) {
            return JSON.parse(fs.readFileSync(DATABASE_FILE, 'utf8'));
        }
    } catch (e) {}
    return getDefaultDatabase();
}

function saveDatabase(data) {
    fs.writeFileSync(DATABASE_FILE, JSON.stringify(data, null, 2));
    logAudit('DATABASE_SAVE', 'System', 'Database saved');
}

function getDefaultDatabase() {
    return {
        settings: {
            schoolName: 'Demo School',
            schoolAddress: '',
            schoolPhone: '',
            schoolEmail: '',
            schoolWebsite: '',
            currentTerm: 'Term 1',
            currentYear: '2024',
            gradingScheme: 'standard',
            features: {
                photoProcessing: true,
                pdfBranding: true,
                emailLetters: false,
                cloudBackup: false
            }
        },
        users: [
            { id: 'USR001', username: 'jordan', password: 'jordan123', name: 'Jordan (Super Admin)', role: 'super_admin', email: '', phone: '', active: true },
            { id: 'USR002', username: 'admin', password: 'admin123', name: 'School Administrator', role: 'admin', email: '', phone: '', active: true },
            { id: 'USR003', username: 'director', password: 'pass123', name: 'School Director', role: 'director', email: '', phone: '', active: true },
            { id: 'USR004', username: 'dos', password: 'pass123', name: 'Director of Studies', role: 'dos', email: '', phone: '', active: true },
            { id: 'USR005', username: 'teacher1', password: 'pass123', name: 'Class Teacher', role: 'class_teacher', email: '', phone: '', active: true },
            { id: 'USR006', username: 'subject1', password: 'pass123', name: 'Subject Teacher', role: 'subject_teacher', email: '', phone: '', active: true },
            { id: 'USR007', username: 'bursar', password: 'pass123', name: 'School Bursar', role: 'bursar', email: '', phone: '', active: true },
            { id: 'USR008', username: 'secretary', password: 'pass123', name: 'School Secretary', role: 'secretary', email: '', phone: '', active: true }
        ],
        students: [
            { id: 'STD001', admissionNo: 'SCH/2024/001', firstName: 'Alice', lastName: 'Nakato', class: 'S.4', stream: 'Science', gender: 'Female', dob: '2008-05-15', parentName: 'John Nakato', parentPhone: '0771234567', address: '', photo: null, status: 'active', admittedDate: '2024-01-15' },
            { id: 'STD002', admissionNo: 'SCH/2024/002', firstName: 'Bob', lastName: 'Mukasa', class: 'S.4', stream: 'Science', gender: 'Male', dob: '2008-03-20', parentName: 'Mary Mukasa', parentPhone: '0782345678', address: '', photo: null, status: 'active', admittedDate: '2024-01-15' },
            { id: 'STD003', admissionNo: 'SCH/2024/003', firstName: 'Carol', lastName: 'Amono', class: 'S.3', stream: 'Arts', gender: 'Female', dob: '2009-08-10', parentName: 'Peter Amono', parentPhone: '0773456789', address: '', photo: null, status: 'active', admittedDate: '2024-01-15' },
            { id: 'STD004', admissionNo: 'SCH/2024/004', firstName: 'David', lastName: 'Ssemakula', class: 'S.4', stream: 'Commerce', gender: 'Male', dob: '2008-11-25', parentName: 'Grace Ssemakula', parentPhone: '0784567890', address: '', photo: null, status: 'active', admittedDate: '2024-01-15' },
            { id: 'STD005', admissionNo: 'SCH/2024/005', firstName: 'Eve', lastName: 'Nabisere', class: 'S.2', stream: 'Science', gender: 'Female', dob: '2010-02-14', parentName: 'James Nabisere', parentPhone: '0775678901', address: '', photo: null, status: 'active', admittedDate: '2024-01-15' }
        ],
        staff: [
            { id: 'STF001', staffNo: 'TCH001', firstName: 'Kigozi', lastName: 'John', role: 'Teacher', subjects: ['Mathematics'], classes: ['S.4'], gender: 'Male', phone: '0771111111', email: '', status: 'active' },
            { id: 'STF002', staffNo: 'TCH002', firstName: 'Nakato', lastName: 'Sarah', role: 'Head of Department', subjects: ['English'], classes: ['S.1', 'S.2', 'S.3', 'S.4'], gender: 'Female', phone: '0772222222', email: '', status: 'active' },
            { id: 'STF003', staffNo: 'TCH003', firstName: 'Ssekitoleko', lastName: 'Michael', role: 'Teacher', subjects: ['Physics', 'Mathematics'], classes: ['S.4', 'S.5', 'S.6'], gender: 'Male', phone: '0773333333', email: '', status: 'active' }
        ],
        subjects: [
            { id: 'SUB001', code: 'MATH', name: 'Mathematics', teacher: 'Kigozi John', classes: ['S.1', 'S.2', 'S.3', 'S.4', 'S.5', 'S.6'] },
            { id: 'SUB002', code: 'ENG', name: 'English', teacher: 'Nakato Sarah', classes: ['S.1', 'S.2', 'S.3', 'S.4'] },
            { id: 'SUB003', code: 'PHY', name: 'Physics', teacher: 'Ssekitoleko Michael', classes: ['S.4', 'S.5', 'S.6'] },
            { id: 'SUB004', code: 'CHEM', name: 'Chemistry', teacher: '', classes: ['S.4', 'S.5', 'S.6'] },
            { id: 'SUB005', code: 'BIO', name: 'Biology', teacher: '', classes: ['S.4', 'S.5', 'S.6'] },
            { id: 'SUB006', code: 'HIST', name: 'History', teacher: '', classes: ['S.1', 'S.2', 'S.3', 'S.4'] },
            { id: 'SUB007', code: 'GEO', name: 'Geography', teacher: '', classes: ['S.1', 'S.2', 'S.3', 'S.4'] },
            { id: 'SUB008', code: 'CRE', name: 'CRE', teacher: '', classes: ['S.1', 'S.2', 'S.3', 'S.4'] }
        ],
        classes: [
            { id: 'CLS001', name: 'S.1', streams: ['North', 'South'], capacity: 50 },
            { id: 'CLS002', name: 'S.2', streams: ['North', 'South'], capacity: 50 },
            { id: 'CLS003', name: 'S.3', streams: ['Arts', 'Science'], capacity: 45 },
            { id: 'CLS004', name: 'S.4', streams: ['Science', 'Commerce', 'Arts'], capacity: 40 },
            { id: 'CLS005', name: 'S.5', streams: ['Science', 'Commerce'], capacity: 35 },
            { id: 'CLS006', name: 'S.6', streams: ['Science', 'Commerce'], capacity: 35 }
        ],
        fees: [
            { id: 'FEE001', class: 'S.1', amount: 800000, description: 'Tuition Fee', term: 'all' },
            { id: 'FEE002', class: 'S.2', amount: 850000, description: 'Tuition Fee', term: 'all' },
            { id: 'FEE003', class: 'S.3', amount: 900000, description: 'Tuition Fee', term: 'all' },
            { id: 'FEE004', class: 'S.4', amount: 1200000, description: 'Tuition Fee', term: 'all' },
            { id: 'FEE005', class: 'S.5', amount: 1400000, description: 'Tuition Fee', term: 'all' },
            { id: 'FEE006', class: 'S.6', amount: 1500000, description: 'Tuition Fee', term: 'all' }
        ],
        payments: [
            { id: 'PAY001', studentId: 'STD001', amount: 1200000, date: '2024-01-15', method: 'cash', reference: '', term: 'Term 1', year: '2024', recordedBy: 'bursar' },
            { id: 'PAY002', studentId: 'STD002', amount: 600000, date: '2024-01-18', method: 'mpesa', reference: 'MG8X2K9L', term: 'Term 1', year: '2024', recordedBy: 'bursar' },
            { id: 'PAY003', studentId: 'STD003', amount: 900000, date: '2024-01-10', method: 'cash', reference: '', term: 'Term 1', year: '2024', recordedBy: 'bursar' }
        ],
        marks: [
            { id: 'MK001', studentId: 'STD001', subject: 'Mathematics', class: 'S.4', term: 'Term 1', year: '2024', cat1: 85, cat2: 90, exam: 88, total: 263, grade: 'A', rank: 1 },
            { id: 'MK002', studentId: 'STD001', subject: 'English', class: 'S.4', term: 'Term 1', year: '2024', cat1: 78, cat2: 82, exam: 80, total: 240, grade: 'B+', rank: 2 },
            { id: 'MK003', studentId: 'STD001', subject: 'Physics', class: 'S.4', term: 'Term 1', year: '2024', cat1: 82, cat2: 85, exam: 87, total: 254, grade: 'A', rank: 1 },
            { id: 'MK004', studentId: 'STD002', subject: 'Mathematics', class: 'S.4', term: 'Term 1', year: '2024', cat1: 70, cat2: 75, exam: 72, total: 217, grade: 'B+', rank: 2 },
            { id: 'MK005', studentId: 'STD002', subject: 'English', class: 'S.4', term: 'Term 1', year: '2024', cat1: 65, cat2: 68, exam: 70, total: 203, grade: 'B', rank: 3 },
            { id: 'MK006', studentId: 'STD003', subject: 'English', class: 'S.3', term: 'Term 1', year: '2024', cat1: 88, cat2: 92, exam: 90, total: 270, grade: 'A', rank: 1 }
        ],
        attendance: [],
        library: [
            { id: 'LIB001', isbn: '978-0-12-345678-9', title: 'Advanced Mathematics', author: 'J. Smith', copies: 25, available: 20, category: 'Mathematics' },
            { id: 'LIB002', isbn: '978-0-12-345678-0', title: 'Physics for UACE', author: 'P. Jones', copies: 30, available: 25, category: 'Physics' }
        ],
        disciplinary: [],
        medical: [],
        announcements: [
            { id: 'ANN001', title: 'Term 1 Opening', message: 'School opens on Monday 15th January 2024', date: '2024-01-10', author: 'admin' }
        ],
        publishedTerms: [],
        auditLog: []
    };
}

function logAudit(action, user, details) {
    try {
        const log = { timestamp: new Date().toISOString(), action, user, details };
        let db = getDatabase();
        if (!db.auditLog) db.auditLog = [];
        db.auditLog.push(log);
        if (db.auditLog.length > 1000) db.auditLog = db.auditLog.slice(-1000);
        fs.writeFileSync(AUDIT_LOG_FILE, JSON.stringify(log, null, 2) + '\n', { flag: 'a' });
    } catch (e) {}
}

// ============== LAN SERVER FOR PARENT PORTAL ==============
let lanServer = null;

function startLanServer(port = 8080) {
    if (lanServer) return;
    
    const ip = getLocalIP();
    
    lanServer = http.createServer((req, res) => {
        const db = getDatabase();
        const url = req.url.split('?')[0];
        
        res.writeHead(200, { 'Content-Type': 'text/html', 'Access-Control-Allow-Origin': '*' });
        
        if (url === '/' || url === '/portal') {
            res.end(getParentPortalHTML(db));
        } else if (url === '/api/login') {
            let body = '';
            req.on('data', chunk => body += chunk);
            req.on('end', () => {
                const { username, password } = JSON.parse(body || '{}');
                const student = db.students.find(s => s.admissionNo === username && s.parentPhone === password);
                if (student) {
                    res.end(JSON.stringify({ success: true, student }));
                } else {
                    res.end(JSON.stringify({ success: false, error: 'Invalid credentials' }));
                }
            });
        } else if (url.startsWith('/api/student/')) {
            const studentId = url.split('/')[3];
            const student = db.students.find(s => s.id === studentId);
            if (student) {
                const payments = db.payments.filter(p => p.studentId === studentId);
                const marks = db.marks.filter(m => m.studentId === studentId);
                const attendance = db.attendance.filter(a => a.studentId === studentId);
                res.end(JSON.stringify({ student, payments, marks, attendance }));
            } else {
                res.end(JSON.stringify({ error: 'Not found' }));
            }
        } else {
            res.end('<h1>JD HUB Parent Portal</h1><p>Scan QR code to access</p>');
        }
    });
    
    lanServer.listen(port, () => {
        console.log(`LAN Server running at http://${ip}:${port}`);
    });
}

function getParentPortalHTML(db) {
    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JD HUB - Parent Portal</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Arial, sans-serif; }
        body { background: #f8fafc; color: #0f172a; min-height: 100vh; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #1e40af, #2563eb); color: white; padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 20px; }
        .header h1 { font-size: 24px; margin-bottom: 10px; }
        .login-box { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .login-box h2 { margin-bottom: 20px; color: #1e40af; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: 500; }
        .form-group input { width: 100%; padding: 12px; border: 2px solid #e2e8f0; border-radius: 8px; font-size: 16px; }
        .btn { width: 100%; padding: 14px; background: #2563eb; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; }
        .btn:hover { background: #1d4ed8; }
        .dashboard { display: none; }
        .card { background: white; padding: 20px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .card h3 { color: #1e40af; margin-bottom: 15px; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
        .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .info-item { padding: 10px; background: #f8fafc; border-radius: 8px; }
        .info-item label { font-size: 12px; color: #64748b; }
        .info-item span { font-size: 16px; font-weight: 600; display: block; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #e2e8f0; }
        th { background: #f8fafc; font-weight: 600; }
        .grade-A { color: #22c55e; font-weight: bold; }
        .grade-B { color: #3b82f6; }
        .grade-C { color: #f59e0b; }
        .grade-D, .grade-E, .grade-F { color: #ef4444; }
        .balance-paid { color: #22c55e; }
        .balance-pending { color: #ef4444; }
        .logout-btn { background: #dc2626; margin-top: 20px; }
        .announcement { background: #fef3c7; padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b; margin-bottom: 10px; }
        .announcement h4 { color: #92400e; }
        @media (max-width: 600px) { .info-grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>JD HUB Parent Portal</h1>
            <p>Stay connected with your child's education</p>
        </div>
        
        <div class="login-box" id="loginBox">
            <h2>Parent Login</h2>
            <p style="color: #64748b; margin-bottom: 20px;">Enter your child's Admission Number and your registered phone number</p>
            <div class="form-group">
                <label>Student Admission No.</label>
                <input type="text" id="username" placeholder="e.g., SCH/2024/001">
            </div>
            <div class="form-group">
                <label>Parent Phone Number</label>
                <input type="password" id="password" placeholder="Your registered phone number">
            </div>
            <button class="btn" onclick="login()">Login</button>
            <p id="error" style="color: #ef4444; margin-top: 10px; display: none;"></p>
        </div>
        
        <div class="dashboard" id="dashboard">
            <div class="card">
                <h3>Student Information</h3>
                <div class="info-grid">
                    <div class="info-item"><label>Name</label><span id="studentName"></span></div>
                    <div class="info-item"><label>Class</label><span id="studentClass"></span></div>
                    <div class="info-item"><label>Stream</label><span id="studentStream"></span></div>
                    <div class="info-item"><label>Gender</label><span id="studentGender"></span></div>
                </div>
            </div>
            
            <div class="card" id="announcementsCard">
                <h3>Announcements</h3>
                <div id="announcements"></div>
            </div>
            
            <div class="card" id="marksCard">
                <h3>Academic Performance - Term 1</h3>
                <table>
                    <thead><tr><th>Subject</th><th>CAT 1</th><th>CAT 2</th><th>Exam</th><th>Total</th><th>Grade</th></tr></thead>
                    <tbody id="marksTable"></tbody>
                </table>
            </div>
            
            <div class="card" id="paymentsCard">
                <h3>Fee Payment History</h3>
                <table>
                    <thead><tr><th>Date</th><th>Amount</th><th>Method</th><th>Term</th></tr></thead>
                    <tbody id="paymentsTable"></tbody>
                </table>
                <div class="info-grid" style="margin-top: 20px;">
                    <div class="info-item"><label>Total Paid</label><span class="balance-paid" id="totalPaid">0</span></div>
                    <div class="info-item"><label>Balance</label><span class="balance-pending" id="balance">0</span></div>
                </div>
            </div>
            
            <button class="btn logout-btn" onclick="logout()">Logout</button>
        </div>
    </div>
    
    <script>
        let currentStudent = null;
        
        async function login() {
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value.trim();
            
            if (!username || !password) {
                document.getElementById('error').textContent = 'Please enter all fields';
                document.getElementById('error').style.display = 'block';
                return;
            }
            
            try {
                const res = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                const data = await res.json();
                
                if (data.success) {
                    currentStudent = data.student;
                    showDashboard(data.student);
                } else {
                    document.getElementById('error').textContent = 'Invalid credentials';
                    document.getElementById('error').style.display = 'block';
                }
            } catch (e) {
                document.getElementById('error').textContent = 'Connection error';
                document.getElementById('error').style.display = 'block';
            }
        }
        
        async function showDashboard(student) {
            document.getElementById('loginBox').style.display = 'none';
            document.getElementById('dashboard').style.display = 'block';
            
            document.getElementById('studentName').textContent = student.firstName + ' ' + student.lastName;
            document.getElementById('studentClass').textContent = student.class;
            document.getElementById('studentStream').textContent = student.stream;
            document.getElementById('studentGender').textContent = student.gender;
            
            // Load marks
            try {
                const res = await fetch('/api/student/' + student.id);
                const data = await res.json();
                
                // Marks
                let marksHtml = '';
                data.marks.forEach(m => {
                    marksHtml += '<tr><td>' + m.subject + '</td><td>' + m.cat1 + '</td><td>' + m.cat2 + '</td><td>' + m.exam + '</td><td>' + m.total + '</td><td class="grade-' + m.grade.charAt(0) + '">' + m.grade + '</td></tr>';
                });
                document.getElementById('marksTable').innerHTML = marksHtml || '<tr><td colspan="6">No marks available</td></tr>';
                
                // Payments
                let totalPaid = 0;
                let paymentsHtml = '';
                data.payments.forEach(p => {
                    totalPaid += parseInt(p.amount);
                    paymentsHtml += '<tr><td>' + p.date + '</td><td>UGX ' + p.amount.toLocaleString() + '</td><td>' + p.method + '</td><td>' + p.term + '</td></tr>';
                });
                document.getElementById('paymentsTable').innerHTML = paymentsHtml || '<tr><td colspan="4">No payments recorded</td></tr>';
                document.getElementById('totalPaid').textContent = 'UGX ' + totalPaid.toLocaleString();
                
                const fees = ${JSON.stringify(db.fees)};
                const classFee = fees.find(f => f.class === student.class);
                const balance = classFee ? classFee.amount - totalPaid : 0;
                document.getElementById('balance').textContent = 'UGX ' + Math.max(0, balance).toLocaleString();
                
                // Announcements
                const anns = ${JSON.stringify(db.announcements)};
                let annHtml = '';
                anns.slice(0, 3).forEach(a => {
                    annHtml += '<div class="announcement"><h4>' + a.title + '</h4><p>' + a.message + '</p><small>' + a.date + '</small></div>';
                });
                document.getElementById('announcements').innerHTML = annHtml || '<p>No announcements</p>';
                
            } catch (e) {
                console.log('Error loading data');
            }
        }
        
        function logout() {
            currentStudent = null;
            document.getElementById('loginBox').style.display = 'block';
            document.getElementById('dashboard').style.display = 'none';
            document.getElementById('username').value = '';
            document.getElementById('password').value = '';
        }
        
        document.getElementById('password').addEventListener('keypress', e => { if (e.key === 'Enter') login(); });
    </script>
</body>
</html>`;
}

// ============== MAIN WINDOW ==============
let mainWindow;
let tray = null;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1500,
        height: 950,
        minWidth: 1200,
        minHeight: 700,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        title: 'JD HUB Enterprise School Management System',
        backgroundColor: '#f8fafc'
    });
    
    mainWindow.loadFile('index.html');
    
    // Start LAN server
    startLanServer(8080);
    
    // Setup menu
    const menuTemplate = [
        { label: 'File', submenu: [{ label: 'Backup Database', click: () => mainWindow.webContents.send('menu-action', 'backup') }, { label: 'Export Data', click: () => mainWindow.webContents.send('menu-action', 'export') }, { type: 'separator' }, { label: 'Exit', click: () => app.quit() }] },
        { label: 'View', submenu: [{ label: 'Dashboard', click: () => mainWindow.webContents.send('menu-action', 'dashboard') }, { label: 'Refresh', click: () => mainWindow.webContents.send('menu-action', 'refresh') }, { type: 'separator' }, { role: 'toggleDevTools' }] },
        { label: 'Help', submenu: [{ label: 'About', click: () => dialog.showMessageBox(mainWindow, { type: 'info', title: 'About JD HUB', message: 'JD HUB Enterprise SMS v1.0.0\n\nContact: 0754687597' }) }] }
    ];
    
    const menu = Menu.buildFromTemplate(menuTemplate);
    Menu.setApplicationMenu(menu);
}

// ============== IPC HANDLERS ==============
ipcMain.handle('get-machine-id', () => getMachineId());
ipcMain.handle('get-local-ip', () => getLocalIP());
ipcMain.handle('get-portal-url', () => `http://${getLocalIP()}:8080`);

ipcMain.handle('validate-license', (event, licenseKey) => {
    const machineId = getMachineId();
    const result = validateLicense(licenseKey, machineId);
    if (result.valid) {
        const license = { key: licenseKey, machineId, type: result.type, activatedAt: new Date().toISOString() };
        saveLicense(license);
        logAudit('LICENSE_ACTIVATED', 'System', `Machine: ${machineId}, Type: ${result.type}`);
    }
    return result;
});

ipcMain.handle('check-license', () => {
    const license = loadLicense();
    if (license) {
        const result = validateLicense(license.key, license.machineId);
        return { activated: result.valid, type: license.type, schoolName: license.schoolName || 'Activated' };
    }
    return { activated: false };
});

ipcMain.handle('activate-school', (event, schoolName) => {
    const license = loadLicense();
    if (license) {
        license.schoolName = schoolName;
        saveLicense(license);
        logAudit('SCHOOL_ACTIVATED', 'System', schoolName);
        return { success: true };
    }
    return { success: false };
});

ipcMain.handle('get-database', () => getDatabase());
ipcMain.handle('save-database', (event, data) => { saveDatabase(data); return { success: true }; });

ipcMain.handle('save-settings', (event, settings) => {
    let db = getDatabase();
    db.settings = { ...db.settings, ...settings };
    saveDatabase(db);
    logAudit('SETTINGS_UPDATED', 'System', 'Settings modified');
    return { success: true };
});

ipcMain.handle('save-users', (event, users) => {
    let db = getDatabase();
    db.users = users;
    saveDatabase(db);
    logAudit('USERS_UPDATED', 'System', 'Users modified');
    return { success: true };
});

ipcMain.handle('save-students', (event, students) => {
    let db = getDatabase();
    db.students = students;
    saveDatabase(db);
    return { success: true };
});

ipcMain.handle('save-staff', (event, staff) => {
    let db = getDatabase();
    db.staff = staff;
    saveDatabase(db);
    return { success: true };
});

ipcMain.handle('save-subjects', (event, subjects) => {
    let db = getDatabase();
    db.subjects = subjects;
    saveDatabase(db);
    return { success: true };
});

ipcMain.handle('save-classes', (event, classes) => {
    let db = getDatabase();
    db.classes = classes;
    saveDatabase(db);
    return { success: true };
});

ipcMain.handle('save-fees', (event, fees) => {
    let db = getDatabase();
    db.fees = fees;
    saveDatabase(db);
    return { success: true };
});

ipcMain.handle('save-payments', (event, payments) => {
    let db = getDatabase();
    db.payments = payments;
    saveDatabase(db);
    logAudit('PAYMENT_RECORDED', 'Bursar', `Payment added`);
    return { success: true };
});

ipcMain.handle('save-marks', (event, marks) => {
    let db = getDatabase();
    db.marks = marks;
    saveDatabase(db);
    return { success: true };
});

ipcMain.handle('save-library', (event, library) => {
    let db = getDatabase();
    db.library = library;
    saveDatabase(db);
    return { success: true };
});

ipcMain.handle('save-announcements', (event, announcements) => {
    let db = getDatabase();
    db.announcements = announcements;
    saveDatabase(db);
    return { success: true };
});

ipcMain.handle('save-attendance', (event, attendance) => {
    let db = getDatabase();
    db.attendance = attendance;
    saveDatabase(db);
    return { success: true };
});

ipcMain.handle('save-disciplinary', (event, disciplinary) => {
    let db = getDatabase();
    db.disciplinary = disciplinary;
    saveDatabase(db);
    return { success: true };
});

ipcMain.handle('save-medical', (event, medical) => {
    let db = getDatabase();
    db.medical = medical;
    saveDatabase(db);
    return { success: true };
});

ipcMain.handle('get-audit-log', () => {
    try {
        if (fs.existsSync(AUDIT_LOG_FILE)) {
            const logs = fs.readFileSync(AUDIT_LOG_FILE, 'utf8').split('\n').filter(l => l.trim()).map(l => JSON.parse(l));
            return logs.slice(-100).reverse();
        }
    } catch (e) {}
    return [];
});

ipcMain.handle('publish-term', (event, term, year) => {
    let db = getDatabase();
    if (!db.publishedTerms) db.publishedTerms = [];
    db.publishedTerms.push({ term, year, publishedAt: new Date().toISOString() });
    saveDatabase(db);
    logAudit('TERM_PUBLISHED', 'Admin', `Term ${term} ${year} published`);
    return { success: true };
});

ipcMain.handle('export-database', async () => {
    const result = await dialog.showSaveDialog(mainWindow, {
        title: 'Export Database',
        defaultPath: `JDHub_Backup_${new Date().toISOString().split('T')[0]}.json`,
        filters: [{ name: 'JSON Files', extensions: ['json'] }]
    });
    
    if (!result.canceled && result.filePath) {
        const db = getDatabase();
        fs.writeFileSync(result.filePath, JSON.stringify(db, null, 2));
        return { success: true, path: result.filePath };
    }
    return { success: false };
});

ipcMain.handle('import-database', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
        title: 'Import Database',
        filters: [{ name: 'JSON Files', extensions: ['json'] }],
        properties: ['openFile']
    });
    
    if (!result.canceled && result.filePaths.length > 0) {
        try {
            const data = JSON.parse(fs.readFileSync(result.filePaths[0], 'utf8'));
            saveDatabase(data);
            return { success: true };
        } catch (e) {
            return { success: false, error: e.message };
        }
    }
    return { success: false };
});

ipcMain.handle('backup-to-usb', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
        title: 'Select USB Drive',
        properties: ['openDirectory']
    });
    
    if (!result.canceled && result.filePaths.length > 0) {
        const backupPath = path.join(result.filePaths[0], `JDHub_Backup_${new Date().toISOString().split('T')[0]}.json`);
        const db = getDatabase();
        fs.writeFileSync(backupPath, JSON.stringify(db, null, 2));
        logAudit('USB_BACKUP', 'System', `Backup to ${backupPath}`);
        return { success: true, path: backupPath };
    }
    return { success: false };
});

ipcMain.handle('log-audit', (event, action, details) => {
    logAudit(action, details.user || 'System', details.message || '');
    return { success: true };
});

ipcMain.handle('generate-id', () => uuidv4());

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (lanServer) lanServer.close();
    if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
