#!/usr/bin/env python3
"""
Simple Database Setup Script
Creates development database from production (SAFE - never deletes existing data)
"""

import os
import sys
from database_setup import create_development_database

def main():
    print("=" * 60)
    print("🔧 Database Setup for Development and Production")
    print("=" * 60)
    
    print("\n📋 What this script does:")
    print("✅ Creates a NEW development database")
    print("✅ Copies schema and data FROM production")
    print("✅ NEVER deletes any existing data")
    print("✅ Sets up environment variables for easy switching")
    
    print("\n📊 Current setup:")
    prod_url = os.environ.get('DATABASE_URL')
    if prod_url:
        print(f"Production database: {prod_url.split('@')[1] if '@' in prod_url else 'configured'}")
    else:
        print("❌ No production database URL found")
        return
    
    print("\n🔄 Creating development database...")
    
    if create_development_database():
        print("\n✅ Development database setup complete!")
        
        # Load the created environment file
        if os.path.exists('.env.development'):
            with open('.env.development', 'r') as f:
                content = f.read()
                for line in content.split('\n'):
                    if line.startswith('DATABASE_URL='):
                        dev_url = line.split('=', 1)[1]
                        print(f"Development database: {dev_url.split('@')[1] if '@' in dev_url else 'configured'}")
        
        print("\n🎯 How to switch between databases:")
        print("For DEVELOPMENT:")
        print("  export ENVIRONMENT=development")
        print("  export DEV_DATABASE_URL=<your_dev_database_url>")
        print("\nFor PRODUCTION:")
        print("  export ENVIRONMENT=production")
        print("  (or just remove ENVIRONMENT variable)")
        
        print("\n🔧 Quick commands:")
        print("  python environment_config.py dev   # Switch to development")
        print("  python environment_config.py prod  # Switch to production")
        
    else:
        print("\n❌ Failed to create development database")

if __name__ == "__main__":
    main()