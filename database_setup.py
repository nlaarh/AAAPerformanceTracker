#!/usr/bin/env python3
"""
Database Setup Script for Development and Production Environments
Creates separate databases with identical schema and data
"""

import os
import sys
import subprocess
from urllib.parse import urlparse
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import sessionmaker

def parse_database_url(url):
    """Parse PostgreSQL URL into components"""
    parsed = urlparse(url)
    return {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'user': parsed.username,
        'password': parsed.password,
        'database': parsed.path[1:],  # Remove leading slash
        'scheme': parsed.scheme
    }

def create_database_url(host, port, user, password, database):
    """Create PostgreSQL URL from components"""
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"

def run_command(cmd, env=None):
    """Run shell command with error handling"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
        if result.returncode != 0:
            print(f"Error running command: {cmd}")
            print(f"Error output: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Exception running command: {cmd}")
        print(f"Exception: {e}")
        return False

def create_development_database():
    """Create development database with same schema and data as production - SAFE VERSION"""
    
    # Get production database URL
    prod_url = os.environ.get('DATABASE_URL')
    if not prod_url:
        print("ERROR: DATABASE_URL environment variable not found")
        return False
    
    # Parse production URL
    prod_db = parse_database_url(prod_url)
    
    # Create development database name
    dev_database = f"{prod_db['database']}_development"
    
    print(f"🔒 SAFE MODE: Creating development database: {dev_database}")
    print(f"📊 Based on production database: {prod_db['database']}")
    print(f"⚠️  IMPORTANT: This will NOT overwrite any existing development data")
    
    # Create development database URL
    dev_url = create_database_url(
        prod_db['host'], 
        prod_db['port'], 
        prod_db['user'], 
        prod_db['password'], 
        dev_database
    )
    
    # Set environment for PostgreSQL commands
    pg_env = os.environ.copy()
    pg_env['PGPASSWORD'] = prod_db['password']
    
    # Create development database (only if it doesn't exist)
    create_db_cmd = f"createdb -h {prod_db['host']} -p {prod_db['port']} -U {prod_db['user']} {dev_database}"
    print(f"Creating database (if it doesn't exist): {create_db_cmd}")
    
    if not run_command(create_db_cmd, pg_env):
        print("✅ Database already exists - preserving existing data")
    
    # Use Python to safely copy data (without overwriting)
    print("🔄 Using Python SQLAlchemy to safely copy database structure and data...")
    return copy_database_with_python(prod_url, dev_url)

def copy_database_with_python(source_url, target_url):
    """Copy database using Python SQLAlchemy"""
    try:
        # Create engines
        source_engine = create_engine(source_url)
        target_engine = create_engine(target_url)
        
        # Copy schema using our existing models
        print("Copying schema...")
        from app import app, db
        
        with app.app_context():
            # Create all tables in target database
            db.create_all()
            print("✅ Schema copied successfully")
            
            # Copy data table by table
            print("Copying data...")
            
            # Get table names from metadata
            metadata = MetaData()
            metadata.reflect(bind=source_engine)
            
            # Copy data for each table
            for table_name in metadata.tables:
                print(f"Copying table: {table_name}")
                
                # Read from source
                with source_engine.connect() as source_conn:
                    result = source_conn.execute(text(f"SELECT * FROM {table_name}"))
                    rows = result.fetchall()
                    columns = result.keys()
                
                # Write to target (only if target table is empty - NEVER delete existing data)
                if rows:
                    with target_engine.connect() as target_conn:
                        # Check if target table has data
                        existing_count = target_conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                        
                        if existing_count > 0:
                            print(f"⚠️  Table {table_name} has {existing_count} existing rows - SKIPPING to preserve data")
                            continue
                        
                        # Only insert if table is empty
                        print(f"Table {table_name} is empty - safe to copy data")
                        
                        # Insert data
                        for row in rows:
                            column_names = ', '.join(columns)
                            placeholders = ', '.join([f":{col}" for col in columns])
                            insert_sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
                            
                            row_dict = dict(zip(columns, row))
                            target_conn.execute(text(insert_sql), row_dict)
                        
                        target_conn.commit()
                
                print(f"✅ Copied {len(rows)} rows from {table_name}")
            
            print("✅ All data copied successfully")
            return True
            
    except Exception as e:
        print(f"Error copying database: {e}")
        return False
    
    # Restore to development database
    restore_cmd = f"psql -h {prod_db['host']} -p {prod_db['port']} -U {prod_db['user']} -d {dev_database} < development_full_dump.sql"
    print(f"Restoring to development database: {restore_cmd}")
    
    if not run_command(restore_cmd, pg_env):
        print("Failed to restore to development database")
        return False
    
    print(f"\n✅ Development database created successfully!")
    print(f"Production Database URL: {prod_url}")
    print(f"Development Database URL: {dev_url}")
    
    # Save URLs to environment file
    with open('.env.development', 'w') as f:
        f.write(f"DATABASE_URL={dev_url}\n")
        f.write(f"PRODUCTION_DATABASE_URL={prod_url}\n")
    
    print(f"\n📁 Database URLs saved to .env.development file")
    print(f"\n🔧 To use development database, set:")
    print(f"   export DATABASE_URL='{dev_url}'")
    print(f"\n🔧 To use production database, set:")
    print(f"   export DATABASE_URL='{prod_url}'")
    
    return True

def sync_databases():
    """Sync development database with production data"""
    print("Syncing development database with production...")
    
    # Load environment file
    if os.path.exists('.env.development'):
        with open('.env.development', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    prod_url = os.environ.get('PRODUCTION_DATABASE_URL')
    dev_url = os.environ.get('DATABASE_URL')
    
    if not prod_url or not dev_url:
        print("ERROR: Database URLs not found in environment")
        return False
    
    prod_db = parse_database_url(prod_url)
    dev_db = parse_database_url(dev_url)
    
    pg_env = os.environ.copy()
    pg_env['PGPASSWORD'] = prod_db['password']
    
    # Dump production data
    dump_cmd = f"pg_dump -h {prod_db['host']} -p {prod_db['port']} -U {prod_db['user']} {prod_db['database']} > sync_dump.sql"
    print(f"Dumping production data...")
    
    if not run_command(dump_cmd, pg_env):
        print("Failed to dump production database")
        return False
    
    # NEVER drop development database to preserve data
    print("⚠️  SAFETY: Development database will NOT be dropped to preserve existing data")
    print("⚠️  If you want to completely refresh development data, manually drop the database first")
    
    pg_env['PGPASSWORD'] = dev_db['password']
    
    # Restore to development
    restore_cmd = f"psql -h {dev_db['host']} -p {dev_db['port']} -U {dev_db['user']} -d {dev_db['database']} < sync_dump.sql"
    print(f"Restoring to development database...")
    
    if not run_command(restore_cmd, pg_env):
        print("Failed to restore to development database")
        return False
    
    print("✅ Development database synced with production!")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sync":
        sync_databases()
    else:
        create_development_database()