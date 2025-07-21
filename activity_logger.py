from flask import request
from app import db
from models import ActivityLog
from datetime import datetime

def log_activity(user_id, action, description=None):
    """Log user activity with IP address and user agent"""
    try:
        activity = ActivityLog(
            user_id=user_id,
            action=action,
            description=description,
            ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
            user_agent=request.environ.get('HTTP_USER_AGENT', 'Unknown')
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        print(f"Error logging activity: {e}")
        db.session.rollback()

def get_activity_logs(limit=100):
    """Get recent activity logs for admin view"""
    return ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(limit).all()

def get_user_activity_logs(user_id, limit=50):
    """Get activity logs for a specific user"""
    return ActivityLog.query.filter_by(user_id=user_id).order_by(ActivityLog.timestamp.desc()).limit(limit).all()