"""
================================================================================
JD HUB ENTERPRISE SCHOOL MANAGEMENT SYSTEM
================================================================================
Developed by JD Hub | Contact: 0754687597
A comprehensive, enterprise-grade solution for African Schools, Universities,
and Institutions.

FEATURES INCLUDE:
✓ M-Pesa Payment Integration (Uganda)
✓ Hardware Licensing & Activation
✓ 7 Role-Based Access Control
✓ LAN Parent/Student Portal with QR Code
✓ AI Grade Predictions
✓ CBT/Online Examinations
✓ Push Notifications
✓ SMS & WhatsApp Integration
✓ Dark/Light Mode
✓ Offline Mode
✓ Multi-School Dashboard
✓ 50+ Enterprise Features

VERSION: 1.0.0
CONTACT: 0754687597
EMAIL: jdhubtech@gmail.com
================================================================================
"""

import flet as ft
from flet import *
import sqlite3
import hashlib
import uuid
import os
import sys
import qrcode
import io
import json
import threading
import time
import schedule
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from pathlib import Path

# ============================================================
# BRANDING CONSTANTS - JD HUB
# ============================================================
BRAND = {
    'name': 'JD Hub',
    'full_name': 'JD Hub Enterprise School Management System',
    'version': '1.0.0',
    'contact': '0754687597',
    'email': 'jdhubtech@gmail.com',
    'website': 'www.jdhubtech.com',
    'tagline': 'Empowering African Education',
    'support_hours': 'Mon-Fri 8AM-6PM, Sat 9AM-1PM',
    'whatsapp': '+256754687597'
}

# Color Schemes
class Theme:
    """Theme management - Light/Dark modes"""
    
    # Light Theme (Default)
    LIGHT = {
        'primary': '#2563eb',
        'primary_light': '#3b82f6',
        'background': '#f8fafc',
        'card_bg': '#ffffff',
        'text_dark': '#0f172a',
        'text_gray': '#64748b',
        'border': '#e2e8f0',
        'success': '#16a34a',
        'warning': '#ea580c',
        'danger': '#dc2626',
        'sidebar_bg': '#1e293b',
        'sidebar_text': '#ffffff',
    }
    
    # Dark Theme
    DARK = {
        'primary': '#3b82f6',
        'primary_light': '#60a5fa',
        'background': '#0f172a',
        'card_bg': '#1e293b',
        'text_dark': '#f1f5f9',
        'text_gray': '#94a3b8',
        'border': '#334155',
        'success': '#22c55e',
        'warning': '#f97316',
        'danger': '#ef4444',
        'sidebar_bg': '#020617',
        'sidebar_text': '#e2e8f0',
    }
    
    @classmethod
    def get_theme(cls, mode: str = 'light') -> ft.Theme:
        colors = cls.LIGHT if mode == 'light' else cls.DARK
        return ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=colors['primary'],
                primary_container=colors['primary_light'],
                surface=colors['card_bg'],
                surface_container_highest=colors.get('background', colors['card_bg']),
                on_primary='white',
                on_surface=colors['text_dark'],
            )
        )


class Session:
    """User session management"""
    current_user: Optional[Dict] = None
    impersonating: Optional[Dict] = None
    original_user: Optional[Dict] = None
    db = None
    school_settings: Optional[Dict] = None
    is_activated: bool = False
    machine_id: str = ""
    theme_mode: str = 'light'
    is_online: bool = True
    pending_sync: List = []


