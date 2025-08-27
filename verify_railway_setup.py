#!/usr/bin/env python3
"""
Railway Deployment Verification Script
Checks if all necessary files and configurations are in place for Railway deployment.
"""

import os
import json
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists and print status"""
    if Path(file_path).exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - MISSING")
        return False

def check_railway_config():
    """Check railway.json configuration"""
    if not Path("railway.json").exists():
        return False
    
    try:
        with open("railway.json", "r") as f:
            config = json.load(f)
        
        # Check required sections
        required_sections = ["build", "deploy"]
        for section in required_sections:
            if section not in config:
                print(f"❌ railway.json missing section: {section}")
                return False
        
        print("✅ railway.json configuration is valid")
        return True
    except json.JSONDecodeError:
        print("❌ railway.json is not valid JSON")
        return False

def check_python_package():
    """Check if the Python package structure is correct"""
    base_dir = Path("base")
    if not base_dir.exists():
        print("❌ base/ directory not found")
        return False
    
    pyproject_file = base_dir / "pyproject.toml"
    if not pyproject_file.exists():
        print("❌ base/pyproject.toml not found")
        return False
    
    axiestudio_dir = base_dir / "axiestudio"
    if not axiestudio_dir.exists():
        print("❌ base/axiestudio/ directory not found")
        return False
    
    main_file = axiestudio_dir / "main.py"
    if not main_file.exists():
        print("❌ base/axiestudio/main.py not found")
        return False
    
    print("✅ Python package structure is correct")
    return True

def main():
    """Main verification function"""
    print("🔍 Verifying Railway deployment setup...\n")
    
    all_good = True
    
    # Check essential files
    files_to_check = [
        ("railway.json", "Railway configuration"),
        ("Procfile", "Process file"),
        ("nixpacks.toml", "Nixpacks configuration"),
        ("start.py", "Production startup script"),
        ("requirements.txt", "Python requirements"),
        (".env.railway", "Environment variables reference"),
        ("RAILWAY_DEPLOYMENT_GUIDE.md", "Deployment guide"),
    ]
    
    for file_path, description in files_to_check:
        if not check_file_exists(file_path, description):
            all_good = False
    
    print()
    
    # Check railway.json configuration
    if not check_railway_config():
        all_good = False
    
    # Check Python package structure
    if not check_python_package():
        all_good = False
    
    # Check git repository
    if Path(".git").exists():
        print("✅ Git repository initialized")
    else:
        print("❌ Git repository not initialized")
        all_good = False
    
    print("\n" + "="*50)
    
    if all_good:
        print("🎉 All checks passed! Your backend is Railway-ready!")
        print("\nNext steps:")
        print("1. Go to https://railway.app")
        print("2. Connect your GitHub repository: axiestudio/backend")
        print("3. Set up environment variables (see .env.railway)")
        print("4. Deploy!")
    else:
        print("⚠️  Some issues found. Please fix them before deploying.")
    
    print("\n📖 See RAILWAY_DEPLOYMENT_GUIDE.md for detailed instructions.")

if __name__ == "__main__":
    main()
