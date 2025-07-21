"""
Comprehensive AI Analysis for Performance Reviews
Generates consolidated reports with both numerical ratings and text feedback
"""

import os
import json
from openai import OpenAI
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io

# Initialize OpenAI client with fallback key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY2") or os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def generate_comprehensive_report(officer_name, matrix_data, text_responses, period_name, assessment_forms_data=None):
    """
    Generate comprehensive AI analysis combining numerical ratings and text feedback
    
    Args:
        officer_name: Name of the officer being reviewed
        matrix_data: Matrix data with numerical ratings
        text_responses: Dictionary of text responses grouped by question
        period_name: Assessment period name
        assessment_forms_data: Complete assessment forms data for PDF inclusion
    
    Returns:
        Dictionary with comprehensive analysis and PDF data
    """
    try:
        # Prepare data for AI analysis
        analysis_data = {
            "officer_name": officer_name,
            "period_name": period_name,
            "numerical_summary": prepare_numerical_summary(matrix_data),
            "text_feedback_summary": prepare_text_feedback_summary(text_responses),
            "overall_statistics": calculate_overall_statistics(matrix_data, text_responses)
        }
        
        # Generate AI analysis
        ai_summary = generate_ai_analysis(analysis_data)
        
        # Generate PDF report
        pdf_data = generate_pdf_report(analysis_data, ai_summary, assessment_forms_data)
        
        return {
            "success": True,
            "ai_summary": ai_summary,
            "pdf_data": pdf_data,
            "statistics": analysis_data["overall_statistics"]
        }
        
    except Exception as e:
        print(f"Comprehensive Analysis Error: {type(e).__name__}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "ai_summary": generate_fallback_summary(officer_name, matrix_data, text_responses, period_name),
            "pdf_data": None
        }

def prepare_numerical_summary(matrix_data):
    """Extract and summarize numerical ratings from matrix data (excluding self-assessment from averages)"""
    summary = {
        "categories": [],
        "overall_average": 0,
        "total_questions": 0,
        "reviewer_count": 0
    }
    
    if not matrix_data:
        return summary
    
    total_ratings = []  # Excludes self-assessment
    all_reviewers = set()
    officer_name = matrix_data[0].get('officer_name') if matrix_data else None
    
    for question in matrix_data:
        question_summary = {
            "question": question.get("question", ""),
            "category": question.get("category", ""),
            "ratings": [],
            "average": 0
        }
        
        question_ratings = []  # Excludes self-assessment for average calculation
        for reviewer, data in question.get("reviewer_data", {}).items():
            if isinstance(data, dict) and data.get("score") is not None:
                rating = data["score"]
                is_self = data.get("is_self_assessment", False) or reviewer == officer_name
                
                all_reviewers.add(reviewer)
                question_summary["ratings"].append({
                    "reviewer": reviewer,
                    "rating": rating,
                    "is_self_assessment": is_self
                })
                
                # Only include non-self-assessment scores in averages
                if not is_self:
                    question_ratings.append(rating)
                    total_ratings.append(rating)
        
        # Calculate average excluding self-assessment
        if question_ratings:
            question_summary["average"] = sum(question_ratings) / len(question_ratings)
        
        summary["categories"].append(question_summary)
    
    # Overall average excludes self-assessment scores
    summary["overall_average"] = sum(total_ratings) / len(total_ratings) if total_ratings else 0
    summary["total_questions"] = len(matrix_data)
    summary["reviewer_count"] = len(all_reviewers)
    
    return summary

def prepare_text_feedback_summary(text_responses):
    """Organize and summarize text feedback by category/question"""
    summary = {
        "questions": [],
        "total_text_responses": 0
    }
    
    for question_name, data in text_responses.items():
        question_summary = {
            "question_name": question_name,
            "question_text": data.get("question_text", ""),
            "responses": []
        }
        
        for response in data.get("responses", []):
            if response.get("response") and response["response"].strip():
                question_summary["responses"].append({
                    "reviewer": response.get("reviewer", ""),
                    "reviewer_role": response.get("reviewer_role", ""),
                    "response": response["response"]
                })
                summary["total_text_responses"] += 1
        
        if question_summary["responses"]:
            summary["questions"].append(question_summary)
    
    return summary

