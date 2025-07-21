"""
Enhanced Assessment Activity Logger
Comprehensive logging system for assessment workflow events
"""
from flask import request
from app import db
from models import AssessmentActivityLog, User, AssessmentPeriod, AssessmentAssignment
from datetime import datetime
import json

class AssessmentEvents:
    """Define all assessment event types"""
    # Assignment Events
    SELF_ASSESSMENT_ASSIGNED = 'self_assessment_assigned'
    REVIEWER_ASSIGNMENT_CREATED = 'reviewer_assignment_created'
    ASSIGNMENT_NOTIFICATION_SENT = 'assignment_notification_sent'
    
    # Self-Assessment Events
    SELF_ASSESSMENT_STARTED = 'self_assessment_started'
    SELF_ASSESSMENT_DRAFT_SAVED = 'self_assessment_draft_saved'
    SELF_ASSESSMENT_SUBMITTED = 'self_assessment_submitted'
    
    # Admin Review Events
    ADMIN_REVIEW_STARTED = 'admin_review_started'
    SELF_ASSESSMENT_APPROVED = 'self_assessment_approved'
    SELF_ASSESSMENT_REJECTED = 'self_assessment_rejected'
    REVIEWERS_RELEASED = 'reviewers_released'
    
    # Reviewer Events
    REVIEWER_NOTIFIED = 'reviewer_notified'
    REVIEWER_ASSESSMENT_STARTED = 'reviewer_assessment_started'
    REVIEWER_DRAFT_SAVED = 'reviewer_draft_saved'
    REVIEWER_ASSESSMENT_SUBMITTED = 'reviewer_assessment_submitted'
    
    # Final Review Events
    ALL_REVIEWERS_COMPLETED = 'all_reviewers_completed'
    FINAL_ADMIN_REVIEW_STARTED = 'final_admin_review_started'
    ASSESSMENT_APPROVED_FINAL = 'assessment_approved_final'
    
    # Results Events
    RESULTS_RELEASED_TO_REVIEWEE = 'results_released_to_reviewee'
    REVIEWEE_ACKNOWLEDGED_RESULTS = 'reviewee_acknowledged_results'
    ASSESSMENT_CLOSED = 'assessment_closed'
    
    # AI/Report Events
    AI_REPORT_GENERATION_STARTED = 'ai_report_generation_started'
    AI_REPORT_GENERATED = 'ai_report_generated'
    AI_REPORT_FAILED = 'ai_report_failed'

class AssessmentCategories:
    """Define event categories"""
    ASSIGNMENT = 'assignment'
    SUBMISSION = 'submission'
    APPROVAL = 'approval'
    NOTIFICATION = 'notification'
    AI_PROCESSING = 'ai_processing'
    RESULTS = 'results'

