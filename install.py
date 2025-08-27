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
    
    # Install the package in editable mode
    if not run_command("pip install --upgrade pip", cwd=base_dir):
        print("❌ Failed to upgrade pip")
        sys.exit(1)
    
    if not run_command("pip install -e .", cwd=base_dir):
        print("❌ Failed to install axiestudio package")
        sys.exit(1)
    
    print("✅ Installation complete!")
    
    # Verify installation
    try:
        import axiestudio
        print(f"✅ Axiestudio imported successfully")
        print(f"📍 Package location: {axiestudio.__file__}")
    except ImportError as e:
        print(f"❌ Failed to import axiestudio: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
