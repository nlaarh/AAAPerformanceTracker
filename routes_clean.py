from flask import render_template, request, redirect, url_for, flash, jsonify, make_response, session
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.orm import joinedload
from app import app, db
from models import User, Assessment, Category, CategoryRating, AssessmentPeriod, AssessmentAssignment, ActivityLog, AssessmentForm, AssessmentQuestion, AssessmentResponse, PeriodFormAssignment
from forms import LoginForm, AssessmentForm, CategoryRatingForm, UserForm, EditUserForm, AssessmentPeriodForm, AssignmentForm, CategoryForm
from utils import admin_required, generate_pdf_report, export_csv_data
from email_service import email_service
from activity_logger import log_activity, get_activity_logs, get_user_activity_logs
from datetime import datetime, date
import csv
import io

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact an administrator.', 'error')
                log_activity(user.id, 'login_blocked', f'Inactive user attempted login from {request.remote_addr}')
            else:
                login_user(user)
                log_activity(user.id, 'login', f'User logged in successfully')
                next_page = request.args.get('next')
                flash(f'Welcome back, {user.name}!', 'success')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html', form=form)



@app.route('/logout')
@login_required
def logout():
    if current_user.is_authenticated:
        log_activity(current_user.id, 'logout', f'User logged out')
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    log_activity(current_user.id, 'view_dashboard', f'User accessed main dashboard')
    
    if current_user.role == 'admin':
        # Admin gets the beautiful dashboard with charts and visualizations
        return admin_dashboard()
    elif current_user.role == 'officer':
        return redirect(url_for('officer_view'))
    else:  # board_member
        return redirect(url_for('reviewer_dashboard'))

@app.route('/reviewer_dashboard')
@login_required
def reviewer_dashboard():
    if current_user.role not in ['board_member', 'admin']:
        flash('Access denied. Board members and administrators only.', 'error')
        return redirect(url_for('dashboard'))
    
    log_activity(current_user.id, 'view_reviewer_dashboard', f'User accessed reviewer dashboard')
    
    # Get pending review assignments
    pending_assignments = AssessmentAssignment.query.filter_by(
        reviewer_id=current_user.id,
        is_completed=False
    ).join(AssessmentPeriod).filter(AssessmentPeriod.is_active == True).all()
    
    # Get completed review assignments for this year
    current_year = datetime.now().year
    completed_assignments = AssessmentAssignment.query.filter_by(
        reviewer_id=current_user.id,
        is_completed=True
    ).join(AssessmentPeriod).filter(
        db.extract('year', AssessmentPeriod.start_date) == current_year
    ).all()
    
    # Group assignments by assessment period
    pending_by_period = {}
    completed_by_period = {}
    
    for assignment in pending_assignments:
        period_name = assignment.period.name
        if period_name not in pending_by_period:
            pending_by_period[period_name] = []
        pending_by_period[period_name].append(assignment)
    
    for assignment in completed_assignments:
        period_name = assignment.period.name
        if period_name not in completed_by_period:
            completed_by_period[period_name] = []
        completed_by_period[period_name].append(assignment)
    
    # Get total statistics
    total_pending = len(pending_assignments)
    total_completed = len(completed_assignments)
    total_assigned = total_pending + total_completed
    
    completion_rate = round((total_completed / total_assigned * 100), 1) if total_assigned > 0 else 0
    
    return render_template('reviewer_dashboard.html',
                         pending_assignments=pending_assignments,
                         completed_assignments=completed_assignments,
                         pending_by_period=pending_by_period,
                         completed_by_period=completed_by_period,
                         total_pending=total_pending,
                         total_completed=total_completed,
                         completion_rate=completion_rate)

