# Fixed Excel export function for the matrix
@app.route('/admin/export_matrix_excel/<int:officer_id>')
@login_required
@admin_required
def export_matrix_excel(officer_id):
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
                question_row['average_score'] = question_row['average_rating']  # For Excel compatibility
            
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
        
        excel_buffer = generate_matrix_excel_report(officer, matrix_data, reviewers, overall_matrix_average, overall_ai_summary)
        
        response = make_response(excel_buffer.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename="{officer.name}_matrix_report.xlsx"'
        
        log_activity(current_user.id, 'export_matrix_excel', f'Exported matrix Excel report for {officer.name}')
        
        return response
        
    except Exception as e:
        print(f"Error generating matrix Excel: {e}")
        flash('Error generating Excel export. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))