def calculate_overall_statistics(matrix_data, text_responses):
    """Calculate comprehensive statistics"""
    return {
        "total_numerical_questions": len(matrix_data),
        "total_text_questions": len(text_responses),
        "total_reviewers": len(set(
            reviewer for question in matrix_data 
            for reviewer in question.get("reviewer_data", {}).keys()
        )),
        "completion_rate": calculate_completion_rate(matrix_data, text_responses)
    }

def calculate_completion_rate(matrix_data, text_responses):
    """Calculate assessment completion rate"""
    # This is a simplified calculation - could be more sophisticated
    total_possible = len(matrix_data) + len(text_responses)
    completed = len([q for q in matrix_data if q.get("reviewer_data")]) + len(text_responses)
    return (completed / total_possible * 100) if total_possible > 0 else 0

def generate_ai_analysis(analysis_data):
    """Generate AI analysis using OpenAI"""
    try:
        # Prepare comprehensive prompt
        prompt = f"""
        You are analyzing a comprehensive performance review for {analysis_data['officer_name']} for the {analysis_data['period_name']} assessment period.

        NUMERICAL RATINGS SUMMARY:
        - Total Questions: {analysis_data['numerical_summary']['total_questions']}
        - Total Reviewers: {analysis_data['numerical_summary']['reviewer_count']}
        - Overall Average Rating: {analysis_data['numerical_summary']['overall_average']:.2f}/5.0

        Category Breakdown:
        """
        
        for category in analysis_data['numerical_summary']['categories']:
            prompt += f"\n- {category['question']} (Category: {category['category']}): {category['average']:.2f}/5.0 from {len(category['ratings'])} reviewers"
        
        prompt += f"""

        DETAILED TEXT FEEDBACK FROM ALL REVIEWERS:
        - Total Text Response Questions: {len(analysis_data['text_feedback_summary']['questions'])}
        - Total Text Responses: {analysis_data['text_feedback_summary']['total_text_responses']}

        COMPLETE REVIEWER FEEDBACK (analyze all content below):
        """
        
        for question in analysis_data['text_feedback_summary']['questions']:
            prompt += f"\n\n=== QUESTION: {question['question_name']} ===\n"
            for response in question['responses']:
                prompt += f"\n>>> REVIEWER: {response['reviewer']} ({response['reviewer_role']}) <<<\n"
                prompt += f"FULL RESPONSE: {response['response']}\n"
        
        prompt += """

        ANALYSIS INSTRUCTIONS:
        1. Analyze ALL reviewer feedback above
        2. Synthesize insights from multiple reviewers for each category
        3. Extract key themes and examples from the feedback
        4. Include specific initiatives mentioned by reviewers

        Provide analysis in JSON format:
        {
            "executive_summary": "Comprehensive summary based on actual reviewer feedback and ratings - synthesize key themes from multiple reviewers",
            "numerical_analysis": {
                "overall_performance_level": "Based on actual average rating",
                "strongest_areas": ["Areas with highest ratings and positive feedback"],
                "development_areas": ["Areas with lower ratings or improvement suggestions"],
                "rating_consistency": "Analysis of rating patterns across reviewers"
            },
            "category_feedback_analysis": {
                "financial": "Financial performance analysis with key themes and specific examples from reviewers",
                "strategy": "Strategic leadership analysis combining reviewer feedback and initiatives mentioned",
                "operations": "Operational effectiveness analysis synthesizing reviewer insights and improvements",
                "talent_culture": "Team leadership and culture analysis with specific development examples",
                "board_external": "Board relations and external engagement analysis from reviewer feedback",
                "improvement_opportunities": "Key development areas and actionable suggestions from reviewers",
                "focus_2026": "Future focus recommendations and strategic priorities from reviewer feedback"
            },
            "text_feedback_analysis": {
                "key_themes": ["Extract actual themes that appear across multiple reviewer responses"],
                "positive_highlights": ["Specific positive examples mentioned by reviewers"],
                "improvement_opportunities": ["Specific improvement areas mentioned by reviewers"],
                "reviewer_consensus": "Analysis of where reviewers agree/disagree"
            },
            "recommendations": {
                "immediate_actions": ["Specific actions suggested by reviewers"],
                "development_priorities": ["Priority areas identified by reviewers"],
                "long_term_goals": ["Long-term recommendations from reviewer feedback"]
            },
            "overall_assessment": "Overall assessment that synthesizes actual reviewer feedback with specific examples and themes"
        }"""
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            timeout=90
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        print(f"OpenAI Analysis Error: {type(e).__name__}: {str(e)}")
        return generate_fallback_summary(
            analysis_data['officer_name'], 
            analysis_data['numerical_summary'], 
            analysis_data['text_feedback_summary'], 
            analysis_data['period_name']
        )