@app.route('/my_assignments')
@login_required
def my_assignments():
    """My Assignments page for non-admin users"""
    log_activity(current_user.id, 'my_assignments_access', 'Accessed my assignments page')
    
    # Get assignments where user is a reviewer (reviewing others - exclude self-assessments)
    reviewer_assignments = AssessmentAssignment.query.filter_by(
        reviewer_id=current_user.id
    ).filter(AssessmentAssignment.officer_id != current_user.id).join(AssessmentPeriod).order_by(AssessmentPeriod.created_at.desc()).all()
    
    # Get self-assessment assignments (where user reviews themselves)
    self_assessment_assignments = AssessmentAssignment.query.filter_by(
        officer_id=current_user.id,
        reviewer_id=current_user.id
    ).join(AssessmentPeriod).order_by(AssessmentPeriod.created_at.desc()).all()
    
    # Combine all assignments
    all_assignments = reviewer_assignments + self_assessment_assignments
    officer_assignments = self_assessment_assignments
    
    # Remove duplicates (in case user is both reviewer and officer for same assignment)
    unique_assignments = []
    seen_ids = set()
    for assignment in all_assignments:
        if assignment.id not in seen_ids:
            unique_assignments.append(assignment)
            seen_ids.add(assignment.id)
    
    # Sort by creation date
    unique_assignments.sort(key=lambda x: x.created_at, reverse=True)
    
    # Calculate stats
    pending_assignments = [a for a in unique_assignments if not a.is_completed]
    completed_assignments = [a for a in unique_assignments if a.is_completed]
    
    pending_count = len(pending_assignments)
    completed_count = len(completed_assignments)
    total_assignments = len(unique_assignments)
    completion_rate = (completed_count / total_assignments * 100) if total_assignments > 0 else 0
    
    return render_template('my_assignments.html',
                         assignments=unique_assignments,
                         reviewer_assignments=reviewer_assignments,
                         officer_assignments=officer_assignments,
                         pending_count=pending_count,
                         completed_count=completed_count,
                         completion_rate=round(completion_rate, 1))

@app.route('/admin')
@login_required
@admin_required
def admin_main():
    """Admin main page with tabbed interface"""
    log_activity(current_user.id, 'view_admin_main', 'Accessed admin main page')
    
    # Get assessment form statistics
    from models import AssessmentForm, AssessmentQuestion
    assessment_forms_count = AssessmentForm.query.filter_by(is_active=True).count()
    assessment_questions_count = AssessmentQuestion.query.filter_by(is_active=True).count()
    
    # Get categories for traditional questions
    categories = Category.query.filter_by(is_active=True).order_by(Category.order).all()
    active_periods = AssessmentPeriod.query.filter_by(is_active=True).order_by(AssessmentPeriod.created_at.desc()).limit(3).all()
    
    # Get basic statistics
    total_users = User.query.filter_by(is_active=True).count()
    total_officers = User.query.filter_by(role='officer', is_active=True).count()
    total_board_members = User.query.filter_by(role='board_member', is_active=True).count()
    total_assessments = Assessment.query.count()
    
    return render_template('admin_main.html',
                         assessment_forms_count=assessment_forms_count,
                         assessment_questions_count=assessment_questions_count,
                         categories=categories,
                         active_periods=active_periods,
                         total_users=total_users,
                         total_officers=total_officers,
                         total_board_members=total_board_members,
                         total_assessments=total_assessments)

