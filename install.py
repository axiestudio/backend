    #!/usr/bin/env python3
"""
Installation script for Railway deployment
This script ensures the axiestudio package is properly installed
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True,
            cwd=cwd
        )
        print(f"Success: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False

def main():
    """Main installation function"""
    print("🔧 Installing Axie Studio for Railway deployment...")

    # Change to base directory
    base_dir = Path(__file__).parent / "base"
    if not base_dir.exists():
        print("❌ base/ directory not found!")
        sys.exit(1)

    # Install core dependencies first
    print("📦 Installing core dependencies...")
    if not run_command("pip install --upgrade pip setuptools wheel"):
        print("❌ Failed to upgrade pip and setuptools")
        sys.exit(1)

    # Install the package in editable mode
    print("📦 Installing axiestudio package...")
    if not run_command("pip install -e .", cwd=base_dir):
        print("❌ Failed to install axiestudio package")
        sys.exit(1)

    print("✅ Installation complete!")

    # Verify installation
    try:
        # Add the base directory to Python path
        sys.path.insert(0, str(base_dir))
        import axiestudio
        print(f"✅ Axiestudio imported successfully")
        print(f"📍 Package location: {axiestudio.__file__}")

        # Test critical imports
        print("🔍 Testing critical imports...")
        from axiestudio.main import create_app
        from axiestudio.services.deps import get_settings_service
        print("✅ Critical imports successful")

    except ImportError as e:
        print(f"❌ Failed to import axiestudio: {e}")
        print("🔧 Attempting fallback installation...")

        # Fallback: install requirements manually
        requirements_file = Path(__file__).parent / "requirements.txt"
        if requirements_file.exists():
            if not run_command(f"pip install -r {requirements_file}"):
                print("❌ Failed to install requirements")
                sys.exit(1)

            # Try installing the package again
            if not run_command("pip install -e .", cwd=base_dir):
                print("❌ Failed to install axiestudio package after requirements")
                sys.exit(1)
        else:
            print("❌ No requirements.txt found for fallback")
            sys.exit(1)

if __name__ == "__main__":
    main()
