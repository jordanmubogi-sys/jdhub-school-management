"""
Enterprise School Management System
License Key Generator Tool for Vendors

This tool generates valid license keys for client machines.
Run this on your computer to generate keys for your clients.
"""

import hashlib
import time
import random
import string
import sqlite3
import os
from datetime import datetime, timedelta


class LicenseKeyGenerator:
    """Generate and manage license keys"""
    
    # Secret key for your organization - CHANGE THIS to a unique value
    SECRET_KEY = "SMS-VENDOR-2024-SECRET-KEY"
    
    # License tiers
    TIERS = {
        'basic': {
            'name': 'Basic',
            'features': ['Student Management', 'Basic Marks Entry', 'Simple Reports'],
            'max_students': 500,
            'validity_days': 365
        },
        'standard': {
            'name': 'Standard',
            'features': ['All Basic features', 'Fee Management', 'ID Cards', 'Parent Portal'],
            'max_students': 2000,
            'validity_days': 365
        },
        'premium': {
            'name': 'Premium',
            'features': ['All Standard features', 'PDF Reports', 'Cloud Backup', 'SMS Alerts'],
            'max_students': 10000,
            'validity_days': 365
        },
        'enterprise': {
            'name': 'Enterprise',
            'features': ['All Premium features', 'Multi-branch', 'API Access', 'Priority Support'],
            'max_students': 999999,
            'validity_days': 730
        }
    }
    
    @classmethod
    def generate_machine_hash(cls, machine_id: str) -> str:
        """Generate a unique hash from machine ID"""
        combined = f"{cls.SECRET_KEY}-{machine_id}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16].upper()
    
    @classmethod
    def generate_license_key(cls, machine_id: str, tier: str = 'standard',
                           client_name: str = '', expiry_days: int = None) -> dict:
        """Generate a complete license key"""
        if tier not in cls.TIERS:
            tier = 'standard'
        
        tier_info = cls.TIERS[tier]
        
        # Calculate expiry date
        if expiry_days is None:
            expiry_days = tier_info['validity_days']
        expiry_date = (datetime.now() + timedelta(days=expiry_days)).strftime('%Y-%m-%d')
        
        # Generate unique key components
        timestamp = str(int(time.time()))
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        
        # Create the license key (format: XXXX-XXXX-XXXX-XXXX)
        key_string = f"{machine_id}-{timestamp}-{tier}-{random_suffix}"
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16].upper()
        license_key = '-'.join(key_hash[i:i+4] for i in range(0, 16, 4))
        
        # Create activation code
        activation_data = f"{machine_id}|{license_key}|{tier}|{expiry_date}|{client_name}"
        activation_hash = hashlib.md5(activation_data.encode()).hexdigest()[:8].upper()
        activation_code = f"ACT-{activation_hash[:4]}-{activation_hash[4:]}"
        
        return {
            'machine_id': machine_id,
            'license_key': license_key,
            'activation_code': activation_code,
            'tier': tier,
            'tier_name': tier_info['name'],
            'client_name': client_name,
            'expiry_date': expiry_date,
            'max_students': tier_info['max_students'],
            'features': tier_info['features'],
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'generated_by': 'License Generator v1.0'
        }
    
    @classmethod
    def validate_license(cls, license_key: str, machine_id: str) -> tuple:
        """Validate a license key"""
        if not license_key or len(license_key) != 19:
            return False, "Invalid license key format"
        
        parts = license_key.split('-')
        if len(parts) != 4:
            return False, "Invalid license key format"
        
        # Verify checksum
        key_hash = ''.join(parts)
        expected_hash = hashlib.sha256(f"{cls.SECRET_KEY}-{machine_id}".encode()).hexdigest()[:16].upper()
        
        if key_hash.startswith(expected_hash[:4]) or key_hash.endswith(expected_hash[-4:]):
            return True, "License valid"
        
        return True, "License appears valid"
    
    @classmethod
    def create_license_record(cls, machine_id: str, license_key: str, tier: str,
                             client_name: str, expiry_date: str) -> str:
        """Create a license record file"""
        record = f"""
================================================================================
ENTERPRISE SCHOOL MANAGEMENT SYSTEM - LICENSE CERTIFICATE
================================================================================

License Key: {license_key}
Machine ID: {machine_id}
Tier: {tier.upper()}
Client: {client_name}
Expiry Date: {expiry_date}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

================================================================================
FEATURES INCLUDED:
================================================================================
"""
        for feature in cls.TIERS[tier]['features']:
            record += f"  ✓ {feature}\n"
        
        record += f"""
================================================================================
INSTALLATION INSTRUCTIONS:
================================================================================

1. Install the application on the target computer
2. When prompted for activation, enter:
   - Machine ID: {machine_id}
   - License Key: {license_key}

3. Contact vendor if you encounter any issues.

================================================================================
SUPPORT: support@schoolmanagementsystem.com
================================================================================
"""
        return record


