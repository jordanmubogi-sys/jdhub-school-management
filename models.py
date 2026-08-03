"""
Enterprise School Management System - Core Database Models
Supports Schools, Universities, and Institutions with Custom Programs
"""

import sqlite3
import hashlib
import uuid
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

class Database:
    """Central database manager for the entire system"""
    
    def __init__(self, db_path: str = "school_data.db"):
        self.db_path = db_path
        self.conn = None
        self._init_db()
    
    def _init_db(self):
        """Initialize database with all required tables"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        self._seed_defaults()
    
    def _create_tables(self):
        """Create all database tables"""
        cursor = self.conn.cursor()
        
        # School Settings (Configurable for any institution type)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS school_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_name TEXT NOT NULL,
                school_logo BLOB,
                motto TEXT,
                address TEXT,
                phone TEXT,
                email TEXT,
                website TEXT,
                registration_prefix TEXT DEFAULT 'SCH',
                academic_year_format TEXT DEFAULT 'YYYY-YY',
                institution_type TEXT DEFAULT 'school',
                grading_scheme TEXT DEFAULT '{}',
                stamp_image BLOB,
                signature_image BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Hardware Licensing
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id TEXT UNIQUE NOT NULL,
                license_key TEXT,
                activation_date TIMESTAMP,
                expiry_date TIMESTAMP,
                is_active INTEGER DEFAULT 0,
                client_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Feature Toggles (Monetization)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feature_toggles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_name TEXT UNIQUE NOT NULL,
                feature_key TEXT UNIQUE NOT NULL,
                is_enabled INTEGER DEFAULT 0,
                client_id TEXT,
                price_tier TEXT DEFAULT 'basic',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Users (Staff)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                role TEXT NOT NULL CHECK(role IN ('super_admin', 'admin', 'director_studies', 'class_teacher', 'subject_teacher', 'bursar', 'secretary')),
                employee_id TEXT UNIQUE,
                photo BLOB,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Academic Terms
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS academic_terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term_name TEXT NOT NULL,
                start_date DATE,
                end_date DATE,
                academic_year TEXT NOT NULL,
                is_current INTEGER DEFAULT 0,
                is_published INTEGER DEFAULT 0,
                published_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Streams/Classes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS streams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stream_name TEXT NOT NULL,
                stream_code TEXT UNIQUE NOT NULL,
                level TEXT,
                class_teacher_id INTEGER REFERENCES users(id),
                capacity INTEGER DEFAULT 40,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Subjects
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_name TEXT NOT NULL,
                subject_code TEXT UNIQUE NOT NULL,
                subject_type TEXT DEFAULT 'core',
                is_compulsory INTEGER DEFAULT 0,
                department TEXT,
                pass_mark INTEGER DEFAULT 40,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Stream-Subject Assignment
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stream_subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stream_id INTEGER REFERENCES streams(id),
                subject_id INTEGER REFERENCES subjects(id),
                UNIQUE(stream_id, subject_id)
            )
        ''')
        
        # Students
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                middle_name TEXT,
                last_name TEXT NOT NULL,
                date_of_birth DATE,
                gender TEXT,
                admission_date DATE,
                photo BLOB,
                blood_group TEXT,
                nationality TEXT,
                stream_id INTEGER REFERENCES streams(id),
                status TEXT DEFAULT 'active' CHECK(status IN ('active', 'suspended', 'expelled', 'graduated', 'transferred')),
                medical_conditions TEXT,
                allergies TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Parents/Guardians
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT REFERENCES students(student_id),
                parent_name TEXT NOT NULL,
                relationship TEXT,
                primary_phone TEXT NOT NULL,
                alternate_phone TEXT,
                email TEXT,
                occupation TEXT,
                address TEXT,
                is_primary INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Student Subjects
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT REFERENCES students(student_id),
                subject_id INTEGER REFERENCES subjects(id),
                stream_id INTEGER REFERENCES streams(id),
                term_id INTEGER REFERENCES academic_terms(id),
                UNIQUE(student_id, subject_id, term_id)
            )
        ''')
        
        # Marks/Results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS marks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT REFERENCES students(student_id),
                subject_id INTEGER REFERENCES subjects(id),
                stream_id INTEGER REFERENCES streams(id),
                term_id INTEGER REFERENCES academic_terms(id),
                class_work REAL,
                homework REAL,
                midterm REAL,
                final_exam REAL,
                total_score REAL,
                grade TEXT,
                remarks TEXT,
                position_in_class INTEGER,
                position_in_stream INTEGER,
                is_locked INTEGER DEFAULT 0,
                entered_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_id, subject_id, term_id)
            )
        ''')
        
        # Attendance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT REFERENCES students(student_id),
                term_id INTEGER REFERENCES academic_terms(id),
                days_school_opened INTEGER DEFAULT 0,
                days_present INTEGER DEFAULT 0,
                days_absent INTEGER DEFAULT 0,
                days_late INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Comments/Remarks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT REFERENCES students(student_id),
                term_id INTEGER REFERENCES academic_terms(id),
                class_teacher_comment TEXT,
                head_teacher_comment TEXT,
                created_by INTEGER REFERENCES users(id),
                is_edited INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Disciplinary Records
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS disciplinary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT REFERENCES students(student_id),
                incident_date DATE,
                incident_type TEXT,
                description TEXT,
                action_taken TEXT,
                reported_by INTEGER REFERENCES users(id),
                is_resolved INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Fee Structure
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fee_structure (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stream_id INTEGER REFERENCES streams(id),
                academic_year TEXT,
                term_id INTEGER REFERENCES academic_terms(id),
                fee_name TEXT NOT NULL,
                amount REAL NOT NULL,
                due_date DATE,
                is_mandatory INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Fee Payments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fee_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT REFERENCES students(student_id),
                term_id INTEGER REFERENCES academic_terms(id),
                fee_structure_id INTEGER REFERENCES fee_structure(id),
                amount_paid REAL NOT NULL,
                payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                payment_method TEXT DEFAULT 'cash',
                receipt_number TEXT UNIQUE,
                received_by INTEGER REFERENCES users(id),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Announcements
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                priority TEXT DEFAULT 'normal',
                target_audience TEXT DEFAULT 'all',
                published_by INTEGER REFERENCES users(id),
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Library Books
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS library_books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id TEXT UNIQUE,
                title TEXT NOT NULL,
                author TEXT,
                isbn TEXT,
                publisher TEXT,
                category TEXT,
                total_copies INTEGER DEFAULT 1,
                available_copies INTEGER DEFAULT 1,
                shelf_location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Book Issues
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS book_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id TEXT REFERENCES library_books(book_id),
                student_id TEXT REFERENCES students(student_id),
                issue_date DATE,
                due_date DATE,
                return_date DATE,
                status TEXT DEFAULT 'issued',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Staff Attendance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff_attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                date DATE,
                status TEXT DEFAULT 'present',
                check_in TIME,
                check_out TIME,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Payroll
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payroll (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                month TEXT,
                year INTEGER,
                basic_salary REAL,
                allowances REAL DEFAULT 0,
                deductions REAL DEFAULT 0,
                net_salary REAL,
                payment_date DATE,
                payment_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Alumni Records
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alumni (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT REFERENCES students(student_id),
                graduation_year INTEGER,
                graduation_class TEXT,
                current_occupation TEXT,
                current_institution TEXT,
                contact_info TEXT,
                achievements TEXT,
                archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Audit Trail
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_trail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                action TEXT NOT NULL,
                table_affected TEXT,
                record_id INTEGER,
                old_value TEXT,
                new_value TEXT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Backup History
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backup_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_type TEXT,
                location TEXT,
                file_name TEXT,
                file_size INTEGER,
                status TEXT DEFAULT 'success',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Term Advancement
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS term_advancement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_term_id INTEGER REFERENCES academic_terms(id),
                to_term_id INTEGER REFERENCES academic_terms(id),
                advanced_by INTEGER REFERENCES users(id),
                authorized_by INTEGER REFERENCES users(id),
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_stream ON students(stream_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_marks_student ON marks(student_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_marks_term ON marks(term_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_payments_student ON fee_payments(student_id)')
        
        self.conn.commit()
    
    def _seed_defaults(self):
        """Seed default data"""
        cursor = self.conn.cursor()
        
        # Check if Super Admin exists
        cursor.execute("SELECT id FROM users WHERE role = 'super_admin'")
        if not cursor.fetchone():
            # Create Super Admin (Jordan)
            password_hash = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute('''
                INSERT INTO users (username, password_hash, full_name, role, email)
                VALUES (?, ?, ?, ?, ?)
            ''', ('Jordan', password_hash, 'Jordan Admin', 'super_admin', 'jordan@school.edu'))
        
        # Check if school settings exist
        cursor.execute("SELECT id FROM school_settings")
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO school_settings (school_name, motto, institution_type)
                VALUES (?, ?, ?)
            ''', ('My School', 'Education for Excellence', 'school'))
        
        # Seed default feature toggles
        features = [
            ('Student Photo Processing & ID Cards', 'photo_id_cards', 0),
            ('High-Res Custom PDF Branding', 'pdf_branding', 0),
            ('Automated Email Fee Letters', 'email_fee_letters', 0),
            ('Automated Cloud Backup Sync', 'cloud_backup', 0),
        ]
        
        for name, key, enabled in features:
            cursor.execute('''
                INSERT OR IGNORE INTO feature_toggles (feature_name, feature_key, is_enabled)
                VALUES (?, ?, ?)
            ''', (name, key, enabled))
        
        self.conn.commit()
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def verify_user(self, username: str, password: str) -> Optional[Dict]:
        """Verify user credentials"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM users 
            WHERE username = ? AND password_hash = ? AND is_active = 1
        ''', (username, password_hash))
        row = cursor.fetchone()
        if row:
            cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (row['id'],))
            self.conn.commit()
        return dict(row) if row else None
    
    def execute(self, query: str, params: tuple = ()):
        """Execute a query"""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict]:
        """Fetch all results"""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """Fetch one result"""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def backup_to_usb(self, usb_path: str) -> bool:
        """Backup database to USB"""
        try:
            import shutil
            backup_name = f"school_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(self.db_path, os.path.join(usb_path, backup_name))
            
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO backup_history (backup_type, location, file_name, file_size)
                VALUES (?, ?, ?, ?)
            ''', ('usb', usb_path, backup_name, os.path.getsize(os.path.join(usb_path, backup_name))))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Backup error: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
