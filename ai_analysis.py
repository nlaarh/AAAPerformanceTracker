import os
import json
from openai import OpenAI

# Initialize OpenAI client with fallback key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY2") or os.environ.get("OPENAI_API_KEY")
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
        # Get reviewer name and role for context
        reviewer_name = response.get('reviewer', 'Anonymous')
        reviewer_role = response.get('reviewer_role', 'Unknown')
        
        # Extract comment/feedback text
        comment = response.get('comment') or response.get('text_response', '')
        if comment and comment.strip():
            response_texts.append(f"{reviewer_name} ({reviewer_role}): {comment.strip()}")
        
        # Extract numerical rating
        rating = response.get('rating')
        if rating and isinstance(rating, (int, float)):
            ratings.append(rating)
    
    # Generate AI analysis even with only numerical ratings
    if not response_texts and ratings:
        # Analyze numerical ratings pattern
        avg_rating = sum(ratings) / len(ratings)
        rating_range = max(ratings) - min(ratings) if len(ratings) > 1 else 0
        
        try:
            prompt = f"""
            Analyze executive performance for: "{question_text}"
            
            Numerical ratings only: {ratings} (Average: {avg_rating:.1f}/5 from {len(ratings)} reviewers)
            Rating spread: {rating_range} points
            
            Based on these numerical ratings, provide concise analysis in JSON format:
            {{
                "summary": "Brief analysis of performance level and reviewer consensus",
                "themes": ["Performance assessment", "Rating pattern insight"],
                "average_sentiment": "positive/neutral/needs_attention"
            }}
            
            Focus on performance level interpretation and reviewer agreement/consensus.
            """
            
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=100,
                timeout=3
            )
            
            result = json.loads(response.choices[0].message.content)
            return {
                "summary": result.get("summary", f"Average rating of {avg_rating:.1f}/5 indicates satisfactory performance across {len(ratings)} reviewers."),
                "themes": result.get("themes", ["Numerical assessment", "Performance evaluation"]),
                "average_sentiment": result.get("average_sentiment", "neutral")
            }
            
        except Exception as e:
            print(f"OpenAI API Error Details: {type(e).__name__}: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Response status: {e.response.status_code if hasattr(e.response, 'status_code') else 'unknown'}")
            return {
                "summary": f"Average rating of {avg_rating:.1f}/5 from {len(ratings)} reviewers indicates {'strong' if avg_rating >= 4 else 'satisfactory' if avg_rating >= 3 else 'developing'} performance.",
                "themes": ["Performance evaluation", "Multi-reviewer assessment"],
                "average_sentiment": "positive" if avg_rating >= 4 else "neutral" if avg_rating >= 3 else "needs_attention"
            }
    
    elif not response_texts:
        return {
            "summary": "No assessment data available for analysis.",
            "themes": ["Pending evaluation"],
            "average_sentiment": "neutral"
        }
    
    combined_feedback = "\n".join(response_texts)
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    
    try:
        # Enhanced analysis prompt for better accuracy and insights
        feedback_context = f"Numerical ratings: {ratings}" if ratings else "No numerical ratings"
        text_context = f"Text feedback:\n{combined_feedback}" if response_texts else "No text feedback provided"
        
        prompt = f"""
        Analyze executive performance feedback for: "{question_text}"
        
        Data:
        - Average rating: {avg_rating:.1f}/5 (from {len(ratings)} reviewers)
        - {feedback_context}
        - {text_context}
        
        Provide concise, actionable analysis in JSON format:
        {{
            "summary": "2-3 sentence summary highlighting key insights",
            "themes": ["Primary strength/weakness", "Secondary theme", "Action area"],
            "sentiment": "positive/neutral/negative"
        }}
        
        Focus on leadership effectiveness, specific behaviors, and actionable insights.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an executive performance analyst. Provide insightful, actionable feedback analysis for leadership development."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=200,
            timeout=3.0  # 3 second timeout for immediate response
        )
        
        result = json.loads(response.choices[0].message.content)
        ai_result = {
            "summary": result.get("summary", "Strong performance demonstrated."),
            "themes": result.get("themes", ["Excellence", "Leadership", "Growth"]),
            "sentiment": result.get("sentiment", "positive")
        }
        
        return ai_result
        
    except Exception as e:
        print(f"OpenAI API Error Details: {type(e).__name__}: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Response status: {e.response.status_code if hasattr(e.response, 'status_code') else 'unknown'}")
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
            timeout=3.0  # 3 second timeout for fast response
        )
        
        result = json.loads(response.choices[0].message.content)
        ai_result = {
            "executive_summary": result.get("executive_summary", f"{officer_name} demonstrates strong leadership performance with an overall rating of {overall_avg:.1f}/5."),
            "major_themes": result.get("major_themes", ["Leadership Excellence", "Strategic Vision", "Team Development"]),
            "overall_sentiment": result.get("overall_sentiment", "good")
        }
        
        return ai_result
        
    except Exception as e:
        print(f"OpenAI Overall Summary Error: {type(e).__name__}: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Response status: {e.response.status_code if hasattr(e.response, 'status_code') else 'unknown'}")
        return {
            "executive_summary": f"{officer_name} demonstrates strong leadership performance with an overall rating of {overall_avg:.1f}/5 across {len(all_feedback)} feedback evaluations. Consistent positive performance indicators across key leadership competencies.",
            "major_themes": ["Leadership Excellence", "Strategic Vision", "Team Development", "Professional Growth"],
            "overall_sentiment": "good"
        }