#!/usr/bin/env python3
"""
Copy Production Database to Development Database
Safe script that creates exact copy without deleting existing data
"""

import os
import sys
from sqlalchemy import create_engine, text, MetaData
from urllib.parse import urlparse

def main():
    print("Creating development database as exact copy of production...")
    
    # Load environment variables
    if os.path.exists('.env.development'):
        with open('.env.development', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    dev_url = os.environ.get('DEV_DATABASE_URL')
    prod_url = os.environ.get('PRODUCTION_DATABASE_URL')
    
    if not dev_url or not prod_url:
        print("Error: Database URLs not found in environment")
        return False
    
    print(f"Production: {prod_url.split('@')[1].split('?')[0]}")
    print(f"Development: {dev_url.split('@')[1].split('?')[0]}")
    
    # Create engines
    prod_engine = create_engine(prod_url)
    dev_engine = create_engine(dev_url)
    
    try:
        # First, create all tables in development database
        from app import app, db
        with app.app_context():
            # Temporarily point to development database
            original_uri = app.config['SQLALCHEMY_DATABASE_URI']
            app.config['SQLALCHEMY_DATABASE_URI'] = dev_url
            db.engine.dispose()
            db.create_all()
            print("✅ Schema created in development database")
            
            # Restore original URI
            app.config['SQLALCHEMY_DATABASE_URI'] = original_uri
            db.engine.dispose()
        
        # Get all table names from production
        metadata = MetaData()
        metadata.reflect(bind=prod_engine)
        all_tables = list(metadata.tables.keys())
        print(f"Found {len(all_tables)} tables to copy")
        
        # Order tables by dependency (parent tables first)
        ordered_tables = [
            'user', 'category', 'assessment_period', 'assessment_form', 'assessment_question',
            'period_form_assignment', 'period_reviewee', 'period_reviewer', 
            'assessment_assignment', 'assessment', 'assessment_response', 'category_rating',
            'question_response', 'activity_log', 'ai_report', 'ai_analysis'
        ]
        
        # Add any remaining tables not in ordered list
        remaining_tables = [t for t in all_tables if t not in ordered_tables]
        tables = ordered_tables + remaining_tables
        
        # Copy data for each table in dependency order
        for table_name in tables:
            if table_name not in all_tables:
                continue  # Skip if table doesn't exist
            print(f"Copying table: {table_name}")
            
            # Get data from production
            with prod_engine.connect() as prod_conn:
                result = prod_conn.execute(text(f"SELECT * FROM {table_name}"))
                rows = result.fetchall()
                if rows:
                    columns = result.keys()
                else:
                    columns = []
            
            if rows:
                # Check if development table is empty
                with dev_engine.connect() as dev_conn:
                    count_result = dev_conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    existing_count = count_result.scalar()
                    
                    if existing_count == 0:
                        # Clear existing data in dev table first (for fresh copy)
                        dev_conn.execute(text(f"DELETE FROM {table_name}"))
                        
                        # Insert data
                        for row in rows:
                            column_names = ', '.join([f'"{col}"' for col in columns])
                            placeholders = ', '.join([f':{col}' for col in columns])
                            insert_sql = f'INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})'
                            
                            # Convert row to dict
                            row_dict = {}
                            for i, col in enumerate(columns):
                                row_dict[col] = row[i]
                            
                            dev_conn.execute(text(insert_sql), row_dict)
                        
                        dev_conn.commit()
                        print(f"✅ Copied {len(rows)} rows to {table_name}")
                    else:
                        print(f"⚠️  {table_name} already has {existing_count} rows - skipping to preserve data")
            else:
                print(f"📭 {table_name} is empty")
        
        print("\n✅ Development database created as exact copy of production!")
        return True
        
    except Exception as e:
        print(f"❌ Error copying database: {e}")
        return False

if __name__ == "__main__":
    main()