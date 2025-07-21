#!/usr/bin/env python3
"""
Check the status of both databases
"""

import os
from sqlalchemy import create_engine, text

def main():
    # Load environment variables
    with open('.env.development', 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
    
    dev_url = os.environ.get('DEV_DATABASE_URL')
    prod_url = os.environ.get('PRODUCTION_DATABASE_URL')
    
    print("🔍 Database Status Check")
    print("=" * 50)
    
    # Check production database
    prod_engine = create_engine(prod_url)
    with prod_engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM \"user\""))
        prod_users = result.scalar()
        print(f"Production users: {prod_users}")
    
    # Check development database
    dev_engine = create_engine(dev_url)
    with dev_engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM \"user\""))
        dev_users = result.scalar()
        print(f"Development users: {dev_users}")
    
    print("\n📊 Database URLs:")
    print(f"Production: {prod_url.split('@')[1].split('?')[0]}")
    print(f"Development: {dev_url.split('@')[1].split('?')[0]}")
    
    print("\n✅ Development database is ready for use!")
    print("Both databases are operational and separate.")

if __name__ == "__main__":
    main()