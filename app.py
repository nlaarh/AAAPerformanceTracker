import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "AAA-Performance-Tracker-Secret-Key-2025"
app.config['WTF_CSRF_ENABLED'] = False
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///performance_tracker.db")
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

with app.app_context():
    # Import models to ensure tables are created
    import models
    db.create_all()
    
    # Initialize default data
    from utils import initialize_default_data
    initialize_default_data()

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
            pending_count = AssessmentAssignment.query.filter(
                AssessmentAssignment.reviewer_id == current_user.id,
                AssessmentAssignment.is_completed == False
            ).join(AssessmentPeriod).filter(AssessmentPeriod.is_active == True).count()
        
        return dict(pending_assignments_count=pending_count)
    return dict(pending_assignments_count=0)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
