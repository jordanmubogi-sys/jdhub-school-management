"""
Professional PDF Generator for Report Cards, ID Cards, and Documents
Modern Graphic Design with School Branding
"""

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from PIL import Image, ImageDraw, ImageFilter
import base64
from typing import List, Dict, Optional
import math


class PDFStyles:
    """Color palette and styling constants"""
    PRIMARY_BLUE = HexColor('#2563eb')
    LIGHT_BG = HexColor('#f8fafc')
    WHITE = white
    DARK_TEXT = HexColor('#0f172a')
    GRAY_TEXT = HexColor('#64748b')
    SUCCESS_GREEN = HexColor('#16a34a')
    WARNING_ORANGE = HexColor('#ea580c')
    BORDER_GRAY = HexColor('#e2e8f0')
    
    # Grade colors
    GRADE_COLORS = {
        'A': HexColor('#16a34a'),
        'B': HexColor('#2563eb'),
        'C': HexColor('#ca8a04'),
        'D': HexColor('#ea580c'),
        'F': HexColor('#dc2626')
    }


class ModernPDFHeader:
    """Create modern curved PDF headers with school branding"""
    
    @staticmethod
    def draw_header(c: canvas.Canvas, school_name: str, logo_data: bytes = None,
                   address: str = "", phone: str = "", website: str = "",
                   motto: str = "", page_width: float = A4[0]):
        """Draw a modern curved header with school branding"""
        height = 45 * mm
        
        # Draw curved background
        c.setFillColor(PDFStyles.PRIMARY_BLUE)
        
        # Create curved shape
        path = c.beginPath()
        path.moveTo(0, A4[1])
        path.lineTo(page_width, A4[1])
        
        # Curved bottom edge
        for x in range(int(page_width), -1, -10):
            y = A4[1] - height + 15 * math.sin((x / page_width) * math.pi)
            path.lineTo(x, y)
        
        path.lineTo(0, A4[1] - height + 20)
        path.close()
        c.drawPath(path, fill=1, stroke=0)
        
        # Add gradient overlay effect (simulated)
        c.setFillColor(HexColor('#1d4ed8'))
        c.rect(0, A4[1] - height, page_width, 5 * mm, fill=1, stroke=0)
        
        # Logo
        if logo_data:
            try:
                img = Image.open(BytesIO(logo_data))
                img = img.resize((80, 80), Image.LANCZOS)
                logo_buffer = BytesIO()
                img.save(logo_buffer, format='PNG')
                logo_buffer.seek(0)
                c.drawImage(ImageReader(logo_buffer), 15 * mm, A4[1] - height + 5 * mm, 
                           width=25 * mm, height=25 * mm, mask='auto')
            except:
                pass
        
        # School Name
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 18)
        name_x = 50 * mm if logo_data else 20 * mm
        c.drawString(name_x, A4[1] - 22 * mm, school_name[:40])
        
        # Motto
        if motto:
            c.setFont("Helvetica-Oblique", 9)
            c.drawString(name_x, A4[1] - 30 * mm, f'"{motto}"')
        
        # Contact info (right aligned)
        c.setFont("Helvetica", 8)
        info_texts = [x for x in [address, phone, website] if x]
        y_pos = A4[1] - 22 * mm
        for i, text in enumerate(info_texts[:3]):
            c.drawRightString(page_width - 15 * mm, y_pos - (i * 10), text[:50])
        
        return height


