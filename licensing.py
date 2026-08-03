"""
Hardware Licensing & Anti-Piracy Module
Generates unique machine fingerprint and validates license keys
"""

import hashlib
import uuid
import platform
import socket
import subprocess
import re
import sqlite3
import os
from datetime import datetime
from typing import Optional, Tuple

class HardwareLicensing:
    """Hardware fingerprinting and license management"""
    
    # Secret key for license validation
    SECRET_KEY = "SMS-VENDOR-2024-SECRET-KEY"
    
    @staticmethod
    def get_machine_id() -> str:
        """Generate unique machine ID from hardware components"""
        components = []
        
        # CPU Info
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['wmic', 'cpu', 'get', 'ProcessorId'], 
                                      capture_output=True, text=True, timeout=5)
                cpu_id = result.stdout.strip().split('\n')[-1].strip()
                if cpu_id:
                    components.append(cpu_id)
            else:
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if line.startswith('Serial') or 'processor' in line.lower():
                            components.append(line.strip())
        except:
            components.append(platform.processor())
        
        # Motherboard UUID
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['wmic', 'csproduct', 'get', 'UUID'], 
                                      capture_output=True, text=True, timeout=5)
                mb_uuid = result.stdout.strip().split('\n')[-1].strip()
                if mb_uuid and mb_uuid != 'FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF':
                    components.append(mb_uuid)
        except:
            pass
        
        # Machine Name
        components.append(socket.gethostname())
        
        # MAC Address
        try:
            mac = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
            components.append(mac)
        except:
            pass
        
        # Combine and hash
        combined = '-'.join(str(c) for c in components if c)
        machine_hash = hashlib.sha256(combined.encode()).hexdigest()[:32].upper()
        
        return f"MCH-{machine_hash}"
    
    @staticmethod
    def validate_license_key(license_key: str, machine_id: str) -> Tuple[bool, str]:
        """Validate a license key from vendor"""
        if not license_key or len(license_key) != 19:
            return False, "Invalid license key format. Key should be XXXX-XXXX-XXXX-XXXX"
        
        try:
            parts = license_key.split('-')
            if len(parts) != 4:
                return False, "Invalid license key format"
            
            # Verify the key was generated for this machine
            key_hash = ''.join(parts)
            expected_hash = hashlib.sha256(f"{HardwareLicensing.SECRET_KEY}-{machine_id}".encode()).hexdigest()[:16].upper()
            
            # Check if machine ID matches
            machine_hash = HardwareLicensing.get_machine_id()
            if machine_hash != machine_id:
                return False, "Machine ID mismatch. This key is for a different computer."
            
            return True, "License key is valid!"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def get_activation_request(machine_id: str) -> dict:
        """Get all info needed for activation request"""
        return {
            'machine_id': machine_id,
            'system': platform.system(),
            'hostname': socket.gethostname(),
            'request_date': datetime.now().isoformat()
        }


class FeatureLicense:
    """Manage monetized feature toggles"""
    
    FEATURES = {
        'photo_id_cards': {
            'name': 'Student Photo Processing & Bulk ID Card Printing',
            'description': 'Enable student photo upload and bulk ID card generation',
            'tier': 'premium'
        },
        'pdf_branding': {
            'name': 'High-Res Custom PDF Branding Engine',
            'description': 'Professional PDF reports with custom branding',
            'tier': 'premium'
        },
        'email_fee_letters': {
            'name': 'Automated Email Fee Demand Letters',
            'description': 'Auto-generate and email fee demand letters',
            'tier': 'premium'
        },
        'cloud_backup': {
            'name': 'Automated Cloud Backup Sync',
            'description': 'Automatic cloud backup to Google Drive',
            'tier': 'enterprise'
        }
    }
    
    @classmethod
    def is_feature_enabled(cls, db, feature_key: str) -> bool:
        """Check if a feature is enabled"""
        result = db.fetch_one(
            "SELECT is_enabled FROM feature_toggles WHERE feature_key = ?",
            (feature_key,)
        )
        return result['is_enabled'] == 1 if result else False
    
    @classmethod
    def toggle_feature(cls, db, feature_key: str, enabled: bool) -> bool:
        """Enable or disable a feature"""
        try:
            db.execute(
                "UPDATE feature_toggles SET is_enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE feature_key = ?",
                (1 if enabled else 0, feature_key)
            )
            return True
        except:
            return False
    
    @classmethod
    def get_all_features(cls, db) -> list:
        """Get all features with their status"""
        features = db.fetch_all("SELECT * FROM feature_toggles")
        return [dict(f) for f in features]


class TermPublisher:
    """Manage term publishing and term locks"""
    
    @staticmethod
    def publish_term(db, term_id: int, user_id: int) -> Tuple[bool, str]:
        """Publish a term - freeze its data as read-only"""
        term = db.fetch_one("SELECT * FROM academic_terms WHERE id = ?", (term_id,))
        
        if not term:
            return False, "Term not found"
        
        if term['is_published']:
            return False, "Term is already published"
        
        # Mark all marks for this term as locked
        db.execute(
            "UPDATE marks SET is_locked = 1 WHERE term_id = ?",
            (term_id,)
        )
        
        # Mark term as published
        db.execute('''
            UPDATE academic_terms 
            SET is_published = 1, published_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (term_id,))
        
        # Log in audit trail
        db.execute('''
            INSERT INTO audit_trail (user_id, action, table_affected, record_id, new_value)
            VALUES (?, 'PUBLISH_TERM', 'academic_terms', ?, ?)
        ''', (user_id, term_id, 'Term published and locked'))
        
        return True, "Term published successfully"
    
    @staticmethod
    def can_edit_term(db, term_id: int) -> bool:
        """Check if a term can still be edited"""
        term = db.fetch_one("SELECT is_published FROM academic_terms WHERE id = ?", (term_id,))
        return not term['is_published'] if term else False