def log_assessment_event(event_type, officer_id, period_id, actor_id, description, 
                        reviewer_id=None, assignment_id=None, metadata=None, event_status='completed'):
    """
    Log assessment workflow events with comprehensive context
    
    Args:
        event_type: Type of event (use AssessmentEvents constants)
        officer_id: ID of the officer being assessed
        period_id: ID of the assessment period
        actor_id: ID of the user performing the action
        description: Human-readable description of the event
        reviewer_id: ID of reviewer (for reviewer-specific events)
        assignment_id: ID of the assignment (if applicable)
        metadata: Dictionary of additional event data
        event_status: Status of the event ('completed', 'pending', 'failed')
    """
    try:
        # Check for duplicate entries within the last 5 seconds to prevent spam
        from datetime import datetime, timedelta
        recent_threshold = datetime.utcnow() - timedelta(seconds=5)
        
        existing_log = AssessmentActivityLog.query.filter(
            AssessmentActivityLog.event_type == event_type,
            AssessmentActivityLog.officer_id == officer_id,
            AssessmentActivityLog.actor_id == actor_id,
            AssessmentActivityLog.timestamp >= recent_threshold
        ).first()
        
        if existing_log:
            print(f"Skipping duplicate log entry: {event_type} for officer {officer_id} by actor {actor_id}")
            return existing_log
        
        # Determine event category
        category_map = {
            # Assignment category events
            AssessmentEvents.SELF_ASSESSMENT_ASSIGNED: AssessmentCategories.ASSIGNMENT,
            AssessmentEvents.REVIEWER_ASSIGNMENT_CREATED: AssessmentCategories.ASSIGNMENT,
            AssessmentEvents.ASSIGNMENT_NOTIFICATION_SENT: AssessmentCategories.NOTIFICATION,
            AssessmentEvents.REVIEWER_NOTIFIED: AssessmentCategories.NOTIFICATION,
            
            # Submission category events
            AssessmentEvents.SELF_ASSESSMENT_STARTED: AssessmentCategories.SUBMISSION,
            AssessmentEvents.SELF_ASSESSMENT_DRAFT_SAVED: AssessmentCategories.SUBMISSION,
            AssessmentEvents.SELF_ASSESSMENT_SUBMITTED: AssessmentCategories.SUBMISSION,
            AssessmentEvents.REVIEWER_ASSESSMENT_STARTED: AssessmentCategories.SUBMISSION,
            AssessmentEvents.REVIEWER_DRAFT_SAVED: AssessmentCategories.SUBMISSION,
            AssessmentEvents.REVIEWER_ASSESSMENT_SUBMITTED: AssessmentCategories.SUBMISSION,
            
            # Approval category events
            AssessmentEvents.ADMIN_REVIEW_STARTED: AssessmentCategories.APPROVAL,
            AssessmentEvents.SELF_ASSESSMENT_APPROVED: AssessmentCategories.APPROVAL,
            AssessmentEvents.SELF_ASSESSMENT_REJECTED: AssessmentCategories.APPROVAL,
            AssessmentEvents.REVIEWERS_RELEASED: AssessmentCategories.APPROVAL,
            AssessmentEvents.FINAL_ADMIN_REVIEW_STARTED: AssessmentCategories.APPROVAL,
            AssessmentEvents.ASSESSMENT_APPROVED_FINAL: AssessmentCategories.APPROVAL,
            
            # Results category events
            AssessmentEvents.RESULTS_RELEASED_TO_REVIEWEE: AssessmentCategories.RESULTS,
            AssessmentEvents.REVIEWEE_ACKNOWLEDGED_RESULTS: AssessmentCategories.RESULTS,
            AssessmentEvents.ASSESSMENT_CLOSED: AssessmentCategories.RESULTS,
            
            # AI Processing events
            AssessmentEvents.AI_REPORT_GENERATION_STARTED: AssessmentCategories.AI_PROCESSING,
            AssessmentEvents.AI_REPORT_GENERATED: AssessmentCategories.AI_PROCESSING,
            AssessmentEvents.AI_REPORT_FAILED: AssessmentCategories.AI_PROCESSING,
        }
        
        event_category = category_map.get(event_type, 'other')
        
        # Create activity log entry with explicit timestamp
        from datetime import datetime
        activity = AssessmentActivityLog(
            event_type=event_type,
            event_category=event_category,
            officer_id=officer_id,
            period_id=period_id,
            reviewer_id=reviewer_id,
            assignment_id=assignment_id,
            description=description,
            event_status=event_status,
            actor_id=actor_id,
            timestamp=datetime.utcnow(),  # Explicit timestamp for every event
            ip_address=request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr) if request else None,
            user_agent=request.environ.get('HTTP_USER_AGENT', 'System') if request else 'System'
        )
        
        if metadata:
            activity.set_event_data(metadata)
        
        db.session.add(activity)
        db.session.commit()
        
        return activity
        
    except Exception as e:
        print(f"Error logging assessment activity: {e}")
        db.session.rollback()
        return None

def get_assessment_activity_logs(officer_id=None, period_id=None, reviewer_id=None, event_category=None, user_id=None, event_type=None, limit=100):
    """Get assessment activity logs with optional filtering"""
    query = AssessmentActivityLog.query
    
    # Support both officer_id and user_id parameters for compatibility
    if officer_id:
        query = query.filter_by(officer_id=officer_id)
    elif user_id:
        query = query.filter_by(officer_id=user_id)
        
    if period_id:
        query = query.filter_by(period_id=period_id)
    if reviewer_id:
        query = query.filter_by(reviewer_id=reviewer_id)
    if event_category:
        query = query.filter_by(event_category=event_category)
    if event_type and event_type.strip():
        query = query.filter_by(event_type=event_type)
    
    return query.order_by(AssessmentActivityLog.timestamp.desc()).limit(limit).all()

