"""
Backup Manager Module
Handles USB backups, cloud backups, and disaster recovery
"""

import os
import shutil
import sqlite3
import json
import hashlib
import threading
import schedule
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path
from cryptography.fernet import Fernet
import base64


class BackupManager:
    """Manage all backup operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db_dir = os.path.dirname(db_path)
        self.backup_dir = os.path.join(self.db_dir, 'backups')
        self.encryption_key = self._get_or_create_key()
        self.fernet = Fernet(self.encryption_key)
        
        # Create backup directory
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key"""
        key_file = os.path.join(self.db_dir, '.backup_key')
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Protect the key file
            os.chmod(key_file, 0o600)
            return key
    
    # ==================== LOCAL BACKUP ====================
    
    def create_local_backup(self) -> Tuple[bool, str]:
        """Create an encrypted local backup"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"school_backup_{timestamp}.enc"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Read database
            with open(self.db_path, 'rb') as f:
                data = f.read()
            
            # Encrypt
            encrypted = self.fernet.encrypt(data)
            
            # Save
            with open(backup_path, 'wb') as f:
                f.write(encrypted)
            
            # Log backup
            self._log_backup('local', backup_path, backup_name, os.path.getsize(backup_path))
            
            return True, backup_path
        
        except Exception as e:
            return False, str(e)
    
    def restore_local_backup(self, backup_path: str) -> Tuple[bool, str]:
        """Restore from an encrypted local backup"""
        try:
            # Read encrypted backup
            with open(backup_path, 'rb') as f:
                encrypted = f.read()
            
            # Decrypt
            data = self.fernet.decrypt(encrypted)
            
            # Create safety backup of current db
            safety_backup = self.db_path + '.safety_backup'
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, safety_backup)
            
            # Restore
            with open(self.db_path, 'wb') as f:
                f.write(data)
            
            return True, "Backup restored successfully"
        
        except Exception as e:
            return False, str(e)
    
    # ==================== USB BACKUP ====================
    
    def detect_usb_drives(self) -> List[str]:
        """Detect connected USB drives"""
        drives = []
        
        if os.name == 'nt':  # Windows
            import subprocess
            result = subprocess.run(['wmic', 'path', 'win32_logicaldisk', 
                                   'where', "DriveType=2", 'get', 'DeviceID'],
                                  capture_output=True, text=True)
            for line in result.stdout.strip().split('\n')[1:]:
                if line.strip():
                    drives.append(line.strip())
        else:  # Linux/Mac
            for mount in ['/media', '/mnt', '/Volumes']:
                if os.path.exists(mount):
                    for item in os.listdir(mount):
                        drives.append(os.path.join(mount, item))
        
        return drives
    
    def backup_to_usb(self, usb_path: str) -> Tuple[bool, str]:
        """Backup to USB drive"""
        try:
            # Check if USB is connected
            if not os.path.exists(usb_path):
                return False, "USB drive not found"
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"school_backup_{timestamp}.enc"
            backup_path = os.path.join(usb_path, backup_name)
            
            # Read and encrypt database
            with open(self.db_path, 'rb') as f:
                data = f.read()
            
            encrypted = self.fernet.encrypt(data)
            
            # Save to USB
            with open(backup_path, 'wb') as f:
                f.write(encrypted)
            
            # Log backup
            self._log_backup('usb', usb_path, backup_name, os.path.getsize(backup_path))
            
            return True, f"Backup saved to {backup_path}"
        
        except Exception as e:
            return False, str(e)
    
    def restore_from_usb(self, usb_path: str, backup_file: str) -> Tuple[bool, str]:
        """Restore from USB backup"""
        try:
            backup_path = os.path.join(usb_path, backup_file)
            
            if not os.path.exists(backup_path):
                return False, "Backup file not found"
            
            # Read and decrypt
            with open(backup_path, 'rb') as f:
                encrypted = f.read()
            
            data = self.fernet.decrypt(encrypted)
            
            # Safety backup
            safety_backup = self.db_path + '.safety_backup'
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, safety_backup)
            
            # Restore
            with open(self.db_path, 'wb') as f:
                f.write(data)
            
            return True, "Restore completed successfully"
        
        except Exception as e:
            return False, str(e)
    
    def list_usb_backups(self, usb_path: str) -> List[Dict]:
        """List available backups on USB"""
        backups = []
        
        if not os.path.exists(usb_path):
            return backups
        
        for f in os.listdir(usb_path):
            if f.startswith('school_backup_') and f.endswith('.enc'):
                full_path = os.path.join(usb_path, f)
                stat = os.stat(full_path)
                backups.append({
                    'filename': f,
                    'path': full_path,
                    'size': stat.st_size,
                    'date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        return sorted(backups, key=lambda x: x['date'], reverse=True)
    
    # ==================== CLOUD BACKUP ====================
    
    def backup_to_google_drive(self, credentials_path: str = None) -> Tuple[bool, str]:
        """Upload backup to Google Drive"""
        # Note: This requires Google Drive API setup
        # For a full implementation, use google-api-python-client
        
        if not credentials_path or not os.path.exists(credentials_path):
            return False, "Google Drive credentials not configured"
        
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            
            # Create local backup first
            success, result = self.create_local_backup()
            if not success:
                return False, f"Local backup failed: {result}"
            
            # Upload to Google Drive
            # This is a simplified version - full implementation would need
            # proper OAuth flow and Drive API setup
            
            SCOPES = ['https://www.googleapis.com/auth/drive.file']
            
            creds = None
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_info(
                    json.loads(open('token.json').read()), SCOPES)
            
            if not creds or not creds.valid:
                return False, "Google Drive authentication required"
            
            service = build('drive', 'v3', credentials=creds)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_metadata = {
                'name': f'school_backup_{timestamp}.enc',
                'parents': ['appDataFolder']
            }
            
            media = MediaFileUpload(result, resumable=True)
            
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            # Log backup
            self._log_backup('cloud', 'Google Drive', 
                           f'school_backup_{timestamp}.enc', os.path.getsize(result))
            
            # Clean up local backup
            os.remove(result)
            
            return True, f"Uploaded to Google Drive: {file.get('id')}"
        
        except ImportError:
            return False, "Google Drive API libraries not installed"
        except Exception as e:
            return False, str(e)
    
    def check_internet_connection(self) -> bool:
        """Check if internet is available"""
        import socket
        try:
            socket.create_connection(("www.google.com", 80), timeout=5)
            return True
        except OSError:
            return False
    
    # ==================== SCHEDULED BACKUPS ====================
    
    def start_scheduled_backups(self, usb_path: str = None,
                               interval_hours: int = 168):  # Default: weekly
        """Start automated backup schedule"""
        def backup_job():
            if usb_path and os.path.exists(usb_path):
                self.backup_to_usb(usb_path)
            
            # Always create local backup
            self.create_local_backup()
            
            # Check for cloud backup if configured
            if self.check_internet_connection():
                self.backup_to_google_drive()
        
        # Schedule the job
        schedule.every(interval_hours).hours.do(backup_job)
        
        # Run in background thread
        def run_schedule():
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        thread = threading.Thread(target=run_schedule, daemon=True)
        thread.start()
    
    # ==================== EMERGENCY RESTORE ====================
    
    def emergency_restore(self, backup_source: str) -> Tuple[bool, str]:
        """One-click emergency restore from any backup source"""
        # Detect backup type and restore
        if os.path.isfile(backup_source):
            # Local file
            if backup_source.endswith('.enc'):
                return self.restore_local_backup(backup_source)
            else:
                return self._restore_unencrypted(backup_source)
        
        elif os.path.isdir(backup_source):
            # USB drive - find latest backup
            backups = self.list_usb_backups(backup_source)
            if backups:
                return self.restore_from_usb(backup_source, backups[0]['filename'])
            return False, "No backups found on USB"
        
        return False, "Invalid backup source"
    
    def _restore_unencrypted(self, backup_path: str) -> Tuple[bool, str]:
        """Restore from unencrypted backup"""
        try:
            # Safety backup
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, self.db_path + '.safety_backup')
            
            # Copy backup
            shutil.copy2(backup_path, self.db_path)
            
            return True, "Restore completed"
        
        except Exception as e:
            return False, str(e)
    
    # ==================== UTILITY ====================
    
    def _log_backup(self, backup_type: str, location: str, 
                   filename: str, file_size: int):
        """Log backup in database"""
        if os.path.exists(self.db_path):
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute("""
                    INSERT INTO backup_history 
                    (backup_type, location, file_name, file_size, status)
                    VALUES (?, ?, ?, ?, 'success')
                """, (backup_type, location, filename, file_size))
                conn.commit()
                conn.close()
            except:
                pass
    
    def get_backup_history(self, limit: int = 20) -> List[Dict]:
        """Get backup history"""
        if os.path.exists(self.db_path):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(
                "SELECT * FROM backup_history ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            history = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return history
        return []
    
    def verify_backup_integrity(self, backup_path: str) -> Tuple[bool, str]:
        """Verify backup file integrity"""
        try:
            with open(backup_path, 'rb') as f:
                encrypted = f.read()
            
            self.fernet.decrypt(encrypted)
            return True, "Backup is valid and can be restored"
        
        except Exception as e:
            return False, f"Backup verification failed: {str(e)}"
    
    def cleanup_old_backups(self, keep_local: int = 10, 
                           keep_usb: int = 52) -> int:
        """Clean up old backup files"""
        deleted = 0
        
        # Local backups
        if os.path.exists(self.backup_dir):
            backups = sorted(
                [f for f in os.listdir(self.backup_dir) if f.startswith('school_backup_')],
                reverse=True
            )
            
            for backup in backups[keep_local:]:
                try:
                    os.remove(os.path.join(self.backup_dir, backup))
                    deleted += 1
                except:
                    pass
        
        return deleted
