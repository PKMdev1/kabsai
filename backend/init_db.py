#!/usr/bin/env python3
"""
Database initialization script for KABS Assistant
Creates tables and default admin user
"""

import os
import sys
from sqlalchemy import create_engine
from app.database import engine, SessionLocal
from app.models import Base, User
from app.auth import get_password_hash
from app.config import settings

def init_database():
    """Initialize the database with tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")

def create_admin_user():
    """Create a default admin user"""
    db = SessionLocal()
    
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            print("✅ Admin user already exists")
            return
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@kabs.com",
            full_name="KABS Administrator",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_admin=True,
            role="admin"
        )
        
        db.add(admin_user)
        db.commit()
        print("✅ Admin user created successfully")
        print("   Username: admin")
        print("   Password: admin123")
        print("   ⚠️  Please change the password after first login!")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Main initialization function"""
    print("🚀 Initializing KABS Assistant Database...")
    print("=" * 50)
    
    try:
        # Test database connection
        print("Testing database connection...")
        engine.connect()
        print("✅ Database connection successful")
        
        # Initialize database
        init_database()
        
        # Create admin user
        create_admin_user()
        
        print("=" * 50)
        print("🎉 Database initialization completed!")
        print("\nNext steps:")
        print("1. Start the backend server: uvicorn main:app --reload")
        print("2. Start the frontend: npm run dev (in frontend directory)")
        print("3. Login with admin/admin123 and change the password")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("\nPlease check:")
        print("1. PostgreSQL is running")
        print("2. Database 'kabs_assistant' exists")
        print("3. DATABASE_URL is correctly configured in .env")
        sys.exit(1)

if __name__ == "__main__":
    main()