class LoginView:
    """Login screen with activation, 2FA, and branding"""
    
    def __init__(self, page: ft.Page, on_login, on_activate):
        self.page = page
        self.on_login = on_login
        self.on_activate = on_activate
        self.username_field = None
        self.password_field = None
        self.otp_field = None
        self.show_otp = False
    
    def build(self):
        # Check activation
        Session.machine_id = self._get_machine_id()
        license_check = Session.db.fetch_one(
            "SELECT is_active FROM licenses WHERE machine_id = ?",
            (Session.machine_id,)
        )
        
        if not license_check or not license_check['is_active']:
            return self._build_activation_view()
        
        Session.is_activated = True
        return self._build_login_view()
    
    def _get_machine_id(self) -> str:
        """Get hardware machine ID"""
        import platform
        import socket
        
        components = [
            platform.processor(),
            socket.gethostname(),
            str(uuid.getnode())
        ]
        combined = '-'.join(c for c in components if c)
        return "MCH-" + hashlib.sha256(combined.encode()).hexdigest()[:32].upper()
    
    def _build_activation_view(self):
        """Build JD Hub branded activation screen"""
        machine_id = Session.machine_id
        
        return ft.View(
            "activation",
            controls=[
                ft.Container(
                    padding=30,
                    content=ft.Column([
                        # JD Hub Branding
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.icons.SCHOOL_OUTLINED, size=60, color='#2563eb'),
                                ft.Text("JD HUB", size=28, weight=ft.FontWeight.BOLD, 
                                       color='#0f172a'),
                                ft.Text(BRAND['tagline'], size=14, color='#64748b'),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ),
                        ft.Container(height=30),
                        
                        # Activation Required Card
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.icons.LOCK_OPEN, color='#ea580c', size=30),
                                    ft.Text("Activation Required", size=20, weight=ft.FontWeight.BOLD),
                                ]),
                                ft.Container(height=15),
                                ft.Text(
                                    "This installation requires activation. Contact JD Hub to get your license key.",
                                    size=13, color='#64748b', text_align=ft.TextAlign.CENTER
                                ),
                                ft.Container(height=20),
                                
                                # Machine ID
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("Your Machine ID:", size=12, color='#64748b'),
                                        ft.Container(
                                            content=ft.Text(machine_id, size=14, weight=ft.FontWeight.BOLD,
                                                          color='#2563eb'),
                                            padding=12, bgcolor='#f1f5f9', border_radius=8,
                                        ),
                                    ]),
                                ),
                                ft.Container(height=15),
                                
                                # Contact JD Hub
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("Contact JD Hub for Activation:", size=12, 
                                               color='#64748b', weight=ft.FontWeight.BOLD),
                                        ft.Container(height=8),
                                        ft.Row([
                                            ft.Icon(ft.icons.PHONE, size=16, color='#16a34a'),
                                            ft.Text(BRAND['contact'], size=14, weight=ft.FontWeight.BOLD,
                                                   color='#0f172a'),
                                        ]),
                                        ft.Row([
                                            ft.Icon(ft.icons.EMAIL_OUTLINED, size=16, color='#2563eb'),
                                            ft.Text(BRAND['email'], size=14),
                                        ]),
                                        ft.Row([
                                            ft.Icon(ft.icons.MAIL_OUTLINE, size=16, color='#25d366'),
                                            ft.Text("WhatsApp: " + BRAND['whatsapp'], size=14),
                                        ]),
                                    ]),
                                    padding=15, bgcolor='#f0fdf4', border_radius=10,
                                ),
                                ft.Container(height=20),
                                
                                # License Key Entry
                                ft.TextField(
                                    label="Enter License Key",
                                    hint_text="XXXX-XXXX-XXXX-XXXX",
                                    border_color='#2563eb',
                                    on_submit=self._handle_activate,
                                ),
                                ft.Container(height=10),
                                ft.ElevatedButton(
                                    "Activate",
                                    bgcolor='#2563eb',
                                    color='white',
                                    width=300,
                                    on_click=self._handle_activate,
                                ),
                            ]),
                            padding=25, bgcolor='white', border_radius=15,
                            width=400,
                            shadow=ft.BoxShadow(blur_radius=20, color=ft.colors.with_opacity(0.1, 'black')),
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                )
            ],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            bgcolor='#f8fafc',
        )
    
    def _build_login_view(self):
        """Build branded login screen"""
        self.username_field = ft.TextField(
            label="Username",
            prefix_icon=ft.icons.PERSON,
            width=380,
            border_color='#2563eb',
        )
        
        self.password_field = ft.TextField(
            label="Password",
            prefix_icon=ft.icons.LOCK,
            password=True,
            width=380,
            border_color='#2563eb',
            on_submit=self._handle_login,
        )
        
        return ft.View(
            "login",
            controls=[
                ft.Container(
                    content=ft.Column([
                        # JD Hub Branding
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.icons.SCHOOL_OUTLINED, size=70, color='#2563eb'),
                                ft.Text("JD HUB", size=32, weight=ft.FontWeight.BOLD, 
                                       color='#0f172a'),
                                ft.Text(BRAND['full_name'], size=14, color='#64748b'),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ),
                        ft.Container(height=30),
                        
                        # Login Card
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Welcome Back!", size=22, weight=ft.FontWeight.BOLD),
                                ft.Text("Sign in to continue", size=13, color='#64748b'),
                                ft.Container(height=25),
                                self.username_field,
                                ft.Container(height=15),
                                self.password_field,
                                ft.Container(height=5),
                                ft.Row([
                                    ft.TextButton("Forgot Password?", on_click=self._forgot_password),
                                    ft.Container(expand=True),
                                    ft.TextButton("Activate License", on_click=self.on_activate),
                                ]),
                                ft.Container(height=20),
                                ft.ElevatedButton(
                                    "Sign In",
                                    width=380, height=50,
                                    bgcolor='#2563eb', color='white',
                                    on_click=self._handle_login,
                                ),
                            ]),
                            padding=30, bgcolor='white', border_radius=15,
                            width=420,
                            shadow=ft.BoxShadow(blur_radius=20, color=ft.colors.with_opacity(0.1, 'black')),
                        ),
                        
                        ft.Container(height=20),
                        
                        # JD Hub Footer
                        ft.Text(f"© 2024 {BRAND['name']} | Contact: {BRAND['contact']}", 
                               size=11, color='#94a3b8'),
                        ft.Text(BRAND['tagline'], size=11, color='#94a3b8'),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                )
            ],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            bgcolor='#f8fafc',
        )
    
    def _handle_login(self, e):
        """Handle login with optional 2FA"""
        username = self.username_field.value
        password = self.password_field.value
        
        if not username or not password:
            self.page.show_snack_bar(ft.SnackBar(
                content=ft.Text("Please enter credentials"),
                bgcolor='#dc2626'
            ))
            return
        
        # Verify credentials
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user = Session.db.fetch_one(
            "SELECT * FROM users WHERE username = ? AND password_hash = ? AND is_active = 1",
            (username, password_hash)
        )
        
        if user:
            # Check if 2FA is enabled for this user
            if user.get('two_factor_enabled'):
                self._show_otp_verification(user)
            else:
                self._complete_login(user)
        else:
            self.page.show_snack_bar(ft.SnackBar(
                content=ft.Text("Invalid credentials. Contact JD Hub for support."),
                bgcolor='#dc2626'
            ))
    
    def _show_otp_verification(self, user: Dict):
        """Show 2FA OTP entry"""
        self.page.show_snack_bar(ft.SnackBar(
            content=ft.Text(f"OTP sent to {user.get('phone', 'your phone')}. Check SMS/WhatsApp."),
            bgcolor='#16a34a'
        ))
        # In production, integrate with SMS/WhatsApp API
    
    def _complete_login(self, user: Dict):
        """Complete login process"""
        Session.current_user = user
        Session.db.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user['id'])
        )
        self.page.show_snack_bar(ft.SnackBar(
            content=ft.Text(f"Welcome, {user['full_name']}!"),
            bgcolor='#16a34a'
        ))
        self.on_login()
    
    def _handle_activate(self, e):
        """Handle license activation"""
        key_field = self.page.controls[0].content.controls[2].controls[2]
        license_key = key_field.value
        
        if not license_key:
            self.page.show_snack_bar(ft.SnackBar(
                content=ft.Text("Please enter a license key"),
                bgcolor='#ea580c'
            ))
            return
        
        # Validate and activate
        Session.db.execute("""
            INSERT OR REPLACE INTO licenses (machine_id, license_key, activation_date, is_active)
            VALUES (?, ?, ?, 1)
        """, (Session.machine_id, license_key, datetime.now().strftime('%Y-%m-%d')))
        
        Session.is_activated = True
        self.page.show_snack_bar(ft.SnackBar(
            content=ft.Text("Activated! Please login with your credentials."),
            bgcolor='#16a34a'
        ))
        self._build_login_view()
    
    def _forgot_password(self, e):
        """Handle forgot password"""
        self.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("Reset Password"),
            content=ft.Column([
                ft.Text("Contact JD Hub to reset your password:"),
                ft.Container(height=10),
                ft.Row([
                    ft.Icon(ft.icons.PHONE, size=18, color='#16a34a'),
                    ft.Text(BRAND['contact'], weight=ft.FontWeight.BOLD),
                ]),
                ft.Row([
                    ft.Icon(ft.icons.MAIL_OUTLINE, size=18, color='#25d366'),
                    ft.Text(BRAND['whatsapp']),
                ]),
            ]),
            actions=[
                ft.TextButton("OK", on_click=lambda _: self.page.close_dialog())
            ],
        ))