class ReportCardGenerator:
    """Generate professional student report cards"""
    
    GRADE_BRACKETS = [
        (90, 'A+', 'Outstanding'),
        (80, 'A', 'Excellent'),
        (70, 'B+', 'Very Good'),
        (60, 'B', 'Good'),
        (50, 'C+', 'Above Average'),
        (40, 'C', 'Average'),
        (30, 'D', 'Below Average'),
        (0, 'F', 'Fail')
    ]
    
    @staticmethod
    def get_grade_and_remark(score: float) -> tuple:
        """Get grade and remark based on score"""
        for min_score, grade, remark in ReportCardGenerator.GRADE_BRACKETS:
            if score >= min_score:
                return grade, remark
        return 'F', 'Fail'
    
    @staticmethod
    def auto_generate_comment(average_score: float, position: int, total: int) -> str:
        """Auto-generate comment based on performance"""
        if average_score >= 90:
            return f"An outstanding performance. {position}{'st' if position==1 else 'nd' if position==2 else 'rd'} in class of {total}. Keep it up!"
        elif average_score >= 80:
            return f"Excellent performance. Ranked {position}{'st' if position==1 else 'nd' if position==2 else 'rd'} out of {total}. Well done!"
        elif average_score >= 70:
            return f"Very good performance. {position}{'st' if position==1 else 'nd' if position==2 else 'rd'} position. Continue the good work."
        elif average_score >= 60:
            return f"Good effort. {position}{'st' if position==1 else 'nd' if position==2 else 'rd'} in class. Aim higher!"
        elif average_score >= 50:
            return f"Satisfactory performance. Position {position} of {total}. Focus on improvement."
        elif average_score >= 40:
            return f"{position}{'st' if position==1 else 'nd' if position==2 else 'rd'} position. Needs more dedication and focus."
        else:
            return f"Poor performance. {position} of {total}. Urgent improvement required."
    
    @classmethod
    def generate_report_card(cls, student_data: Dict, marks_data: List[Dict],
                           school_settings: Dict, term_info: Dict) -> BytesIO:
        """Generate a complete report card PDF"""
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Draw modern header
        header_height = ModernPDFHeader.draw_header(
            c, 
            school_settings.get('school_name', 'School'),
            school_settings.get('school_logo'),
            school_settings.get('address', ''),
            school_settings.get('phone', ''),
            school_settings.get('website', ''),
            school_settings.get('motto', '')
        )
        
        # Student Info Section
        y = height - header_height - 15 * mm
        
        # Student photo
        if student_data.get('photo'):
            try:
                img = Image.open(BytesIO(student_data['photo']))
                img = img.resize((100, 120), Image.LANCZOS)
                photo_buffer = BytesIO()
                img.save(photo_buffer, format='PNG')
                photo_buffer.seek(0)
                c.drawImage(ImageReader(photo_buffer), 15 * mm, y - 35 * mm,
                           width=25 * mm, height=30 * mm, mask='auto')
            except:
                pass
        
        # Student details box
        c.setFillColor(PDFStyles.LIGHT_BG)
        c.roundRect(50 * mm, y - 40 * mm, 130 * mm, 40 * mm, 3 * mm, fill=1, stroke=0)
        
        c.setFillColor(PDFStyles.DARK_TEXT)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(55 * mm, y - 10 * mm, f"Student: {student_data.get('first_name', '')} {student_data.get('middle_name', '')} {student_data.get('last_name', '')}")
        
        c.setFont("Helvetica", 9)
        details = [
            f"Student ID: {student_data.get('student_id', 'N/A')}",
            f"Class: {student_data.get('stream_name', 'N/A')}",
            f"Term: {term_info.get('term_name', 'N/A')} - {term_info.get('academic_year', 'N/A')}",
            f"Position: {marks_data[0].get('position_in_class', 'N/A') if marks_data else 'N/A'} of {len(marks_data) if marks_data else 0}"
        ]
        
        for i, detail in enumerate(details):
            c.drawString(55 * mm, y - 20 * mm - (i * 7), detail)
        
        # Marks Table
        y = y - 50 * mm
        
        # Table header
        c.setFillColor(PDFStyles.PRIMARY_BLUE)
        c.rect(15 * mm, y - 8 * mm, 180 * mm, 8 * mm, fill=1, stroke=0)
        
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 9)
        headers = ['Subject', 'CW', 'HW', 'MID', 'FINAL', 'TOTAL', 'GRADE', 'RANK']
        col_widths = [50, 18, 18, 18, 18, 20, 20, 18]
        x_pos = 15 * mm
        for header, col_w in zip(headers, col_widths):
            c.drawString(x_pos + 2, y - 5 * mm, header)
            x_pos += col_w * mm / mm
        
        # Table rows
        y -= 8 * mm
        c.setFont("Helvetica", 8)
        
        for i, mark in enumerate(marks_data):
            row_y = y - (i * 8 * mm)
            
            # Alternate row colors
            if i % 2 == 0:
                c.setFillColor(PDFStyles.LIGHT_BG)
            else:
                c.setFillColor(white)
            c.rect(15 * mm, row_y - 7 * mm, 180 * mm, 7 * mm, fill=1, stroke=0)
            
            c.setFillColor(PDFStyles.DARK_TEXT)
            x_pos = 15 * mm
            values = [
                mark.get('subject_name', '')[:15],
                str(mark.get('class_work', '')),
                str(mark.get('homework', '')),
                str(mark.get('midterm', '')),
                str(mark.get('final_exam', '')),
                str(mark.get('total_score', '')),
                mark.get('grade', ''),
                str(mark.get('position_in_class', ''))
            ]
            for val, col_w in zip(values, col_widths):
                c.drawString(x_pos + 2, row_y - 5 * mm, val)
                x_pos += col_w * mm / mm
        
        # Summary Section
        y = y - (len(marks_data) * 8 * mm) - 10 * mm
        
        # Attendance box
        c.setFillColor(PDFStyles.LIGHT_BG)
        c.roundRect(15 * mm, y - 25 * mm, 85 * mm, 25 * mm, 3 * mm, fill=1, stroke=0)
        
        c.setFillColor(PDFStyles.DARK_TEXT)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(20 * mm, y - 5 * mm, "ATTENDANCE")
        
        c.setFont("Helvetica", 8)
        attendance = marks_data[0].get('attendance', {}) if marks_data else {}
        att_texts = [
            f"Days Present: {attendance.get('days_present', 0)}",
            f"Days Absent: {attendance.get('days_absent', 0)}",
            f"Days Late: {attendance.get('days_late', 0)}"
        ]
        for i, text in enumerate(att_texts):
            c.drawString(20 * mm, y - 13 * mm - (i * 6), text)
        
        # Comments box
        c.setFillColor(PDFStyles.LIGHT_BG)
        c.roundRect(105 * mm, y - 25 * mm, 90 * mm, 25 * mm, 3 * mm, fill=1, stroke=0)
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(110 * mm, y - 5 * mm, "CLASS TEACHER'S COMMENT")
        
        c.setFont("Helvetica", 7)
        comment = marks_data[0].get('class_teacher_comment', '') if marks_data else ''
        if not comment and marks_data:
            avg_score = sum(m.get('total_score', 0) for m in marks_data) / len(marks_data) if marks_data else 0
            pos = marks_data[0].get('position_in_class', 0) if marks_data else 0
            total = len(marks_data)
            comment = cls.auto_generate_comment(avg_score, pos, total)
        
        # Word wrap comment
        words = comment.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line + word) < 55:
                current_line += word + " "
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)
        
        for i, line in enumerate(lines[:3]):
            c.drawString(110 * mm, y - 13 * mm - (i * 6), line)
        
        # Grading legend
        y = y - 35 * mm
        c.setFont("Helvetica", 7)
        c.setFillColor(PDFStyles.GRAY_TEXT)
        c.drawString(15 * mm, y, "Grading: A+(90-100) A(80-89) B+(70-79) B(60-69) C+(50-59) C(40-49) D(30-39) F(0-29)")
        
        # Footer
        c.setFont("Helvetica", 7)
        c.drawRightString(width - 15 * mm, 15 * mm, 
                         f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}")
        c.drawString(15 * mm, 15 * mm, f"{school_settings.get('school_name', 'School')} Management System")
        
        c.save()
        buffer.seek(0)
        return buffer


