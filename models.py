from app import db
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum

class AssessmentStatus(Enum):
    PENDING_SELF_ASSESSMENT = "pending_self_assessment"
    SELF_ASSESSMENT_SUBMITTED = "self_assessment_submitted"
    AWAITING_ADMIN_REVIEW = "awaiting_admin_review"
    ADMIN_REVIEW_COMPLETED = "admin_review_completed"
    AWAITING_REVIEWER_ASSESSMENTS = "awaiting_reviewer_assessments"
    REVIEWER_ASSESSMENTS_IN_PROGRESS = "reviewer_assessments_in_progress"
    REVIEWER_ASSESSMENT_SUBMITTED = "reviewer_assessment_submitted"
    REVIEWER_ASSESSMENTS_COMPLETED = "reviewer_assessments_completed"
    AWAITING_FINAL_ADMIN_APPROVAL = "awaiting_final_admin_approval"
    ASSESSMENT_APPROVED_BY_ADMIN = "assessment_approved_by_admin"
    RESULTS_RELEASED_TO_REVIEWEE = "results_released_to_reviewee"
    REVIEWEE_ACKNOWLEDGED_RESULTS = "reviewee_acknowledged_results"
    ASSESSMENT_CLOSED = "assessment_closed"
    
    @classmethod
    def get_status_display(cls, status):
        status_map = {
            cls.PENDING_SELF_ASSESSMENT: "Pending Self-Assessment",
            cls.SELF_ASSESSMENT_SUBMITTED: "Self-Assessment Submitted",
            cls.AWAITING_ADMIN_REVIEW: "Awaiting Admin Review",
            cls.ADMIN_REVIEW_COMPLETED: "Admin Review Completed",
            cls.AWAITING_REVIEWER_ASSESSMENTS: "Awaiting Reviewer Assessments",
            cls.REVIEWER_ASSESSMENTS_IN_PROGRESS: "Reviewer Assessments In Progress",
            cls.REVIEWER_ASSESSMENT_SUBMITTED: "Reviewer Assessment Submitted",
            cls.REVIEWER_ASSESSMENTS_COMPLETED: "Reviewer Assessments Completed",
            cls.AWAITING_FINAL_ADMIN_APPROVAL: "Awaiting Final Admin Approval",
            cls.ASSESSMENT_APPROVED_BY_ADMIN: "Assessment Approved by Admin",
            cls.RESULTS_RELEASED_TO_REVIEWEE: "Results Released to Reviewee",
            cls.REVIEWEE_ACKNOWLEDGED_RESULTS: "Reviewee Acknowledged Results",
            cls.ASSESSMENT_CLOSED: "Assessment Closed"
        }
        return status_map.get(status, status.value)
    
    @classmethod
    def get_next_status(cls, current_status):
        """Get the next logical status in the workflow"""
        next_status_map = {
            cls.PENDING_SELF_ASSESSMENT: cls.SELF_ASSESSMENT_SUBMITTED,
            cls.SELF_ASSESSMENT_SUBMITTED: cls.AWAITING_ADMIN_REVIEW,
            cls.AWAITING_ADMIN_REVIEW: cls.ADMIN_REVIEW_COMPLETED,
            cls.ADMIN_REVIEW_COMPLETED: cls.AWAITING_REVIEWER_ASSESSMENTS,
            cls.AWAITING_REVIEWER_ASSESSMENTS: cls.REVIEWER_ASSESSMENTS_IN_PROGRESS,
            cls.REVIEWER_ASSESSMENTS_IN_PROGRESS: cls.REVIEWER_ASSESSMENT_SUBMITTED,
            cls.REVIEWER_ASSESSMENT_SUBMITTED: cls.REVIEWER_ASSESSMENTS_COMPLETED,
            cls.REVIEWER_ASSESSMENTS_COMPLETED: cls.AWAITING_FINAL_ADMIN_APPROVAL,
            cls.AWAITING_FINAL_ADMIN_APPROVAL: cls.ASSESSMENT_APPROVED_BY_ADMIN,
            cls.ASSESSMENT_APPROVED_BY_ADMIN: cls.RESULTS_RELEASED_TO_REVIEWEE,
            cls.RESULTS_RELEASED_TO_REVIEWEE: cls.REVIEWEE_ACKNOWLEDGED_RESULTS,
            cls.REVIEWEE_ACKNOWLEDGED_RESULTS: cls.ASSESSMENT_CLOSED,
        }
        return next_status_map.get(current_status)
    
    @classmethod
    def can_reviewer_access(cls, status):
        """Check if reviewers can access their assessment tasks"""
        return status in [
            cls.AWAITING_REVIEWER_ASSESSMENTS,
            cls.REVIEWER_ASSESSMENTS_IN_PROGRESS,
            cls.REVIEWER_ASSESSMENT_SUBMITTED,
            cls.REVIEWER_ASSESSMENTS_COMPLETED
        ]
    
    @classmethod
    def can_reviewee_access_results(cls, status):
        """Check if reviewee can access their results"""
        return status in [
            cls.RESULTS_RELEASED_TO_REVIEWEE,
            cls.REVIEWEE_ACKNOWLEDGED_RESULTS,
            cls.ASSESSMENT_CLOSED
        ]

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, board_member, officer
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assessments_given = db.relationship('Assessment', foreign_keys='Assessment.reviewer_id', backref='reviewer', lazy='dynamic')
    assessments_received = db.relationship('Assessment', foreign_keys='Assessment.officer_id', backref='officer', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.name} ({self.role})>'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    questions = db.relationship('Question', backref='category', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), default='rating')  # rating, text, textarea
    order = db.Column(db.Integer, default=0)
    is_required = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # For rating questions
    min_rating = db.Column(db.Integer, default=1)
    max_rating = db.Column(db.Integer, default=5)
    
    def __repr__(self):
        return f'<Question {self.text[:50]}>'