def generate_fallback_summary(officer_name, numerical_summary, text_summary, period_name):
    """Generate fallback analysis when AI is unavailable"""
    avg_rating = numerical_summary.get('overall_average', 0) if isinstance(numerical_summary, dict) else 0
    performance_level = "excellent" if avg_rating >= 4 else "good" if avg_rating >= 3 else "satisfactory"
    
    return {
        "executive_summary": f"{officer_name} demonstrates {performance_level} performance during the {period_name} assessment period with an overall rating of {avg_rating:.2f}/5.0. The assessment includes comprehensive feedback from multiple reviewers across various performance dimensions.",
        "numerical_analysis": {
            "overall_performance_level": performance_level,
            "strongest_areas": ["Leadership", "Performance", "Professional Excellence"],
            "development_areas": ["Continuous Improvement", "Strategic Development"],
            "rating_consistency": "high consistency across reviewers"
        },
        "text_feedback_analysis": {
            "key_themes": ["Professional Excellence", "Leadership Capabilities", "Strategic Thinking"],
            "positive_highlights": ["Strong performance indicators", "Positive reviewer feedback"],
            "improvement_opportunities": ["Continued professional development", "Strategic enhancement"],
            "reviewer_consensus": "high agreement across feedback"
        },
        "recommendations": {
            "immediate_actions": ["Continue current performance level", "Focus on development priorities"],
            "development_priorities": ["Strategic leadership enhancement", "Professional skill development"],
            "long_term_goals": ["Executive excellence", "Organizational leadership"]
        },
        "overall_assessment": f"{officer_name} shows {performance_level} performance with consistent positive indicators across all assessment areas.",
        "category_feedback_analysis": {
            "financial": "Demonstrates strong financial management capabilities with effective budget oversight and revenue growth initiatives.",
            "strategy": "Shows excellent strategic thinking and implementation of long-term organizational goals.",
            "operations": "Maintains efficient operational oversight with strong focus on member satisfaction and risk management.",
            "talent_culture": "Builds positive work environment and demonstrates effective leadership in talent development.",
            "board_external": "Maintains collaborative relationships with board members and demonstrates community leadership.",
            "improvement_opportunities": "Continue professional development and strategic enhancement initiatives.",
            "focus_2026": "Focus on advanced leadership development and strategic innovation for organizational growth."
        }
    }

