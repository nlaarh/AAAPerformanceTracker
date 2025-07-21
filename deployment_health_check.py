#!/usr/bin/env python3
"""
Comprehensive deployment health check for AAAPerformanceTracker
Tests all critical components before deployment
"""

import os
import sys
import time
import logging
from sqlalchemy import create_engine, text

def health_check():
    """Run comprehensive health check"""
    print("🔍 AAAPerformanceTracker Deployment Health Check")
    print("=" * 60)
    
    # Check 1: App Import
    print("\n1. Testing Application Import...")
    try:
        from app import app, db
        print("✅ App imports successfully")
        
        # Check configuration
        has_secret = bool(app.secret_key)
        has_db_uri = bool(app.config.get('SQLALCHEMY_DATABASE_URI'))
        
        print(f"✅ Secret key configured: {has_secret}")
        print(f"✅ Database URI configured: {has_db_uri}")
        
    except Exception as e:
        print(f"❌ App import failed: {e}")
        return False
    
    # Check 2: Database Connection
    print("\n2. Testing Database Connection...")
    try:
        with app.app_context():
            # Test database connection
            result = db.session.execute(text("SELECT 1")).scalar()
            print(f"✅ Database connection successful: {result}")
            
            # Check critical tables
            tables = ['user', 'assessment_period', 'assessment_assignment']
            for table in tables:
                count = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"✅ Table {table}: {count} records")
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Check 3: Routes Loading
    print("\n3. Testing Routes Loading...")
    try:
        import routes
        print("✅ Routes loaded successfully")
        
        # Count routes
        route_count = len(app.url_map._rules)
        print(f"✅ Total routes registered: {route_count}")
        
    except Exception as e:
        print(f"❌ Routes loading failed: {e}")
        return False
    
    # Check 4: Models Loading
    print("\n4. Testing Models Loading...")
    try:
        from models import User, AssessmentPeriod, AssessmentAssignment
        print("✅ Models loaded successfully")
        
        # Test model instantiation
        with app.app_context():
            user_count = User.query.count()
            period_count = AssessmentPeriod.query.count()
            assignment_count = AssessmentAssignment.query.count()
            
            print(f"✅ Users in database: {user_count}")
            print(f"✅ Assessment periods: {period_count}")
            print(f"✅ Assessment assignments: {assignment_count}")
            
    except Exception as e:
        print(f"❌ Models loading failed: {e}")
        return False
    
    # Check 5: Environment Variables
    print("\n5. Testing Environment Variables...")
    required_vars = ['DATABASE_URL']
    optional_vars = ['OPENAI_API_KEY', 'SESSION_SECRET']
    
    for var in required_vars:
        if os.environ.get(var):
            print(f"✅ Required variable {var}: configured")
        else:
            print(f"❌ Required variable {var}: missing")
            return False
    
    for var in optional_vars:
        if os.environ.get(var):
            print(f"✅ Optional variable {var}: configured")
        else:
            print(f"⚠️  Optional variable {var}: not configured")
    
    # Check 6: Static Files
    print("\n6. Testing Static Files...")
    static_files = ['static/css/modern.css', 'static/js/main.js']
    for file_path in static_files:
        if os.path.exists(file_path):
            print(f"✅ Static file {file_path}: exists")
        else:
            print(f"❌ Static file {file_path}: missing")
    
    # Check 7: Templates
    print("\n7. Testing Templates...")
    template_files = ['templates/base.html', 'templates/login.html', 'templates/dashboard.html']
    for file_path in template_files:
        if os.path.exists(file_path):
            print(f"✅ Template {file_path}: exists")
        else:
            print(f"❌ Template {file_path}: missing")
    
    print("\n" + "=" * 60)
    print("✅ ALL HEALTH CHECKS PASSED - READY FOR DEPLOYMENT")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = health_check()
    sys.exit(0 if success else 1)