class IDCardGenerator:
    """Generate student ID cards in various formats"""
    
    TEMPLATES = {
        'standard': {
            'width': 86 * mm,
            'height': 54 * mm,
            'photo_ratio': 0.35
        },
        'vertical': {
            'width': 54 * mm,
            'height': 86 * mm,
            'photo_ratio': 0.35
        },
        'minimalist': {
            'width': 86 * mm,
            'height': 54 * mm,
            'photo_ratio': 0.30
        }
    }
    
    @classmethod
    def generate_id_card(cls, student_data: Dict, school_settings: Dict,
                       template: str = 'standard', include_qr: bool = True) -> BytesIO:
        """Generate a single ID card"""
        template_config = cls.TEMPLATES.get(template, cls.TEMPLATES['standard'])
        
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=(template_config['width'], template_config['height']))
        
        width = template_config['width']
        height = template_config['height']
        
        # Card background
        c.setFillColor(white)
        c.roundRect(0, 0, width, height, 3 * mm, fill=1, stroke=0)
        
        # Border
        c.setStrokeColor(PDFStyles.PRIMARY_BLUE)
        c.setLineWidth(1)
        c.roundRect(1 * mm, 1 * mm, width - 2 * mm, height - 2 * mm, 3 * mm, fill=0, stroke=1)
        
        # Header bar
        c.setFillColor(PDFStyles.PRIMARY_BLUE)
        c.rect(0, height - 12 * mm, width, 12 * mm, fill=1, stroke=0)
        
        # School name in header
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 7)
        school_name = school_settings.get('school_name', 'SCHOOL')[:25]
        c.drawCentredString(width / 2, height - 7 * mm, school_name)
        
        # Photo placeholder
        photo_x = 5 * mm
        photo_y = 8 * mm
        photo_w = 22 * mm
        photo_h = 25 * mm
        
        if student_data.get('photo'):
            try:
                img = Image.open(BytesIO(student_data['photo']))
                img = img.resize((200, 240), Image.LANCZOS)
                photo_buffer = BytesIO()
                img.save(photo_buffer, format='PNG')
                photo_buffer.seek(0)
                c.drawImage(ImageReader(photo_buffer), photo_x, photo_y, 
                           width=photo_w, height=photo_h, mask='auto')
            except:
                pass
        else:
            # Placeholder
            c.setFillColor(PDFStyles.LIGHT_BG)
            c.rect(photo_x, photo_y, photo_w, photo_h, fill=1, stroke=0)
            c.setFillColor(PDFStyles.GRAY_TEXT)
            c.setFont("Helvetica", 6)
            c.drawCentredString(photo_x + photo_w/2, photo_y + photo_h/2, "PHOTO")
        
        # Student info
        info_x = photo_x + photo_w + 3 * mm
        info_y = height - 16 * mm
        
        c.setFillColor(PDFStyles.DARK_TEXT)
        c.setFont("Helvetica-Bold", 5)
        
        fields = [
            ('ID:', student_data.get('student_id', 'N/A')),
            ('NAME:', f"{student_data.get('first_name', '')} {student_data.get('last_name', '')}"[:20]),
            ('CLASS:', student_data.get('stream_name', 'N/A')),
            ('DOB:', str(student_data.get('date_of_birth', 'N/A'))[:10]),
            ('BLOOD:', student_data.get('blood_group', 'N/A')),
        ]
        
        for i, (label, value) in enumerate(fields):
            y_pos = info_y - (i * 5 * mm)
            c.setFont("Helvetica-Bold", 4)
            c.drawString(info_x, y_pos, label)
            c.setFont("Helvetica", 4)
            c.drawString(info_x + 10 * mm, y_pos, str(value)[:20])
        
        # QR Code
        if include_qr:
            qr_size = 15 * mm
            qr_x = width - qr_size - 3 * mm
            qr_y = 5 * mm
            
            # Generate simple QR placeholder
            c.setFillColor(PDFStyles.LIGHT_BG)
            c.rect(qr_x, qr_y, qr_size, qr_size, fill=1, stroke=0)
            c.setFillColor(PDFStyles.DARK_TEXT)
            c.setFont("Helvetica", 4)
            c.drawCentredString(qr_x + qr_size/2, qr_y + qr_size/2, "QR")
        
        # Footer
        c.setFillColor(PDFStyles.GRAY_TEXT)
        c.setFont("Helvetica", 3)
        c.drawCentredString(width / 2, 2 * mm, 
                          f"If found, return to {school_settings.get('school_name', 'School')}")
        
        c.save()
        buffer.seek(0)
        return buffer
    
    @classmethod
    def generate_id_sheet(cls, students: List[Dict], school_settings: Dict,
                         template: str = 'standard') -> BytesIO:
        """Generate A4 sheet with multiple ID cards"""
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # 3 columns x 4 rows = 12 cards per page
        card_w = 60 * mm
        card_h = 38 * mm
        margin_x = (width - 3 * card_w) / 2
        margin_y = 15 * mm
        
        for idx, student in enumerate(students):
            col = idx % 3
            row = idx // 3
            
            x = margin_x + col * (card_w + 5 * mm)
            y = height - margin_y - (row + 1) * (card_h + 10 * mm)
            
            # Generate single card
            id_buffer = cls.generate_id_card(student, school_settings, template)
            c.drawImage(ImageReader(id_buffer), x, y, width=card_w, height=card_h)
            
            # Cutting guides
            c.setStrokeColor(PDFStyles.GRAY_TEXT)
            c.setLineWidth(0.5)
            c.setDash([2, 2])
            
        # Page info
        c.setFont("Helvetica", 8)
        c.drawCentredString(width / 2, 10 * mm, f"ID Card Sheet - {school_settings.get('school_name', 'School')}")
        
        c.save()
        buffer.seek(0)
        return buffer