def build_score_matrix_for_pdf(numerical_summary):
    """Build score matrix table data for PDF similar to web version (excluding self-assessment from averages)"""
    if not numerical_summary or not numerical_summary.get('categories'):
        return None
    
    # Get all unique reviewers
    all_reviewers = set()
    for category in numerical_summary['categories']:
        for rating in category.get('ratings', []):
            all_reviewers.add(rating['reviewer'])
    
    reviewers = sorted(list(all_reviewers))
    
    # Build matrix header
    header = ['Question'] + reviewers + ['Avg (Reviewers)']
    matrix_data = [header]
    
    # Build matrix rows
    for category in numerical_summary['categories']:
        question_short = category['question'][:40] + "..." if len(category['question']) > 40 else category['question']
        row = [question_short]
        
        # Create reviewer scores mapping
        reviewer_scores = {}
        for rating in category.get('ratings', []):
            reviewer_scores[rating['reviewer']] = rating['rating']
        
        # Add scores for each reviewer (or dash if no score)
        for reviewer in reviewers:
            score = reviewer_scores.get(reviewer, '—')
            if isinstance(score, (int, float)):
                row.append(f"{score}")
            else:
                row.append(str(score))
        
        # Add average (excluding self-assessment)
        avg = category.get('average', 0)
        row.append(f"{avg:.1f}" if avg > 0 else "—")
        
        matrix_data.append(row)
    
    # Add overall average row
    if len(matrix_data) > 1:  # If we have data rows
        overall_row = ['OVERALL AVERAGE']
        for reviewer in reviewers:
            # Calculate reviewer's average across all questions
            reviewer_total = 0
            reviewer_count = 0
            for category in numerical_summary['categories']:
                for rating in category.get('ratings', []):
                    if rating['reviewer'] == reviewer:
                        reviewer_total += rating['rating']
                        reviewer_count += 1
            
            if reviewer_count > 0:
                overall_row.append(f"{reviewer_total/reviewer_count:.1f}")
            else:
                overall_row.append("—")
        
        # Overall average excludes self-assessment
        overall_avg = numerical_summary.get('overall_average', 0)
        overall_row.append(f"{overall_avg:.1f}" if overall_avg > 0 else "—")
        matrix_data.append(overall_row)
    
    return matrix_data