@app.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    log_activity(current_user.id, 'view_admin_dashboard', f'Admin accessed admin dashboard')
    current_year = datetime.now().year
    
    # Get current active assessment period
    current_period = AssessmentPeriod.query.filter_by(is_active=True).first()
    
    # Get all assessment periods for context
    all_periods = AssessmentPeriod.query.order_by(AssessmentPeriod.created_at.desc()).limit(5).all()
    
    # Get assessment form statistics
    from models import AssessmentForm, AssessmentQuestion
    assessment_forms_count = AssessmentForm.query.filter_by(is_active=True).count()
    assessment_questions_count = AssessmentQuestion.query.filter_by(is_active=True).count()
    template_forms_count = AssessmentForm.query.filter_by(is_active=True, is_template=True).count()
    # Get categories for traditional questions
    categories = Category.query.filter_by(is_active=True).order_by(Category.order).all()
    active_periods = AssessmentPeriod.query.filter_by(is_active=True).order_by(AssessmentPeriod.created_at.desc()).limit(3).all()
    
    # Get statistics for current period
    if current_period:
        total_assignments = AssessmentAssignment.query.filter_by(period_id=current_period.id).count()
        completed_assignments = AssessmentAssignment.query.filter_by(period_id=current_period.id, is_completed=True).count()
        pending_assignments = total_assignments - completed_assignments
        completion_rate = round((completed_assignments / total_assignments * 100), 1) if total_assignments > 0 else 0
        
        # Get assignment data for current period
        assignments_by_officer = db.session.query(
            User.name.label('officer_name'),
            User.id.label('officer_id'),
            db.func.count(AssessmentAssignment.id).label('total_reviews'),
            db.func.sum(db.case((AssessmentAssignment.is_completed == True, 1), else_=0)).label('completed_reviews')
        ).join(
            AssessmentAssignment, User.id == AssessmentAssignment.officer_id
        ).filter(
            AssessmentAssignment.period_id == current_period.id
        ).group_by(User.id, User.name).all()
        
        # Get recent activity for current period
        recent_assessments = Assessment.query.join(
            AssessmentAssignment, Assessment.id == AssessmentAssignment.assessment_id
        ).filter(
            AssessmentAssignment.period_id == current_period.id
        ).order_by(Assessment.submitted_at.desc()).limit(10).all()
        
        # Get reviewer progress
        reviewer_progress = db.session.query(
            User.name.label('reviewer_name'),
            User.id.label('reviewer_id'),
            db.func.count(AssessmentAssignment.id).label('total_assigned'),
            db.func.sum(db.case((AssessmentAssignment.is_completed == True, 1), else_=0)).label('completed')
        ).join(
            AssessmentAssignment, User.id == AssessmentAssignment.reviewer_id
        ).filter(
            AssessmentAssignment.period_id == current_period.id
        ).group_by(User.id, User.name).all()
        
    else:
        total_assignments = completed_assignments = pending_assignments = 0
        completion_rate = 0
        assignments_by_officer = []
        recent_assessments = []
        reviewer_progress = []
    
    # Get overall system statistics
    total_officers = User.query.filter_by(role='officer').count()
    total_board_members = User.query.filter_by(role='board_member').count()
    total_assessments = Assessment.query.filter_by(year=current_year).count()
    
    # Get monthly assessment trend for the chart
    monthly_data = []
    for month in range(1, 13):
        month_assessments = Assessment.query.filter(
            db.extract('year', Assessment.submitted_at) == current_year,
            db.extract('month', Assessment.submitted_at) == month
        ).count()
        monthly_data.append({
            'month': month,
            'count': month_assessments,
            'month_name': datetime(current_year, month, 1).strftime('%b')
        })
    
    return render_template('admin_dashboard.html',
                         current_period=current_period,
                         all_periods=all_periods,
                         total_assignments=total_assignments,
                         completed_assignments=completed_assignments,
                         pending_assignments=pending_assignments,
                         completion_rate=completion_rate,
                         assignments_by_officer=assignments_by_officer,
                         recent_assessments=recent_assessments,
                         reviewer_progress=reviewer_progress,
                         total_officers=total_officers,
                         total_board_members=total_board_members,
                         total_assessments=total_assessments,
                         monthly_data=monthly_data,
                         assessment_forms_count=assessment_forms_count,
                         assessment_questions_count=assessment_questions_count,
                         template_forms_count=template_forms_count,
                         categories=categories,
                         active_periods=active_periods)

