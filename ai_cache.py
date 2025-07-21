import hashlib
import json
from datetime import datetime

def generate_cache_key(question_text, responses_data, cache_type='question'):
    """Generate a unique cache key based on question and responses"""
    # Create a stable hash of the question and responses
    content = {
        'question': question_text,
        'responses': sorted([
            {
                'reviewer': r.get('reviewer', ''),
                'rating': r.get('rating'),
                'comment': r.get('comment', ''),
                'reviewer_role': r.get('reviewer_role', '')
            }
            for r in responses_data
        ], key=lambda x: x['reviewer']),  # Sort for consistency
        'type': cache_type
    }
    
    content_str = json.dumps(content, sort_keys=True)
    return hashlib.md5(content_str.encode()).hexdigest()

def get_cached_analysis(cache_key):
    """Get cached AI analysis if it exists"""
    try:
        from models import AIAnalysisCache
        from app import db
        
        cached = AIAnalysisCache.query.filter_by(cache_key=cache_key).first()
        if cached:
            try:
                return json.loads(cached.analysis_data)
            except json.JSONDecodeError:
                # Invalid cache, delete it
                db.session.delete(cached)
                db.session.commit()
        return None
    except Exception as e:
        print(f"Cache access error: {e}")
        return None

def save_analysis_to_cache(cache_key, cache_type, analysis_data):
    """Save AI analysis result to cache"""
    try:
        from models import AIAnalysisCache
        from app import db
        
        # Check if already exists
        existing = AIAnalysisCache.query.filter_by(cache_key=cache_key).first()
        
        if existing:
            # Update existing
            existing.analysis_data = json.dumps(analysis_data)
            existing.updated_at = datetime.utcnow()
        else:
            # Create new
            new_cache = AIAnalysisCache(
                cache_key=cache_key,
                cache_type=cache_type,
                analysis_data=json.dumps(analysis_data)
            )
            db.session.add(new_cache)
        
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error saving AI analysis to cache: {e}")
        try:
            db.session.rollback()
        except:
            pass
        return False

def clear_analysis_cache_for_officer(officer_id):
    """Clear all cached AI analysis for a specific officer (when responses change)"""
    try:
        from models import AIAnalysisCache
        from app import db
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(hours=24)
        
        old_entries = AIAnalysisCache.query.filter(
            AIAnalysisCache.updated_at < cutoff_date
        ).all()
        
        for entry in old_entries:
            db.session.delete(entry)
        
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error clearing AI analysis cache: {e}")
        try:
            db.session.rollback()
        except:
            pass
        return False