class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False, default=lambda: datetime.now().year)
    overall_rating = db.Column(db.Float)
    accomplishments = db.Column(db.Text)
    improvement_opportunities = db.Column(db.Text)
    focus_for_next_year = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_self_assessment = db.Column(db.Boolean, default=False)
    
    # Relationships
    category_ratings = db.relationship('CategoryRating', backref='assessment', lazy='dynamic', cascade='all, delete-orphan')
    
    def calculate_overall_rating(self):
        ratings = self.category_ratings.all()
        if not ratings:
            return 0
        return sum(rating.rating for rating in ratings) / len(ratings)
    
    def __repr__(self):
        return f'<Assessment {self.officer.name} by {self.reviewer.name} ({self.year})>'

class CategoryRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessment.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 scale
    
    # Relationships
    category = db.relationship('Category', backref='ratings')
    
    def __repr__(self):
        return f'<CategoryRating {self.category.name}: {self.rating}>'

class AssessmentPeriod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=True)  # Due date for assessment completion
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='created_periods')
    assignments = db.relationship('AssessmentAssignment', backref='period', lazy='dynamic', cascade='all, delete-orphan')
    period_reviewees = db.relationship('PeriodReviewee', backref='assessment_period', lazy='dynamic', cascade='all, delete-orphan')
    period_reviewers = db.relationship('PeriodReviewer', backref='assessment_period', lazy='dynamic', cascade='all, delete-orphan')
    

    
    @property
    def is_current(self):
        today = datetime.now().date()
        return self.start_date <= today <= self.end_date and self.is_active
    
    @property
    def completion_rate(self):
        total_assignments = self.assignments.count()
        if total_assignments == 0:
            return 0
        completed = self.assignments.filter_by(is_completed=True).count()
        return round((completed / total_assignments) * 100, 1)
    
    def get_reviewees(self):
        """Get list of selected reviewees for this period"""
        reviewee_ids = [pr.user_id for pr in self.period_reviewees]
        return User.query.filter(User.id.in_(reviewee_ids)).order_by(User.name).all() if reviewee_ids else []
    
    def get_reviewers(self):
        """Get list of selected reviewers for this period"""
        reviewer_ids = [pr.user_id for pr in self.period_reviewers]
        return User.query.filter(User.id.in_(reviewer_ids)).order_by(User.name).all() if reviewer_ids else []
    
    def __repr__(self):
        return f'<AssessmentPeriod {self.name}>'

