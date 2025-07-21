"""
Assessment Progress Visualizer
Creates stunning visual charts for assessment workflow progress using Plotly
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from models import AssessmentProject, AssessmentStatus, AssessmentAssignment, User, AssessmentPeriod
from assessment_activity_logger import get_assessment_timeline, get_assessment_progress_summary
import json

class AssessmentVisualizer:
    
    # Beautiful color scheme
    COLORS = {
        'not_started': '#E5E7EB',      # Light gray
        'in_progress': '#3B82F6',       # Blue
        'completed': '#10B981',         # Green
        'pending': '#F59E0B',           # Orange
        'blocked': '#EF4444',           # Red
        'approved': '#8B5CF6',          # Purple
        'background': '#F9FAFB',        # Very light gray
        'text': '#1F2937',              # Dark gray
        'accent': '#6366F1'             # Indigo
    }
    
    WORKFLOW_STAGES = [
        {'id': 'assignment', 'name': 'Assignment Created', 'icon': '📋'},
        {'id': 'self_assessment', 'name': 'Self-Assessment', 'icon': '📝'},
        {'id': 'admin_review', 'name': 'Admin Review', 'icon': '✅'},
        {'id': 'reviewers_released', 'name': 'Reviewers Released', 'icon': '🚀'},
        {'id': 'reviewer_assessments', 'name': 'Reviewer Assessments', 'icon': '👥'},
        {'id': 'final_approval', 'name': 'Final Admin Approval', 'icon': '🏆'},
        {'id': 'results_released', 'name': 'Results Released', 'icon': '📊'},
        {'id': 'acknowledged', 'name': 'Reviewee Acknowledged', 'icon': '✅'},
        {'id': 'closed', 'name': 'Assessment Closed', 'icon': '🎯'}
    ]
    
    def __init__(self):
        pass
    
    def create_assessment_timeline_chart(self, officer_id, period_id):
        """Create a comprehensive workflow diagram with reviewer branches"""
        try:
            from models import AssessmentAssignment, User, AssessmentPeriod
            
            # Get timeline data and assessment assignments
            timeline = get_assessment_timeline(officer_id, period_id)
            completed_events = [item['event_type'] for item in timeline] if timeline else []
            
            # Get all assignments for this officer/period to show reviewer branches
            assignments = AssessmentAssignment.query.filter_by(
                officer_id=officer_id,
                period_id=period_id
            ).all()
            
            # Get period and officer info
            period = AssessmentPeriod.query.get(period_id)
            officer = User.query.get(officer_id)
            
            # Define main workflow stages
            main_stages = [
                {'id': 'assignment', 'name': 'Assignment\nCreated', 'icon': '📋'},
                {'id': 'self_assessment', 'name': 'Self-Assessment\nCompleted', 'icon': '📝'},
                {'id': 'admin_review', 'name': 'Admin\nApproval', 'icon': '✅'},
                {'id': 'reviewers_released', 'name': 'Reviewers\nReleased', 'icon': '🚀'},
                {'id': 'final_approval', 'name': 'Final Admin\nApproval', 'icon': '🏆'},
                {'id': 'results_released', 'name': 'Results\nReleased', 'icon': '📊'}
            ]
            
            def get_stage_status(stage_id):
                stage_events = {
                    'assignment': ['self_assessment_assigned', 'reviewer_assignment_created'],
                    'self_assessment': ['self_assessment_submitted'],
                    'admin_review': ['self_assessment_approved'],
                    'reviewers_released': ['reviewers_released'],
                    'final_approval': ['assessment_approved_final'],
                    'results_released': ['results_released_to_reviewee']
                }
                
                events = stage_events.get(stage_id, [])
                if any(event in completed_events for event in events):
                    return 'completed'
                
                # Check if we should mark as in progress
                stage_index = next(i for i, s in enumerate(main_stages) if s['id'] == stage_id)
                if stage_index > 0:
                    prev_stage = main_stages[stage_index - 1]
                    prev_events = stage_events.get(prev_stage['id'], [])
                    if any(event in completed_events for event in prev_events):
                        return 'in_progress'
                elif stage_index == 0 and completed_events:
                    return 'in_progress'
                
                return 'not_started'
            
            # SVG dimensions for horizontal workflow with vertical reviewer branches
            svg_width = 1000
            svg_height = 300 + (len(assignments) * 80)  # Space for reviewer branches
            circle_radius = 12
            stage_spacing = 60
            start_x = 100
            start_y = 80
            
            # Status colors
            colors = {
                'completed': '#10B981',     # Green
                'in_progress': '#3B82F6',   # Blue  
                'not_started': '#E5E7EB',   # Light gray
                'pending': '#F59E0B'        # Orange
            }
            
            # Build SVG elements for simple horizontal workflow with vertical reviewer branches
            svg_elements = []
            
            # Title
            svg_elements.append(f'<text x="{svg_width//2}" y="30" text-anchor="middle" font-family="Arial Black" font-size="18" fill="#1F2937">Assessment Workflow for {officer.name if officer else "Officer"}</text>')
            svg_elements.append(f'<text x="{svg_width//2}" y="50" text-anchor="middle" font-family="Arial" font-size="14" fill="#6B7280">{period.name if period else "Assessment Period"}</text>')
            
            # Main horizontal workflow line
            main_y = 100
            main_stages = [
                {'id': 'self_assessment', 'name': 'Self Assessment', 'x': 100},
                {'id': 'admin_review', 'name': 'Admin Review', 'x': 300},
                {'id': 'reviewers_released', 'name': 'Reviewers Released', 'x': 500},
                {'id': 'final_approval', 'name': 'Admin Approval', 'x': 700},
                {'id': 'results_released', 'name': 'Results Released', 'x': 900}
            ]
            
            # Draw main horizontal line
            svg_elements.append(f'<line x1="100" y1="{main_y}" x2="900" y2="{main_y}" stroke="#D1D5DB" stroke-width="4"/>')
            
            # Draw main workflow stages
            for stage in main_stages:
                status = get_stage_status(stage['id'])
                x = stage['x']
                
                # Draw circle
                if status == 'completed':
                    svg_elements.append(f'<circle cx="{x}" cy="{main_y}" r="{circle_radius}" fill="#22C55E" stroke="#22C55E" stroke-width="2"/>')
                    svg_elements.append(f'<text x="{x}" y="{main_y + 4}" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="white">✓</text>')
                elif status == 'in_progress':
                    svg_elements.append(f'<circle cx="{x}" cy="{main_y}" r="{circle_radius}" fill="#3B82F6" stroke="#3B82F6" stroke-width="2"/>')
                else:
                    svg_elements.append(f'<circle cx="{x}" cy="{main_y}" r="{circle_radius}" fill="none" stroke="#E5E7EB" stroke-width="2"/>')
                
                # Stage label
                svg_elements.append(f'<text x="{x}" y="{main_y + 35}" text-anchor="middle" font-family="Arial" font-size="11" font-weight="500" fill="#374151">{stage["name"]}</text>')
            
            # Draw vertical branches for each reviewer from "Reviewers Released" point
            reviewer_start_x = 500  # Position of "Reviewers Released" stage
            reviewer_base_y = main_y + 60
            reviewer_spacing = 80
            
            svg_elements.append(f'<text x="50" y="{reviewer_base_y + 10}" font-family="Arial" font-size="12" font-weight="bold" fill="#374151">Individual Reviewers:</text>')
            
            for idx, assignment in enumerate(assignments):
                reviewer = assignment.reviewer
                is_self = assignment.officer_id == assignment.reviewer_id
                
                reviewer_y = reviewer_base_y + 30 + (idx * reviewer_spacing)
                
                # Draw vertical line down from main workflow
                svg_elements.append(f'<line x1="{reviewer_start_x}" y1="{main_y + 20}" x2="{reviewer_start_x}" y2="{reviewer_y - 30}" stroke="#E5E7EB" stroke-width="2"/>')
                
                # Draw horizontal line for this reviewer
                svg_elements.append(f'<line x1="{reviewer_start_x}" y1="{reviewer_y}" x2="800" y2="{reviewer_y}" stroke="#E5E7EB" stroke-width="2"/>')
                
                # Reviewer label
                reviewer_label = f"{'SELF: ' if is_self else ''}{reviewer.name}"
                svg_elements.append(f'<text x="100" y="{reviewer_y + 4}" font-family="Arial" font-size="11" font-weight="500" fill="#374151">{reviewer_label}</text>')
                
                # Badge
                badge_color = '#8B5CF6' if is_self else '#6B7280'
                badge_text = 'Self' if is_self else 'External'
                svg_elements.append(f'<rect x="250" y="{reviewer_y - 8}" width="40" height="16" rx="8" fill="{badge_color}"/>')
                svg_elements.append(f'<text x="270" y="{reviewer_y + 2}" text-anchor="middle" font-family="Arial" font-size="9" font-weight="bold" fill="white">{badge_text}</text>')
                
                # Reviewer status circles
                # Pending Assessment circle
                pending_x = 550
                if assignment.is_completed:
                    svg_elements.append(f'<circle cx="{pending_x}" cy="{reviewer_y}" r="{circle_radius}" fill="#22C55E" stroke="#22C55E" stroke-width="2"/>')
                    svg_elements.append(f'<text x="{pending_x}" y="{reviewer_y + 4}" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="white">✓</text>')
                elif get_stage_status('reviewers_released') == 'completed':
                    svg_elements.append(f'<circle cx="{pending_x}" cy="{reviewer_y}" r="{circle_radius}" fill="#3B82F6" stroke="#3B82F6" stroke-width="2"/>')
                else:
                    svg_elements.append(f'<circle cx="{pending_x}" cy="{reviewer_y}" r="{circle_radius}" fill="none" stroke="#E5E7EB" stroke-width="2"/>')
                
                # Individual Approval circle (before final approval)
                approval_x = 650
                if assignment.is_completed:
                    svg_elements.append(f'<circle cx="{approval_x}" cy="{reviewer_y}" r="{circle_radius}" fill="#22C55E" stroke="#22C55E" stroke-width="2"/>')
                    svg_elements.append(f'<text x="{approval_x}" y="{reviewer_y + 4}" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="white">✓</text>')
                else:
                    svg_elements.append(f'<circle cx="{approval_x}" cy="{reviewer_y}" r="{circle_radius}" fill="none" stroke="#E5E7EB" stroke-width="2"/>')
                
                # Connect back to main workflow at Final Approval
                if assignment.is_completed:
                    svg_elements.append(f'<line x1="{approval_x + 15}" y1="{reviewer_y}" x2="700" y2="{main_y + 20}" stroke="#22C55E" stroke-width="2" stroke-dasharray="3,3"/>')
            
            # Add labels for reviewer stages
            svg_elements.append(f'<text x="550" y="{reviewer_base_y + 15}" text-anchor="middle" font-family="Arial" font-size="10" font-weight="500" fill="#374151">Assessment</text>')
            svg_elements.append(f'<text x="650" y="{reviewer_base_y + 15}" text-anchor="middle" font-family="Arial" font-size="10" font-weight="500" fill="#374151">Completed</text>')
            
            # Simple legend matching the circles
            legend_y = svg_height - 40
            
            svg_elements.append(f'<text x="50" y="{legend_y - 15}" font-family="Arial" font-size="12" font-weight="bold" fill="#374151">Status Legend:</text>')
            
            # Completed legend - green circle with checkmark
            legend_x = 50
            svg_elements.append(f'<circle cx="{legend_x}" cy="{legend_y}" r="12" fill="#22C55E" stroke="#22C55E" stroke-width="2"/>')
            svg_elements.append(f'<text x="{legend_x}" y="{legend_y + 4}" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="white">✓</text>')
            svg_elements.append(f'<text x="{legend_x + 20}" y="{legend_y + 4}" font-family="Arial" font-size="11" fill="#374151">Completed</text>')
            
            # In Progress legend - blue filled circle
            legend_x += 120
            svg_elements.append(f'<circle cx="{legend_x}" cy="{legend_y}" r="12" fill="#3B82F6" stroke="#3B82F6" stroke-width="2"/>')
            svg_elements.append(f'<text x="{legend_x + 20}" y="{legend_y + 4}" font-family="Arial" font-size="11" fill="#374151">In Progress</text>')
            
            # Not Started legend - empty circle
            legend_x += 120
            svg_elements.append(f'<circle cx="{legend_x}" cy="{legend_y}" r="12" fill="none" stroke="#E5E7EB" stroke-width="2"/>')
            svg_elements.append(f'<text x="{legend_x + 20}" y="{legend_y + 4}" font-family="Arial" font-size="11" fill="#374151">Not Started</text>')
            
            # Complete SVG
            svg_content = f'''
            <div class="comprehensive-workflow" style="background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.1); margin: 20px 0;">
                <svg width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}" style="width: 100%; height: auto; min-height: 300px;">
                    {''.join(svg_elements)}
                </svg>
            </div>
            '''
            
            return svg_content
            
        except Exception as e:
            print(f"Error creating comprehensive workflow chart: {e}")
            return '<div class="alert alert-warning">Error creating workflow chart</div>'

    
    def create_reviewer_progress_chart(self, officer_id, period_id):
        """Create a chart showing individual reviewer progress"""
        # Get all assignments for this officer/period
        assignments = AssessmentAssignment.query.filter_by(
            officer_id=officer_id,
            period_id=period_id
        ).all()
        
        reviewer_data = []
        for assignment in assignments:
            reviewer = assignment.reviewer
            is_self = assignment.officer_id == assignment.reviewer_id
            
            status = 'Completed' if assignment.is_completed else 'Pending'
            review_type = 'Self-Assessment' if is_self else 'External Review'
            
            reviewer_data.append({
                'Reviewer': reviewer.name,
                'Type': review_type,
                'Status': status,
                'Completed Date': assignment.completed_at.strftime('%Y-%m-%d') if assignment.completed_at else 'Pending'
            })
        
        df = pd.DataFrame(reviewer_data)
        
        # Create sunburst chart for reviewer distribution
        fig = go.Figure(go.Sunburst(
            labels=['All Reviewers'] + df['Reviewer'].tolist() + df['Type'].tolist(),
            parents=[''] + ['All Reviewers'] * len(df) + df['Reviewer'].tolist(),
            values=[len(df)] + [1] * len(df) + [1] * len(df),
            branchvalues='total',
            hovertemplate='<b>%{label}</b><br>Count: %{value}<extra></extra>',
            marker=dict(
                colors=[self.COLORS['accent']] + 
                       [self.COLORS['completed'] if status == 'Completed' else self.COLORS['pending'] 
                        for status in df['Status']] +
                       [self.COLORS['in_progress'] if review_type == 'Self-Assessment' else self.COLORS['accent'] 
                        for review_type in df['Type']]
            )
        ))
        
        fig.update_layout(
            title=dict(
                text='Reviewer Assignment Overview',
                font=dict(size=18, color=self.COLORS['text']),
                x=0.5
            ),
            font=dict(family='Inter, sans-serif', color=self.COLORS['text']),
            paper_bgcolor='white',
            height=500
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id="reviewer-chart")
    
    def create_assessment_status_gauge(self, officer_id, period_id):
        """Create a gauge chart showing overall assessment completion"""
        # Get assessment project
        project = AssessmentProject.query.filter_by(
            officer_id=officer_id,
            period_id=period_id
        ).first()
        
        # Calculate completion percentage based on status
        status_progress = {
            AssessmentStatus.PENDING_SELF_ASSESSMENT: 0,
            AssessmentStatus.SELF_ASSESSMENT_SUBMITTED: 15,
            AssessmentStatus.AWAITING_ADMIN_REVIEW: 25,
            AssessmentStatus.ADMIN_REVIEW_COMPLETED: 35,
            AssessmentStatus.AWAITING_REVIEWER_ASSESSMENTS: 45,
            AssessmentStatus.REVIEWER_ASSESSMENTS_IN_PROGRESS: 65,
            AssessmentStatus.REVIEWER_ASSESSMENTS_COMPLETED: 75,
            AssessmentStatus.AWAITING_FINAL_ADMIN_APPROVAL: 85,
            AssessmentStatus.ASSESSMENT_APPROVED_BY_ADMIN: 90,
            AssessmentStatus.RESULTS_RELEASED_TO_REVIEWEE: 95,
            AssessmentStatus.REVIEWEE_ACKNOWLEDGED_RESULTS: 98,
            AssessmentStatus.ASSESSMENT_CLOSED: 100
        }
        
        progress = status_progress.get(project.status if project else AssessmentStatus.PENDING_SELF_ASSESSMENT, 0)
        status_text = AssessmentStatus.get_status_display(project.status) if project else "Not Started"
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=progress,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"Assessment Completion<br><span style='font-size:0.8em;color:gray'>{status_text}</span>"},
            delta={'reference': 100},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': self.COLORS['in_progress']},
                'steps': [
                    {'range': [0, 25], 'color': self.COLORS['not_started']},
                    {'range': [25, 50], 'color': self.COLORS['pending']},
                    {'range': [50, 75], 'color': self.COLORS['in_progress']},
                    {'range': [75, 100], 'color': self.COLORS['completed']}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(
            paper_bgcolor='white',
            font=dict(family='Inter, sans-serif', color=self.COLORS['text']),
            height=400
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id="status-gauge")
    
    def create_period_overview_chart(self, period_id):
        """Create overview chart for entire assessment period"""
        # Get all projects in this period
        projects = AssessmentProject.query.filter_by(period_id=period_id).all()
        
        status_counts = {}
        for project in projects:
            status_display = AssessmentStatus.get_status_display(project.status)
            status_counts[status_display] = status_counts.get(status_display, 0) + 1
        
        # Create donut chart
        fig = go.Figure(go.Pie(
            labels=list(status_counts.keys()),
            values=list(status_counts.values()),
            hole=0.5,
            marker_colors=[
                self.COLORS['not_started'] if 'Pending' in label else
                self.COLORS['pending'] if 'Awaiting' in label else
                self.COLORS['in_progress'] if 'Progress' in label else
                self.COLORS['completed'] if 'Completed' in label or 'Closed' in label else
                self.COLORS['approved'] if 'Approved' in label else
                self.COLORS['accent']
                for label in status_counts.keys()
            ],
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
        ))
        
        # Add center text
        total_assessments = len(projects)
        fig.add_annotation(
            text=f"<b>{total_assessments}</b><br>Total<br>Assessments",
            x=0.5, y=0.5,
            font_size=16,
            showarrow=False
        )
        
        fig.update_layout(
            title=dict(
                text='Assessment Period Overview',
                font=dict(size=18, color=self.COLORS['text']),
                x=0.5
            ),
            paper_bgcolor='white',
            font=dict(family='Inter, sans-serif', color=self.COLORS['text']),
            height=400,
            showlegend=True,
            legend=dict(
                orientation='v',
                yanchor='middle',
                y=0.5,
                xanchor='left',
                x=1.05
            )
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id="period-overview")
    
    def create_activity_heatmap(self, period_id, days=30):
        """Create activity heatmap showing daily assessment activity"""
        from assessment_activity_logger import get_assessment_activity_logs
        
        # Get recent activity logs
        activities = get_assessment_activity_logs(period_id=period_id, limit=1000)
        
        # Create daily activity data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        activity_data = {date.date(): 0 for date in date_range}
        
        for activity in activities:
            activity_date = activity.timestamp.date()
            if start_date <= activity_date <= end_date:
                activity_data[activity_date] += 1
        
        # Create heatmap data
        dates = list(activity_data.keys())
        values = list(activity_data.values())
        
        # Create calendar heatmap
        fig = go.Figure(go.Heatmap(
            x=[d.strftime('%Y-%m-%d') for d in dates],
            y=['Activity'],
            z=[values],
            colorscale=[
                [0, self.COLORS['not_started']],
                [0.3, self.COLORS['pending']],
                [0.6, self.COLORS['in_progress']],
                [1, self.COLORS['completed']]
            ],
            hovertemplate='<b>%{x}</b><br>Activities: %{z}<extra></extra>',
            showscale=True,
            colorbar=dict(title="Activity Count")
        ))
        
        fig.update_layout(
            title=dict(
                text=f'Assessment Activity Heatmap (Last {days} Days)',
                font=dict(size=16, color=self.COLORS['text']),
                x=0.5
            ),
            xaxis=dict(
                title='Date',
                tickangle=45
            ),
            yaxis=dict(
                title='',
                showticklabels=False
            ),
            paper_bgcolor='white',
            font=dict(family='Inter, sans-serif', color=self.COLORS['text']),
            height=200,
            margin=dict(l=50, r=50, t=60, b=80)
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id="activity-heatmap")
    
    def create_comprehensive_dashboard(self, officer_id, period_id):
        """Create a comprehensive dashboard with multiple visualizations"""
        charts = {
            'timeline': self.create_assessment_timeline_chart(officer_id, period_id),
            'reviewer_progress': self.create_reviewer_progress_chart(officer_id, period_id),
            'status_gauge': self.create_assessment_status_gauge(officer_id, period_id),
            'activity_heatmap': self.create_activity_heatmap(period_id)
        }
        
        return charts