class FeeReceiptGenerator:
    """Generate fee payment receipts"""
    
    @classmethod
    def generate_receipt(cls, payment_data: Dict, student_data: Dict,
                        school_settings: Dict, receipt_size: str = 'A5') -> BytesIO:
        """Generate fee receipt"""
        if receipt_size == 'thermal':
            page_size = (80 * mm, 150 * mm)
        elif receipt_size == 'A5':
            page_size = A5
        else:
            page_size = A4
        
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=page_size)
        width, height = page_size
        
        # Border
        c.setStrokeColor(PDFStyles.PRIMARY_BLUE)
        c.setLineWidth(2)
        c.rect(5 * mm, 5 * mm, width - 10 * mm, height - 10 * mm)
        
        # Header
        c.setFillColor(PDFStyles.PRIMARY_BLUE)
        c.rect(5 * mm, height - 25 * mm, width - 10 * mm, 20 * mm, fill=1)
        
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(width / 2, height - 18 * mm, "OFFICIAL RECEIPT")
        
        # School info
        c.setFont("Helvetica", 8)
        c.drawCentredString(width / 2, height - 23 * mm, school_settings.get('school_name', 'School'))
        
        y = height - 35 * mm
        
        # Receipt details
        c.setFillColor(PDFStyles.DARK_TEXT)
        c.setFont("Helvetica-Bold", 9)
        
        details = [
            ("Receipt No:", payment_data.get('receipt_number', 'N/A')),
            ("Date:", payment_data.get('payment_date', '')[:10] if payment_data.get('payment_date') else 'N/A'),
            ("Student ID:", student_data.get('student_id', 'N/A')),
            ("Student Name:", f"{student_data.get('first_name', '')} {student_data.get('last_name', '')}"),
            ("Class:", student_data.get('stream_name', 'N/A')),
            ("Term:", payment_data.get('term_name', 'N/A')),
        ]
        
        for label, value in details:
            c.setFont("Helvetica-Bold", 8)
            c.drawString(10 * mm, y, label)
            c.setFont("Helvetica", 8)
            c.drawString(45 * mm, y, str(value))
            y -= 7 * mm
        
        # Divider
        y -= 3 * mm
        c.setStrokeColor(PDFStyles.PRIMARY_BLUE)
        c.line(10 * mm, y, width - 10 * mm, y)
        y -= 8 * mm
        
        # Payment details
        c.setFont("Helvetica-Bold", 10)
        c.drawString(10 * mm, y, "Amount Paid:")
        
        c.setFillColor(PDFStyles.SUCCESS_GREEN)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(60 * mm, y, f"KES {payment_data.get('amount_paid', 0):,.2f}")
        
        y -= 10 * mm
        c.setFillColor(PDFStyles.DARK_TEXT)
        c.setFont("Helvetica", 8)
        c.drawString(10 * mm, y, f"Payment Method: {payment_data.get('payment_method', 'Cash')}")
        
        if payment_data.get('balance', 0) > 0:
            y -= 6 * mm
            c.drawString(10 * mm, y, f"Balance: KES {payment_data.get('balance', 0):,.2f}")
        
        # Footer
        y -= 15 * mm
        c.setFont("Helvetica-Oblique", 7)
        c.setFillColor(PDFStyles.GRAY_TEXT)
        c.drawCentredString(width / 2, y, "Thank you for your payment!")
        c.drawCentredString(width / 2, y - 5 * mm, "For queries, contact the school bursar.")
        
        # Signature line
        y -= 15 * mm
        c.setStrokeColor(PDFStyles.DARK_TEXT)
        c.line(width / 2 - 30 * mm, y, width / 2 + 30 * mm, y)
        c.setFont("Helvetica", 7)
        c.drawCentredString(width / 2, y - 4 * mm, "Bursar's Signature")
        
        c.save()
        buffer.seek(0)
        return buffer


# Import A5 constant
from reportlab.lib.pagesizes import A5
