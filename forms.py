from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, IntegerField, SubmitField, HiddenField, DateField, SelectMultipleField, BooleanField
from wtforms.validators import DataRequired, Email, Length, NumberRange, ValidationError, Optional
from wtforms.widgets import CheckboxInput, ListWidget
from models import User, Category, AssessmentStatus
from datetime import datetime, timedelta

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class AssessmentForm(FlaskForm):
    officer_id = HiddenField('Officer ID', validators=[DataRequired()])
    accomplishments = TextAreaField('Key Accomplishments', validators=[Length(max=2000)],
                                  render_kw={'rows': 4, 'placeholder': 'Describe the key accomplishments achieved this year...'})
    improvement_opportunities = TextAreaField('Areas for Improvement', validators=[Length(max=2000)],
                                            render_kw={'rows': 4, 'placeholder': 'Identify areas where improvement or development would be beneficial...'})
    focus_for_next_year = TextAreaField('Focus for Next Year', validators=[Length(max=2000)],
                                      render_kw={'rows': 4, 'placeholder': 'Outline priorities and focus areas for the upcoming year...'})
    submit = SubmitField('Submit Assessment')

class CategoryRatingForm(FlaskForm):
    category_id = HiddenField('Category ID', validators=[DataRequired()])
    rating = SelectField('Rating', choices=[
        (1, '1 - Unsatisfactory'),
        (2, '2 - Below Expectations'),
        (3, '3 - Meets Expectations'),
        (4, '4 - Exceeds Expectations'),
        (5, '5 - Outstanding')
    ], coerce=int, validators=[DataRequired(), NumberRange(min=1, max=5)])

class UserForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=[
        ('admin', 'Administrator'),
        ('board_member', 'Board Member'),
        ('officer', 'Officer')
    ], validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Create User')


class EditUserForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=[
        ('admin', 'Administrator'),
        ('board_member', 'Board Member'),
        ('officer', 'Officer')
    ], validators=[DataRequired()])
    new_password = PasswordField('New Password (leave blank to keep current)', validators=[Length(min=6)])
    confirm_password = PasswordField('Confirm New Password')
    submit = SubmitField('Update User')
    
    def validate_confirm_password(self, field):
        if self.new_password.data and field.data != self.new_password.data:
            raise ValidationError('Passwords must match.')

class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class AssessmentPeriodForm(FlaskForm):
    name = StringField('Assessment Project Name', validators=[DataRequired(), Length(min=5, max=200)],
                      render_kw={'placeholder': 'e.g., Q4 2025 Annual Review'})
    description = TextAreaField('Description', validators=[Length(max=500)],
                               render_kw={'rows': 3, 'placeholder': 'Brief description of this assessment project...'})
    start_date = DateField('Start Date', validators=[DataRequired()], 
                          default=lambda: datetime.now().replace(month=1, day=1).date())
    end_date = DateField('End Date', validators=[DataRequired()],
                        default=lambda: datetime.now().replace(month=12, day=31).date())
    due_date = DateField('Assessment Due Date', validators=[Optional()],
                        render_kw={'placeholder': 'Optional: When assessments should be completed'})
    
    # Assessment Form Assignment
    reviewer_form_ids = SelectMultipleField('Reviewer Forms (Used by reviewers to evaluate reviewees)', coerce=int)
    self_review_form_ids = SelectMultipleField('Self-Assessment Forms (Used by reviewees for self-evaluation)', coerce=int)
    
    # User Selection for this Project
    selected_reviewees = MultiCheckboxField('Reviewees (People to be reviewed)', coerce=int)
    selected_reviewers = MultiCheckboxField('Reviewers (People who will conduct reviews)', coerce=int)
    
    submit = SubmitField('Create Assessment Project')
    
    def __init__(self, *args, **kwargs):
        super(AssessmentPeriodForm, self).__init__(*args, **kwargs)
        from models import AssessmentForm, User
        
        # Populate assessment forms for both reviewer and self-review selection (only active forms)
        forms = AssessmentForm.query.filter_by(is_active=True).order_by(AssessmentForm.title).all()
        form_choices = [(f.id, f.title) for f in forms]
        self.reviewer_form_ids.choices = form_choices
        self.self_review_form_ids.choices = form_choices
        
        # Populate user choices for reviewees and reviewers (only active users)
        reviewee_users = User.query.filter(User.role.in_(['officer', 'admin']), User.is_active == True).order_by(User.name).all()
        reviewer_users = User.query.filter(User.role.in_(['board_member', 'admin', 'officer']), User.is_active == True).order_by(User.name).all()
        
        self.selected_reviewees.choices = [(u.id, f"{u.name} ({u.role.replace('_', ' ').title()})") for u in reviewee_users]
        self.selected_reviewers.choices = [(u.id, f"{u.name} ({u.role.replace('_', ' ').title()})") for u in reviewer_users]

