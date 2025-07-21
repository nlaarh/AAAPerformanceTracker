"""
Simple Table-Based Workflow Visualization
Creates a clean table showing workflow stages as columns and reviewers as rows
"""

def create_workflow_table(officer_id, period_id):
    """Create a simple table showing workflow stages as columns and reviewers as rows"""
    try:
        from models import AssessmentAssignment, User, AssessmentPeriod
        from assessment_activity_logger import get_assessment_timeline
        
        # Get timeline data and assessment assignments
        timeline = get_assessment_timeline(officer_id, period_id)
        completed_events = [item['event_type'] for item in timeline] if timeline else []
        
        # Get all assignments for this officer/period
        assignments = AssessmentAssignment.query.filter_by(
            officer_id=officer_id,
            period_id=period_id
        ).all()
        
        # Get period and officer info
        period = AssessmentPeriod.query.get(period_id)
        officer = User.query.get(officer_id)
        
        def get_stage_status(stage_id):
            # Check the actual events in the database for accurate status
            if stage_id == 'assignment':
                # Assignment is completed if there are any assessment assignments
                return 'completed' if assignments else 'not_started'
            
            elif stage_id == 'self_assessment':
                # Check if self-assessment was submitted
                if 'self_assessment_submitted' in completed_events:
                    return 'completed'
                elif 'self_assessment_draft_saved' in completed_events:
                    return 'in_progress'
                else:
                    return 'not_started'
            
            elif stage_id == 'admin_review':
                # Admin review comes after self-assessment submission
                if 'self_assessment_approved' in completed_events:
                    return 'completed'
                elif 'self_assessment_submitted' in completed_events:
                    # Check if reviewers are already working - indicates implicit approval
                    reviewer_activities = [e for e in completed_events if 'reviewer_assessment' in e]
                    if reviewer_activities:
                        return 'completed'  # Implicitly approved since reviewers are working
                    else:
                        return 'pending_admin'  # Waiting for admin approval
                else:
                    return 'not_started'
            
            elif stage_id == 'reviewers_released':
                # Reviewers are released after admin approves self-assessment
                if 'reviewers_released' in completed_events:
                    return 'completed'
                elif 'self_assessment_approved' in completed_events:
                    return 'ready_to_release'  # Admin can release reviewers
                else:
                    # Check if reviewers are already working - indicates implicit release
                    reviewer_activities = [e for e in completed_events if 'reviewer_assessment' in e]
                    if reviewer_activities:
                        return 'completed'  # Implicitly released since reviewers are working
                    else:
                        return 'not_started'
            
            elif stage_id == 'final_approval':
                if 'assessment_approved_final' in completed_events:
                    return 'completed'
                else:
                    return 'not_started'
            
            elif stage_id == 'results_released':
                if 'results_released_to_reviewee' in completed_events:
                    return 'completed'
                else:
                    return 'not_started'
            
            return 'not_started'
        
        # Define workflow stages
        stages = [
            {'id': 'assignment', 'name': 'Assignment Created'},
            {'id': 'self_assessment', 'name': 'Self Assessment'},
            {'id': 'admin_review', 'name': 'Admin Review'},
            {'id': 'reviewers_released', 'name': 'Reviewers Released'},
            {'id': 'pending_review', 'name': 'Pending Review'},
            {'id': 'review_completed', 'name': 'Review Completed'},
            {'id': 'final_approval', 'name': 'Final Approval'},
            {'id': 'results_released', 'name': 'Results Released'}
        ]
        
        # Create table HTML
        table_html = f'''
        <div class="workflow-table-container" style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.1); margin: 20px 0;">
            <h4 class="text-center mb-4">Assessment Workflow Status for {officer.name if officer else "Officer"}</h4>
            <p class="text-center text-muted mb-4">{period.name if period else "Assessment Period"}</p>
            
            <div class="table-responsive">
                <table class="table table-bordered table-hover">
                    <thead class="table-light">
                        <tr>
                            <th style="width: 200px;">Reviewer / Role</th>
        '''
        
        # Add column headers for each stage
        for stage in stages:
            table_html += f'<th class="text-center" style="min-width: 120px;">{stage["name"]}</th>'
        
        table_html += '</tr></thead><tbody>'
        
        # Add rows for each reviewer
        for assignment in assignments:
            reviewer = assignment.reviewer
            is_self = assignment.officer_id == assignment.reviewer_id
            
            # Reviewer name and badge
            badge_class = 'badge bg-primary' if is_self else 'badge bg-secondary'
            badge_text = 'Self' if is_self else 'External'
            
            table_html += f'''
            <tr>
                <td>
                    <strong>{'SELF: ' if is_self else ''}{reviewer.name}</strong>
                    <br><span class="{badge_class}">{badge_text}</span>
                </td>
            '''
            
            # Add status for each stage - show only RELEVANT information
            for stage in stages:
                cell_html = ''
                
                if is_self:
                    # Self-assessment row - only show status for self-assessment related stages
                    if stage['id'] == 'assignment':
                        status = get_stage_status('assignment')
                        cell_html = '<span class="badge bg-success">✓ Assigned</span>' if status == 'completed' else '<span class="badge bg-light text-dark">○ Not Started</span>'
                    elif stage['id'] == 'self_assessment':
                        status = get_stage_status('self_assessment')
                        if status == 'completed':
                            cell_html = '<span class="badge bg-success">✓ Submitted</span>'
                        elif status == 'in_progress':
                            cell_html = '<span class="badge bg-primary">● In Progress</span>'
                        else:
                            cell_html = '<span class="badge bg-light text-dark">○ Not Started</span>'
                    elif stage['id'] == 'admin_review':
                        status = get_stage_status('admin_review')
                        if status == 'completed':
                            cell_html = '<span class="badge bg-success">✓ Approved</span>'
                        elif status == 'pending_admin':
                            cell_html = '<span class="badge bg-warning">⏳ Pending Admin</span>'
                        else:
                            cell_html = ''  # Empty until self-assessment is done
                    elif stage['id'] == 'reviewers_released':
                        status = get_stage_status('reviewers_released')
                        if status == 'completed':
                            cell_html = '<span class="badge bg-success">✓ Released</span>'
                        elif status == 'ready_to_release':
                            cell_html = '<span class="badge bg-info">Ready to Release</span>'
                        else:
                            cell_html = ''  # Empty until applicable
                    else:
                        cell_html = ''  # Empty for non-relevant stages
                else:
                    # External reviewer row - check individual reviewer status
                    # Get events specific to this reviewer by checking assignments
                    reviewer_events = []
                    for event in timeline:
                        # Check if this event is related to this specific reviewer
                        if event.get('reviewer') == reviewer.name or (
                            'reviewer_assessment' in event.get('event_type', '') and 
                            event.get('assignment_id') == assignment.id
                        ):
                            reviewer_events.append(event)
                    
                    reviewer_event_types = [event['event_type'] for event in reviewer_events]
                    
                    if stage['id'] == 'assignment':
                        cell_html = '<span class="badge bg-success">✓ Assigned</span>' if get_stage_status('assignment') == 'completed' else ''
                    elif stage['id'] == 'reviewers_released':
                        if get_stage_status('reviewers_released') == 'completed':
                            cell_html = '<span class="badge bg-success">✓ Released</span>'
                        else:
                            cell_html = ''  # Empty until released
                    elif stage['id'] == 'pending_review':
                        # Show individual reviewer status during review phase
                        if get_stage_status('reviewers_released') == 'completed':
                            if assignment.is_completed:
                                cell_html = '<span class="badge bg-success">✓ Submitted</span>'
                            elif 'reviewer_draft_saved' in reviewer_event_types:
                                cell_html = '<span class="badge bg-primary">● In Progress</span>'
                            else:
                                cell_html = '<span class="badge bg-warning">⏳ Not Started</span>'
                        elif get_stage_status('admin_review') == 'pending_admin':
                            cell_html = '<span class="badge bg-secondary">⏸ Waiting for Approval</span>'
                        else:
                            cell_html = ''  # Empty until reviewers are released
                    elif stage['id'] == 'review_completed':
                        # Show completion status
                        if assignment.is_completed:
                            cell_html = '<span class="badge bg-success">✓ Completed</span>'
                        elif get_stage_status('reviewers_released') == 'completed':
                            cell_html = '<span class="badge bg-light text-dark">○ Pending</span>'
                        else:
                            cell_html = ''  # Empty until reviewer phase
                    else:
                        cell_html = ''  # Empty for non-relevant stages
                
                table_html += f'<td class="text-center">{cell_html}</td>'
            
            table_html += '</tr>'
        
        table_html += '''
                    </tbody>
                </table>
            </div>
            
            <div class="mt-3">
                <small class="text-muted">
                    <strong>Legend:</strong>
                    <span class="badge bg-success ms-2">✓ Completed</span>
                    <span class="badge bg-primary ms-2">● In Progress</span>
                    <span class="badge bg-warning ms-2">⏳ Pending</span>
                    <span class="badge bg-info ms-2">Ready</span>
                    <span class="badge bg-secondary ms-2">⏸ Waiting</span>
                    <span class="badge bg-light text-dark ms-2">○ Not Started</span>
                    <br><strong>Note:</strong> Empty cells indicate the stage is not relevant for that reviewer type.
                </small>
            </div>
        </div>
        '''
        
        return table_html
        
    except Exception as e:
        print(f"Error creating workflow table: {e}")
        return '<div class="alert alert-warning">Error creating workflow table</div>'