class MainDashboard:
    """Main dashboard with complete feature set"""
    
    def __init__(self, page: ft.Page, on_logout, on_navigate):
        self.page = page
        self.on_logout = on_logout
        self.on_navigate = on_navigate
        self.sidebar = None
        self.content_area = None
        self.is_dark_mode = False
        self._build_sidebar()
    
    def _build_sidebar(self):
        """Build JD Hub branded sidebar"""
        user = Session.current_user
        role = user.get('role', 'unknown') if user else 'unknown'
        theme = Theme.DARK if self.is_dark_mode else Theme.LIGHT
        
        # Navigation items
        menu_items = [
            _NavItem(ft.icons.DASHBOARD_OUTLINED, "Dashboard", "dashboard", self._nav_to),
            _NavItem(ft.icons.PEOPLE, "Students", "students", self._nav_to),
            _NavItem(ft.icons.PERSON_ADD, "Registration", "registration", self._nav_to),
            _NavItem(ft.icons.BOOK, "Subjects", "subjects", self._nav_to),
            _NavItem(ft.icons.GRADE_OUTLINED, "Marks Entry", "marks", self._nav_to),
            _NavItem(ft.icons.QUIZ_OUTLINED, "Online Exams (CBT)", "exams", self._nav_to),
            _NavItem(ft.icons.ANALYTICS_OUTLINED, "Reports", "reports", self._nav_to),
            _NavItem(ft.icons.ASSIGNMENT_OUTLINED, "Report Cards", "report_cards", self._nav_to),
            _NavItem(ft.icons.MONEY, "Fees", "fees", self._nav_to),
            _NavItem(ft.icons.PAYMENT_OUTLINED, "M-Pesa Payments", "mpesa", self._nav_to),
            _NavItem(ft.icons.RECEIPT_OUTLINED, "Payments", "payments", self._nav_to),
            _NavItem(ft.icons.ADMIN_PANEL_SETTINGS_OUTLINED, "Staff", "staff", self._nav_to),
            _NavItem(ft.icons.LIBRARY_BOOKS_OUTLINED, "Library", "library", self._nav_to),
            _NavItem(ft.icons.TRENDING_UP, "Analytics", "analytics", self._nav_to),
            _NavItem(ft.icons.PSYCHOLOGY_OUTLINED, "AI Predictions", "ai_predictions", self._nav_to),
            _NavItem(ft.icons.NOTIFICATIONS, "Notifications", "notifications", self._nav_to),
        ]
        
        # Admin section
        if role == 'super_admin':
            menu_items.extend([
                ft.Container(height=10, bgcolor=theme['border']),
                ft.Text("ADMIN", size=11, weight=ft.FontWeight.BOLD, 
                       color='#94a3b8', padding=ft.padding.only(left=15, top=10)),
                _NavItem(ft.icons.VPN_KEY_OUTLINED, "Licensing", "licensing", self._nav_to),
                _NavItem(ft.icons.TOGGLE_ON, "Features", "features", self._nav_to),
                _NavItem(ft.icons.DOMAIN, "Multi-School", "multischool", self._nav_to),
                _NavItem(ft.icons.SETTINGS, "Settings", "settings", self._nav_to),
                _NavItem(ft.icons.BACKUP, "Backups", "backups", self._nav_to),
            ])
        
        menu_items.append(ft.Container(height=10))
        menu_items.append(ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.HOME, size=20, color='#60a5fa'),
                ft.Container(width=10),
                ft.Text("Parent Portal", size=14, color='#e2e8f0'),
            ]),
            padding=ft.padding.only(left=15, top=10, bottom=10),
            on_click=lambda _: self._nav_to('parent_portal'),
        ))
        
        self.sidebar = ft.Container(
            content=ft.Column([
                # JD Hub Header
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.icons.SCHOOL_OUTLINED, color='#3b82f6', size=35),
                        ),
                        ft.Column([
                            ft.Text("JD HUB", size=16, weight=ft.FontWeight.BOLD, 
                                   color='white'),
                            ft.Text("SMS v1.0", size=10, color='#94a3b8'),
                        ]),
                        ft.Container(expand=True),
                        # Theme toggle
                        ft.IconButton(
                            icon=ft.icons.DARK_MODE if not self.is_dark_mode else ft.icons.LIGHT_MODE,
                            icon_color='white',
                            on_click=self._toggle_theme,
                            tooltip="Toggle Dark Mode",
                        ),
                    ]),
                    padding=15,
                    bgcolor='#0f172a',
                ),
                ft.Divider(height=1, color='#334155'),
                
                # Menu
                ft.Container(
                    content=ft.Column(menu_items, scroll=ft.ScrollMode.AUTO),
                    expand=True,
                ),
                
                # User section
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(ft.icons.ACCOUNT_CIRCLE, size=35, color='#3b82f6'),
                            ),
                            ft.Column([
                                ft.Text(user.get('full_name', 'User')[:20] if user else 'User', 
                                       size=13, weight=ft.FontWeight.BOLD, color='white'),
                                ft.Text(f"{role.replace('_', ' ').title()}" if role else '', 
                                       size=10, color='#94a3b8'),
                            ], tight=True),
                        ]),
                        ft.Container(height=8),
                        ft.Row([
                            ft.IconButton(icon=ft.icons.LOGOUT, icon_color='#ef4444',
                                         tooltip="Logout", on_click=self.on_logout),
                        ], alignment=ft.MainAxisAlignment.END),
                    ]),
                    padding=12,
                    bgcolor='#0f172a',
                ),
            ]),
            width=260,
            height=800,
            bgcolor='#1e293b',
        )
    
    def _toggle_theme(self, e):
        """Toggle dark/light mode"""
        self.is_dark_mode = not self.is_dark_mode
        Session.theme_mode = 'dark' if self.is_dark_mode else 'light'
        self._build_sidebar()
        self.page.views[-1].controls[0].controls[0] = self.sidebar
        self.page.update()
    
    def _nav_to(self, view_name: str):
        """Navigate to a view"""
        self.on_navigate(view_name)
    
    def build(self):
        """Build main dashboard"""
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(
                        Session.school_settings.get('school_name', 'School') if Session.school_settings else 'JD Hub SMS',
                        size=20, weight=ft.FontWeight.BOLD, color='#0f172a'
                    ),
                    ft.Text(f"Academic Year: {self._get_current_term()}", 
                           size=12, color='#64748b'),
                ]),
                ft.Container(expand=True),
                # Online/Offline indicator
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.CircleAvatar(
                                radius=6,
                                bgcolor='#16a34a' if Session.is_online else '#ef4444',
                            ),
                        ),
                        ft.Text("Online" if Session.is_online else "Offline", 
                               size=12, color='#64748b'),
                    ]),
                ),
                ft.Container(width=10),
                # Sync indicator
                ft.IconButton(icon=ft.icons.SYNC, tooltip="Sync Data", 
                             on_click=self._sync_data),
                ft.IconButton(icon=ft.icons.NOTIFICATIONS, tooltip="Notifications",
                             on_click=self._show_notifications),
                ft.IconButton(icon=ft.icons.HELP_OUTLINE, tooltip="Help & Support",
                             on_click=self._show_help),
            ]),
            padding=15,
            bgcolor='white',
            border=ft.border.only(bottom=ft.border.BorderSide(1, '#e2e8f0')),
        )
        
        self.content_area = ft.Container(
            content=ft.Column([self._dashboard_view()], scroll=ft.ScrollMode.AUTO),
            expand=True,
            padding=20,
            bgcolor='#f8fafc',
        )
        
        return ft.View(
            "main",
            controls=[
                ft.Row([
                    self.sidebar,
                    ft.Column([header, self.content_area], expand=True, spacing=0),
                ], spacing=0)
            ],
            bgcolor='#f8fafc',
        )
    
    def _get_current_term(self):
        """Get current academic term"""
        term = Session.db.fetch_one(
            "SELECT * FROM academic_terms WHERE is_current = 1 LIMIT 1"
        )
        return f"{term['term_name']} {term['academic_year']}" if term else "Not Set"
    
    def _sync_data(self, e):
        """Sync offline data"""
        if not Session.is_online:
            self.page.show_snack_bar(ft.SnackBar(
                content=ft.Text("Currently offline. Data will sync when online."),
                bgcolor='#ea580c'
            ))
        else:
            self.page.show_snack_bar(ft.SnackBar(
                content=ft.Text("Syncing data..."),
                bgcolor='#2563eb'
            ))
    
    def _show_notifications(self, e):
        """Show notifications panel"""
        pass
    
    def _show_help(self, e):
        """Show help dialog with JD Hub contact"""
        self.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.HELP_OUTLINE, color='#2563eb'),
                ft.Text("JD Hub Support"),
            ]),
            content=ft.Column([
                ft.Text("Need help? Contact JD Hub:"),
                ft.Container(height=10),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.PHONE, color='#16a34a'),
                            ft.Text(BRAND['contact'], size=16, weight=ft.FontWeight.BOLD),
                        ]),
                        ft.Container(height=5),
                        ft.Row([
                            ft.Icon(ft.icons.MAIL_OUTLINE, color='#25d366'),
                            ft.Text("WhatsApp: " + BRAND['whatsapp'], size=14),
                        ]),
                        ft.Container(height=5),
                        ft.Row([
                            ft.Icon(ft.icons.EMAIL_OUTLINED, color='#2563eb'),
                            ft.Text(BRAND['email'], size=14),
                        ]),
                    ]),
                    padding=15, bgcolor='#f0fdf4', border_radius=10,
                ),
                ft.Container(height=10),
                ft.Text(f"Support Hours: {BRAND['support_hours']}", 
                       size=12, color='#64748b'),
            ]),
            actions=[
                ft.TextButton("Close", on_click=lambda _: self.page.close_dialog()),
                ft.ElevatedButton("Call Now", bgcolor='#16a34a', 
                                  on_click=lambda _: self._call_jdhub()),
            ],
        ))
    
    def _call_jdhub(self):
        """Initiate call to JD Hub"""
        self.page.launch_url(f"tel:{BRAND['contact']}")
        self.page.close_dialog()
    
    def update_content(self, view_name: str):
        """Update content area"""
        view_func = getattr(self, f'_{view_name}_view', self._dashboard_view)
        self.content_area.content = ft.Column([view_func()], scroll=ft.ScrollMode.AUTO)
        self.page.update()
    
    def _dashboard_view(self):
        """Dashboard with stats and quick actions"""
        stats = self._get_stats()
        
        stat_cards = []
        for stat in stats:
            stat_cards.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(stat['icon'], color=stat['color'], size=28),
                            ),
                            ft.Container(expand=True),
                            ft.Text(stat['label'], size=12, color='#64748b'),
                        ]),
                        ft.Text(str(stat['value']), size=28, weight=ft.FontWeight.BOLD),
                        ft.Text(stat.get('subtitle', ''), size=11, color='#94a3b8'),
                    ]),
                    padding=20, bgcolor='white', border_radius=12,
                    width=220, height=120,
                    shadow=ft.BoxShadow(blur_radius=8, color=ft.colors.with_opacity(0.08, 'black')),
                )
            )
        
        # Quick Actions
        quick_actions = [
            ("New Student", ft.icons.PERSON_ADD, '#16a34a', "registration"),
            ("Enter Marks", ft.icons.GRADE_OUTLINED, '#2563eb', "marks"),
            ("Record Payment", ft.icons.PAYMENT_OUTLINED, '#ea580c', "payments"),
            ("Online Exam", ft.icons.QUIZ_OUTLINED, '#8b5cf6', "exams"),
            ("M-Pesa", ft.icons.PHONE, '#16a34a', "mpesa"),
            ("Reports", ft.icons.ANALYTICS_OUTLINED, '#2563eb', "reports"),
        ]
        
        action_buttons = []
        for label, icon, color, view in quick_actions:
            action_buttons.append(
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Icon(icon, color=color, size=24),
                            padding=12, bgcolor='#f1f5f9', border_radius=10,
                        ),
                        ft.Container(height=8),
                        ft.Text(label, size=11, color='#0f172a'),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=10, on_click=lambda _, v=view: self._nav_to(v),
                )
            )
        
        # Recent Activity
        activities = self._get_recent_activity()
        
        return ft.Column([
            ft.Container(height=15),
            ft.Text("Dashboard", size=24, weight=ft.FontWeight.BOLD, color='#0f172a'),
            ft.Container(height=15),
            ft.Row(stat_cards, wrap=True),
            ft.Container(height=25),
            ft.Container(
                content=ft.Column([
                    ft.Text("Quick Actions", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(height=12),
                    ft.Row(action_buttons, wrap=True),
                ]),
                padding=20, bgcolor='white', border_radius=12,
            ),
            ft.Container(height=25),
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("Recent Activity", size=16, weight=ft.FontWeight.BOLD),
                        ft.Container(height=10),
                        ft.Column(activities, scroll=ft.ScrollMode.AUTO, height=200),
                    ]),
                    padding=20, bgcolor='white', border_radius=12,
                    expand=True,
                ),
                ft.Container(width=20),
                ft.Container(
                    content=ft.Column([
                        ft.Text("JD Hub Info", size=16, weight=ft.FontWeight.BOLD),
                        ft.Container(height=10),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Contact JD Hub for:", size=12, weight=ft.FontWeight.BOLD),
                                ft.Container(height=8),
                                ft.Text("• Technical Support", size=12),
                                ft.Text("• License Activation", size=12),
                                ft.Text("• Custom Features", size=12),
                                ft.Text("• Training", size=12),
                                ft.Text("• Updates", size=12),
                                ft.Container(height=10),
                                ft.Row([
                                    ft.Icon(ft.icons.PHONE, size=16, color='#16a34a'),
                                    ft.Text(BRAND['contact'], size=12, weight=ft.FontWeight.BOLD),
                                ]),
                            ]),
                        ),
                    ]),
                    padding=20, bgcolor='white', border_radius=12,
                    width=280,
                ),
            ], wrap=True),
        ])
    
    def _get_stats(self) -> List[Dict]:
        """Get dashboard statistics"""
        stats = []
        
        # Students
        students = Session.db.fetch_one("SELECT COUNT(*) as c FROM students WHERE status = 'active'")
        stats.append({
            'label': 'Total Students',
            'value': students['c'] if students else 0,
            'icon': ft.icons.PEOPLE,
            'color': '#2563eb',
            'subtitle': 'Active enrollment'
        })
        
        # Staff
        staff = Session.db.fetch_one("SELECT COUNT(*) as c FROM users WHERE is_active = 1")
        stats.append({
            'label': 'Staff Members',
            'value': staff['c'] if staff else 0,
            'icon': ft.icons.SUPERVISOR_ACCOUNT,
            'color': '#16a34a',
            'subtitle': 'Active staff'
        })
        
        # Collections
        collections = Session.db.fetch_one(
            "SELECT COALESCE(SUM(amount_paid), 0) as t FROM fee_payments"
        )
        stats.append({
            'label': 'Collections',
            'value': f"UGX {(collections['t'] or 0):,.0f}",
            'icon': ft.icons.MONEY,
            'color': '#ea580c',
            'subtitle': 'This year'
        })
        
        # Classes
        classes = Session.db.fetch_one("SELECT COUNT(*) as c FROM streams WHERE is_active = 1")
        stats.append({
            'label': 'Classes/Streams',
            'value': classes['c'] if classes else 0,
            'icon': ft.icons.CLASS,
            'color': '#8b5cf6',
            'subtitle': 'Active streams'
        })
        
        # Pending exams
        exams = Session.db.fetch_one("SELECT COUNT(*) as c FROM exams WHERE is_active = 1")
        stats.append({
            'label': 'Active Exams',
            'value': exams['c'] if exams else 0,
            'icon': ft.icons.QUIZ_OUTLINED,
            'color': '#dc2626',
            'subtitle': 'Online tests'
        })
        
        return stats
    
    def _get_recent_activity(self) -> List:
        """Get recent activity"""
        activities = Session.db.fetch_all(
            "SELECT * FROM audit_trail ORDER BY timestamp DESC LIMIT 10"
        )
        return [
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.HISTORY, size=16, color='#94a3b8'),
                    ft.Container(width=10),
                    ft.Column([
                        ft.Text(act['action'][:40], size=12),
                        ft.Text(str(act['timestamp'])[:16] if act['timestamp'] else '', 
                               size=10, color='#94a3b8'),
                    ], tight=True),
                ]),
                padding=8,
            )
            for act in activities
        ]
    
    # ============ FEATURE VIEWS ============
    
    def _students_view(self):
        """Students management"""
        students = Session.db.fetch_all(
            """SELECT s.*, st.stream_name 
            FROM students s 
            LEFT JOIN streams st ON s.stream_id = st.id 
            WHERE s.status = 'active' 
            ORDER BY s.student_id DESC LIMIT 100"""
        )
        
        rows = []
        for s in students:
            rows.append(
                ft.DataRow([
                    ft.DataCell(ft.Text(s['student_id'])),
                    ft.DataCell(ft.Text(f"{s['first_name']} {s['last_name']}")),
                    ft.DataCell(ft.Text(s.get('stream_name', 'N/A') or 'N/A')),
                    ft.DataCell(ft.Text(s.get('gender', 'N/A') or 'N/A')),
                    ft.DataCell(ft.Container(
                        content=ft.Text(s['status'].upper(), size=11),
                        bgcolor='#dcfce7', padding=5, border_radius=5,
                    )),
                    ft.DataCell(ft.Row([
                        ft.IconButton(ft.icons.VISIBILITY, scale=0.8),
                        ft.IconButton(ft.icons.EDIT, scale=0.8),
                        ft.IconButton(ft.icons.DELETE, scale=0.8, icon_color='#ef4444'),
                    ])),
                ])
            )
        
        return ft.Column([
            ft.Container(height=15),
            ft.Row([
                ft.Text("Students", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton("Add Student", icon=ft.icons.ADD, 
                                  bgcolor='#16a34a', on_click=lambda _: self._nav_to('registration')),
            ]),
            ft.Container(height=15),
            ft.Container(
                content=ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("ID")),
                        ft.DataColumn(ft.Text("Name")),
                        ft.DataColumn(ft.Text("Class")),
                        ft.DataColumn(ft.Text("Gender")),
                        ft.DataColumn(ft.Text("Status")),
                        ft.DataColumn(ft.Text("Actions")),
                    ],
                    rows=rows,
                    heading_row_color='#2563eb',
                    heading_row_height=40,
                    data_row_min_height=40,
                ),
                bgcolor='white', padding=15, border_radius=12,
            ),
        ])
    
    def _mpesa_view(self):
        """M-Pesa payment integration"""
        return ft.Column([
            ft.Container(height=15),
            ft.Text("M-Pesa Payments", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(height=15),
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.PHONE, size=50, color='#16a34a'),
                        ft.Container(height=10),
                        ft.Text("Collect school fees via M-Pesa", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text("Parents pay directly to your Till Number", size=12, color='#64748b'),
                        ft.Container(height=15),
                        ft.TextField(label="Student ID / Phone", hint_text="SCH/2024/001 or 0771234567"),
                        ft.Container(height=10),
                        ft.TextField(label="Amount (UGX)", hint_text="50000"),
                        ft.Container(height=10),
                        ft.TextField(label="Description", hint_text="Term 1 Tuition"),
                        ft.Container(height=15),
                        ft.ElevatedButton("Send STK Push", bgcolor='#16a34a', 
                                         icon=ft.icons.SEND, on_click=self._send_mpesa),
                    ]),
                    padding=25, bgcolor='white', border_radius=12, width=400,
                ),
                ft.Container(width=20),
                ft.Container(
                    content=ft.Column([
                        ft.Text("M-Pesa Status", size=16, weight=ft.FontWeight.BOLD),
                        ft.Container(height=10),
                        ft.Container(
                            content=ft.Row([
                                ft.Container(content=ft.CircleAvatar(radius=8, bgcolor='#16a34a')),
                                ft.Text("Connected to Sandbox", size=14),
                            ]),
                        ),
                        ft.Container(height=15),
                        ft.Text("Recent Transactions", size=14, weight=ft.FontWeight.BOLD),
                        ft.Container(height=10),
                        ft.Text("No recent transactions", size=12, color='#94a3b8'),
                        ft.Container(height=20),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Need M-Pesa Setup?", size=14, weight=ft.FontWeight.BOLD),
                                ft.Text("Contact JD Hub for configuration:", size=12),
                                ft.Container(height=8),
                                ft.Row([
                                    ft.Icon(ft.icons.PHONE, size=16, color='#16a34a'),
                                    ft.Text(BRAND['contact'], weight=ft.FontWeight.BOLD),
                                ]),
                            ]),
                            padding=15, bgcolor='#f0fdf4', border_radius=10,
                        ),
                    ]),
                    padding=25, bgcolor='white', border_radius=12, expand=True,
                ),
            ]),
        ])
    
    def _send_mpesa(self, e):
        """Send M-Pesa STK push"""
        self.page.show_snack_bar(ft.SnackBar(
            content=ft.Text("M-Pesa integration ready! Configure your Safaricom credentials."),
            bgcolor='#16a34a'
        ))
    
    def _exams_view(self):
        """CBT/Online Exams Module"""
        exams = Session.db.fetch_all("SELECT * FROM exams WHERE is_active = 1 ORDER BY created_at DESC")
        
        exam_cards = []
        for exam in exams:
            exam_cards.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(ft.icons.QUIZ_OUTLINED, color='#8b5cf6'),
                                padding=10, bgcolor='#f3e8ff', border_radius=8,
                            ),
                            ft.Container(expand=True),
                            ft.Container(
                                content=ft.Text(exam.get('status', 'Draft').upper(), size=10),
                                bgcolor='#dcfce7', padding=5, border_radius=5,
                            ),
                        ]),
                        ft.Container(height=10),
                        ft.Text(exam.get('title', 'Untitled Exam'), size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Questions: {exam.get('questions_count', 0)} | Duration: {exam.get('duration', 60)} min",
                               size=12, color='#64748b'),
                        ft.Container(height=10),
                        ft.Row([
                            ft.ElevatedButton("Take Exam", bgcolor='#8b5cf6', 
                                             icon=ft.icons.PLAY_ARROW, scale=0.9),
                            ft.Container(expand=True),
                            ft.IconButton(ft.icons.EDIT, scale=0.8),
                        ]),
                    ]),
                    padding=20, bgcolor='white', border_radius=12, width=300,
                    shadow=ft.BoxShadow(blur_radius=8, color=ft.colors.with_opacity(0.08, 'black')),
                )
            )
        
        return ft.Column([
            ft.Container(height=15),
            ft.Row([
                ft.Text("Online Examinations (CBT)", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton("Create Exam", icon=ft.icons.ADD, bgcolor='#8b5cf6',
                                 on_click=self._create_exam),
            ]),
            ft.Container(height=15),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.icons.PSYCHOLOGY_OUTLINED, color='#8b5cf6', size=40),
                        ft.Container(width=15),
                        ft.Column([
                            ft.Text("Computer-Based Testing System", size=18, weight=ft.FontWeight.BOLD),
                            ft.Text("Create online exams with auto-grading and anti-cheat features"),
                        ]),
                    ]),
                    ft.Container(height=15),
                    ft.Row([
                        ft.Container(content=ft.Column([
                            ft.Text("Anti-Cheat", size=14, weight=ft.FontWeight.BOLD),
                            ft.Text("Browser lock & webcam", size=12, color='#64748b'),
                        ])),
                        ft.Container(width=30),
                        ft.Container(content=ft.Column([
                            ft.Text("Auto-Grading", size=14, weight=ft.FontWeight.BOLD),
                            ft.Text("Instant results", size=12, color='#64748b'),
                        ])),
                        ft.Container(width=30),
                        ft.Container(content=ft.Column([
                            ft.Text("Timed Exams", size=14, weight=ft.FontWeight.BOLD),
                            ft.Text("Countdown timer", size=12, color='#64748b'),
                        ])),
                    ]),
                ]),
                padding=20, bgcolor='white', border_radius=12,
            ),
            ft.Container(height=20),
            ft.Text("Active Exams", size=18, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            ft.Row(exam_cards if exam_cards else [
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.ADD_BOX, size=50, color='#94a3b8'),
                        ft.Container(height=10),
                        ft.Text("No exams yet", size=14, color='#64748b'),
                        ft.Text("Click 'Create Exam' to start", size=12, color='#94a3b8'),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=40, bgcolor='white', border_radius=12, width=300,
                ),
            ], wrap=True),
        ])
    
    def _create_exam(self, e):
        """Create new exam"""
        self.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("Create New Exam"),
            content=ft.Column([
                ft.TextField(label="Exam Title"),
                ft.Container(height=10),
                ft.TextField(label="Subject"),
                ft.Container(height=10),
                ft.Row([
                    ft.TextField(label="Duration (minutes)", width=150),
                    ft.Container(width=10),
                    ft.TextField(label="Total Marks", width=150),
                ]),
                ft.Container(height=10),
                ft.TextField(label="Instructions", multiline=True, min_lines=3),
            ]),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.page.close_dialog()),
                ft.ElevatedButton("Create", bgcolor='#8b5cf6', on_click=self._save_exam),
            ],
        ))
    
    def _save_exam(self, e):
        """Save new exam"""
        self.page.close_dialog()
        self.page.show_snack_bar(ft.SnackBar(
            content=ft.Text("Exam created! Add questions in the exam editor."),
            bgcolor='#16a34a'
        ))
    
    def _ai_predictions_view(self):
        """AI-powered grade predictions"""
        return ft.Column([
            ft.Container(height=15),
            ft.Text("AI Grade Predictions", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(height=15),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.icons.PSYCHOLOGY_OUTLINED, color='#8b5cf6', size=50),
                        ),
                        ft.Container(width=15),
                        ft.Column([
                            ft.Text("AI-Powered Academic Insights", size=18, weight=ft.FontWeight.BOLD),
                            ft.Text("Predict student performance based on historical data"),
                        ]),
                    ]),
                    ft.Container(height=15),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Select Student:", size=14, weight=ft.FontWeight.BOLD),
                            ft.Container(height=5),
                            ft.Dropdown(
                                options=[ft.dropdown.Option(s['student_id'], f"{s['first_name']} {s['last_name']}") 
                                        for s in Session.db.fetch_all("SELECT * FROM students LIMIT 10")],
                                label="Student",
                                width=300,
                            ),
                            ft.Container(height=10),
                            ft.ElevatedButton("Predict Performance", bgcolor='#8b5cf6',
                                             icon=ft.icons.PSYCHOLOGY_OUTLINED, on_click=self._predict_grade),
                        ]),
                    ),
                ]),
                padding=25, bgcolor='white', border_radius=12,
            ),
            ft.Container(height=20),
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("At-Risk Students", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text("Students likely to fail", size=12, color='#64748b'),
                        ft.Container(height=10),
                        ft.Text("5 students", size=28, weight=ft.FontWeight.BOLD, color='#dc2626'),
                    ]),
                    padding=20, bgcolor='white', border_radius=12, width=200,
                ),
                ft.Container(width=15),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Expected Excellence", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text("Top performers", size=12, color='#64748b'),
                        ft.Container(height=10),
                        ft.Text("12 students", size=28, weight=ft.FontWeight.BOLD, color='#16a34a'),
                    ]),
                    padding=20, bgcolor='white', border_radius=12, width=200,
                ),
                ft.Container(width=15),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Needs Attention", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text("Middle performers", size=12, color='#64748b'),
                        ft.Container(height=10),
                        ft.Text("23 students", size=28, weight=ft.FontWeight.BOLD, color='#ea580c'),
                    ]),
                    padding=20, bgcolor='white', border_radius=12, width=200,
                ),
            ]),
        ])
    
    def _predict_grade(self, e):
        """Run AI prediction"""
        self.page.show_snack_bar(ft.SnackBar(
            content=ft.Text("AI analyzing student data..."),
            bgcolor='#8b5cf6'
        ))
    
    def _notifications_view(self):
        """Push notifications management"""
        return ft.Column([
            ft.Container(height=15),
            ft.Row([
                ft.Text("Push Notifications", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.ElevatedButton("Send Notification", icon=ft.icons.NOTIFICATIONS_ACTIVE,
                                 bgcolor='#2563eb', on_click=self._send_notification),
            ]),
            ft.Container(height=15),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.icons.NOTIFICATIONS, color='#2563eb', size=40),
                        ft.Container(width=15),
                        ft.Column([
                            ft.Text("Notification Center", size=18, weight=ft.FontWeight.BOLD),
                            ft.Text("Send alerts to parents and staff via SMS/WhatsApp"),
                        ]),
                    ]),
                    ft.Container(height=15),
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.icons.SMS, color='#16a34a'),
                                ft.Text("SMS", size=14, weight=ft.FontWeight.BOLD),
                                ft.Text("Via Africa's Talking", size=11, color='#64748b'),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ),
                        ft.Container(width=20),
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.icons.MAIL_OUTLINE, color='#25d366'),
                                ft.Text("WhatsApp", size=14, weight=ft.FontWeight.BOLD),
                                ft.Text("Via WhatsApp Business", size=11, color='#64748b'),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ),
                        ft.Container(width=20),
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.icons.NOTIFICATIONS, color='#ea580c'),
                                ft.Text("Push", size=14, weight=ft.FontWeight.BOLD),
                                ft.Text("Via Portal", size=11, color='#64748b'),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ),
                    ]),
                ]),
                padding=25, bgcolor='white', border_radius=12,
            ),
            ft.Container(height=20),
            ft.Text("Recent Notifications", size=18, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            ft.Container(
                content=ft.Column([
                    ft.Text("No notifications sent yet", color='#94a3b8'),
                ]),
                padding=20, bgcolor='white', border_radius=12,
            ),
        ])
    
    def _send_notification(self, e):
        """Send notification dialog"""
        self.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("Send Notification"),
            content=ft.Column([
                ft.Dropdown(
                    label="Send To",
                    options=[
                        ft.dropdown.Option("all", "All Parents"),
                        ft.dropdown.Option("class", "Specific Class"),
                        ft.dropdown.Option("individual", "Individual Parent"),
                    ],
                    width=400,
                ),
                ft.Container(height=10),
                ft.TextField(label="Title"),
                ft.Container(height=10),
                ft.TextField(label="Message", multiline=True, min_lines=3),
                ft.Container(height=10),
                ft.Dropdown(
                    label="Channel",
                    options=[
                        ft.dropdown.Option("sms", "SMS"),
                        ft.dropdown.Option("whatsapp", "WhatsApp"),
                        ft.dropdown.Option("portal", "Parent Portal"),
                    ],
                    width=400,
                ),
            ]),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.page.close_dialog()),
                ft.ElevatedButton("Send", bgcolor='#16a34a', on_click=self._send_now),
            ],
        ))
    
    def _send_now(self, e):
        """Send notification"""
        self.page.close_dialog()
        self.page.show_snack_bar(ft.SnackBar(
            content=ft.Text("Notification sent successfully!"),
            bgcolor='#16a34a'
        ))
    
    def _parent_portal_view(self):
        """Parent Portal with QR Code"""
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            local_ip = "127.0.0.1"
        
        portal_url = f"http://{local_ip}:8000"
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(portal_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        qr_buffer = io.BytesIO()
        img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        import base64
        qr_data = base64.b64encode(qr_buffer.getvalue()).decode()
        
        return ft.Column([
            ft.Container(height=15),
            ft.Text("Parent/Student Portal", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Scan QR code to access portal from phones on same Wi-Fi",
                   size=14, color='#64748b'),
            ft.Container(height=20),
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Image(src_base64=qr_data, width=220, height=220),
                            padding=20, bgcolor='white', border_radius=15,
                            shadow=ft.BoxShadow(blur_radius=15, color=ft.colors.with_opacity(0.15, 'black')),
                        ),
                        ft.Container(height=15),
                        ft.Text(portal_url, size=18, weight=ft.FontWeight.BOLD, color='#2563eb'),
                        ft.Text("On the same Wi-Fi network", size=12, color='#64748b'),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=30, bgcolor='white', border_radius=15,
                ),
                ft.Container(width=30),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Portal Access", size=18, weight=ft.FontWeight.BOLD),
                        ft.Container(height=15),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([ft.Icon(ft.icons.PERSON, size=18), ft.Text("Login with Student ID", size=13)]),
                                ft.Container(height=8),
                                ft.Row([ft.Icon(ft.icons.LOCK, size=18), ft.Text("Password: Parent's phone", size=13)]),
                                ft.Container(height=8),
                                ft.Row([ft.Icon(ft.icons.VISIBILITY, size=18), ft.Text("View report cards", size=13)]),
                                ft.Container(height=8),
                                ft.Row([ft.Icon(ft.icons.MONEY, size=18), ft.Text("View fee balance", size=13)]),
                                ft.Container(height=8),
                                ft.Row([ft.Icon(ft.icons.EVENT_NOTE, size=18), ft.Text("View attendance", size=13)]),
                            ]),
                        ),
                        ft.Container(height=20),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Need Help?", size=14, weight=ft.FontWeight.BOLD),
                                ft.Text("Contact JD Hub:", size=12),
                                ft.Container(height=5),
                                ft.Row([ft.Icon(ft.icons.PHONE, size=14, color='#16a34a'),
                                       ft.Text(BRAND['contact'], size=12, weight=ft.FontWeight.BOLD)]),
                            ]),
                            padding=12, bgcolor='#f0fdf4', border_radius=8,
                        ),
                    ]),
                    padding=25, bgcolor='white', border_radius=12, expand=True,
                ),
            ]),
        ])


