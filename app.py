import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging - use INFO level for production
logging.basicConfig(level=logging.INFO)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "AAA-Performance-Tracker-Secret-Key-2025"
app.config['WTF_CSRF_ENABLED'] = False
app.config['SESSION_COOKIE_SECURE'] = False  # Disable for development compatibility
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database with environment awareness
def get_database_url():
    """Get database URL based on environment"""
    # Check for development mode
    if os.environ.get('ENVIRONMENT') == 'development':
        dev_url = os.environ.get('DEV_DATABASE_URL')
        if dev_url:
            logging.info("Using DEVELOPMENT database")
            return dev_url
    
    # Default to production
    prod_url = os.environ.get('DATABASE_URL')
    if prod_url:
        logging.info("Using PRODUCTION database")
        return prod_url
    
    # Fallback for local development
    return "sqlite:///performance_tracker.db"

database_url = get_database_url()

# Handle PostgreSQL URL format for SQLAlchemy 2.0
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)
# csrf = CSRFProtect(app)  # Disabled for now
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Import routes after app initialization
from routes import *

# Lazy initialization - only run when needed, not at import time
def init_database():
    """Initialize database tables and default data - run only when needed"""
    try:
        with app.app_context():
            import models
            db.create_all()
            from utils import initialize_default_data
            initialize_default_data()
        return True
    except Exception as e:
        app.logger.error(f"Database initialization failed: {e}")
        return False

# Health check endpoint for deployment
@app.route('/health')
def health_check():
    """Health check endpoint for deployment monitoring"""
    try:
        # Test database connection
        with app.app_context():
            db.session.execute(text("SELECT 1"))
        return {'status': 'healthy', 'database': 'connected'}, 200
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}, 500

# Context processor for pending assignments count
@app.context_processor
def inject_pending_assignments():
    from flask_login import current_user
    if current_user.is_authenticated and current_user.role in ['board_member', 'admin', 'officer']:
        from models import AssessmentAssignment, AssessmentPeriod
        from sqlalchemy import or_
        
        # Count pending assignments based on user role
        if current_user.role == 'officer':
            # Officers only count their self-assessment tasks (where they are both officer and reviewer)
            pending_count = AssessmentAssignment.query.filter(
                AssessmentAssignment.officer_id == current_user.id,
                AssessmentAssignment.reviewer_id == current_user.id,
                AssessmentAssignment.is_completed == False
            ).join(AssessmentPeriod).filter(AssessmentPeriod.is_active == True).count()
        else:
            # Board members and admins count assignments where they are reviewers
            # Only count assignments where officer's self-assessment is approved
            pending_count = 0
            raw_assignments = AssessmentAssignment.query.filter(
                AssessmentAssignment.reviewer_id == current_user.id,
                AssessmentAssignment.officer_id != current_user.id,  # Exclude self-assessments
                AssessmentAssignment.is_completed == False
            ).join(AssessmentPeriod).filter(AssessmentPeriod.is_active == True).all()
            
            # Count only assignments where officer's self-assessment is approved
            for assignment in raw_assignments:
                officer_self = AssessmentAssignment.query.filter_by(
                    officer_id=assignment.officer_id,
                    reviewer_id=assignment.officer_id,
                    period_id=assignment.period_id
                ).first()
                if officer_self and officer_self.is_admin_approved:
                    pending_count += 1
        
        # Admin pending count for approval tasks
        admin_pending_count = 0
        if current_user.role == 'admin':
            admin_pending_count = AssessmentAssignment.query.filter_by(
                is_submitted=True,
                is_admin_approved=False
            ).count()
        
        return dict(pending_assignments_count=pending_count, admin_pending_count=admin_pending_count)
    return dict(pending_assignments_count=0, admin_pending_count=0)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
