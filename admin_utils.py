"""
Enterprise Features & Admin Utilities
Includes all 20 enterprise features and admin functions
"""

import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
from io import BytesIO
import hashlib


class StaffManager:
    """Manage staff members, attendance, and payroll"""
    
    def __init__(self, db):
        self.db = db
    
    def create_staff(self, username: str, password: str, full_name: str,
                    email: str = None, phone: str = None,
                    role: str = 'subject_teacher') -> int:
        """Create a new staff member"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Generate employee ID
        count = self.db.fetch_one("SELECT COUNT(*) as count FROM users") or {'count': 0}
        employee_id = f"EMP/{datetime.now().year}/{count['count'] + 1:04d}"
        
        cursor = self.db.execute("""
            INSERT INTO users 
            (username, password_hash, full_name, email, phone, role, employee_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username, password_hash, full_name, email, phone, role, employee_id))
        
        return cursor.lastrowid
    
    def record_staff_attendance(self, user_id: int, status: str = 'present',
                               check_in: str = None, check_out: str = None,
                               remarks: str = None) -> bool:
        """Record staff attendance for the day"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        self.db.execute("""
            INSERT OR REPLACE INTO staff_attendance 
            (user_id, date, status, check_in, check_out, remarks)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, today, status, check_in, check_out, remarks))
        
        return True
    
    def get_staff_attendance(self, user_id: int = None, 
                            start_date: str = None, 
                            end_date: str = None) -> List[Dict]:
        """Get staff attendance records"""
        query = """
            SELECT sa.*, u.full_name, u.role
            FROM staff_attendance sa
            JOIN users u ON sa.user_id = u.id
            WHERE 1=1
        """
        params = []
        
        if user_id:
            query += " AND sa.user_id = ?"
            params.append(user_id)
        
        if start_date:
            query += " AND sa.date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND sa.date <= ?"
            params.append(end_date)
        
        query += " ORDER BY sa.date DESC"
        
        return self.db.fetch_all(query, params)
    
    def create_payroll(self, user_id: int, month: str, year: int,
                      basic_salary: float, allowances: float = 0,
                      deductions: float = 0) -> bool:
        """Create payroll entry"""
        net_salary = basic_salary + allowances - deductions
        
        self.db.execute("""
            INSERT INTO payroll 
            (user_id, month, year, basic_salary, allowances, deductions, net_salary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, month, year, basic_salary, allowances, deductions, net_salary))
        
        return True
    
    def get_payroll_records(self, user_id: int = None, 
                           month: str = None, year: int = None) -> List[Dict]:
        """Get payroll records"""
        query = """
            SELECT p.*, u.full_name, u.role, u.employee_id
            FROM payroll p
            JOIN users u ON p.user_id = u.id
            WHERE 1=1
        """
        params = []
        
        if user_id:
            query += " AND p.user_id = ?"
            params.append(user_id)
        
        if month:
            query += " AND p.month = ?"
            params.append(month)
        
        if year:
            query += " AND p.year = ?"
            params.append(year)
        
        query += " ORDER BY p.year DESC, p.month DESC"
        
        return self.db.fetch_all(query, params)


class LibraryManager:
    """Library and book inventory management"""
    
    def __init__(self, db):
        self.db = db
    
    def add_book(self, title: str, author: str = None, isbn: str = None,
                publisher: str = None, category: str = None,
                total_copies: int = 1, shelf_location: str = None) -> int:
        """Add a book to the library"""
        # Generate book ID
        book_id = f"BK{datetime.now().strftime('%Y%m%d')}{hashlib.md5(title.encode()).hexdigest()[:4].upper()}"
        
        cursor = self.db.execute("""
            INSERT INTO library_books 
            (book_id, title, author, isbn, publisher, category, 
             total_copies, available_copies, shelf_location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (book_id, title, author, isbn, publisher, category,
              total_copies, total_copies, shelf_location))
        
        return cursor.lastrowid
    
    def issue_book(self, book_id: str, student_id: str,
                  due_days: int = 14) -> bool:
        """Issue a book to a student"""
        # Check availability
        book = self.db.fetch_one(
            "SELECT * FROM library_books WHERE book_id = ? AND available_copies > 0",
            (book_id,)
        )
        
        if not book:
            return False
        
        issue_date = datetime.now().date()
        due_date = (datetime.now() + timedelta(days=due_days)).date()
        
        self.db.execute("""
            INSERT INTO book_issues 
            (book_id, student_id, issue_date, due_date, status)
            VALUES (?, ?, ?, ?, 'issued')
        """, (book_id, student_id, issue_date, due_date))
        
        # Update available copies
        self.db.execute(
            "UPDATE library_books SET available_copies = available_copies - 1 WHERE book_id = ?",
            (book_id,)
        )
        
        return True
    
    def return_book(self, book_id: str, student_id: str) -> bool:
        """Return a book"""
        self.db.execute("""
            UPDATE book_issues 
            SET return_date = ?, status = 'returned'
            WHERE book_id = ? AND student_id = ? AND status = 'issued'
        """, (datetime.now().date(), book_id, student_id))
        
        # Update available copies
        self.db.execute(
            "UPDATE library_books SET available_copies = available_copies + 1 WHERE book_id = ?",
            (book_id,)
        )
        
        return True
    
    def get_issued_books(self, student_id: str = None) -> List[Dict]:
        """Get currently issued books"""
        query = """
            SELECT bi.*, lb.title, lb.author, s.first_name, s.last_name
            FROM book_issues bi
            JOIN library_books lb ON bi.book_id = lb.book_id
            JOIN students s ON bi.student_id = s.student_id
            WHERE bi.status = 'issued'
        """
        params = []
        
        if student_id:
            query += " AND bi.student_id = ?"
            params.append(student_id)
        
        return self.db.fetch_all(query, params)
    
    def search_books(self, query: str) -> List[Dict]:
        """Search library books"""
        search_term = f"%{query}%"
        return self.db.fetch_all("""
            SELECT * FROM library_books
            WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ?
            ORDER BY title
        """, (search_term, search_term, search_term))


class MedicalManager:
    """Medical and health records management"""
    
    def __init__(self, db):
        self.db = db
    
    def update_medical_info(self, student_id: str, 
                           blood_group: str = None,
                           medical_conditions: str = None,
                           allergies: str = None) -> bool:
        """Update student medical information"""
        self.db.execute("""
            UPDATE students 
            SET blood_group = ?, medical_conditions = ?, allergies = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE student_id = ?
        """, (blood_group, medical_conditions, allergies, student_id))
        
        return True
    
    def get_medical_report(self, student_id: str) -> Dict:
        """Get complete medical report for a student"""
        student = self.db.fetch_one(
            "SELECT * FROM students WHERE student_id = ?",
            (student_id,)
        )
        
        # Get attendance
        attendance = self.db.fetch_all(
            "SELECT * FROM attendance WHERE student_id = ? ORDER BY term_id",
            (student_id,)
        )
        
        return {
            'student': student,
            'attendance': attendance
        }


class DisciplinaryManager:
    """Disciplinary and behavior tracking"""
    
    def __init__(self, db):
        self.db = db
    
    def record_incident(self, student_id: str, incident_type: str,
                       description: str, action_taken: str = None,
                       reported_by: int = None) -> bool:
        """Record a disciplinary incident"""
        self.db.execute("""
            INSERT INTO disciplinary 
            (student_id, incident_date, incident_type, description, 
             action_taken, reported_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, datetime.now().date(), incident_type,
              description, action_taken, reported_by))
        
        return True
    
    def get_student_record(self, student_id: str) -> List[Dict]:
        """Get disciplinary record for a student"""
        return self.db.fetch_all("""
            SELECT * FROM disciplinary 
            WHERE student_id = ?
            ORDER BY incident_date DESC
        """, (student_id,))
    
    def resolve_incident(self, incident_id: int) -> bool:
        """Mark an incident as resolved"""
        self.db.execute(
            "UPDATE disciplinary SET is_resolved = 1 WHERE id = ?",
            (incident_id,)
        )
        return True


class AlumniManager:
    """Alumni and graduation records"""
    
    def __init__(self, db):
        self.db = db
    
    def archive_alumni(self, student_id: str, graduation_year: int,
                      graduation_class: str = None,
                      current_occupation: str = None,
                      current_institution: str = None,
                      contact_info: str = None,
                      achievements: str = None) -> bool:
        """Archive a student as alumni"""
        # Update student status
        self.db.execute(
            "UPDATE students SET status = 'graduated' WHERE student_id = ?",
            (student_id,)
        )
        
        # Create alumni record
        self.db.execute("""
            INSERT INTO alumni 
            (student_id, graduation_year, graduation_class, current_occupation,
             current_institution, contact_info, achievements)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (student_id, graduation_year, graduation_class, current_occupation,
              current_institution, contact_info, achievements))
        
        return True
    
    def get_alumni_list(self, year: int = None) -> List[Dict]:
        """Get alumni list"""
        query = """
            SELECT a.*, s.first_name, s.last_name, s.student_id,
                   st.stream_name
            FROM alumni a
            JOIN students s ON a.student_id = s.student_id
            JOIN streams st ON s.stream_id = st.id
        """
        params = []
        
        if year:
            query += " WHERE a.graduation_year = ?"
            params.append(year)
        
        query += " ORDER BY a.graduation_year DESC, s.last_name"
        
        return self.db.fetch_all(query, params)


class AuditManager:
    """Audit trail and system activity logs"""
    
    def __init__(self, db):
        self.db = db
    
    def log_action(self, user_id: int, action: str,
                  table_affected: str = None, record_id: int = None,
                  old_value: str = None, new_value: str = None,
                  ip_address: str = None) -> bool:
        """Log an audit action"""
        self.db.execute("""
            INSERT INTO audit_trail 
            (user_id, action, table_affected, record_id, 
             old_value, new_value, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, action, table_affected, record_id,
              old_value, new_value, ip_address))
        
        return True
    
    def get_audit_log(self, user_id: int = None,
                     table_name: str = None,
                     start_date: str = None,
                     end_date: str = None,
                     limit: int = 100) -> List[Dict]:
        """Get audit log with filters"""
        query = """
            SELECT at.*, u.full_name, u.username
            FROM audit_trail at
            JOIN users u ON at.user_id = u.id
            WHERE 1=1
        """
        params = []
        
        if user_id:
            query += " AND at.user_id = ?"
            params.append(user_id)
        
        if table_name:
            query += " AND at.table_affected = ?"
            params.append(table_name)
        
        if start_date:
            query += " AND at.timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND at.timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY at.timestamp DESC LIMIT ?"
        params.append(limit)
        
        return self.db.fetch_all(query, params)


class ImpersonationManager:
    """Super Admin user impersonation"""
    
    def __init__(self, db):
        self.db = db
    
    def impersonate_user(self, admin_id: int, target_user_id: int) -> Tuple[bool, str]:
        """Impersonate another user (Super Admin only)"""
        # Verify admin is Super Admin
        admin = self.db.fetch_one(
            "SELECT role FROM users WHERE id = ?",
            (admin_id,)
        )
        
        if not admin or admin['role'] != 'super_admin':
            return False, "Only Super Admin can impersonate users"
        
        # Get target user
        target = self.db.fetch_one(
            "SELECT * FROM users WHERE id = ? AND is_active = 1",
            (target_user_id,)
        )
        
        if not target:
            return False, "Target user not found or inactive"
        
        return True, "Impersonation started"
    
    def end_impersonation(self) -> None:
        """End impersonation session"""
        pass  # Handled in session management


class AnnouncementManager:
    """School announcements management"""
    
    def __init__(self, db):
        self.db = db
    
    def create_announcement(self, title: str, content: str,
                           priority: str = 'normal',
                           target_audience: str = 'all',
                           published_by: int = None) -> bool:
        """Create a new announcement"""
        self.db.execute("""
            INSERT INTO announcements 
            (title, content, priority, target_audience, published_by)
            VALUES (?, ?, ?, ?, ?)
        """, (title, content, priority, target_audience, published_by))
        
        return True
    
    def get_active_announcements(self, audience: str = 'all') -> List[Dict]:
        """Get active announcements"""
        query = "SELECT * FROM announcements WHERE is_active = 1"
        params = []
        
        if audience != 'all':
            query += " AND (target_audience = ? OR target_audience = 'all')"
            params.append(audience)
        
        query += " ORDER BY created_at DESC"
        
        return self.db.fetch_all(query, params)


class IDCardDesigner:
    """Custom ID card template designer"""
    
    TEMPLATES = {
        'standard': {
            'name': 'Standard Card',
            'layout': 'horizontal',
            'elements': ['logo', 'header', 'photo', 'info', 'qr']
        },
        'vertical': {
            'name': 'Vertical Card',
            'layout': 'vertical',
            'elements': ['logo', 'header', 'photo', 'info', 'qr']
        },
        'minimalist': {
            'name': 'Minimalist',
            'layout': 'horizontal',
            'elements': ['header', 'photo', 'info']
        },
        'premium': {
            'name': 'Premium',
            'layout': 'horizontal',
            'elements': ['logo', 'header', 'photo', 'info', 'qr', 'signature', 'stamp']
        }
    }
    
    @classmethod
    def get_templates(cls) -> Dict:
        """Get all available templates"""
        return cls.TEMPLATES
    
    @classmethod
    def get_template(cls, template_key: str) -> Dict:
        """Get a specific template"""
        return cls.TEMPLATES.get(template_key, cls.TEMPLATES['standard'])