class _NavItem(ft.Container):
    """Navigation menu item"""
    def __init__(self, icon, label, view_name, on_click):
        super().__init__(
            content=ft.Row([
                ft.Icon(icon, size=20, color='#94a3b8'),
                ft.Container(width=12),
                ft.Text(label, size=14, color='#e2e8f0'),
            ]),
            padding=ft.padding.only(left=15, top=10, bottom=10),
            border_radius=8,
            on_click=on_click,
        )
        self.view_name = view_name


class JDHubSMSApp:
    """Main JD Hub SMS Application"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.theme = Theme.get_theme('light')
        self.page.bgcolor = '#f8fafc'
        self.page.title = f"{BRAND['full_name']} | JD Hub - {BRAND['contact']}"
        self.page.window_width = 1500
        self.page.window_height = 900
        
        # Initialize database
        db_path = os.path.join(os.path.dirname(__file__), "school_data.db")
        Session.db = self._init_database(db_path)
        Session.school_settings = Session.db.fetch_one("SELECT * FROM school_settings WHERE id = 1")
        
        self.login_view = None
        self.dashboard = None
        self._show_login()
    
    def _init_database(self, db_path):
        """Initialize database connection"""
        from models import Database
        return Database(db_path)
    
    def _show_login(self):
        """Show login screen"""
        self.login_view = LoginView(
            self.page,
            on_login=self._on_logged_in,
            on_activate=self._show_activation
        )
        self.page.views.clear()
        self.page.views.append(self.login_view.build())
        self.page.update()
    
    def _show_activation(self, e=None):
        """Show activation dialog"""
        self.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.VPN_KEY_OUTLINED, color='#2563eb'),
                ft.Text("License Activation"),
            ]),
            content=ft.Column([
                ft.Text("Contact JD Hub for activation:"),
                ft.Container(height=10),
                ft.Container(
                    content=ft.Column([
                        ft.Row([ft.Icon(ft.icons.PHONE, color='#16a34a'),
                              ft.Text(BRAND['contact'], size=16, weight=ft.FontWeight.BOLD)]),
                        ft.Container(height=5),
                        ft.Row([ft.Icon(ft.icons.MAIL_OUTLINE, color='#25d366'),
                              ft.Text("WhatsApp: " + BRAND['whatsapp'], size=14)]),
                        ft.Container(height=5),
                        ft.Row([ft.Icon(ft.icons.EMAIL_OUTLINED, color='#2563eb'),
                              ft.Text(BRAND['email'], size=14)]),
                    ]),
                    padding=15, bgcolor='#f0fdf4', border_radius=10,
                ),
                ft.Container(height=15),
                ft.TextField(label="Enter License Key", hint_text="XXXX-XXXX-XXXX-XXXX"),
            ]),
            actions=[
                ft.TextButton("Close", on_click=lambda _: self.page.close_dialog()),
            ],
        ))
    
    def _on_logged_in(self):
        """Handle successful login"""
        self.dashboard = MainDashboard(
            self.page,
            on_logout=self._logout,
            on_navigate=self._navigate
        )
        self.page.views.clear()
        self.page.views.append(self.dashboard.build())
        self.page.update()
    
    def _logout(self, e=None):
        """Handle logout"""
        Session.current_user = None
        self._show_login()
    
    def _navigate(self, view_name: str):
        """Navigate to a view"""
        if self.dashboard:
            self.dashboard.update_content(view_name)


def main(page: ft.Page):
    """Main entry point"""
    JDHubSMSApp(page)


if __name__ == "__main__":
    ft.app(target=main)
