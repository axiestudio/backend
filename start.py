#!/usr/bin/env python3
"""
Production startup script for Axie Studio on Railway
"""
import os
import sys
from pathlib import Path

def setup_environment():
    """Set up environment variables for Railway deployment"""
    
    # Ensure we're in the base directory
    base_dir = Path(__file__).parent / "base"
    if base_dir.exists():
        os.chdir(base_dir)
        sys.path.insert(0, str(base_dir))
    
    # Set default environment variables if not already set
    env_defaults = {
        "AXIESTUDIO_HOST": "0.0.0.0",
        "AXIESTUDIO_BACKEND_ONLY": "true",
        "AXIESTUDIO_LOG_LEVEL": "info",
        "AXIESTUDIO_AUTO_LOGIN": "false",
        "AXIESTUDIO_OPEN_BROWSER": "false",
        "AXIESTUDIO_DEV": "false",
        "AXIESTUDIO_WORKERS": "1",
        "AXIESTUDIO_SECRET_KEY": os.environ.get("SECRET_KEY", "railway-default-secret-key"),
        "AXIESTUDIO_SUPERUSER": "admin",
        "AXIESTUDIO_SUPERUSER_PASSWORD": os.environ.get("ADMIN_PASSWORD", "admin123"),
    }
    
    # Set Railway-specific port
    if "PORT" in os.environ:
        env_defaults["AXIESTUDIO_PORT"] = os.environ["PORT"]
    
    # Set database URL if provided by Railway
    if "DATABASE_URL" in os.environ:
        env_defaults["AXIESTUDIO_DATABASE_URL"] = os.environ["DATABASE_URL"]
    
    # Set Redis URL if provided by Railway
    if "REDIS_URL" in os.environ:
        env_defaults["AXIESTUDIO_REDIS_URL"] = os.environ["REDIS_URL"]
    
    # Apply defaults only if not already set
    for key, value in env_defaults.items():
        if key not in os.environ:
            os.environ[key] = value
    
    print("Environment setup complete for Railway deployment")
    print(f"Host: {os.environ.get('AXIESTUDIO_HOST')}")
    print(f"Port: {os.environ.get('AXIESTUDIO_PORT', 'Not set')}")
    print(f"Backend Only: {os.environ.get('AXIESTUDIO_BACKEND_ONLY')}")
    print(f"Database URL: {'Set' if os.environ.get('AXIESTUDIO_DATABASE_URL') else 'Not set'}")

def main():
    """Main startup function"""
    setup_environment()
    
    # Import and run axiestudio
    try:
        from axiestudio.__main__ import main as axiestudio_main
        axiestudio_main()
    except ImportError as e:
        print(f"Error importing axiestudio: {e}")
        print("Make sure axiestudio is properly installed")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting axiestudio: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
