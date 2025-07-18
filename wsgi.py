"""
WSGI entry point for production deployment
"""
import os
import sys
import logging

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

try:
    from app import app as application, init_database
    logging.info("Application loaded successfully")
    
    # Initialize database for production
    if init_database():
        logging.info("Database initialized successfully")
    else:
        logging.warning("Database initialization failed - continuing with existing schema")
        
except Exception as e:
    logging.error(f"Failed to load application: {e}")
    raise

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000, debug=False)