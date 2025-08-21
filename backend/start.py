#!/usr/bin/env python3
"""
KABS Assistant Backend Startup Script
This script initializes and starts the KABS Assistant backend server.
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'psycopg2',
        'openai',
        'pydantic',
        'python-jose',
        'passlib',
        'python-multipart'
    ]
    
    missing_packages = []
    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall dependencies with:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    
    print("✅ All required dependencies are installed")

def check_env_file():
    """Check if .env file exists and has required variables."""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  Warning: .env file not found")
        print("Please create .env file from .env.example")
        print("cp .env.example .env")
        print("Then edit .env with your configuration")
        return False
    
    # Check for critical environment variables
    required_vars = [
        'DATABASE_URL',
        'OPENAI_API_KEY',
        'SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️  Warning: Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    print("✅ Environment configuration looks good")
    return True

def check_database():
    """Check if database is accessible."""
    try:
        from app.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Please check your DATABASE_URL in .env file")
        return False

def initialize_database():
    """Initialize database tables if needed."""
    try:
        from app.database import engine
        from app.models import Base
        
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create database tables: {e}")
        return False

def start_server():
    """Start the FastAPI server with uvicorn."""
    print("\n🚀 Starting KABS Assistant Backend Server...")
    print("=" * 50)
    
    # Server configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print(f"📍 Server will be available at: http://{host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    print(f"🔧 Auto-reload: {'enabled' if reload else 'disabled'}")
    print("=" * 50)
    
    # Start uvicorn server
    cmd = [
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", host,
        "--port", str(port)
    ]
    
    if reload:
        cmd.append("--reload")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

def main():
    """Main startup function."""
    print("KABS Assistant Backend Startup")
    print("=" * 40)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Run checks
    check_python_version()
    check_dependencies()
    
    env_ok = check_env_file()
    if not env_ok:
        print("\nPlease configure your environment and try again.")
        sys.exit(1)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check database
    if not check_database():
        print("\nPlease fix database connection and try again.")
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        print("\nPlease fix database issues and try again.")
        sys.exit(1)
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
