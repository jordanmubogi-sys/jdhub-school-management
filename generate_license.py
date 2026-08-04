#!/usr/bin/env python3
"""
JD HUB License Key Generator
Use this script to generate license keys for schools
"""

import hashlib
import datetime

def generate_license_key(machine_id, school_name, contact_phone=""):
    """Generate a license key for a school"""
    
    # The license key format: JD-XXXX-XXXX-XXXX-XXXX
    # Extract the machine ID parts
    parts = machine_id.upper().replace('JD-', '').replace('-', '')
    
    if len(parts) != 16:
        return None, "Invalid Machine ID format"
    
    # For demo, the license key is the same as machine ID
    # In production, you would encrypt/sign this differently
    license_key = f"JD-{parts[0:4]}-{parts[4:8]}-{parts[8:12]}-{parts[12:16]}"
    
    return license_key, None

def main():
    print("=" * 50)
    print("   JD HUB LICENSE KEY GENERATOR")
    print("=" * 50)
    print()
    
    while True:
        print("Enter school details (or 'q' to quit):")
        print("-" * 40)
        
        machine_id = input("School Machine ID: ").strip()
        if machine_id.lower() == 'q':
            break
            
        school_name = input("School Name: ").strip()
        if school_name.lower() == 'q':
            break
            
        contact = input("Contact Phone (optional): ").strip()
        
        license_key, error = generate_license_key(machine_id, school_name)
        
        if error:
            print(f"\n❌ Error: {error}\n")
        else:
            print()
            print("=" * 50)
            print("✅ LICENSE KEY GENERATED!")
            print("=" * 50)
            print(f"School: {school_name}")
            print(f"Machine ID: {machine_id}")
            print(f"License Key: {license_key}")
            print(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 50)
            print()
            
            # Save to file for records
            with open("generated_licenses.txt", "a") as f:
                f.write(f"{datetime.datetime.now()}|{school_name}|{machine_id}|{license_key}|{contact}\n")
            
            print("📝 License saved to 'generated_licenses.txt'")
            print()
        
        print("-" * 40)
        print()

if __name__ == "__main__":
    main()
