#!/usr/bin/env python3
# setup_mac.py
"""
Setup script for DialLoop Pro macOS
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    return True

def check_macos_version():
    """Check macOS version"""
    mac_version = platform.mac_ver()[0]
    if mac_version:
        print(f"✅ macOS {mac_version} detected")
        return True
    else:
        print("❌ This script requires macOS")
        return False

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_launch_script():
    """Create .command file for easy launching"""
    script_content = '''#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || true
python3 dialloop_mac.py
'''
    
    with open("DialLoopPro.command", "w") as f:
        f.write(script_content)
    
    # Make it executable
    os.chmod("DialLoopPro.command", 0o755)
    print("✅ Created launch script: DialLoopPro.command")

def setup_accessibility():
    """Guide user through accessibility setup"""
    print("\n🔒 Accessibility Permissions Required")
    print("=" * 50)
    print("DialLoop Pro needs accessibility permissions to:")
    print("  • Control mouse and keyboard")
    print("  • Activate other applications")
    print("  • Read window titles")
    print("\nTo grant permissions:")
    print("1. Open System Preferences")
    print("2. Go to Security & Privacy")
    print("3. Select the Privacy tab")
    print("4. Select Accessibility from the left sidebar")
    print("5. Click the lock icon to make changes")
    print("6. Click [+] and add:")
    print("   • Terminal (if running from Terminal)")
    print("   • Python (if running .py file directly)")
    print("   • DialLoopPro.command (if using launch script)")
    print("\nYou may need to restart the app after granting permissions.")
    print("=" * 50)

def migrate_windows_config():
    """Migrate Windows INI files if they exist"""
    windows_ini = "settings.ini"
    if os.path.exists(windows_ini):
        print("🔧 Migrating Windows configuration...")
        # The config manager will handle the migration
        print("✅ Configuration migrated")
    else:
        print("✅ No Windows configuration found - fresh start")

def create_virtualenv():
    """Create virtual environment"""
    print("🐍 Creating virtual environment...")
    
    if not os.path.exists("venv"):
        try:
            subprocess.check_call([sys.executable, "-m", "venv", "venv"])
            print("✅ Virtual environment created")
            return True
        except subprocess.CalledProcessError:
            print("⚠️  Could not create virtual environment")
            print("   Continuing with global Python...")
            return False
    else:
        print("✅ Virtual environment already exists")
        return True

def main():
    print("=" * 60)
    print("DialLoop Pro v4.4 - macOS Setup")
    print("=" * 60)
    
    # Check requirements
    if not check_macos_version():
        return 1
    
    if not check_python_version():
        return 1
    
    # Create virtual environment
    create_virtualenv()
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Migrate Windows config
    migrate_windows_config()
    
    # Create launch script
    create_launch_script()
    
    # Setup instructions
    setup_accessibility()
    
    print("\n" + "=" * 60)
    print("✅ Setup Complete!")
    print("\nTo start DialLoop Pro:")
    print("   Option 1: Double-click 'DialLoopPro.command'")
    print("   Option 2: Run: python3 dialloop_mac.py")
    print("\nHotkeys (use ⌘ instead of Ctrl):")
    print("   ⌘+Alt+C = Start dialing")
    print("   ⌘+Alt+S = Stop dialing")
    print("   ⌘+Alt+H = Hangup & next")
    print("   ⌘+Alt+L = On/Off call")
    print("   ⌘+Alt+O = Configuration")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())