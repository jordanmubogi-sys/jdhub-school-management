"""
Academic Management Module
Handles marks, subjects, classes, rankings, and academic operations
"""

import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class AcademicManager:
    """Manage academic operations"""
    
    def __init__(self, db):
        self.db = db
    
    # ==================== STREAM/CLASS MANAGEMENT ====================
    
    def create_stream(self, stream_name: str, stream_code: str, level: str = None, 
                     capacity: int = 40) -> int:
        """Create a new stream/class"""
        try:
            cursor = self.db.execute(
                """INSERT INTO streams (stream_name, stream_code, level, capacity)
                   VALUES (?, ?, ?, ?)""",
                (stream_name, stream_code, level, capacity)
            )
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"Stream code '{stream_code}' already exists")
    
    def get_streams(self, active_only: bool = True) -> List[Dict]:
        """Get all streams"""
        query = "SELECT * FROM streams"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY stream_name"
        return self.db.fetch_all(query)
    
    def assign_class_teacher(self, stream_id: int, teacher_id: int) -> bool:
        """Assign a class teacher to a stream"""
        self.db.execute(
            "UPDATE streams SET class_teacher_id = ? WHERE id = ?",
            (teacher_id, stream_id)
        )
        return True
    
    # ==================== SUBJECT MANAGEMENT ====================
    
    def create_subject(self, subject_name: str, subject_code: str,
                      subject_type: str = 'core', is_compulsory: bool = False,
                      department: str = None, pass_mark: int = 40) -> int:
        """Create a new subject"""
        try:
            cursor = self.db.execute(
                """INSERT INTO subjects (subject_name, subject_code, subject_type, 
                                        is_compulsory, department, pass_mark)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (subject_name, subject_code, subject_type, is_compulsory, 
                 department, pass_mark)
            )
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"Subject code '{subject_code}' already exists")
    
    def assign_subject_to_stream(self, stream_id: int, subject_id: int) -> bool:
        """Assign a subject to a stream"""
        try:
            self.db.execute(
                "INSERT INTO stream_subjects (stream_id, subject_id) VALUES (?, ?)",
                (stream_id, subject_id)
            )
            return True
        except sqlite3.IntegrityError:
            return False  # Already assigned
    
    def get_stream_subjects(self, stream_id: int) -> List[Dict]:
        """Get all subjects for a stream"""
        return self.db.fetch_all("""
            SELECT s.* FROM subjects s
            JOIN stream_subjects ss ON s.id = ss.subject_id
            WHERE ss.stream_id = ?
            ORDER BY s.subject_name
        """, (stream_id,))
    
    # ==================== MARKS MANAGEMENT ====================
    
    def enter_marks(self, student_id: str, subject_id: int, term_id: int,
                   class_work: float = None, homework: float = None,
                   midterm: float = None, final_exam: float = None) -> bool:
        """Enter or update marks for a student"""
        # Calculate total
        components = [class_work, homework, midterm, final_exam]
        total = sum(c for c in components if c is not None)
        
        # Get grade
        grade = self._calculate_grade(total)
        
        # Get or determine stream
        student = self.db.fetch_one(
            "SELECT stream_id FROM students WHERE student_id = ?",
            (student_id,)
        )
        stream_id = student['stream_id'] if student else None
        
        # Insert or update
        self.db.execute("""
            INSERT OR REPLACE INTO marks 
            (student_id, subject_id, stream_id, term_id, class_work, homework, 
             midterm, final_exam, total_score, grade, entered_by, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (student_id, subject_id, stream_id, term_id, class_work, homework,
              midterm, final_exam, total, grade, None))
        
        return True
    
    def _calculate_grade(self, score: float) -> str:
        """Calculate grade from score"""
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B+'
        elif score >= 60:
            return 'B'
        elif score >= 50:
            return 'C+'
        elif score >= 40:
            return 'C'
        elif score >= 30:
            return 'D'
        else:
            return 'F'
    
    def calculate_rankings(self, term_id: int, stream_id: int = None) -> None:
        """Calculate student rankings for a term"""
        # Calculate total scores per student
        query = """
            SELECT student_id, SUM(total_score) as total,
                   AVG(total_score) as average,
                   COUNT(*) as subjects_count
            FROM marks
            WHERE term_id = ?
        """
        params = [term_id]
        
        if stream_id:
            query += " AND stream_id = ?"
            params.append(stream_id)
        
        query += " GROUP BY student_id ORDER BY total DESC"
        
        students = self.db.fetch_all(query, params)
        
        # Update rankings
        for rank, student in enumerate(students, 1):
            # Get position in class
            position = rank
            
            # Update all marks for this student/term with ranking
            self.db.execute("""
                UPDATE marks 
                SET position_in_class = ?
                WHERE student_id = ? AND term_id = ?
            """, (position, student['student_id'], term_id))
    
    def get_student_marks(self, student_id: str, term_id: int) -> List[Dict]:
        """Get all marks for a student in a term"""
        return self.db.fetch_all("""
            SELECT m.*, s.subject_name, s.subject_code
            FROM marks m
            JOIN subjects s ON m.subject_id = s.id
            WHERE m.student_id = ? AND m.term_id = ?
            ORDER BY s.subject_name
        """, (student_id, term_id))
    
    def get_class_broadsheet(self, stream_id: int, term_id: int) -> List[Dict]:
        """Get complete class broadsheet with all students and subjects"""
        # Get all subjects for this stream
        subjects = self.get_stream_subjects(stream_id)
        
        # Get all students in this stream
        students = self.db.fetch_all("""
            SELECT * FROM students 
            WHERE stream_id = ? AND status = 'active'
            ORDER BY first_name, last_name
        """, (stream_id,))
        
        broadsheet = []
        for student in students:
            row = {
                'student_id': student['student_id'],
                'name': f"{student['first_name']} {student['last_name']}",
                'marks': {}
            }
            
            for subject in subjects:
                mark = self.db.fetch_one("""
                    SELECT * FROM marks 
                    WHERE student_id = ? AND subject_id = ? AND term_id = ?
                """, (student['student_id'], subject['id'], term_id))
                
                row['marks'][subject['id']] = mark['total_score'] if mark else None
            
            broadsheet.append(row)
        
        return broadsheet
    
    # ==================== TERM MANAGEMENT ====================
    
    def create_term(self, term_name: str, academic_year: str,
                   start_date: str = None, end_date: str = None) -> int:
        """Create a new academic term"""
        # Set previous term as not current
        self.db.execute("UPDATE academic_terms SET is_current = 0")
        
        cursor = self.db.execute("""
            INSERT INTO academic_terms 
            (term_name, academic_year, start_date, end_date, is_current)
            VALUES (?, ?, ?, ?, 1)
        """, (term_name, academic_year, start_date, end_date))
        
        return cursor.lastrowid
    
    def publish_term(self, term_id: int, user_id: int) -> Tuple[bool, str]:
        """Publish a term - lock all marks"""
        from licensing import TermPublisher
        return TermPublisher.publish_term(self.db, term_id, user_id)
    
    def advance_term(self, user_id: int) -> Tuple[bool, str]:
        """Advance to next term (requires authorization)"""
        # Check if current term is published
        current = self.db.fetch_one(
            "SELECT * FROM academic_terms WHERE is_current = 1"
        )
        
        if not current:
            return False, "No current term set"
        
        if not current['is_published']:
            return False, "Current term must be published first"
        
        # Create next term
        term_name = current['term_name']
        year = current['academic_year']
        
        # Simple term rotation: Term 1 -> Term 2 -> Term 3 -> Next Year Term 1
        if term_name == 'Term 1':
            next_term = 'Term 2'
            next_year = year
        elif term_name == 'Term 2':
            next_term = 'Term 3'
            next_year = year
        else:
            next_term = 'Term 1'
            # Parse year (e.g., "2024-25")
            parts = year.split('-')
            next_year = f"{parts[0]}-{int(parts[1]) + 1 if len(parts) > 1 else '25'}"
        
        # Create and set as current
        self.create_term(next_term, next_year)
        
        return True, f"Advanced to {next_term} {next_year}"
    
    # ==================== COMMENTS ====================
    
    def generate_auto_comment(self, average_score: float, position: int, 
                            total: int) -> str:
        """Auto-generate a teacher comment based on performance"""
        from pdf_generator import ReportCardGenerator
        return ReportCardGenerator.auto_generate_comment(average_score, position, total)
    
    def save_comment(self, student_id: str, term_id: int, 
                    class_teacher_comment: str = None,
                    head_teacher_comment: str = None,
                    user_id: int = None) -> bool:
        """Save or update student comment"""
        self.db.execute("""
            INSERT OR REPLACE INTO comments 
            (student_id, term_id, class_teacher_comment, head_teacher_comment, 
             created_by, is_edited, updated_at)
            VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
        """, (student_id, term_id, class_teacher_comment, head_teacher_comment, user_id))
        return True
    
    # ==================== PROMOTION ====================
    
    def promote_students(self, from_year: str, to_year: str, 
                         criteria: Dict = None) -> Dict:
        """Promote all students to the next year"""
        if criteria is None:
            criteria = {'min_average': 40, 'max_repeats': 2}
        
        # Get all students from the year
        students = self.db.fetch_all("""
            SELECT s.*, st.stream_name,
                   (SELECT AVG(total_score) FROM marks WHERE student_id = s.student_id) as avg_score
            FROM students s
            JOIN streams st ON s.stream_id = st.id
            WHERE st.academic_year = ? AND s.status = 'active'
        """, (from_year,))
        
        promoted = []
        not_promoted = []
        
        for student in students:
            avg = student.get('avg_score', 0) or 0
            
            if avg >= criteria['min_average']:
                promoted.append(student)
                # Archive current status
                self.db.execute("""
                    INSERT INTO student_history (student_id, year, status, avg_score)
                    VALUES (?, ?, 'promoted', ?)
                """, (student['student_id'], from_year, avg))
            else:
                not_promoted.append({
                    'student': student,
                    'reason': 'Below minimum average'
                })
        
        return {
            'promoted_count': len(promoted),
            'not_promoted': not_promoted,
            'total': len(students)
        }


class RankingEngine:
    """Generate student and class rankings"""
    
    def __init__(self, db):
        self.db = db
    
    def get_stream_rankings(self, stream_id: int, term_id: int) -> List[Dict]:
        """Get student rankings for a stream"""
        return self.db.fetch_all("""
            SELECT s.student_id, s.first_name, s.last_name,
                   SUM(m.total_score) as total,
                   AVG(m.total_score) as average,
                   RANK() OVER (ORDER BY SUM(m.total_score) DESC) as position
            FROM students s
            JOIN marks m ON s.student_id = m.student_id
            WHERE s.stream_id = ? AND m.term_id = ?
            GROUP BY s.student_id
            ORDER BY total DESC
        """, (stream_id, term_id))
    
    def get_subject_rankings(self, subject_id: int, term_id: int,
                           stream_id: int = None) -> List[Dict]:
        """Get student rankings for a subject"""
        query = """
            SELECT s.student_id, s.first_name, s.last_name, st.stream_name,
                   m.total_score,
                   RANK() OVER (ORDER BY m.total_score DESC) as position
            FROM students s
            JOIN marks m ON s.student_id = m.student_id
            JOIN streams st ON s.stream_id = st.id
            WHERE m.subject_id = ? AND m.term_id = ?
        """
        params = [subject_id, term_id]
        
        if stream_id:
            query += " AND s.stream_id = ?"
            params.append(stream_id)
        
        query += " ORDER BY m.total_score DESC"
        
        return self.db.fetch_all(query, params)
    
    def get_top_students(self, term_id: int, limit: int = 10,
                        year: str = None) -> List[Dict]:
        """Get top performing students"""
        query = """
            SELECT s.student_id, s.first_name, s.last_name, st.stream_name,
                   SUM(m.total_score) as total,
                   AVG(m.total_score) as average
            FROM students s
            JOIN marks m ON s.student_id = m.student_id
            JOIN streams st ON s.stream_id = st.id
            JOIN academic_terms at ON m.term_id = at.id
            WHERE m.term_id = ?
        """
        params = [term_id]
        
        if year:
            query += " AND at.academic_year = ?"
            params.append(year)
        
        query += " GROUP BY s.student_id ORDER BY total DESC LIMIT ?"
        params.append(limit)
        
        return self.db.fetch_all(query, params)
    
    def get_leaderboard(self, term_id: int = None, year: str = None,
                       limit: int = 20) -> List[Dict]:
        """Get overall leaderboard"""
        query = """
            SELECT s.student_id, s.first_name, s.last_name, st.stream_name,
                   s.photo,
                   AVG(m.total_score) as average,
                   SUM(m.total_score) as total_points,
                   COUNT(DISTINCT m.term_id) as terms_count
            FROM students s
            JOIN marks m ON s.student_id = m.student_id
            JOIN streams st ON s.stream_id = st.id
            JOIN academic_terms at ON m.term_id = at.id
            WHERE s.status = 'active'
        """
        params = []
        
        if term_id:
            query += " AND m.term_id = ?"
            params.append(term_id)
        
        if year:
            query += " AND at.academic_year = ?"
            params.append(year)
        
        query += " GROUP BY s.student_id ORDER BY average DESC LIMIT ?"
        params.append(limit)
        
        return self.db.fetch_all(query, params)


class GradingSchemeManager:
    """Custom grading scheme configurator"""
    
    DEFAULT_SCHEMES = {
        'kenya': {
            'name': 'Kenya CBC/8-4-4',
            'grades': [
                (90, 'A', 'Excellent'),
                (80, 'A-', 'Very Good'),
                (70, 'B+', 'Good'),
                (60, 'B', 'Above Average'),
                (50, 'B-', 'Average'),
                (40, 'C+', 'Below Average'),
                (30, 'C', 'Pass'),
                (20, 'C-', 'Pass'),
                (0, 'D', 'Fail'),
            ]
        },
        'uk': {
            'name': 'UK Grading (A*-G)',
            'grades': [
                (90, 'A*', 'Outstanding'),
                (80, 'A', 'Excellent'),
                (70, 'B', 'Very Good'),
                (60, 'C', 'Good'),
                (50, 'D', 'Pass'),
                (40, 'E', 'Below Pass'),
                (30, 'F', 'Fail'),
                (0, 'G', 'Fail'),
            ]
        },
        'us': {
            'name': 'US Grading (A-F)',
            'grades': [
                (90, 'A', 'Excellent'),
                (80, 'B', 'Good'),
                (70, 'C', 'Average'),
                (60, 'D', 'Below Average'),
                (0, 'F', 'Fail'),
            ]
        },
        'percentage': {
            'name': 'Percentage Based',
            'grades': [
                (90, 'A+', 'Outstanding'),
                (80, 'A', 'Excellent'),
                (70, 'B', 'Very Good'),
                (60, 'C', 'Good'),
                (50, 'D', 'Pass'),
                (40, 'E', 'Pass'),
                (0, 'F', 'Fail'),
            ]
        }
    }
    
    @classmethod
    def get_scheme_names(cls) -> List[str]:
        """Get list of available scheme names"""
        return list(cls.DEFAULT_SCHEMES.keys())
    
    @classmethod
    def get_scheme(cls, scheme_key: str) -> Dict:
        """Get a specific grading scheme"""
        return cls.DEFAULT_SCHEMES.get(scheme_key, cls.DEFAULT_SCHEMES['kenya'])
    
    @classmethod
    def calculate_grade(cls, score: float, scheme_key: str = 'kenya') -> Tuple[str, str]:
        """Calculate grade and remark from score"""
        scheme = cls.get_scheme(scheme_key)
        for min_score, grade, remark in scheme['grades']:
            if score >= min_score:
                return grade, remark
        return 'F', 'Fail'
    
    @classmethod
    def save_custom_scheme(cls, db, scheme_name: str, grades: List[Tuple]) -> bool:
        """Save a custom grading scheme to database"""
        import json
        scheme_data = json.dumps({
            'name': scheme_name,
            'grades': grades
        })
        
        db.execute("""
            INSERT OR REPLACE INTO school_settings (id, grading_scheme)
            VALUES (1, ?)
        """, (scheme_data,))
        
        return True
