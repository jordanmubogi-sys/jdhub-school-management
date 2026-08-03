"""
Fee Management Module
Handles fee structures, payments, receipts, and financial reporting
"""

import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from io import BytesIO
import uuid


class FeeManager:
    """Manage school fees and payments"""
    
    def __init__(self, db):
        self.db = db
    
    # ==================== FEE STRUCTURE ====================
    
    def create_fee_item(self, stream_id: int, fee_name: str, amount: float,
                       academic_year: str = None, term_id: int = None,
                       due_date: str = None, is_mandatory: bool = True) -> int:
        """Create a fee structure item"""
        cursor = self.db.execute("""
            INSERT INTO fee_structure 
            (stream_id, fee_name, amount, academic_year, term_id, due_date, is_mandatory)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (stream_id, fee_name, amount, academic_year, term_id, due_date, is_mandatory))
        return cursor.lastrowid
    
    def get_fee_structure(self, stream_id: int = None, 
                         academic_year: str = None) -> List[Dict]:
        """Get fee structure"""
        query = "SELECT fs.*, s.stream_name FROM fee_structure fs LEFT JOIN streams s ON fs.stream_id = s.id WHERE 1=1"
        params = []
        
        if stream_id:
            query += " AND fs.stream_id = ?"
            params.append(stream_id)
        
        if academic_year:
            query += " AND fs.academic_year = ?"
            params.append(academic_year)
        
        query += " ORDER BY s.stream_name, fs.fee_name"
        return self.db.fetch_all(query, params)
    
    def bulk_create_fees(self, stream_ids: List[int], fee_name: str,
                        amount: float, academic_year: str, term_id: int = None) -> int:
        """Create the same fee for multiple streams"""
        count = 0
        for stream_id in stream_ids:
            self.create_fee_item(stream_id, fee_name, amount, academic_year, term_id)
            count += 1
        return count
    
    # ==================== PAYMENTS ====================
    
    def record_payment(self, student_id: str, amount_paid: float,
                      payment_method: str = 'cash', term_id: int = None,
                      fee_structure_id: int = None, received_by: int = None,
                      notes: str = None) -> Tuple[bool, str]:
        """Record a fee payment"""
        # Generate receipt number
        receipt_no = self._generate_receipt_number()
        
        cursor = self.db.execute("""
            INSERT INTO fee_payments 
            (student_id, term_id, fee_structure_id, amount_paid, payment_method,
             receipt_number, received_by, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (student_id, term_id, fee_structure_id, amount_paid, payment_method,
              receipt_no, received_by, notes))
        
        # Log the transaction
        self.db.execute("""
            INSERT INTO audit_trail 
            (user_id, action, table_affected, record_id, new_value)
            VALUES (?, 'PAYMENT', 'fee_payments', ?, ?)
        """, (received_by, cursor.lastrowid, f"Payment: KES {amount_paid}"))
        
        return True, receipt_no
    
    def _generate_receipt_number(self) -> str:
        """Generate unique receipt number"""
        prefix = datetime.now().strftime('%Y%m%d')
        unique = str(uuid.uuid4())[:6].upper()
        return f"RCP/{prefix}/{unique}"
    
    def get_student_balance(self, student_id: str, term_id: int = None) -> Dict:
        """Get student's fee balance"""
        # Total fees
        query = """
            SELECT COALESCE(SUM(fs.amount), 0) as total_fees
            FROM fee_structure fs
            JOIN students s ON fs.stream_id = s.stream_id
            WHERE s.student_id = ?
        """
        params = [student_id]
        
        if term_id:
            query += " AND fs.term_id = ?"
            params.append(term_id)
        
        total_fees = self.db.fetch_one(query, params)['total_fees']
        
        # Total paid
        query = "SELECT COALESCE(SUM(amount_paid), 0) as total_paid FROM fee_payments WHERE student_id = ?"
        params = [student_id]
        
        if term_id:
            query += " AND term_id = ?"
        
        total_paid = self.db.fetch_one(query, params)['total_paid']
        
        return {
            'total_fees': total_fees,
            'total_paid': total_paid,
            'balance': total_fees - total_paid,
            'is_fully_paid': total_fees <= total_paid
        }
    
    def get_payment_history(self, student_id: str = None,
                           term_id: int = None,
                           start_date: str = None,
                           end_date: str = None) -> List[Dict]:
        """Get payment history with filters"""
        query = """
            SELECT fp.*, s.student_id, s.first_name, s.last_name,
                   at.term_name, at.academic_year,
                   u.full_name as received_by_name
            FROM fee_payments fp
            JOIN students s ON fp.student_id = s.student_id
            LEFT JOIN academic_terms at ON fp.term_id = at.id
            LEFT JOIN users u ON fp.received_by = u.id
            WHERE 1=1
        """
        params = []
        
        if student_id:
            query += " AND fp.student_id = ?"
            params.append(student_id)
        
        if term_id:
            query += " AND fp.term_id = ?"
            params.append(term_id)
        
        if start_date:
            query += " AND fp.payment_date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND fp.payment_date <= ?"
            params.append(end_date)
        
        query += " ORDER BY fp.payment_date DESC"
        
        return self.db.fetch_all(query, params)
    
    def get_receipt(self, receipt_number: str) -> Optional[Dict]:
        """Get receipt details"""
        receipt = self.db.fetch_one("""
            SELECT fp.*, s.first_name, s.last_name, st.stream_name,
                   at.term_name, at.academic_year
            FROM fee_payments fp
            JOIN students s ON fp.student_id = s.student_id
            JOIN streams st ON s.stream_id = st.id
            LEFT JOIN academic_terms at ON fp.term_id = at.id
            WHERE fp.receipt_number = ?
        """, (receipt_number,))
        
        return dict(receipt) if receipt else None
    
    # ==================== REPORTS ====================
    
    def get_collection_summary(self, term_id: int = None,
                               start_date: str = None,
                               end_date: str = None) -> Dict:
        """Get fee collection summary"""
        query = """
            SELECT 
                COUNT(DISTINCT fp.student_id) as students_paid,
                COUNT(*) as total_transactions,
                SUM(fp.amount_paid) as total_collected
            FROM fee_payments fp
            WHERE 1=1
        """
        params = []
        
        if term_id:
            query += " AND fp.term_id = ?"
            params.append(term_id)
        
        if start_date:
            query += " AND fp.payment_date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND fp.payment_date <= ?"
            params.append(end_date)
        
        return self.db.fetch_one(query, params) or {}
    
    def get_balance_report(self, term_id: int = None) -> List[Dict]:
        """Get students with outstanding balances"""
        query = """
            SELECT s.student_id, s.first_name, s.last_name, st.stream_name,
                   COALESCE(SUM(fs.amount), 0) as total_fees,
                   COALESCE((SELECT SUM(fp.amount_paid) FROM fee_payments fp WHERE fp.student_id = s.student_id), 0) as total_paid,
                   (COALESCE(SUM(fs.amount), 0) - COALESCE((SELECT SUM(fp.amount_paid) FROM fee_payments fp WHERE fp.student_id = s.student_id), 0)) as balance
            FROM students s
            JOIN streams st ON s.stream_id = st.id
            LEFT JOIN fee_structure fs ON fs.stream_id = s.stream_id
            WHERE s.status = 'active'
        """
        params = []
        
        if term_id:
            query += " AND fs.term_id = ?"
            params.append(term_id)
        
        query += " GROUP BY s.student_id HAVING balance > 0 ORDER BY balance DESC"
        
        return self.db.fetch_all(query, params)
    
    def get_daily_collections(self, start_date: str, end_date: str) -> List[Dict]:
        """Get daily collection totals"""
        return self.db.fetch_all("""
            SELECT DATE(fp.payment_date) as date,
                   COUNT(*) as transactions,
                   SUM(fp.amount_paid) as total
            FROM fee_payments fp
            WHERE fp.payment_date BETWEEN ? AND ?
            GROUP BY DATE(fp.payment_date)
            ORDER BY date DESC
        """, (start_date, end_date))
    
    # ==================== DEMAND LETTERS ====================
    
    def generate_fee_demand_letter_data(self, student_id: str) -> Dict:
        """Generate data for fee demand letter"""
        student = self.db.fetch_one("""
            SELECT s.*, st.stream_name
            FROM students s
            JOIN streams st ON s.stream_id = st.id
            WHERE s.student_id = ?
        """, (student_id,))
        
        if not student:
            return None
        
        # Get latest payment info
        latest = self.db.fetch_one("""
            SELECT * FROM fee_payments 
            WHERE student_id = ? 
            ORDER BY payment_date DESC LIMIT 1
        """, (student_id,))
        
        balance = self.get_student_balance(student_id)
        
        # Get parent info
        parent = self.db.fetch_one("""
            SELECT * FROM parents 
            WHERE student_id = ? AND is_primary = 1
        """, (student_id,))
        
        return {
            'student': student,
            'parent': parent,
            'balance': balance,
            'latest_payment': latest,
            'date': datetime.now().strftime('%Y-%m-%d')
        }


class AutomatedReminders:
    """Generate automated fee reminders"""
    
    def __init__(self, db):
        self.db = db
    
    def get_overdue_students(self, days_overdue: int = 7) -> List[Dict]:
        """Get students with overdue fees"""
        cutoff_date = (datetime.now() - timedelta(days=days_overdue)).strftime('%Y-%m-%d')
        
        return self.db.fetch_all("""
            SELECT s.student_id, s.first_name, s.last_name, st.stream_name,
                   p.primary_phone, p.parent_name,
                   fs.fue_date, fs.amount,
                   (SELECT SUM(fp.amount_paid) FROM fee_payments fp WHERE fp.student_id = s.student_id) as paid
            FROM students s
            JOIN streams st ON s.stream_id = st.id
            JOIN fee_structure fs ON fs.stream_id = s.stream_id
            JOIN parents p ON p.student_id = s.student_id AND p.is_primary = 1
            WHERE fs.due_date < ? AND fs.is_mandatory = 1
            GROUP BY s.student_id
            HAVING (fs.amount - COALESCE((SELECT SUM(fp.amount_paid) FROM fee_payments fp WHERE fp.student_id = s.student_id), 0)) > 0
        """, (cutoff_date,))
    
    def generate_reminder_message(self, student_name: str, balance: float,
                                 due_date: str) -> str:
        """Generate a reminder message"""
        return f"""
Dear Parent/Guardian,

This is a reminder that {student_name} has an outstanding fee balance of KES {balance:,.2f} 
which was due on {due_date}.

Please ensure payment is made promptly to avoid any inconvenience.

For queries, please contact the school bursar.

Regards,
{self.db.fetch_one('SELECT school_name FROM school_settings WHERE id = 1')['school_name']}
        """.strip()
