from app import db
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum

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
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='created_periods')
    assignments = db.relationship('AssessmentAssignment', backref='period', lazy='dynamic', cascade='all, delete-orphan')
    
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
    
    def __repr__(self):
        return f'<AssessmentPeriod {self.name}>'

class AssessmentAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    period_id = db.Column(db.Integer, db.ForeignKey('assessment_period.id'), nullable=False)
    officer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    is_notified = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    officer = db.relationship('User', foreign_keys=[officer_id], backref='officer_assignments')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], backref='reviewer_assignments')
    
    # Link to actual assessment
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessment.id'))
    assessment = db.relationship('Assessment', backref='assignment')
    
    def __repr__(self):
        return f'<AssessmentAssignment {self.reviewer.name} -> {self.officer.name}>'


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


