#!/usr/bin/env python3
"""
Force copy all users from production to development database
This will overwrite existing users in development
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
    
    print("🔄 Force copying all users from production to development...")
    print("⚠️  This will overwrite existing users in development database")
    
    # Create engines
    prod_engine = create_engine(prod_url)
    dev_engine = create_engine(dev_url)
    
    # Get all users from production
    with prod_engine.connect() as prod_conn:
        result = prod_conn.execute(text("SELECT * FROM \"user\""))
        users = result.fetchall()
        columns = result.keys()
    
    print(f"Found {len(users)} users in production database")
    
    # Clear and copy users
    with dev_engine.connect() as dev_conn:
        # Clear existing users
        dev_conn.execute(text("DELETE FROM \"user\""))
        print("Cleared existing users from development database")
        
        # Insert all users from production
        for user in users:
            column_names = ', '.join([f'"{col}"' for col in columns])
            placeholders = ', '.join([f':{col}' for col in columns])
            insert_sql = f'INSERT INTO "user" ({column_names}) VALUES ({placeholders})'
            
            # Convert row to dict
            user_dict = {}
            for i, col in enumerate(columns):
                user_dict[col] = user[i]
            
            dev_conn.execute(text(insert_sql), user_dict)
        
        dev_conn.commit()
        print(f"✅ Copied {len(users)} users to development database")
    
    print("✅ User copy complete! Now run copy_database.py again")

if __name__ == "__main__":
    main()