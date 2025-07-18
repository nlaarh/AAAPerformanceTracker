from app import app, init_database

# Initialize database on application startup
init_database()

if __name__ == '__main__':
    # For development only
    app.run(host='0.0.0.0', port=5000, debug=True)