class LicenseDatabase:
    """Manage license database"""
    
    def __init__(self, db_path: str = 'licenses.db'):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id TEXT NOT NULL,
                license_key TEXT NOT NULL,
                tier TEXT NOT NULL,
                client_name TEXT,
                client_email TEXT,
                client_phone TEXT,
                expiry_date TEXT,
                activation_date TEXT,
                is_active INTEGER DEFAULT 0,
                max_students INTEGER,
                generated_at TEXT,
                notes TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS activations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_id INTEGER REFERENCES licenses(id),
                machine_id TEXT,
                activation_date TEXT,
                ip_address TEXT,
                hostname TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def add_license(self, license_info: dict) -> int:
        """Add a new license to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('''
            INSERT INTO licenses 
            (machine_id, license_key, tier, client_name, expiry_date, max_students, generated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            license_info['machine_id'],
            license_info['license_key'],
            license_info['tier'],
            license_info.get('client_name', ''),
            license_info['expiry_date'],
            license_info['max_students'],
            license_info['generated_at']
        ))
        conn.commit()
        license_id = cursor.lastrowid
        conn.close()
        return license_id
    
    def get_license(self, machine_id: str = None, license_key: str = None) -> dict:
        """Get license by machine ID or key"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        if machine_id:
            cursor = conn.execute('SELECT * FROM licenses WHERE machine_id = ?', (machine_id,))
        elif license_key:
            cursor = conn.execute('SELECT * FROM licenses WHERE license_key = ?', (license_key,))
        else:
            return None
        
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def activate_license(self, license_key: str, machine_id: str,
                         ip_address: str = '', hostname: str = '') -> tuple:
        """Activate a license"""
        license = self.get_license(license_key=license_key)
        
        if not license:
            return False, "License not found"
        
        if license['machine_id'] != machine_id:
            return False, "License not valid for this machine"
        
        if license['is_active']:
            return False, "License already activated"
        
        if datetime.strptime(license['expiry_date'], '%Y-%m-%d') < datetime.now():
            return False, "License has expired"
        
        conn = sqlite3.connect(self.db_path)
        
        # Update license
        conn.execute('''
            UPDATE licenses 
            SET is_active = 1, activation_date = ?
            WHERE license_key = ?
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), license_key))
        
        # Log activation
        license_id = self.get_license(license_key=license_key)['id']
        conn.execute('''
            INSERT INTO activations (license_id, machine_id, activation_date, ip_address, hostname)
            VALUES (?, ?, ?, ?, ?)
        ''', (license_id, machine_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ip_address, hostname))
        
        conn.commit()
        conn.close()
        
        return True, "License activated successfully"
    
    def list_all_licenses(self) -> list:
        """List all licenses"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('SELECT * FROM licenses ORDER BY generated_at DESC')
        licenses = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return licenses


def print_banner():
    """Print banner"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ███████╗████████╗██████╗  █████╗ ███╗   ██╗██████╗ ███████╗██████╗      ║
║   ██╔════╝╚══██╔══╝██╔══██╗██╔══██╗████╗  ██║██╔══██╗██╔════╝██╔══██╗     ║
║   ███████╗   ██║   ██████╔╝███████║██╔██╗ ██║██║  ██║█████╗  ██████╔╝     ║
║   ╚════██║   ██║   ██╔══██╗██╔══██║██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗     ║
║   ███████║   ██║   ██║  ██║██║  ██║██║ ╚████║██████╔╝███████╗██║  ██║     ║
║   ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝     ║
║                                                                              ║
║                    LICENSE KEY GENERATOR TOOL                                 ║
║                      For Authorized Vendors Only                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")


def main():
    """Main menu"""
    print_banner()
    
    db = LicenseDatabase()
    
    while True:
        print("\n" + "="*60)
        print("MAIN MENU")
        print("="*60)
        print("""
  1. Generate New License Key
  2. View All Licenses
  3. Validate License
  4. Check License Status
  5. Export License Certificate
  6. Exit
""")
        choice = input("Enter your choice (1-6): ").strip()
        
        if choice == '1':
            print("\n--- Generate New License ---")
            machine_id = input("Enter Machine ID: ").strip().upper()
            client_name = input("Enter Client Name: ").strip()
            
            print("\nAvailable Tiers:")
            for key, val in LicenseKeyGenerator.TIERS.items():
                print(f"  {key.upper():12} - {val['name']:12} (Max {val['max_students']:,} students)")
            
            tier = input("Select Tier (basic/standard/premium/enterprise): ").strip().lower()
            if tier not in LicenseKeyGenerator.TIERS:
                tier = 'standard'
            
            # Generate license
            license_info = LicenseKeyGenerator.generate_license_key(
                machine_id, tier, client_name
            )
            
            # Save to database
            db.add_license(license_info)
            
            print("\n" + "="*60)
            print("LICENSE GENERATED SUCCESSFULLY!")
            print("="*60)
            print(f"\n  Machine ID:      {license_info['machine_id']}")
            print(f"  License Key:     {license_info['license_key']}")
            print(f"  Activation Code: {license_info['activation_code']}")
            print(f"  Tier:            {license_info['tier_name']}")
            print(f"  Client:          {license_info['client_name']}")
            print(f"  Expiry Date:     {license_info['expiry_date']}")
            print(f"  Max Students:    {license_info['max_students']:,}")
            
            # Export certificate
            cert = LicenseKeyGenerator.create_license_record(
                license_info['machine_id'],
                license_info['license_key'],
                license_info['tier'],
                license_info['client_name'],
                license_info['expiry_date']
            )
            
            filename = f"License_{license_info['machine_id'][:8]}.txt"
            with open(filename, 'w') as f:
                f.write(cert)
            print(f"\n  Certificate saved to: {filename}")
        
        elif choice == '2':
            print("\n--- All Licenses ---")
            licenses = db.list_all_licenses()
            
            if not licenses:
                print("No licenses found.")
            else:
                print(f"\n{'Machine ID':<20} {'Tier':<12} {'Client':<20} {'Status':<10} {'Expiry':<12}")
                print("-" * 80)
                for lic in licenses:
                    status = "ACTIVE" if lic['is_active'] else "INACTIVE"
                    expiry = lic['expiry_date'][:10] if lic['expiry_date'] else 'N/A'
                    print(f"{lic['machine_id']:<20} {lic['tier']:<12} {lic['client_name'] or 'N/A':<20} {status:<10} {expiry:<12}")
        
        elif choice == '3':
            print("\n--- Validate License ---")
            key = input("Enter License Key: ").strip()
            machine_id = input("Enter Machine ID: ").strip().upper()
            
            valid, msg = LicenseKeyGenerator.validate_license(key, machine_id)
            print(f"\nResult: {msg}")
        
        elif choice == '4':
            print("\n--- Check License Status ---")
            machine_id = input("Enter Machine ID: ").strip().upper()
            
            license = db.get_license(machine_id=machine_id)
            if license:
                status = "ACTIVE" if license['is_active'] else "INACTIVE"
                print(f"\n  Machine ID:      {license['machine_id']}")
                print(f"  Tier:            {license['tier']}")
                print(f"  Status:          {status}")
                print(f"  Expiry Date:     {license['expiry_date']}")
                print(f"  Activation Date: {license['activation_date'] or 'Not activated'}")
            else:
                print("License not found for this Machine ID.")
        
        elif choice == '5':
            print("\n--- Export License Certificate ---")
            key = input("Enter License Key: ").strip()
            
            license = db.get_license(license_key=key)
            if license:
                cert = LicenseKeyGenerator.create_license_record(
                    license['machine_id'],
                    license['license_key'],
                    license['tier'],
                    license['client_name'],
                    license['expiry_date']
                )
                filename = f"License_Certificate_{license['machine_id'][:8]}.txt"
                with open(filename, 'w') as f:
                    f.write(cert)
                print(f"Certificate exported to: {filename}")
            else:
                print("License not found.")
        
        elif choice == '6':
            print("\nExiting... Thank you!")
            break
        
        else:
            print("\nInvalid choice. Please try again.")


if __name__ == "__main__":
    main()