class AssignmentForm(FlaskForm):
    period_id = HiddenField('Period ID', validators=[DataRequired()])
    officers = MultiCheckboxField('Officers to be Assessed', coerce=int)
    reviewers = MultiCheckboxField('Reviewers (Board Members)', coerce=int)
    create_todos = SelectField('Create To-Do Activities', 
                              choices=[('yes', 'Create to-do activities for reviewers'), 
                                      ('no', 'Create assignments only')],
                              default='yes')
    submit = SubmitField('Create Assignments')
    
    def __init__(self, *args, **kwargs):
        super(AssignmentForm, self).__init__(*args, **kwargs)
        # Populate choices with only active users
        from models import User
        self.officers.choices = [(u.id, u.name) for u in User.query.filter_by(is_active=True).filter(User.role.in_(['officer', 'admin'])).order_by(User.name).all()]
        self.reviewers.choices = [(u.id, u.name) for u in User.query.filter_by(is_active=True).filter(User.role.in_(['board_member', 'admin'])).order_by(User.name).all()]

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=500)],
                               render_kw={'rows': 3, 'placeholder': 'Describe what this category evaluates...'})
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Category')

class QuestionForm(FlaskForm):
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    text = TextAreaField('Question Text', validators=[DataRequired(), Length(max=1000)],
                        render_kw={'rows': 3, 'placeholder': 'Enter the assessment question...'})
    question_type = SelectField('Question Type', 
                               choices=[('rating', 'Rating Scale (1-5)'), 
                                       ('text', 'Short Text'), 
                                       ('textarea', 'Long Text')],
                               default='rating')
    is_required = BooleanField('Required', default=True)
    is_active = BooleanField('Active', default=True)
    min_rating = IntegerField('Minimum Rating', default=1, validators=[NumberRange(min=1, max=10)])
    max_rating = IntegerField('Maximum Rating', default=5, validators=[NumberRange(min=1, max=10)])
    submit = SubmitField('Save Question')

# Assessment Form Builder Forms
class AssessmentFormForm(FlaskForm):
    title = StringField('Form Title', validators=[DataRequired(), Length(min=5, max=200)],
                       render_kw={'placeholder': 'e.g., Executive Performance Review 2025'})
    description = TextAreaField('Description', validators=[Length(max=1000)],
                               render_kw={'rows': 3, 'placeholder': 'Brief description of this assessment form...'})
    is_template = BooleanField('Save as Template', default=False)
    submit = SubmitField('Create Form')

class AssessmentQuestionForm(FlaskForm):
    question_name = StringField('Question Label', validators=[DataRequired(), Length(max=200)],
                               render_kw={'placeholder': 'Enter a clear question label...'})
    question_text = TextAreaField('Question Text', validators=[DataRequired(), Length(max=1000)],
                                 render_kw={'rows': 3, 'placeholder': 'Enter your survey question...'})
    question_type = SelectField('Question Type', 
                               choices=[
                                   ('rating', 'Rating Scale (1-5)'),
                                   ('text', 'Short Text'),
                                   ('textarea', 'Long Text'),
                                   ('checkbox', 'Checkbox (Multiple Options)'),
                                   ('dropdown', 'Dropdown (Single Choice)'),
                                   ('multiple_choice', 'Multiple Choice (Radio Buttons)'),
                                   ('boolean', 'Yes/No (True/False)'),
                                   ('date', 'Date Picker')
                               ],
                               validators=[DataRequired()])
    is_required = BooleanField('Required Question', default=False)
    
    # Dynamic settings fields (populated via JavaScript based on question type)
    rating_min = IntegerField('Minimum Rating', default=1, validators=[NumberRange(min=1, max=10)])
    rating_max = IntegerField('Maximum Rating', default=5, validators=[NumberRange(min=1, max=10)])
    rating_labels = TextAreaField('Rating Labels (one per line)', 
                                 render_kw={'rows': 5, 'placeholder': '1 - Poor\n2 - Fair\n3 - Good\n4 - Very Good\n5 - Excellent'})
    
    # For checkbox, dropdown, multiple choice options
    options = TextAreaField('Options (one per line)', 
                           render_kw={'rows': 5, 'placeholder': 'Option 1\nOption 2\nOption 3'})
    
    # For text fields
    max_length = IntegerField('Maximum Characters', default=2000, validators=[NumberRange(min=1, max=5000)])
    placeholder = StringField('Placeholder Text', validators=[Length(max=200)])
    
    submit = SubmitField('Add Question')