class PeriodReviewee(db.Model):
    """Association table for selected reviewees in an assessment period"""
    __tablename__ = 'period_reviewee'
    id = db.Column(db.Integer, primary_key=True)
    period_id = db.Column(db.Integer, db.ForeignKey('assessment_period.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='reviewee_periods')
    
    def __repr__(self):
        return f'<PeriodReviewee {self.user.name} in Period {self.period_id}>'

class PeriodReviewer(db.Model):
    """Association table for selected reviewers in an assessment period"""
    __tablename__ = 'period_reviewer'
    id = db.Column(db.Integer, primary_key=True)
    period_id = db.Column(db.Integer, db.ForeignKey('assessment_period.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='reviewer_periods')
    
    def __repr__(self):
        return f'<PeriodReviewer {self.user.name} in Period {self.period_id}>'

class AssessmentAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    period_id = db.Column(db.Integer, db.ForeignKey('assessment_period.id'), nullable=False)
    officer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    is_notified = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Admin approval tracking for individual assessments
    is_submitted = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime)
    is_admin_approved = db.Column(db.Boolean, default=False)
    admin_approved_at = db.Column(db.DateTime)
    admin_approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    admin_notes = db.Column(db.Text)
    
    # Relationships
    officer = db.relationship('User', foreign_keys=[officer_id], backref='officer_assignments')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], backref='reviewer_assignments')
    admin_approver = db.relationship('User', foreign_keys=[admin_approved_by], backref='approved_assignments')
    
    # Link to actual assessment
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessment.id'))
    assessment = db.relationship('Assessment', backref='assignment')
    
    @property
    def is_self_assessment(self):
        """Check if this is a self-assessment"""
        return self.officer_id == self.reviewer_id
    
    @property
    def status_display(self):
        """Get human-readable status for this assignment"""
        if self.is_completed and self.is_admin_approved:
            return "Completed & Approved"
        elif self.is_submitted and not self.is_admin_approved:
            return "Awaiting Admin Approval"
        elif self.is_completed:
            return "Submitted"
        else:
            return "In Progress"
    
    def __repr__(self):
        return f'<AssessmentAssignment {self.reviewer.name} -> {self.officer.name}>'


class AssessmentProject(db.Model):
    """Main assessment project that tracks the overall workflow status"""
    __tablename__ = 'assessment_project'
    id = db.Column(db.Integer, primary_key=True)
    period_id = db.Column(db.Integer, db.ForeignKey('assessment_period.id'), nullable=False)
    officer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Workflow Status
    status = db.Column(db.Enum(AssessmentStatus), default=AssessmentStatus.PENDING_SELF_ASSESSMENT, nullable=False)
    
    # Timestamps for each phase
    self_assessment_submitted_at = db.Column(db.DateTime)
    admin_review_completed_at = db.Column(db.DateTime)
    reviewer_assessments_released_at = db.Column(db.DateTime)
    final_approval_at = db.Column(db.DateTime)
    results_released_at = db.Column(db.DateTime)
    reviewee_acknowledged_at = db.Column(db.DateTime)
    
    # Admin actions
    admin_approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    admin_notes = db.Column(db.Text)
    
    # Reviewer task visibility
    reviewer_tasks_visible = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    period = db.relationship('AssessmentPeriod', backref='assessment_projects')
    officer = db.relationship('User', foreign_keys=[officer_id], backref='assessment_projects')
    admin_approver = db.relationship('User', foreign_keys=[admin_approved_by], backref='approved_assessments')
    
    def get_self_assessment_assignment(self):
        """Get the self-assessment assignment for this project"""
        return AssessmentAssignment.query.filter_by(
            period_id=self.period_id,
            officer_id=self.officer_id,
            reviewer_id=self.officer_id
        ).first()
    
    def get_reviewer_assignments(self):
        """Get all external reviewer assignments for this project"""
        return AssessmentAssignment.query.filter(
            AssessmentAssignment.period_id == self.period_id,
            AssessmentAssignment.officer_id == self.officer_id,
            AssessmentAssignment.reviewer_id != self.officer_id
        ).all()
    
    def get_reviewer_completion_count(self):
        """Get count of completed external reviewer assessments"""
        return AssessmentAssignment.query.filter(
            AssessmentAssignment.period_id == self.period_id,
            AssessmentAssignment.officer_id == self.officer_id,
            AssessmentAssignment.reviewer_id != self.officer_id,
            AssessmentAssignment.is_completed == True
        ).count()
    
    def get_total_reviewer_count(self):
        """Get total count of external reviewer assignments"""
        return AssessmentAssignment.query.filter(
            AssessmentAssignment.period_id == self.period_id,
            AssessmentAssignment.officer_id == self.officer_id,
            AssessmentAssignment.reviewer_id != self.officer_id
        ).count()
    
    def can_reviewer_access_tasks(self):
        """Check if reviewers can access their tasks"""
        return AssessmentStatus.can_reviewer_access(self.status) and self.reviewer_tasks_visible
    
    def can_reviewee_access_results(self):
        """Check if reviewee can access their results"""
        return AssessmentStatus.can_reviewee_access_results(self.status)
    
    def advance_status(self, admin_user_id=None):
        """Advance to next status in workflow"""
        now = datetime.utcnow()
        
        if self.status == AssessmentStatus.PENDING_SELF_ASSESSMENT:
            # Check if self-assessment is submitted
            self_assignment = self.get_self_assessment_assignment()
            if self_assignment and self_assignment.is_completed:
                self.status = AssessmentStatus.SELF_ASSESSMENT_SUBMITTED
                self.self_assessment_submitted_at = now
                return True
        
        elif self.status == AssessmentStatus.SELF_ASSESSMENT_SUBMITTED:
            self.status = AssessmentStatus.AWAITING_ADMIN_REVIEW
            return True
        
        elif self.status == AssessmentStatus.AWAITING_ADMIN_REVIEW:
            if admin_user_id:
                self.status = AssessmentStatus.ADMIN_REVIEW_COMPLETED
                self.admin_review_completed_at = now
                self.admin_approved_by = admin_user_id
                return True
        
        elif self.status == AssessmentStatus.ADMIN_REVIEW_COMPLETED:
            self.status = AssessmentStatus.AWAITING_REVIEWER_ASSESSMENTS
            self.reviewer_assessments_released_at = now
            self.reviewer_tasks_visible = True
            return True
        
        elif self.status == AssessmentStatus.AWAITING_REVIEWER_ASSESSMENTS:
            # Check if any reviewer has started
            reviewer_assignments = self.get_reviewer_assignments()
            if any(assignment.assessment_id for assignment in reviewer_assignments):
                self.status = AssessmentStatus.REVIEWER_ASSESSMENTS_IN_PROGRESS
                return True
        
        elif self.status == AssessmentStatus.REVIEWER_ASSESSMENTS_IN_PROGRESS:
            # Check if all reviewers completed
            total_reviewers = self.get_total_reviewer_count()
            completed_reviewers = self.get_reviewer_completion_count()
            if total_reviewers > 0 and completed_reviewers >= total_reviewers:
                self.status = AssessmentStatus.REVIEWER_ASSESSMENTS_COMPLETED
                return True
        
        elif self.status == AssessmentStatus.REVIEWER_ASSESSMENTS_COMPLETED:
            self.status = AssessmentStatus.AWAITING_FINAL_ADMIN_APPROVAL
            return True
        
        elif self.status == AssessmentStatus.AWAITING_FINAL_ADMIN_APPROVAL:
            if admin_user_id:
                self.status = AssessmentStatus.ASSESSMENT_APPROVED_BY_ADMIN
                self.final_approval_at = now
                return True
        
        elif self.status == AssessmentStatus.ASSESSMENT_APPROVED_BY_ADMIN:
            self.status = AssessmentStatus.RESULTS_RELEASED_TO_REVIEWEE
            self.results_released_at = now
            return True
        
        elif self.status == AssessmentStatus.RESULTS_RELEASED_TO_REVIEWEE:
            self.status = AssessmentStatus.REVIEWEE_ACKNOWLEDGED_RESULTS
            self.reviewee_acknowledged_at = now
            return True
        
        elif self.status == AssessmentStatus.REVIEWEE_ACKNOWLEDGED_RESULTS:
            self.status = AssessmentStatus.ASSESSMENT_CLOSED
            return True
        
        return False
    
    def get_all_reviewer_assignments(self):
        """Get all reviewer assignments (excluding self-assessment)"""
        return AssessmentAssignment.query.filter(
            AssessmentAssignment.period_id == self.period_id,
            AssessmentAssignment.officer_id == self.officer_id,
            AssessmentAssignment.reviewer_id != self.officer_id
        ).all()
    
    def get_completed_reviewer_assignments(self):
        """Get completed reviewer assignments (excluding self-assessment)"""
        return AssessmentAssignment.query.filter(
            AssessmentAssignment.period_id == self.period_id,
            AssessmentAssignment.officer_id == self.officer_id,
            AssessmentAssignment.reviewer_id != self.officer_id,
            AssessmentAssignment.is_completed == True
        ).all()
    
    def __repr__(self):
        return f'<AssessmentProject {self.officer.name} - {self.status.value}>'


class QuestionResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessment.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    response_text = db.Column(db.Text)  # For text/textarea responses
    response_rating = db.Column(db.Integer)  # For rating responses
    comment = db.Column(db.Text)  # Additional comments
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    question = db.relationship('Question', backref='responses')
    assessment = db.relationship('Assessment', backref='question_responses')
    
    def __repr__(self):
        return f'<QuestionResponse {self.id}: Question {self.question_id} in Assessment {self.assessment_id}>'


class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # login, logout, create_assessment, etc.
    description = db.Column(db.Text)  # Detailed description of the action
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6 address
    user_agent = db.Column(db.String(500))  # Browser/device information
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='activity_logs')
    
    def __repr__(self):
        return f'<ActivityLog {self.user.name}: {self.action} at {self.timestamp}>'

