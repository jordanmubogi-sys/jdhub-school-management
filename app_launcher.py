"""
================================================================================
JD HUB ENTERPRISE SCHOOL MANAGEMENT SYSTEM
================================================================================
Developed by JD Hub | Contact: 0754687597
Version: 1.0.0
================================================================================
"""

import sys
import os

# Add current directory to path
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, bundle_dir)
os.chdir(bundle_dir)

# Import flet first
import flet

# Monkey patch to prevent auto-install
import flet.utils.pip as flet_pip
if hasattr(flet_pip, 'ensure_flet_desktop_package_installed'):
    flet_pip.ensure_flet_desktop_package_installed = lambda: None


def main(page: flet.Page):
    """Main entry point for Flet app"""
    from main_app import main as app_main
    app_main(page)


if __name__ == "__main__":
    flet.app(target=main)
