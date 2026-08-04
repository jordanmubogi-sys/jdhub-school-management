"""
================================================================================
JD HUB ENTERPRISE SCHOOL MANAGEMENT SYSTEM
================================================================================
Developed by JD Hub | Contact: 0754687597
Tkinter Version - Built-in, No External Dependencies
================================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
from datetime import datetime
import hashlib

DB_PATH = os.path.join(os.path.dirname(__file__), "sample_data", "school_data.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

class JDHubApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JD HUB School Management System")
        self.root.geometry("1200x700")
        self.root.configure(bg="#1a365d")
        self.current_user = None
        self.show_login_screen()
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def show_login_screen(self):
        self.clear_window()
        main_frame = tk.Frame(self.root, bg="#1a365d")
        main_frame.pack(fill="both", expand=True)
        
        left_frame = tk.Frame(main_frame, bg="#2563eb", width=400)
        left_frame.pack(side="left", fill="both")
        left_frame.pack_propagate(False)
        
        tk.Label(left_frame, text="JD HUB", font=("Arial", 50, "bold"), bg="#2563eb", fg="white").pack(pady=80)
        tk.Label(left_frame, text="School Management", font=("Arial", 20), bg="#2563eb", fg="white").pack()
        tk.Label(left_frame, text="System", font=("Arial", 20), bg="#2563eb", fg="white").pack()
        tk.Label(left_frame, text="\n\nContact: 0754687597", font=("Arial", 12), bg="#2563eb", fg="#bfdbfe").pack(pady=20)
        
        right_frame = tk.Frame(main_frame, bg="white", width=600)
        right_frame.pack(side="right", fill="both", expand=True)
        
        tk.Label(right_frame, text="Welcome Back", font=("Arial", 28, "bold"), bg="white", fg="#1e293b").pack(pady=40)
        
        login_frame = tk.Frame(right_frame, bg="white")
        login_frame.pack(pady=30, padx=50, fill="x")
        
        tk.Label(login_frame, text="Username", font=("Arial", 12, "bold"), bg="white", fg="#374151").pack(anchor="w")
        self.username_entry = tk.Entry(login_frame, font=("Arial", 14), bd=2, relief="groove", height=2)
        self.username_entry.pack(fill="x", pady=(5, 15))
        
        tk.Label(login_frame, text="Password", font=("Arial", 12, "bold"), bg="white", fg="#374151").pack(anchor="w")
        self.password_entry = tk.Entry(login_frame, font=("Arial", 14), bd=2, relief="groove", height=2, show="*")
        self.password_entry.pack(fill="x", pady=(5, 20))
        
        self.password_entry.bind("<Return>", lambda e: self.login())
        
        tk.Button(login_frame, text="Sign In", font=("Arial", 14, "bold"), 
                  bg="#2563eb", fg="white", cursor="hand2", height=2, command=self.login).pack(fill="x")
        
        demo_frame = tk.LabelFrame(right_frame, text="Demo Accounts", font=("Arial", 11, "bold"), 
                                   bg="white", fg="#2563eb", padx=20, pady=15)
        demo_frame.pack(pady=20, padx=50, fill="x")
        
        tk.Label(demo_frame, text="Admin: admin / admin123", font=("Arial", 11), bg="white").pack(anchor="w")
        tk.Label(demo_frame, text="Teacher: teacher1 / pass123", font=("Arial", 11), bg="white").pack(anchor="w")
        tk.Label(demo_frame, text="Parent: parent1 / pass123", font=("Arial", 11), bg="white").pack(anchor="w")
    
    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            conn.close()
            
            if user and user["password"] == hash_password(password):
                self.current_user = dict(user)
                self.show_dashboard()
            else:
                messagebox.showerror("Login Failed", "Invalid username or password")
        except Exception as e:
            messagebox.showerror("Error", f"Login error: {str(e)}")
    
    def show_dashboard(self):
        self.clear_window()
        
        top_bar = tk.Frame(self.root, bg="#1e3a5f", height=60)
        top_bar.pack(fill="x")
        
        tk.Label(top_bar, text="JD HUB School Management", font=("Arial", 16, "bold"), 
                 bg="#1e3a5f", fg="white").pack(side="left", padx=20)
        tk.Label(top_bar, text="Welcome, " + self.current_user["full_name"], font=("Arial", 12), 
                 bg="#1e3a5f", fg="#93c5fd").pack(side="left", padx=20)
        tk.Button(top_bar, text="Logout", command=self.show_login_screen, bg="#dc2626", fg="white",
                  font=("Arial", 10, "bold"), cursor="hand2").pack(side="right", padx=20)
        
        content = tk.Frame(self.root, bg="#f1f5f9")
        content.pack(fill="both", expand=True)
        
        tk.Label(content, text="Dashboard", font=("Arial", 24, "bold"), 
                 bg="#f1f5f9", fg="#1e293b").pack(pady=20)
        
        actions_frame = tk.Frame(content, bg="#f1f5f9")
        actions_frame.pack(pady=20)
        
        buttons = [
            ("Students", "#2563eb", self.show_students),
            ("Marks Entry", "#16a34a", self.show_marks),
            ("Fees", "#ea580c", self.show_fees),
            ("Subjects", "#7c3aed", self.show_subjects),
            ("Staff", "#0891b2", self.show_staff),
            ("Reports", "#be185d", self.show_reports),
        ]
        
        for i, (text, color, cmd) in enumerate(buttons):
            tk.Button(actions_frame, text=text, font=("Arial", 14, "bold"), 
                     bg=color, fg="white", width=15, height=3, cursor="hand2", command=cmd).grid(row=i//3, column=i%3, padx=10, pady=10)
        
        stats_frame = tk.Frame(content, bg="#f1f5f9")
        stats_frame.pack(pady=20)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM students")
            students_count = cursor.fetchone()["cnt"]
            cursor.execute("SELECT COUNT(*) as cnt FROM staff")
            staff_count = cursor.fetchone()["cnt"]
            conn.close()
        except:
            students_count = 0
            staff_count = 0
        
        for title, value, color in [("Total Students", students_count, "#2563eb"), ("Total Staff", staff_count, "#16a34a"), ("Active Users", 3, "#7c3aed")]:
            stat_box = tk.Frame(stats_frame, bg="white", bd=2, relief="groove")
            stat_box.grid(row=0, column=["Total Students", "Total Staff", "Active Users"].index(title), padx=10)
            tk.Label(stat_box, text=str(value), font=("Arial", 36, "bold"), bg="white", fg=color).pack(padx=30, pady=10)
            tk.Label(stat_box, text=title, font=("Arial", 12), bg="white", fg="#64748b").pack(pady=(0, 15))
    
    def show_students(self):
        self.show_module("Students Management", "Add/Edit/Delete Students, View Details, Enrollment, Class Assignment")
    
    def show_marks(self):
        self.show_module("Marks Entry", "Enter Student Marks, Subject-wise Entry, Exam Management, Grade Calculation")
    
    def show_fees(self):
        self.show_module("Fees Management", "Record Payments, Fee Structure, Payment History, M-Pesa Integration")
    
    def show_subjects(self):
        self.show_module("Subjects", "Add/Edit Subjects, Subject Assignment, Curriculum Management")
    
    def show_staff(self):
        self.show_module("Staff Management", "Add/Edit Staff, Role Assignment, Attendance Tracking")
    
    def show_reports(self):
        self.show_module("Reports", "Student Reports, Financial Reports, Performance Reports, Attendance Reports")
    
    def show_module(self, title, content):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("600x400")
        win.configure(bg="white")
        tk.Label(win, text=title, font=("Arial", 20, "bold"), bg="white", fg="#1e293b").pack(pady=20)
        tk.Label(win, text=content, font=("Arial", 12), bg="white", fg="#475569", justify="left").pack(padx=40, fill="both", expand=True)
        tk.Button(win, text="Close", command=win.destroy, bg="#64748b", fg="white", font=("Arial", 11, "bold")).pack(pady=20)


if __name__ == "__main__":
    root = tk.Tk()
    app = JDHubApp(root)
    root.mainloop()