class AIAnalysisCache(db.Model):
    """Cache AI analysis results to avoid regenerating them"""
    __tablename__ = 'ai_analysis_cache'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    period_id = db.Column(db.Integer, db.ForeignKey('assessment_period.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('assessment_question.id'), nullable=True)  # Null for overall analysis
    analysis_type = db.Column(db.String(20), nullable=False)  # 'question' or 'overall'
    
    # AI Analysis Results
    summary = db.Column(db.Text)
    themes = db.Column(db.Text)  # JSON string of themes list
    sentiment = db.Column(db.String(20))
    executive_summary = db.Column(db.Text)  # For overall analysis
    major_themes = db.Column(db.Text)  # JSON string for overall themes
    overall_sentiment = db.Column(db.String(20))  # For overall analysis
    
    # Cache metadata
    content_hash = db.Column(db.String(64), nullable=False)  # Hash of input data
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    officer = db.relationship('User', backref=db.backref('ai_analysis_cache', lazy=True))
    period = db.relationship('AssessmentPeriod', backref=db.backref('ai_analysis_cache', lazy=True))
    question = db.relationship('AssessmentQuestion', backref=db.backref('ai_analysis_cache', lazy=True))
    
    def get_analysis_data(self):
        """Return analysis data as dictionary"""
        if self.analysis_type == 'question':
            import json
            return {
                'summary': self.summary,
                'themes': json.loads(self.themes) if self.themes else [],
                'sentiment': self.sentiment
            }
        else:  # overall
            import json
            return {
                'executive_summary': self.executive_summary,
                'major_themes': json.loads(self.major_themes) if self.major_themes else [],
                'overall_sentiment': self.overall_sentiment
            }
    
    def __repr__(self):
        return f'<AIAnalysisCache {self.analysis_type} for Officer:{self.officer_id} Period:{self.period_id}>'

# Assessment Form Builder Models
class AssessmentForm(db.Model):
    __tablename__ = 'assessment_form'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    is_template = db.Column(db.Boolean, default=False)  # For forms that can be duplicated
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='created_assessment_forms')
    form_questions = db.relationship('AssessmentQuestion', backref='form', lazy='dynamic', cascade='all, delete-orphan')
    period_assignments = db.relationship('PeriodFormAssignment', backref='assessment_form', lazy='dynamic', cascade='all, delete-orphan', foreign_keys='PeriodFormAssignment.form_id')
    
    def __repr__(self):
        return f'<AssessmentForm {self.title}>'

class AssessmentQuestion(db.Model):
    __tablename__ = 'assessment_question'
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey('assessment_form.id'), nullable=False)
    question_name = db.Column(db.String(200), nullable=False)  # Question name/title  
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # rating, text, textarea, checkbox, dropdown, multiple_choice, boolean, date
    order = db.Column(db.Integer, default=0)
    is_required = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Question-specific settings (stored as JSON)
    settings = db.Column(db.Text)  # JSON string for type-specific configurations
    
    # Relationships
    responses = db.relationship('AssessmentResponse', backref='question', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_settings(self):
        """Get question settings as dictionary"""
        if self.settings:
            import json
            return json.loads(self.settings)
        return {}
    
    def set_settings(self, settings_dict):
        """Set question settings from dictionary"""
        import json
        self.settings = json.dumps(settings_dict)
    
    def __repr__(self):
        return f'<AssessmentQuestion {self.question_text[:50]}>'

class PeriodFormAssignment(db.Model):
    """Links assessment periods to specific assessment forms with usage type"""
    id = db.Column(db.Integer, primary_key=True)
    period_id = db.Column(db.Integer, db.ForeignKey('assessment_period.id'), nullable=False)
    form_id = db.Column(db.Integer, db.ForeignKey('assessment_form.id'), nullable=False)
    form_type = db.Column(db.String(20), nullable=False, default='reviewer')  # 'reviewer' or 'self_review'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    period = db.relationship('AssessmentPeriod', backref='form_assignments')
    
    def __repr__(self):
        return f'<PeriodFormAssignment Period:{self.period_id} Form:{self.form_id} Type:{self.form_type}>'

class AssessmentResponse(db.Model):
    """Stores responses to assessment questions"""
    __tablename__ = 'assessment_response'
    id = db.Column(db.Integer, primary_key=True)
    assessment_assignment_id = db.Column(db.Integer, db.ForeignKey('assessment_assignment.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('assessment_question.id'), nullable=False)
    response_text = db.Column(db.Text)  # For text responses
    response_number = db.Column(db.Float)  # For numeric responses (ratings)
    response_boolean = db.Column(db.Boolean)  # For boolean responses
    response_date = db.Column(db.Date)  # For date responses
    response_json = db.Column(db.Text)  # For complex responses (multiple choice, checkbox arrays)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assignment = db.relationship('AssessmentAssignment', backref='assessment_responses')
    
    def get_response_data(self):
        """Get response data as appropriate type"""
        if self.response_json:
            import json
            return json.loads(self.response_json)
        elif self.response_text:
            return self.response_text
        elif self.response_number is not None:
            return self.response_number
        elif self.response_boolean is not None:
            return self.response_boolean
        elif self.response_date:
            return self.response_date
        return None
    
    def set_response_data(self, data):
        """Set response data with appropriate type"""
        if isinstance(data, (list, dict)):
            import json
            self.response_json = json.dumps(data)
        elif isinstance(data, str):
            self.response_text = data
        elif isinstance(data, (int, float)):
            self.response_number = data
        elif isinstance(data, bool):
            self.response_boolean = data
        elif isinstance(data, datetime):
            self.response_date = data.date()
        else:
            self.response_text = str(data)
    
    def __repr__(self):
        return f'<AssessmentResponse Question:{self.question_id} Assignment:{self.assessment_assignment_id}>'

class AISummaryStatus(db.Model):
    """Tracks AI summary generation status for officer assessments"""
    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    period_id = db.Column(db.Integer, db.ForeignKey('assessment_period.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'processing', 'completed', 'error'
    progress = db.Column(db.Integer, default=0)  # 0-100 percentage
    error_message = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    officer = db.relationship('User', foreign_keys=[officer_id], backref='ai_summary_statuses')
    period = db.relationship('AssessmentPeriod', backref='ai_summary_statuses')
    creator = db.relationship('User', foreign_keys=[created_by])
    
    __table_args__ = (db.UniqueConstraint('officer_id', 'period_id', name='unique_officer_period_summary'),)
    
    def __repr__(self):
        return f'<AISummaryStatus Officer:{self.officer_id} Period:{self.period_id} Status:{self.status}>'

class AIGeneratedReport(db.Model):
    """Stores AI-generated comprehensive performance reports as PDFs"""
    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    period_id = db.Column(db.Integer, db.ForeignKey('assessment_period.id'), nullable=False)
    report_title = db.Column(db.String(200))
    summary_text = db.Column(db.Text)  # AI-generated summary text
    report_data = db.Column(db.Text)  # Complete AI report data as JSON
    pdf_data = db.Column(db.LargeBinary)  # Stored PDF file
    pdf_filename = db.Column(db.String(200))
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    generated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Statistics from the analysis
    total_reviewers = db.Column(db.Integer, default=0)
    average_rating = db.Column(db.Float, default=0.0)
    total_questions = db.Column(db.Integer, default=0)
    
    # Relationships
    officer = db.relationship('User', foreign_keys=[officer_id], backref='ai_reports')
    period = db.relationship('AssessmentPeriod', backref='ai_reports')
    creator = db.relationship('User', foreign_keys=[created_by])
    
    __table_args__ = (db.UniqueConstraint('officer_id', 'period_id', name='unique_officer_period_report'),)
    
    def __repr__(self):
        return f'<AIGeneratedReport Officer:{self.officer_id} Period:{self.period_id}>'

class AssessmentActivityLog(db.Model):
    """Enhanced activity logging specifically for assessment workflow events"""
    __tablename__ = 'assessment_activity_log'
    id = db.Column(db.Integer, primary_key=True)
    
    # Event identification
    event_type = db.Column(db.String(50), nullable=False)  # e.g., 'self_assessment_assigned', 'reviewer_notified'
    event_category = db.Column(db.String(30), nullable=False)  # 'assignment', 'submission', 'approval', 'notification'
    
    # Assessment context
    officer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    period_id = db.Column(db.Integer, db.ForeignKey('assessment_period.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # For reviewer-specific events
    assignment_id = db.Column(db.Integer, db.ForeignKey('assessment_assignment.id'), nullable=True)
    
    # Event details
    description = db.Column(db.Text, nullable=False)
    event_status = db.Column(db.String(20), default='completed')  # 'completed', 'pending', 'failed'
    event_data = db.Column(db.Text)  # JSON for additional event data
    
    # Actor information
    actor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Who performed the action
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    
    # Timing
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    officer = db.relationship('User', foreign_keys=[officer_id], backref='assessment_activity_as_officer')
    period = db.relationship('AssessmentPeriod', backref='assessment_activities')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], backref='assessment_activity_as_reviewer')
    assignment = db.relationship('AssessmentAssignment', backref='activity_logs')
    actor = db.relationship('User', foreign_keys=[actor_id], backref='assessment_activities_performed')
    
    def get_event_data(self):
        """Get event data as dictionary"""
        if self.event_data:
            import json
            return json.loads(self.event_data)
        return {}
    
    def set_event_data(self, data):
        """Set event data from dictionary"""
        import json
        self.event_data = json.dumps(data)
    
    def __repr__(self):
        return f'<AssessmentActivityLog {self.event_type} for Officer:{self.officer_id} Period:{self.period_id}>'

# Add relationships for the new association tables
AssessmentPeriod.selected_reviewees = db.relationship('PeriodReviewee', backref='period', lazy='dynamic', cascade='all, delete-orphan')
AssessmentPeriod.selected_reviewers = db.relationship('PeriodReviewer', backref='period', lazy='dynamic', cascade='all, delete-orphan')


