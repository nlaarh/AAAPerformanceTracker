#!/usr/bin/env python3
"""
Production startup script for AAAPerformanceTracker
Handles all initialization tasks required for deployment
"""

import os
import sys
import logging
import time

def main():
    """Main startup function for production deployment"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s'
    )
    
    logging.info("Starting AAAPerformanceTracker production initialization...")
    
    try:
        # Import the application
        from app import app, init_database
        logging.info("Application modules loaded successfully")
        
        # Initialize database
        start_time = time.time()
        if init_database():
            init_time = time.time() - start_time
            logging.info(f"Database initialized successfully in {init_time:.2f} seconds")
        else:
            logging.warning("Database initialization failed - continuing with existing schema")
        
        # Test health endpoint
        with app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                logging.info("Health check endpoint working correctly")
            else:
                logging.error(f"Health check failed: {response.status_code}")
        
        logging.info("Production initialization completed successfully")
        return True
        
    except Exception as e:
        logging.error(f"Production initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)