#!/usr/bin/env python3
"""
Script to create admin user
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database.models import db, User
from getpass import getpass

def create_admin_user():
    app = create_app()
    
    with app.app_context():
        print("=== Create Admin User ===")
        
        username = input("Username: ")
        email = input("Email: ")
        password = getpass("Password: ")
        password_confirm = getpass("Confirm Password: ")
        
        if password != password_confirm:
            print("Error: Passwords don't match")
            return
        
        # Check if user exists
        existing = User.query.filter_by(username=username).first()
        if existing:
            print(f"Error: User '{username}' already exists")
            return
        
        # Create user
        user = User(
            username=username,
            email=email,
            role='admin'
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        print(f"\n✅ Admin user '{username}' created successfully!")
        print(f"ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"Role: {user.role}")

if __name__ == '__main__':
    create_admin_user()