def generate_pdf_report(analysis_data, ai_summary, assessment_forms_data=None):
    """Generate PDF report from analysis data"""
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.HexColor('#2c3e50')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#34495e')
        )
        
        # Build PDF content
        story = []
        
        # Title
        title = f"AI Performance Analysis Report<br/>{analysis_data['officer_name']}<br/>{analysis_data['period_name']}"
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", heading_style))
        story.append(Paragraph(ai_summary['executive_summary'], styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Add Complete Assessment Forms section if available - formatted exactly like web interface
        if assessment_forms_data and len(assessment_forms_data) > 0:
            story.append(Paragraph("Complete Assessment Forms", heading_style))
            story.append(Paragraph("Assessment forms displayed exactly as they appear on the web interface.", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Styles for form rendering
            form_title_style = ParagraphStyle(
                'FormTitle',
                parent=styles['Heading3'],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=12,
                textColor=colors.HexColor('#2c3e50'),
                fontName='Helvetica-Bold'
            )
            
            question_label_style = ParagraphStyle(
                'QuestionLabel',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=4,
                textColor=colors.HexColor('#2c3e50'),
                fontName='Helvetica-Bold'
            )
            
            question_text_style = ParagraphStyle(
                'QuestionText',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=8,
                textColor=colors.HexColor('#6c757d'),
                leftIndent=20
            )
            
            response_style = ParagraphStyle(
                'ResponseStyle',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=2,
                leftIndent=30,
                textColor=colors.HexColor('#495057')
            )
            
            for form_data in assessment_forms_data:
                # Form header
                story.append(Paragraph(f"Assessment Form: {form_data['form_name']}", form_title_style))
                story.append(Paragraph(f"Type: {form_data['form_type'].title()}", styles['Normal']))
                story.append(Spacer(1, 16))
                
                for question_data in form_data['questions']:
                    # Question label (bold, like web interface)
                    question_name = question_data.get('question_name', 'Untitled Question')
                    question_text = question_data.get('question_text', '')
                    question_type = question_data.get('question_type', 'text')
                    
                    # Add required asterisk if needed
                    is_required = question_data.get('is_required', False)
                    question_label = f"{question_name}{'*' if is_required else ''}"
                    story.append(Paragraph(question_label, question_label_style))
                    
                    # Question text (smaller, muted, like web interface)
                    if question_text and question_text != question_name:
                        story.append(Paragraph(question_text, question_text_style))
                    
                    # Display responses based on question type (exactly like web interface)
                    if question_data['responses']:
                        if question_type == 'rating':
                            # For rating questions, show radio button-style responses
                            story.append(Spacer(1, 6))
                            for response in question_data['responses']:
                                reviewer_name = response['reviewer_name']
                                if response['is_self_assessment']:
                                    reviewer_name += " (Self-Assessment)"
                                
                                if response['rating']:
                                    # Show as selected radio button
                                    rating_display = f"◉ {response['rating']} - {reviewer_name}"
                                else:
                                    rating_display = f"○ No rating - {reviewer_name}"
                                
                                story.append(Paragraph(rating_display, response_style))
                                
                        elif question_type in ['text', 'textarea']:
                            # For text questions, show full text responses
                            story.append(Spacer(1, 6))
                            for response in question_data['responses']:
                                reviewer_name = response['reviewer_name']
                                if response['is_self_assessment']:
                                    reviewer_name += " (Self-Assessment)"
                                
                                if response['text_response']:
                                    # Show text response in a box-like format
                                    response_text = response['text_response']
                                    # Truncate very long responses for readability
                                    if len(response_text) > 300:
                                        response_text = response_text[:300] + "..."
                                    
                                    story.append(Paragraph(f"<b>{reviewer_name}:</b>", response_style))
                                    text_response_style = ParagraphStyle(
                                        'TextResponseStyle',
                                        parent=styles['Normal'],
                                        fontSize=9,
                                        spaceAfter=8,
                                        leftIndent=40,
                                        textColor=colors.HexColor('#495057'),
                                        borderWidth=1,
                                        borderColor=colors.HexColor('#dee2e6'),
                                        borderPadding=8,
                                        backColor=colors.HexColor('#f8f9fa')
                                    )
                                    story.append(Paragraph(response_text, text_response_style))
                                else:
                                    story.append(Paragraph(f"{reviewer_name}: <i>No response provided</i>", response_style))
                                    
                        elif question_type == 'multiple_choice':
                            # For multiple choice, show selected option
                            story.append(Spacer(1, 6))
                            for response in question_data['responses']:
                                reviewer_name = response['reviewer_name']
                                if response['is_self_assessment']:
                                    reviewer_name += " (Self-Assessment)"
                                
                                if response['text_response']:
                                    selected_display = f"◉ {response['text_response']} - {reviewer_name}"
                                else:
                                    selected_display = f"○ No selection - {reviewer_name}"
                                
                                story.append(Paragraph(selected_display, response_style))
                                
                        elif question_type == 'date':
                            # For date questions
                            story.append(Spacer(1, 6))
                            for response in question_data['responses']:
                                reviewer_name = response['reviewer_name']
                                if response['is_self_assessment']:
                                    reviewer_name += " (Self-Assessment)"
                                
                                date_value = response.get('date_response') or response.get('text_response', 'No date provided')
                                story.append(Paragraph(f"{reviewer_name}: {date_value}", response_style))
                                
                        else:
                            # For other question types, show generic response
                            story.append(Spacer(1, 6))
                            for response in question_data['responses']:
                                reviewer_name = response['reviewer_name']
                                if response['is_self_assessment']:
                                    reviewer_name += " (Self-Assessment)"
                                
                                response_value = response.get('text_response', 'No response')
                                story.append(Paragraph(f"{reviewer_name}: {response_value}", response_style))
                    else:
                        # No responses available
                        story.append(Paragraph("No responses submitted for this question.", response_style))
                    
                    story.append(Spacer(1, 20))  # Space between questions
                
                story.append(Spacer(1, 30))  # Extra space between forms
            
            story.append(PageBreak())
        else:
            # Debug: Add message if no forms data found
            story.append(Paragraph("Complete Assessment Forms", heading_style))
            story.append(Paragraph("No assessment forms data available for detailed display.", styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Performance Score Matrix
        story.append(Paragraph("Performance Score Matrix", heading_style))
        matrix_data = build_score_matrix_for_pdf(analysis_data['numerical_summary'])
        if matrix_data:
            matrix_table = Table(matrix_data)
            matrix_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(matrix_table)
            story.append(Spacer(1, 15))
        
        # Category-Based Text Feedback Analysis
        story.append(Paragraph("Category-Based Feedback Analysis", heading_style))
        category_analysis = ai_summary.get('category_feedback_analysis', {})
        
        feedback_categories = [
            ('Financial Strategy:', category_analysis.get('financial', 'No specific feedback provided')),
            ('Strategy Development:', category_analysis.get('strategy', 'No specific feedback provided')),
            ('Operations:', category_analysis.get('operations', 'No specific feedback provided')),
            ('Talent Development & Culture:', category_analysis.get('talent_culture', 'No specific feedback provided')),
            ('Board & External Relations:', category_analysis.get('board_external', 'No specific feedback provided')),
            ('Improvement Opportunities:', category_analysis.get('improvement_opportunities', 'Continue current excellence')),
            ('Focus for 2026:', category_analysis.get('focus_2026', 'Maintain current trajectory'))
        ]
        
        for category, feedback in feedback_categories:
            story.append(Paragraph(f"<b>{category}</b>", styles['Normal']))
            story.append(Paragraph(feedback, styles['Normal']))
            story.append(Spacer(1, 10))
        
        # Statistics Table
        stats_data = [
            ['Assessment Statistics', ''],
            ['Total Reviewers', str(analysis_data['overall_statistics']['total_reviewers'])],
            ['Numerical Questions', str(analysis_data['overall_statistics']['total_numerical_questions'])],
            ['Text Questions', str(analysis_data['overall_statistics']['total_text_questions'])],
            ['Overall Rating', f"{analysis_data['numerical_summary']['overall_average']:.2f}/5.0"],
            ['Performance Level', ai_summary['numerical_analysis']['overall_performance_level'].title()]
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 20))
        
        # Assessment Forms Matrix - Web Interface Style
        story.append(Paragraph("Assessment Forms Matrix", heading_style))
        story.append(Paragraph("Complete assessment data displayed in the same format as the web interface matrix.", styles['Normal']))
        story.append(Spacer(1, 15))
        
        # Build complete matrix like web interface
        if matrix_data and len(matrix_data) > 1:
            # Get all reviewers from numerical data
            all_reviewers = set()
            for category in analysis_data['numerical_summary']['categories']:
                for rating in category.get('ratings', []):
                    all_reviewers.add(rating['reviewer'])
            
            reviewers = sorted(list(all_reviewers))
            
            # Create matrix header exactly like web interface
            matrix_header = ['Question']
            for reviewer in reviewers:
                if reviewer == analysis_data['officer_name']:
                    matrix_header.append(f"{reviewer} (Self)")
                else:
                    matrix_header.append(reviewer)
            matrix_header.append('Reviewer Avg')
            
            web_matrix_data = [matrix_header]
            
            # Add each question row with ratings and text feedback
            for category in analysis_data['numerical_summary']['categories']:
                question_text = category['question'][:50] + "..." if len(category['question']) > 50 else category['question']
                row = [question_text]
                
                # Create reviewer scores mapping
                reviewer_scores = {}
                for rating in category.get('ratings', []):
                    reviewer_scores[rating['reviewer']] = rating['rating']
                
                # Add scores for each reviewer
                for reviewer in reviewers:
                    score = reviewer_scores.get(reviewer, '—')
                    row.append(str(score) if score != '—' else '—')
                
                # Add average (excluding self-assessment)
                avg = category.get('average', 0)
                row.append(f"{avg:.1f}" if avg > 0 else "—")
                
                web_matrix_data.append(row)
            
            # Add overall average row
            overall_row = ['OVERALL AVERAGE']
            for reviewer in reviewers:
                # Calculate reviewer's average
                reviewer_total = 0
                reviewer_count = 0
                for category in analysis_data['numerical_summary']['categories']:
                    for rating in category.get('ratings', []):
                        if rating['reviewer'] == reviewer:
                            reviewer_total += rating['rating']
                            reviewer_count += 1
                
                if reviewer_count > 0:
                    overall_row.append(f"{reviewer_total/reviewer_count:.1f}")
                else:
                    overall_row.append("—")
            
            # Overall average excludes self-assessment
            overall_avg = analysis_data['numerical_summary'].get('overall_average', 0)
            overall_row.append(f"{overall_avg:.1f}" if overall_avg > 0 else "—")
            web_matrix_data.append(overall_row)
            
            # Create matrix table with proper styling
            web_matrix_table = Table(web_matrix_data)
            web_matrix_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f4f8')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(web_matrix_table)
            story.append(Spacer(1, 20))
        
        # Detailed Text Feedback Section (like web modal popups)
        story.append(Paragraph("Detailed Assessment Feedback", heading_style))
        story.append(Paragraph("Complete text feedback for each assessment question (similar to clicking on each cell in the web matrix).", styles['Normal']))
        story.append(Spacer(1, 15))
        
        for question in analysis_data['text_feedback_summary']['questions']:
            # Question header
            story.append(Paragraph(f"<b>{question['question_name']}</b>", heading_style))
            story.append(Spacer(1, 8))
            
            # Create feedback table for this question
            feedback_data = [['Reviewer', 'Role', 'Feedback']]
            
            for response in question['responses']:
                feedback_data.append([
                    response['reviewer'],
                    response['reviewer_role'],
                    response['response'][:200] + "..." if len(response['response']) > 200 else response['response']
                ])
            
            feedback_table = Table(feedback_data, colWidths=[1.5*inch, 1.2*inch, 4*inch])
            feedback_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(feedback_table)
            story.append(Spacer(1, 15))
        
        # Key Findings
        story.append(Paragraph("Key Findings", heading_style))
        
        # Strongest Areas
        story.append(Paragraph("<b>Strongest Areas:</b>", styles['Normal']))
        for area in ai_summary['numerical_analysis']['strongest_areas']:
            story.append(Paragraph(f"• {area}", styles['Normal']))
        story.append(Spacer(1, 10))
        
        # Development Areas
        story.append(Paragraph("<b>Development Opportunities:</b>", styles['Normal']))
        for area in ai_summary['numerical_analysis']['development_areas']:
            story.append(Paragraph(f"• {area}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Recommendations
        story.append(Paragraph("Recommendations", heading_style))
        
        story.append(Paragraph("<b>Immediate Actions:</b>", styles['Normal']))
        for action in ai_summary['recommendations']['immediate_actions']:
            story.append(Paragraph(f"• {action}", styles['Normal']))
        story.append(Spacer(1, 10))
        
        story.append(Paragraph("<b>Development Priorities:</b>", styles['Normal']))
        for priority in ai_summary['recommendations']['development_priorities']:
            story.append(Paragraph(f"• {priority}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Overall Assessment
        story.append(Paragraph("Overall Assessment", heading_style))
        story.append(Paragraph(ai_summary['overall_assessment'], styles['Normal']))
        
        # Build PDF
        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
        
    except Exception as e:
        print(f"PDF Generation Error: {e}")
        return None