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
    """Initialize database with default user"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create default user if it doesn't exist
    db = SessionLocal()
    try:
        default_user = db.query(User).filter(User.username == "admin").first()
        if not default_user:
            default_user = User(
                username="admin",
                full_name="Administrator",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_admin=True,
                role="admin"
            )
            db.add(default_user)
            db.commit()
            print("Default user created: admin/admin123")
        else:
            print("Default user already exists")
    except Exception as e:
        print(f"Error creating default user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
