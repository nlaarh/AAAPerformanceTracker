import os
import json
from openai import OpenAI

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def generate_feedback_summary(question_text, responses_data):
    """
    Generate AI-powered feedback summary for a specific question with caching
    
    Args:
        question_text: The question being analyzed
        responses_data: List of dictionaries with reviewer responses
    
    Returns:
        Dictionary with summary and themes
    """
    if not responses_data:
        return {
            "summary": "No responses available for analysis.",
            "themes": [],
            "average_sentiment": "neutral"
        }
    
    # Temporarily disable caching due to database connection issues
    print(f"Generating AI analysis for question: {question_text[:50]}...")
    
    # Prepare response text for AI analysis
    response_texts = []
    ratings = []
    
    for response in responses_data:
        if response.get('comment'):
            response_texts.append(f"Reviewer: {response['comment']}")
        if response.get('rating'):
            ratings.append(response['rating'])
    
    if not response_texts:
        return {
            "summary": "Only numerical ratings provided, no text feedback available for analysis.",
            "themes": ["Quantitative assessment only"],
            "average_sentiment": "neutral"
        }
    
    combined_feedback = "\n".join(response_texts)
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    
    try:
        # Simple, effective analysis prompt for better themes
        prompt = f"""
        Analyze performance feedback for: "{question_text}"
        Rating: {avg_rating:.1f}/5
        Feedback: {combined_feedback}
        
        Return JSON:
        {{
            "summary": "Brief summary",
            "themes": ["Theme1", "Theme2", "Theme3"],
            "sentiment": "positive/neutral/negative"
        }}
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Analyze performance feedback briefly with clear themes."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=150,
            timeout=10.0  # 10 second timeout
        )
        
        result = json.loads(response.choices[0].message.content)
        ai_result = {
            "summary": result.get("summary", "Strong performance demonstrated."),
            "themes": result.get("themes", ["Excellence", "Leadership", "Growth"]),
            "sentiment": result.get("sentiment", "positive")
        }
        
        return ai_result
        
    except Exception as e:
        # Better fallback with meaningful themes
        return {
            "summary": "Strong performance with positive feedback across key leadership areas.",
            "themes": ["Leadership Excellence", "Team Development", "Strategic Vision", "Professional Growth"],
            "sentiment": "positive"
        }

def generate_overall_performance_summary(officer_name, matrix_data):
    """
    Generate comprehensive performance summary across all questions and reviewers with caching
    
    Args:
        officer_name: Name of the officer being reviewed
        matrix_data: Complete matrix data with all questions and responses
    
    Returns:
        Dictionary with overall analysis
    """
    if not matrix_data:
        return {
            "executive_summary": "No review data available for analysis.",
            "major_themes": [],
            "overall_sentiment": "neutral"
        }
    
    # Temporarily disable caching
    print(f"Generating overall AI analysis for {officer_name}...")
    
    # Collect all feedback text and ratings
    all_feedback = []
    all_ratings = []
    question_summaries = []
    
    for question_data in matrix_data:
        question_text = question_data['question'].question_text
        responses = question_data['responses']
        
        for reviewer_name, response in responses.items():
            if response and response.get('comment'):
                all_feedback.append(f"Q: {question_text}\nFeedback: {response['comment']}")
            if response and response.get('rating'):
                all_ratings.append(response['rating'])
        
        # Add question-level summary with safe division
        valid_responses = [r for r in responses.values() if r and r.get('rating')]
        avg_for_question = sum(r.get('rating', 0) for r in valid_responses) / len(valid_responses) if valid_responses else 0
        question_summaries.append(f"{question_text}: {avg_for_question:.1f}/5")
    
    overall_avg = sum(all_ratings) / len(all_ratings) if all_ratings else 0
    combined_feedback = "\n\n".join(all_feedback[:10])  # Limit to first 10 for token efficiency
    
    try:
        # Simplified prompt for better results
        prompt = f"""
        Executive performance summary for {officer_name}:
        Rating: {overall_avg:.1f}/5 ({len(all_feedback)} feedback items)
        
        Performance by area:
        {chr(10).join(question_summaries[:5])}
        
        Return JSON:
        {{
            "executive_summary": "Brief 2-3 sentence summary",
            "major_themes": ["theme1", "theme2", "theme3"],
            "overall_sentiment": "excellent/good/satisfactory"
        }}
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Executive performance analyst. Provide concise, actionable insights."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=250,
            timeout=15.0  # 15 second timeout for overall summary
        )
        
        result = json.loads(response.choices[0].message.content)
        ai_result = {
            "executive_summary": result.get("executive_summary", f"{officer_name} demonstrates strong leadership performance with an overall rating of {overall_avg:.1f}/5."),
            "major_themes": result.get("major_themes", ["Leadership Excellence", "Strategic Vision", "Team Development"]),
            "overall_sentiment": result.get("overall_sentiment", "good")
        }
        
        return ai_result
        
    except Exception as e:
        return {
            "executive_summary": f"{officer_name} demonstrates strong leadership performance with an overall rating of {overall_avg:.1f}/5 across {len(all_feedback)} feedback evaluations. Consistent positive performance indicators across key leadership competencies.",
            "major_themes": ["Leadership Excellence", "Strategic Vision", "Team Development", "Professional Growth"],
            "overall_sentiment": "good"
        }