class DuplicateFormForm(FlaskForm):
    new_title = StringField('New Form Title', validators=[DataRequired(), Length(min=5, max=200)],
                           render_kw={'placeholder': 'Copy of Executive Performance Review 2025'})
    new_description = TextAreaField('Description', validators=[Length(max=1000)],
                                   render_kw={'rows': 3, 'placeholder': 'Description for the duplicated form...'})
    submit = SubmitField('Duplicate Form')

class EditAssessmentFormTitleForm(FlaskForm):
    title = StringField('Form Title', validators=[DataRequired(), Length(min=5, max=200)])
    description = TextAreaField('Description', validators=[Length(max=1000)],
                               render_kw={'rows': 3, 'placeholder': 'Brief description of this assessment form...'})
    submit = SubmitField('Update Form')

class AssignFormToPeriodForm(FlaskForm):
    period_id = SelectField('Assessment Project', coerce=int, validators=[DataRequired()])
    reviewer_form_ids = SelectMultipleField('Reviewer Forms (Used by reviewers)', coerce=int)
    self_review_form_ids = SelectMultipleField('Self-Review Forms (Used by reviewees)', coerce=int)
    submit = SubmitField('Assign Forms to Period')
    
    def __init__(self, *args, **kwargs):
        super(AssignFormToPeriodForm, self).__init__(*args, **kwargs)
        from models import AssessmentPeriod, AssessmentForm
        
        # Populate periods
        periods = AssessmentPeriod.query.filter_by(is_active=True).order_by(AssessmentPeriod.created_at.desc()).all()
        self.period_id.choices = [(p.id, p.name) for p in periods]
        
        # Populate forms for both reviewer and self-review (only active forms)
        forms = AssessmentForm.query.filter_by(is_active=True).order_by(AssessmentForm.created_at.desc()).all()
        form_choices = [(f.id, f.title) for f in forms]
        self.reviewer_form_ids.choices = form_choices
        self.self_review_form_ids.choices = form_choices
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        # At least one form type must be selected
        if not self.reviewer_form_ids.data and not self.self_review_form_ids.data:
            self.reviewer_form_ids.errors.append('At least one reviewer form or self-review form must be selected.')
            return False
        
        return True

class EditAssessmentPeriodForm(FlaskForm):
    name = StringField('Assessment Project Name', validators=[DataRequired(), Length(min=5, max=200)])
    description = TextAreaField('Description', validators=[Length(max=500)],
                               render_kw={'rows': 3, 'placeholder': 'Brief description of this assessment project...'})
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    due_date = DateField('Assessment Due Date', validators=[Optional()],
                        render_kw={'placeholder': 'Optional: When assessments should be completed'})
    submit = SubmitField('Update Assessment Project')

class CloneAssessmentPeriodForm(FlaskForm):
    name = StringField('New Assessment Project Name', validators=[DataRequired(), Length(min=5, max=200)],
                      render_kw={'placeholder': 'e.g., Q1 2026 Annual Review'})
    description = TextAreaField('Description', validators=[Length(max=500)],
                               render_kw={'rows': 3, 'placeholder': 'Brief description of this assessment project...'})
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    due_date = DateField('Assessment Due Date', validators=[Optional()],
                        render_kw={'placeholder': 'Optional: When assessments should be completed'})
    copy_forms = BooleanField('Copy Assessment Forms', default=True)
    submit = SubmitField('Clone Assessment Project')


class AdminReviewForm(FlaskForm):
    """Form for admin to review and approve self-assessments"""
    action = SelectField('Action', choices=[
        ('approve', 'Approve and Release to Reviewers'),
        ('reject', 'Send Back for Revision')
    ], validators=[DataRequired()])
    admin_notes = TextAreaField('Admin Notes', validators=[Length(max=1000)],
                               render_kw={'rows': 4, 'placeholder': 'Add notes about this review decision...'})
    submit = SubmitField('Submit Review')


class FinalApprovalForm(FlaskForm):
    """Form for final admin approval after all reviewers complete"""
    action = SelectField('Action', choices=[
        ('approve', 'Approve and Release Results'),
        ('hold', 'Hold for Further Review')
    ], validators=[DataRequired()])
    admin_notes = TextAreaField('Final Notes', validators=[Length(max=1000)],
                               render_kw={'rows': 4, 'placeholder': 'Final approval notes...'})
    submit = SubmitField('Submit Final Approval')


class AcknowledgeResultsForm(FlaskForm):
    """Form for reviewee to acknowledge their assessment results"""
    acknowledged = BooleanField('I acknowledge that I have reviewed my assessment results', validators=[DataRequired()])
    reviewee_feedback = TextAreaField('Feedback on Assessment Process (Optional)', validators=[Length(max=1000)],
                                    render_kw={'rows': 4, 'placeholder': 'Optional feedback about the assessment process...'})
    submit = SubmitField('Acknowledge Results')