def get_assessment_timeline(officer_id, period_id):
    """Get complete assessment timeline for a specific officer and period"""
    activities = AssessmentActivityLog.query.filter_by(
        officer_id=officer_id,
        period_id=period_id
    ).order_by(AssessmentActivityLog.timestamp.asc()).all()
    
    timeline = []
    for activity in activities:
        timeline.append({
            'timestamp': activity.timestamp,
            'event_type': activity.event_type,
            'event_category': activity.event_category,
            'description': activity.description,
            'actor': activity.actor.name if activity.actor else 'System',
            'reviewer': activity.reviewer.name if activity.reviewer else None,
            'status': activity.event_status,
            'metadata': activity.get_event_data()
        })
    
    return timeline

def get_assessment_progress_summary(officer_id, period_id):
    """Get assessment progress summary with key milestones"""
    activities = get_assessment_timeline(officer_id, period_id)
    
    milestones = {
        'self_assessment_assigned': None,
        'self_assessment_submitted': None,
        'self_assessment_approved': None,
        'reviewers_released': None,
        'all_reviewers_completed': None,
        'final_approval': None,
        'results_released': None,
        'reviewee_acknowledged': None,
        'assessment_closed': None
    }
    
    for activity in activities:
        event_type = activity['event_type']
        if event_type == AssessmentEvents.SELF_ASSESSMENT_ASSIGNED:
            milestones['self_assessment_assigned'] = activity
        elif event_type == AssessmentEvents.SELF_ASSESSMENT_SUBMITTED:
            milestones['self_assessment_submitted'] = activity
        elif event_type == AssessmentEvents.SELF_ASSESSMENT_APPROVED:
            milestones['self_assessment_approved'] = activity
        elif event_type == AssessmentEvents.REVIEWERS_RELEASED:
            milestones['reviewers_released'] = activity
        elif event_type == AssessmentEvents.ALL_REVIEWERS_COMPLETED:
            milestones['all_reviewers_completed'] = activity
        elif event_type == AssessmentEvents.ASSESSMENT_APPROVED_FINAL:
            milestones['final_approval'] = activity
        elif event_type == AssessmentEvents.RESULTS_RELEASED_TO_REVIEWEE:
            milestones['results_released'] = activity
        elif event_type == AssessmentEvents.REVIEWEE_ACKNOWLEDGED_RESULTS:
            milestones['reviewee_acknowledged'] = activity
        elif event_type == AssessmentEvents.ASSESSMENT_CLOSED:
            milestones['assessment_closed'] = activity
    
    return {
        'milestones': milestones,
        'total_events': len(activities),
        'timeline': activities
    }

# Convenience functions for common logging scenarios
def log_self_assessment_assigned(officer_id, period_id, actor_id, assignment_id):
    """Log when self-assessment is assigned"""
    return log_assessment_event(
        AssessmentEvents.SELF_ASSESSMENT_ASSIGNED,
        officer_id=officer_id,
        period_id=period_id,
        actor_id=actor_id,
        description=f"Self-assessment task assigned",
        assignment_id=assignment_id
    )

def log_reviewer_assignment_created(officer_id, period_id, reviewer_id, actor_id, assignment_id):
    """Log when reviewer assignment is created"""
    return log_assessment_event(
        AssessmentEvents.REVIEWER_ASSIGNMENT_CREATED,
        officer_id=officer_id,
        period_id=period_id,
        actor_id=actor_id,
        reviewer_id=reviewer_id,
        description=f"Reviewer assignment created",
        assignment_id=assignment_id
    )

