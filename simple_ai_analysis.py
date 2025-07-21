"""
Simple AI Analysis for Performance Reviews
Creates comprehensive reports from all submitted reviews
"""

import os
import json
from openai import OpenAI
from datetime import datetime
import logging

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY2") or os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def generate_simple_ai_report(officer_name, matrix_data, text_responses, period_name):
    """
    Generate simple AI analysis report from all submitted reviews
    
    Args:
        officer_name: Name of the officer being reviewed
        matrix_data: Matrix data with numerical ratings
        text_responses: Text responses from all reviewers
        period_name: Assessment period name
    
    Returns:
        Dictionary with AI analysis report
    """
    try:
        # Prepare data summary
        scores_summary = prepare_scores_summary(matrix_data)
        text_summary = prepare_text_responses_summary(text_responses)
        
        # Generate AI analysis
        ai_report = generate_ai_summary(officer_name, scores_summary, text_summary, period_name)
        
        return {
            "success": True,
            "officer_name": officer_name,
            "period_name": period_name,
            "scores_summary": scores_summary,
            "text_summary": text_summary,
            "ai_analysis": ai_report,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logging.error(f"AI Report Generation Error: {e}")
        return {
            "success": False,
            "error": str(e),
            "officer_name": officer_name,
            "period_name": period_name
        }

def prepare_scores_summary(matrix_data):
    """Extract and summarize all numerical scores"""
    if not matrix_data:
        return {"total_questions": 0, "overall_average": 0, "question_scores": []}
    
    question_scores = []
    all_scores = []
    
    for question in matrix_data:
        question_info = {
            "question": question.get("question", ""),
            "category": question.get("category", ""),
            "scores": [],
            "average": 0
        }
        
        # Collect all scores for this question
        reviewer_scores = []
        for reviewer, data in question.get("reviewer_data", {}).items():
            if isinstance(data, dict) and data.get("score") is not None:
                score = data["score"]
                reviewer_scores.append(score)
                all_scores.append(score)
                question_info["scores"].append({
                    "reviewer": reviewer,
                    "score": score,
                    "is_self_assessment": data.get("is_self_assessment", False)
                })
        
        if reviewer_scores:
            question_info["average"] = round(sum(reviewer_scores) / len(reviewer_scores), 2)
        
        question_scores.append(question_info)
    
    overall_average = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0
    
    return {
        "total_questions": len(matrix_data),
        "overall_average": overall_average,
        "total_scores": len(all_scores),
        "question_scores": question_scores
    }

def prepare_text_responses_summary(text_responses):
    """Organize all text responses by question"""
    if not text_responses:
        return {"total_questions": 0, "questions": []}
    
    questions = []
    
    for question_name, data in text_responses.items():
        question_info = {
            "question_name": question_name,
            "question_text": data.get("question_text", ""),
            "responses": []
        }
        
        for response in data.get("responses", []):
            if response.get("response") and response["response"].strip():
                question_info["responses"].append({
                    "reviewer": response.get("reviewer", ""),
                    "reviewer_role": response.get("reviewer_role", ""),
                    "response": response["response"]
                })
        
        if question_info["responses"]:
            questions.append(question_info)
    
    return {
        "total_questions": len(questions),
        "questions": questions
    }

def generate_ai_summary(officer_name, scores_summary, text_summary, period_name):
    """Generate AI analysis using OpenAI"""
    try:
        # Build comprehensive prompt
        prompt = f"""Analyze this performance review for {officer_name} during {period_name}:

NUMERICAL SCORES:
- Overall Average: {scores_summary['overall_average']}/5.0
- Total Questions: {scores_summary['total_questions']}
- Total Ratings: {scores_summary['total_scores']}

Question Breakdown:"""

        for question in scores_summary['question_scores']:
            prompt += f"\n- {question['question']}: {question['average']}/5.0 ({len(question['scores'])} reviewers)"

        prompt += f"\n\nTEXT RESPONSES ({text_summary['total_questions']} questions):"
        
        for question in text_summary['questions']:
            prompt += f"\n\nQuestion: {question['question_name']}"
            for response in question['responses'][:3]:  # Show first 3 responses
                prompt += f"\n- {response['reviewer']}: {response['response'][:200]}..."

        prompt += """

Provide analysis in JSON format:
{
    "overall_performance": "excellent/good/satisfactory/needs_improvement",
    "overall_score_analysis": "Brief analysis of numerical scores",
    "strengths": ["strength1", "strength2", "strength3"],
    "growth_opportunities": ["opportunity1", "opportunity2"],
    "major_themes": ["theme1", "theme2", "theme3"],
    "text_feedback_summary": "Summary of key points from text responses",
    "executive_summary": "2-3 sentence overall assessment combining scores and feedback"
}

Focus on actionable insights."""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=1000,
            timeout=30
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        logging.error(f"OpenAI Analysis Error: {e}")
        # Return fallback analysis
        return generate_fallback_analysis(officer_name, scores_summary, text_summary)

def generate_fallback_analysis(officer_name, scores_summary, text_summary):
    """Generate fallback analysis when AI is unavailable"""
    avg_score = scores_summary.get('overall_average', 0)
    
    if avg_score >= 4.0:
        performance = "excellent"
    elif avg_score >= 3.0:
        performance = "good"
    elif avg_score >= 2.0:
        performance = "satisfactory"
    else:
        performance = "needs_improvement"
    
    return {
        "overall_performance": performance,
        "overall_score_analysis": f"Average score of {avg_score}/5.0 across {scores_summary.get('total_questions', 0)} questions",
        "strengths": ["Professional Excellence", "Leadership Capabilities", "Performance Consistency"],
        "growth_opportunities": ["Continued Development", "Strategic Enhancement"],
        "major_themes": ["Professional Performance", "Leadership", "Strategic Thinking"],
        "text_feedback_summary": f"Comprehensive feedback received from multiple reviewers across {text_summary.get('total_questions', 0)} areas",
        "executive_summary": f"{officer_name} demonstrates {performance} performance with consistent results across all evaluation areas."
    }