@app.route('/admin/officer_reviews/<int:officer_id>')
@login_required
@admin_required
def officer_reviews(officer_id):
    try:
        officer = User.query.get_or_404(officer_id)
        log_activity(current_user.id, 'view_officer_reviews', f'Admin viewed comprehensive review matrix for officer: {officer.name}')
        if officer.role != 'officer':
            flash('Invalid officer selection.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        # Get current active assessment period
        current_period = AssessmentPeriod.query.filter_by(is_active=True).first()
        if not current_period:
            flash('No active assessment period found.', 'warning')
            return redirect(url_for('admin_dashboard'))
        
        # Get all assignments for this officer in the current period
        assignments = AssessmentAssignment.query.filter_by(
            officer_id=officer_id,
            period_id=current_period.id
        ).all()
        
        if not assignments:
            flash(f'No assessment assignments found for {officer.name} in the current period.', 'warning')
            return redirect(url_for('admin_dashboard'))
        
        # Create reviewers list from ALL ASSIGNMENTS
        reviewers = {}
        for assignment in assignments:
            reviewers[assignment.reviewer.id] = assignment.reviewer
        
        # Get all assessment forms assigned to this period for reviewers
        reviewer_forms = db.session.query(AssessmentForm).join(PeriodFormAssignment).filter(
            PeriodFormAssignment.period_id == current_period.id,
            PeriodFormAssignment.form_type == 'reviewer',
            PeriodFormAssignment.is_active == True,
            AssessmentForm.is_active == True
        ).all()
        
        # Build matrix data: questions in rows, reviewers in columns
        matrix_data = []
        processed_question_ids = set()  # Track processed questions to prevent duplicates
        
        # Get all questions from all reviewer forms
        all_questions = []
        for form in reviewer_forms:
            form_questions = AssessmentQuestion.query.filter_by(
                form_id=form.id,
                is_active=True
            ).order_by(AssessmentQuestion.order.asc()).all()
            all_questions.extend(form_questions)
        
        for question in all_questions:
            # Skip if we've already processed this question (prevent duplicates)
            if question.id in processed_question_ids:
                continue
            processed_question_ids.add(question.id)
            
            question_row = {
                'question': question,
                'responses': {},
                'average_rating': 0,
                'response_count': 0
            }
            
            total_rating = 0
            rating_count = 0
            responses_for_ai = []
            
            for reviewer_id, reviewer in reviewers.items():
                # Find assignment for this reviewer
                assignment = next((a for a in assignments if a.reviewer_id == reviewer_id), None)
                if assignment:
                    # Find response for this question in this assignment
                    try:
                        response = AssessmentResponse.query.filter_by(
                            assessment_assignment_id=assignment.id,
                            question_id=question.id
                        ).first()
                    except Exception as db_error:
                        print(f"Database error: {db_error}")
                        response = None
                    
                    if response:
                        response_data = response.get_response_data()
                        rating = None
                        comment = ""
                        
                        # Handle different response types
                        if question.question_type == 'rating' and response.response_number is not None:
                            rating = int(response.response_number)
                            comment = response.response_text or ""
                        elif question.question_type in ['text', 'textarea']:
                            comment = response.response_text or ""
                        else:
                            comment = str(response_data) if response_data else ""
                        
                        # Store response data
                        question_row['responses'][reviewer.name] = {
                            'rating': rating,
                            'comment': comment,
                            'text_response': comment,
                            'reviewer': reviewer,
                            'response_data': response_data
                        }
                        
                        if rating:
                            total_rating += rating
                            rating_count += 1
                            
                        # Collect for AI analysis (only valid responses with content)
                        if rating or comment:
                            responses_for_ai.append({
                                'reviewer': reviewer.name,
                                'rating': rating,
                                'comment': comment,
                                'reviewer_role': reviewer.role
                            })
                    else:
                        question_row['responses'][reviewer.name] = None
                else:
                    question_row['responses'][reviewer.name] = None
            
            # Calculate average rating for this question
            if rating_count > 0:
                question_row['average_rating'] = round(total_rating / rating_count, 2)
                question_row['response_count'] = rating_count
            
            # Generate AI-powered analysis for this question
            try:
                from ai_analysis import generate_feedback_summary
                ai_analysis = generate_feedback_summary(question.question_text, responses_for_ai)
                question_row['ai_analysis'] = ai_analysis
            except Exception as e:
                print(f"AI analysis error: {e}")
                question_row['ai_analysis'] = {
                    "summary": "AI analysis temporarily unavailable.",
                    "key_themes": ["Manual review required"],
                    "sentiment": "neutral"
                }
            
            # Add question to matrix if it has any responses or we want to show all
            matrix_data.append(question_row)
        
        # Calculate overall statistics
        total_reviewers = len(reviewers)  # Count ALL assigned reviewers
        completed_assignments = len([a for a in assignments if a.is_completed])
        completion_rate = round((completed_assignments / total_reviewers) * 100, 1) if total_reviewers > 0 else 0
        
        # Calculate overall average across all questions with ratings
        all_ratings = []
        for question_data in matrix_data:
            for reviewer_name, response in question_data['responses'].items():
                if response and response.get('rating'):
                    all_ratings.append(response['rating'])
        
        overall_matrix_average = round(sum(all_ratings) / len(all_ratings), 2) if all_ratings else 0
        
        # Generate comprehensive AI summary
        try:
            from ai_analysis import generate_overall_performance_summary
            overall_ai_summary = generate_overall_performance_summary(officer.name, matrix_data)
        except Exception as e:
            print(f"Overall AI summary error: {e}")
            overall_ai_summary = {
                "executive_summary": "Comprehensive performance analysis available with detailed reviewer feedback.",
                "major_themes": ["Multi-reviewer assessment", "Comprehensive evaluation"],
                "overall_sentiment": "satisfactory"
            }
    
        return render_template('officer_reviews_matrix.html',
                             officer=officer,
                             matrix_data=matrix_data,
                             reviewers=reviewers,
                             avg_rating=overall_matrix_average,
                             total_reviewers=total_reviewers,
                             overall_matrix_average=overall_matrix_average,
                             overall_ai_summary=overall_ai_summary,
                             current_period=current_period,
                             completion_rate=completion_rate,
                             completed_assignments=completed_assignments)
    except Exception as e:
        print(f"Database error in officer_reviews: {e}")
        flash('Database connection error. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/evaluate/<int:officer_id>', methods=['GET', 'POST'])
@login_required
def evaluate_officer(officer_id):
    # Allow board members, admins, and officers doing self-assessment
    if not (current_user.role in ['board_member', 'admin'] or 
            (current_user.role == 'officer' and current_user.id == officer_id)):
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    officer = User.query.get_or_404(officer_id)
    
    if request.method == 'GET':
        log_activity(current_user.id, 'start_evaluation', f'User started evaluation of officer: {officer.name}')
    else:
        log_activity(current_user.id, 'submit_evaluation', f'User submitted evaluation for officer: {officer.name}')
    if officer.role != 'officer':
        flash('Invalid officer selection.', 'error')
        return redirect(url_for('dashboard'))
    
    current_year = datetime.now().year
    
    # Check for existing assessment and assignment
    existing_assessment = Assessment.query.filter_by(
        officer_id=officer_id,
        reviewer_id=current_user.id,
        year=current_year
    ).first()
    
    # Find related assignment from active periods
    assignment = AssessmentAssignment.query.filter_by(
        officer_id=officer_id,
        reviewer_id=current_user.id
    ).join(AssessmentPeriod).filter(
        AssessmentPeriod.is_active == True
    ).first()
    
    # For GET requests with existing assessment, show the evaluation form with existing data (allow editing if period is open)
    # No redirect to view_assessment - let users edit their assessments during open periods
    
    # Load assessment questions from forms assigned to current period
    questions = []
    
    # Find the active assessment period
    current_period = AssessmentPeriod.query.filter_by(is_active=True).first()
    if current_period:
        # Determine if this is a self-assessment or external review
        is_self_assessment = (current_user.id == officer_id)
        form_type = 'self_review' if is_self_assessment else 'reviewer'
        
        # Get forms assigned to this period for the appropriate form type
        period_forms = PeriodFormAssignment.query.filter_by(
            period_id=current_period.id,
            form_type=form_type
        ).all()
        
        # Load questions from all assigned forms
        for period_form in period_forms:
            form_questions = AssessmentQuestion.query.filter_by(
                form_id=period_form.form_id,
                is_active=True
            ).order_by(AssessmentQuestion.order).all()
            questions.extend(form_questions)
    
    categories = Category.query.filter_by(is_active=True).order_by(Category.order).all()
    form = AssessmentForm()
    form.officer_id.data = officer_id
    
    # Load existing responses for editing
    existing_responses = {}
    if assignment:
        responses = AssessmentResponse.query.filter_by(assessment_assignment_id=assignment.id).all()
        for response in responses:
            existing_responses[response.question_id] = response
    
    # Pre-populate form with existing data if editing
    if existing_assessment:
        form.accomplishments.data = existing_assessment.accomplishments
        form.improvement_opportunities.data = existing_assessment.improvement_opportunities  
        form.focus_for_next_year.data = existing_assessment.focus_for_next_year
    
    if request.method == 'POST' and form.validate_on_submit():
        # Create or update assessment
        if existing_assessment:
            assessment = existing_assessment
        else:
            assessment = Assessment(
                officer_id=officer_id,
                reviewer_id=current_user.id,
                year=current_year
            )
            db.session.add(assessment)
        
        assessment.accomplishments = form.accomplishments.data
        assessment.improvement_opportunities = form.improvement_opportunities.data
        assessment.focus_for_next_year = form.focus_for_next_year.data
        assessment.submitted_at = datetime.utcnow()
        
        # Clear existing category ratings and assessment responses
        CategoryRating.query.filter_by(assessment_id=assessment.id).delete()
        # Clear existing assessment responses for this assignment
        if assignment:
            AssessmentResponse.query.filter_by(assessment_assignment_id=assignment.id).delete()
        
        # Process individual question responses
        total_rating = 0
        rating_count = 0
        category_ratings = {}
        
        for question in questions:
            # Get question response
            response_rating = request.form.get(f'question_{question.id}')
            response_comment = request.form.get(f'comment_{question.id}')
            
            if response_rating or response_comment:
                # Create assessment response - link to assignment instead of assessment
                if assignment:
                    question_response = AssessmentResponse(
                        assessment_assignment_id=assignment.id,
                        question_id=question.id
                    )
                    
                    if question.question_type == 'rating' and response_rating:
                        rating_val = int(response_rating)
                        question_response.response_number = rating_val
                        total_rating += rating_val
                        rating_count += 1
                        
                    elif question.question_type in ['text', 'textarea'] and response_rating:
                        question_response.response_text = response_rating
                        
                    elif question.question_type == 'date' and response_rating:
                        try:
                            question_response.response_date = datetime.strptime(response_rating, '%Y-%m-%d').date()
                        except:
                            question_response.response_text = response_rating
                    
                    elif question.question_type == 'boolean' and response_rating:
                        question_response.response_boolean = (response_rating.lower() == 'true')
                        question_response.response_text = response_rating
                    
                    elif question.question_type in ['checkbox', 'dropdown', 'multiple_choice'] and response_rating:
                        question_response.response_text = response_rating
                    
                    # Add comment if provided
                    if response_comment:
                        if question_response.response_text:
                            question_response.response_text += f"\n\nComment: {response_comment}"
                        else:
                            question_response.response_text = response_comment
                    
                    db.session.add(question_response)
        
        # Create category ratings for backward compatibility
        for category_id, ratings in category_ratings.items():
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                category_rating = CategoryRating(
                    assessment=assessment,
                    category_id=category_id,
                    rating=round(avg_rating)
                )
                db.session.add(category_rating)
        
        # Calculate overall rating
        assessment.overall_rating = total_rating / rating_count if rating_count > 0 else 0
        
        # Mark assignment as completed if it exists
        if assignment and not assignment.is_completed:
            assignment.is_completed = True
            assignment.completed_at = datetime.utcnow()
            assignment.assessment = assessment
        
        db.session.commit()
        flash(f'Assessment for {officer.name} has been submitted successfully.', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('evaluate.html', officer=officer, categories=categories, questions=questions, form=form, existing_responses=existing_responses, assignment=assignment)

# Create new assessment viewing system using AssessmentResponse
@app.route('/view_assessment_new/<int:assignment_id>')
@login_required
def view_assessment_new(assignment_id):
    assignment = AssessmentAssignment.query.get_or_404(assignment_id)
    
    # Check if user has permission to view this assessment
    if not (current_user.role == 'admin' or 
            current_user.id == assignment.reviewer_id or 
            current_user.id == assignment.officer_id):
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    log_activity(current_user.id, 'view_assessment_new', f'User viewed assessment for assignment #{assignment_id}')
    
    # Get assessment responses for this assignment
    assessment_responses = AssessmentResponse.query.filter_by(
        assessment_assignment_id=assignment_id
    ).all()
    
    # Get the assessment form used for this assignment
    # Determine form type based on whether it's self-assessment
    is_self_assessment = (assignment.officer_id == assignment.reviewer_id)
    form_type = 'self_review' if is_self_assessment else 'reviewer'
    
    # Get the form assigned to this period
    period_form = PeriodFormAssignment.query.filter_by(
        period_id=assignment.period_id,
        form_type=form_type
    ).first()
    
    assessment_form = None
    questions = []
    if period_form:
        assessment_form = period_form.assessment_form
        questions = AssessmentQuestion.query.filter_by(
            form_id=assessment_form.id,
            is_active=True
        ).order_by(AssessmentQuestion.order).all()
    
    # Create response lookup for easy access
    response_lookup = {resp.question_id: resp for resp in assessment_responses}
    
    return render_template('view_assessment_new.html', 
                         assignment=assignment,
                         assessment_form=assessment_form,
                         questions=questions,
                         responses=response_lookup)

@app.route('/officer_view')
@login_required
def officer_view():
    if current_user.role != 'officer':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    log_activity(current_user.id, 'view_officer_dashboard', f'Officer viewed their dashboard')
    current_year = datetime.now().year
    
    # Get all assessments for this officer
    assessments = Assessment.query.filter_by(
        officer_id=current_user.id,
        year=current_year
    ).all()
    
    # Calculate average ratings by category
    categories = Category.query.order_by(Category.order).all()
    category_averages = {}
    
    for category in categories:
        ratings = []
        for assessment in assessments:
            rating = CategoryRating.query.filter_by(
                assessment_id=assessment.id,
                category_id=category.id
            ).first()
            if rating:
                ratings.append(rating.rating)
        
        if ratings:
            category_averages[category.id] = {
                'category': category,
                'average': round(sum(ratings) / len(ratings), 2),
                'count': len(ratings)
            }
    
    # Calculate overall average
    overall_average = 0
    if assessments:
        total_ratings = sum(assessment.overall_rating for assessment in assessments if assessment.overall_rating)
        overall_average = round(total_ratings / len(assessments), 2) if assessments else 0
    
    return render_template('officer_view.html',
                         assessments=assessments,
                         category_averages=category_averages,
                         overall_average=overall_average,
                         categories=categories)

@app.route('/reports')
@login_required
@admin_required
def reports():
    log_activity(current_user.id, 'view_reports', f'Admin accessed reports page')
    current_year = datetime.now().year
    officers = User.query.filter_by(role='officer').all()
    categories = Category.query.order_by(Category.order).all()
    
    officer_reports = []
    for officer in officers:
        assessments = Assessment.query.filter_by(officer_id=officer.id, year=current_year).all()
        
        if assessments:
            # Calculate category averages
            category_data = {}
            for category in categories:
                ratings = []
                for assessment in assessments:
                    rating = CategoryRating.query.filter_by(
                        assessment_id=assessment.id,
                        category_id=category.id
                    ).first()
                    if rating:
                        ratings.append(rating.rating)
                
                if ratings:
                    category_data[category.id] = round(sum(ratings) / len(ratings), 2)
                else:
                    category_data[category.id] = 0
            
            overall_avg = round(sum(assessment.overall_rating for assessment in assessments if assessment.overall_rating) / len(assessments), 2)
            
            officer_reports.append({
                'officer': officer,
                'assessments_count': len(assessments),
                'overall_average': overall_avg,
                'category_averages': category_data
            })
    
    return render_template('reports.html', officer_reports=officer_reports, categories=categories)

@app.route('/export_pdf/<int:officer_id>')
@login_required
@admin_required
def export_pdf(officer_id):
    officer = User.query.get_or_404(officer_id)
    current_year = datetime.now().year
    
    assessments = Assessment.query.filter_by(officer_id=officer_id, year=current_year).all()
    
    if not assessments:
        flash('No assessments found for this officer.', 'error')
        return redirect(url_for('reports'))
    
    pdf_data = generate_pdf_report(officer, assessments)
    
    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={officer.name}_assessment_{current_year}.pdf'
    
    return response

@app.route('/admin/export_matrix_pdf/<int:officer_id>')
@login_required
@admin_required
def export_matrix_pdf(officer_id):
    try:
        officer = User.query.get_or_404(officer_id)
        if officer.role != 'officer':
            flash('Invalid officer selection.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        # Get current active assessment period
        current_period = AssessmentPeriod.query.filter_by(is_active=True).first()
        if not current_period:
            flash('No active assessment period found.', 'warning')
            return redirect(url_for('admin_dashboard'))
        
        # Get all assignments for this officer in the current period
        assignments = AssessmentAssignment.query.filter_by(
            officer_id=officer_id,
            period_id=current_period.id
        ).all()
        
        if not assignments:
            flash(f'No assessment assignments found for {officer.name} in the current period.', 'warning')
            return redirect(url_for('admin_dashboard'))
        
        # Create reviewers list from ALL ASSIGNMENTS
        reviewers = {}
        for assignment in assignments:
            reviewers[assignment.reviewer.id] = assignment.reviewer
        
        # Get all assessment forms assigned to this period for reviewers
        reviewer_forms = db.session.query(AssessmentForm).join(PeriodFormAssignment).filter(
            PeriodFormAssignment.period_id == current_period.id,
            PeriodFormAssignment.form_type == 'reviewer',
            PeriodFormAssignment.is_active == True,
            AssessmentForm.is_active == True
        ).all()
        
        # Build matrix data: questions in rows, reviewers in columns
        matrix_data = []
        processed_question_ids = set()
        
        # Get all questions from all reviewer forms
        all_questions = []
        for form in reviewer_forms:
            form_questions = AssessmentQuestion.query.filter_by(
                form_id=form.id,
                is_active=True
            ).order_by(AssessmentQuestion.order.asc()).all()
            all_questions.extend(form_questions)
        
        for question in all_questions:
            if question.id in processed_question_ids:
                continue
            processed_question_ids.add(question.id)
            
            question_row = {
                'question': question,
                'responses': {},
                'average_rating': 0,
                'response_count': 0
            }
            
            total_rating = 0
            rating_count = 0
            responses_for_ai = []
            
            for reviewer_id, reviewer in reviewers.items():
                assignment = next((a for a in assignments if a.reviewer_id == reviewer_id), None)
                if assignment:
                    response = AssessmentResponse.query.filter_by(
                        assessment_assignment_id=assignment.id,
                        question_id=question.id
                    ).first()
                    
                    if response:
                        response_data = response.get_response_data()
                        rating = None
                        comment = ""
                        
                        if question.question_type == 'rating' and response.response_number is not None:
                            rating = int(response.response_number)
                            comment = response.response_text or ""
                        elif question.question_type in ['text', 'textarea']:
                            comment = response.response_text or ""
                        else:
                            comment = str(response_data) if response_data else ""
                        
                        question_row['responses'][reviewer.name] = {
                            'rating': rating,
                            'comment': comment,
                            'text_response': comment,
                            'reviewer': reviewer,
                            'response_data': response_data
                        }
                        
                        if rating:
                            total_rating += rating
                            rating_count += 1
                            
                        if rating or comment:
                            responses_for_ai.append({
                                'reviewer': reviewer.name,
                                'rating': rating,
                                'comment': comment,
                                'reviewer_role': reviewer.role
                            })
                    else:
                        question_row['responses'][reviewer.name] = None
                else:
                    question_row['responses'][reviewer.name] = None
            
            if rating_count > 0:
                question_row['average_rating'] = round(total_rating / rating_count, 2)
                question_row['response_count'] = rating_count
            
            try:
                from ai_analysis import generate_feedback_summary
                ai_analysis = generate_feedback_summary(question.question_text, responses_for_ai)
                question_row['ai_analysis'] = ai_analysis
            except Exception as e:
                question_row['ai_analysis'] = {
                    "summary": "AI analysis temporarily unavailable.",
                    "key_themes": ["Manual review required"],
                    "sentiment": "neutral"
                }
            
            matrix_data.append(question_row)
        
        # Calculate overall average
        all_ratings = []
        for question_data in matrix_data:
            for reviewer_name, response in question_data['responses'].items():
                if response and response.get('rating'):
                    all_ratings.append(response['rating'])
        
        overall_matrix_average = round(sum(all_ratings) / len(all_ratings), 2) if all_ratings else 0
        
        # Generate comprehensive AI summary
        try:
            from ai_analysis import generate_overall_performance_summary
            overall_ai_summary = generate_overall_performance_summary(officer.name, matrix_data)
        except Exception as e:
            overall_ai_summary = {
                "executive_summary": "Comprehensive performance analysis available with detailed reviewer feedback.",
                "major_themes": ["Multi-reviewer assessment", "Comprehensive evaluation"],
                "overall_sentiment": "satisfactory"
            }
        
        pdf_buffer = generate_matrix_pdf_report(officer, matrix_data, reviewers, overall_matrix_average, overall_ai_summary)
        
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{officer.name}_matrix_report.pdf"'
        
        log_activity(current_user.id, 'export_matrix_pdf', f'Exported matrix PDF report for {officer.name}')
        
        return response
        
    except Exception as e:
        print(f"Error generating matrix PDF: {e}")
        flash('Error generating PDF export. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))
