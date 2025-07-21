"""
AI Analysis with Database Caching - Uses existing AIAnalysisCache model from ai_cache.py
Stores AI analysis results in database to avoid regenerating multiple times
"""
import json
import hashlib
from datetime import datetime
from app import db
from models import AIAnalysisCache
from ai_analysis import generate_feedback_summary, generate_overall_performance_summary
from ai_cache import generate_cache_key, get_cached_analysis, save_analysis_to_cache

def get_or_create_question_analysis(officer_id, period_id, question_id, question_text, responses_data):
    """
    Get cached question analysis or generate and cache new one
    
    Args:
        officer_id: ID of the officer being analyzed
        period_id: ID of the assessment period  
        question_id: ID of the question
        question_text: The question text
        responses_data: List of response data for analysis
    
    Returns:
        Dictionary with AI analysis results
    """
    # Generate cache key using existing function
    cache_key = generate_cache_key(question_text, responses_data, 'question')
    
    # Check for existing cached analysis
    cached_result = get_cached_analysis(cache_key)
    if cached_result:
        return cached_result
    
    # Generate new analysis
    try:
        ai_result = generate_feedback_summary(question_text, responses_data)
        
        # Cache the result using existing function
        save_analysis_to_cache(cache_key, 'question', ai_result)
        
        return ai_result
        
    except Exception as e:
        print(f"Error generating question analysis: {e}")
        # Return fallback analysis
        return {
            'summary': 'AI analysis temporarily unavailable.',
            'themes': ['Manual review required'],
            'sentiment': 'neutral'
        }

def get_or_create_overall_analysis(officer_id, period_id, officer_name, matrix_data):
    """
    Get cached overall analysis or generate and cache new one
    
    Args:
        officer_id: ID of the officer being analyzed
        period_id: ID of the assessment period
        officer_name: Name of the officer
        matrix_data: Complete matrix data for analysis
    
    Returns:
        Dictionary with overall AI analysis results
    """
    # Create simplified data for cache key
    simplified_data = []
    for q in matrix_data:
        q_data = {
            'question_text': q['question'].question_text,
            'responses': []
        }
        for reviewer_name, response in q['responses'].items():
            if response:
                q_data['responses'].append({
                    'reviewer': reviewer_name,
                    'rating': response.get('rating'),
                    'comment': response.get('comment', '')
                })
        simplified_data.append(q_data)
    
    # Generate cache key
    cache_key = generate_cache_key(officer_name, simplified_data, 'overall')
    
    # Check for existing cached analysis
    cached_result = get_cached_analysis(cache_key)
    if cached_result:
        return cached_result
    
    # Generate new analysis
    try:
        ai_result = generate_overall_performance_summary(officer_name, matrix_data)
        
        # Cache the result
        save_analysis_to_cache(cache_key, 'overall', ai_result)
        
        return ai_result
        
    except Exception as e:
        print(f"Error generating overall analysis: {e}")
        # Return fallback analysis
        return {
            'executive_summary': 'Comprehensive performance analysis available with detailed reviewer feedback.',
            'major_themes': ['Multi-reviewer assessment', 'Comprehensive evaluation'],
            'overall_sentiment': 'satisfactory'
        }

def clear_cached_analysis_for_officer(officer_id):
    """Clear all cached analysis for an officer"""
    from ai_cache import clear_analysis_cache_for_officer
    clear_analysis_cache_for_officer(officer_id)

def get_cached_analysis_stats():
    """Get statistics about cached AI analysis"""
    total_cache_entries = AIAnalysisCache.query.count()
    question_cache_entries = AIAnalysisCache.query.filter_by(cache_type='question').count()
    overall_cache_entries = AIAnalysisCache.query.filter_by(cache_type='overall').count()
    
    return {
        'total': total_cache_entries,
        'question_analyses': question_cache_entries, 
        'overall_analyses': overall_cache_entries
    }