def log_assessment_draft_saved(officer_id, period_id, actor_id, assignment_id, is_self_assessment=False):
    """Log when assessment draft is saved"""
    event_type = AssessmentEvents.SELF_ASSESSMENT_DRAFT_SAVED if is_self_assessment else AssessmentEvents.REVIEWER_DRAFT_SAVED
    description = "Self-assessment draft saved" if is_self_assessment else "Reviewer assessment draft saved"
    
    return log_assessment_event(
        event_type,
        officer_id=officer_id,
        period_id=period_id,
        actor_id=actor_id,
        description=description,
        assignment_id=assignment_id
    )

def log_assessment_submitted(officer_id, period_id, actor_id, assignment_id, is_self_assessment=False):
    """Log when assessment is submitted"""
    event_type = AssessmentEvents.SELF_ASSESSMENT_SUBMITTED if is_self_assessment else AssessmentEvents.REVIEWER_ASSESSMENT_SUBMITTED
    description = "Self-assessment submitted for admin review" if is_self_assessment else "Reviewer assessment submitted"
    
    return log_assessment_event(
        event_type,
        officer_id=officer_id,
        period_id=period_id,
        actor_id=actor_id,
        description=description,
        assignment_id=assignment_id
    )

def log_admin_approval(officer_id, period_id, actor_id, approved=True, stage='self_assessment'):
    """Log admin approval/rejection actions"""
    if stage == 'self_assessment':
        event_type = AssessmentEvents.SELF_ASSESSMENT_APPROVED if approved else AssessmentEvents.SELF_ASSESSMENT_REJECTED
        description = f"Self-assessment {'approved' if approved else 'rejected'} by admin"
    elif stage == 'final_assessment':
        event_type = AssessmentEvents.ASSESSMENT_APPROVED_FINAL if approved else AssessmentEvents.SELF_ASSESSMENT_REJECTED
        description = f"Final assessment {'approved' if approved else 'rejected'} by admin"
    else:
        event_type = AssessmentEvents.ASSESSMENT_APPROVED_FINAL
        description = "Assessment approved by admin"
    
    return log_assessment_event(
        event_type,
        officer_id=officer_id,
        period_id=period_id,
        actor_id=actor_id,
        description=description
    )

def log_results_released(officer_id, period_id, actor_id):
    """Log when results are released to reviewee"""
    return log_assessment_event(
        AssessmentEvents.RESULTS_RELEASED_TO_REVIEWEE,
        officer_id=officer_id,
        period_id=period_id,
        actor_id=actor_id,
        description="Assessment results released to reviewee"
    )

def log_comprehensive_event(event_type, officer_id, period_id, actor_id, description, **kwargs):
    """
    Comprehensive event logging with automatic timestamp tracking
    
    This is a convenience function that ensures every event is logged with:
    - Explicit timestamp (datetime.utcnow())
    - Complete metadata tracking
    - Proper error handling
    - IP address and user agent tracking
    """
    from datetime import datetime
    
    # Add current timestamp to metadata for detailed tracking
    metadata = kwargs.get('metadata', {})
    metadata['logged_at'] = datetime.utcnow().isoformat()
    metadata['event_source'] = 'assessment_activity_logger'
    
    # Update kwargs with enhanced metadata
    kwargs['metadata'] = metadata
    
    return log_assessment_event(
        event_type=event_type,
        officer_id=officer_id,
        period_id=period_id,
        actor_id=actor_id,
        description=description,
        **kwargs
    )

def get_event_statistics(period_id=None):
    """Get comprehensive event statistics with timestamp analysis"""
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    query = AssessmentActivityLog.query
    if period_id:
        query = query.filter_by(period_id=period_id)
    
    # Get event type distribution
    event_counts = query.with_entities(
        AssessmentActivityLog.event_type,
        func.count(AssessmentActivityLog.id).label('count')
    ).group_by(AssessmentActivityLog.event_type).all()
    
    # Get events by day for the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_events = query.filter(
        AssessmentActivityLog.timestamp >= thirty_days_ago
    ).with_entities(
        func.date(AssessmentActivityLog.timestamp).label('date'),
        func.count(AssessmentActivityLog.id).label('count')
    ).group_by(func.date(AssessmentActivityLog.timestamp)).all()
    
    return {
        'event_counts': dict(event_counts),
        'recent_activity': {str(date): count for date, count in recent_events},
        'total_events': query.count(),
        'period_filter': period_id
    }