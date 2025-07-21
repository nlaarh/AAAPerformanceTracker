#!/usr/bin/env python3
"""
Environment Configuration for Development vs Production
"""

import os

def get_environment_config():
    """Get database configuration based on environment"""
    
    # Check if we're in development mode
    is_development = os.environ.get('ENVIRONMENT') == 'development'
    
    if is_development:
        # Use development database
        dev_db_url = os.environ.get('DEV_DATABASE_URL')
        if dev_db_url:
            print("🔧 Using DEVELOPMENT database")
            return dev_db_url
        else:
            print("⚠️  DEV_DATABASE_URL not set, falling back to production")
    
    # Use production database (default)
    prod_db_url = os.environ.get('DATABASE_URL')
    print("🏭 Using PRODUCTION database")
    return prod_db_url

def set_development_mode():
    """Set environment to development mode"""
    os.environ['ENVIRONMENT'] = 'development'
    print("✅ Environment set to DEVELOPMENT")

def set_production_mode():
    """Set environment to production mode"""
    os.environ['ENVIRONMENT'] = 'production'
    print("✅ Environment set to PRODUCTION")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'dev':
            set_development_mode()
        elif sys.argv[1] == 'prod':
            set_production_mode()
        else:
            print("Usage: python environment_config.py [dev|prod]")
    else:
        print(f"Current database: {get_environment_config()}")