"""
Admin AI Chatbot for Assessment Data Analysis
Provides natural language interface to query assessment database
"""

import os
import json
import re
from datetime import datetime
from openai import OpenAI

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# Database schema information for AI context
DATABASE_SCHEMA = """
DATABASE SCHEMA FOR ASSESSMENT SYSTEM:

MAIN TABLES:
1. "user" - Users in the system (use quotes around table name)
   - id (primary key)
   - name (full name)
   - email 
   - role (admin, board_member, officer)
   - is_active (boolean)
   - password_hash
   - created_at

2. assessment_period - Assessment periods/cycles
   - id (primary key)
   - name (e.g., "2025 Annual Review")
   - description
   - start_date, end_date
   - is_active (boolean)
   - created_at

3. assessment_assignment - Links officers to reviewers for specific periods
   - id (primary key)
   - officer_id (references "user".id)
   - reviewer_id (references "user".id) 
   - period_id (references assessment_period.id)
   - is_completed (boolean)
   - created_at

4. assessment_form - Assessment form templates
   - id (primary key)
   - title
   - description
   - is_active, is_template
   - created_at

5. assessment_question - Questions in forms
   - id (primary key)
   - form_id (references assessment_form.id)
   - question_name (short label)
   - question_text (full question)
   - question_type (rating, text, textarea, etc.)
   - is_required, is_active
   - "order" (display order - use quotes as it's a keyword)

6. assessment_response - Individual question responses
   - id (primary key)
   - assessment_assignment_id (references assessment_assignment.id)
   - question_id (references assessment_question.id)
   - response_text (for text responses)
   - response_number (for rating responses)
   - created_at

7. assessment - Legacy assessment records (narrative feedback)
   - id (primary key)
   - officer_id, reviewer_id
   - accomplishments, improvement_opportunities, focus_for_next_year
   - year, submitted_at

8. category - Performance categories
   - id (primary key)
   - name (e.g., "Financial Strategy", "Operations")
   - description
   - "order", is_active

9. category_rating - Ratings by category (legacy)
   - id (primary key)
   - assessment_id (references assessment.id)
   - category_id (references category.id)
   - rating (1-5 scale)

10. ai_generated_report - AI analysis reports
    - id (primary key)
    - officer_id (references "user".id)
    - period_id (references assessment_period.id)
    - report_title
    - summary_text (JSON with AI analysis)
    - pdf_data (binary PDF)
    - total_reviewers, average_rating, total_questions
    - created_at, created_by

CRITICAL SQL RULES:
- Use "user" (with quotes) for the user table as it's a PostgreSQL reserved word
- Use proper table aliases consistently 
- For finding reviewers who submitted assessments for an officer:
  SELECT u_reviewer.name as reviewer_name 
  FROM "user" u_officer
  JOIN assessment_assignment aa ON u_officer.id = aa.officer_id
  JOIN "user" u_reviewer ON aa.reviewer_id = u_reviewer.id
  WHERE u_officer.name = 'Officer Name' AND aa.is_completed = true

EXAMPLE QUERIES:
- Who submitted assessments for Lisa Chen:
  SELECT u_reviewer.name as reviewer_name 
  FROM "user" u_officer
  JOIN assessment_assignment aa ON u_officer.id = aa.officer_id  
  JOIN "user" u_reviewer ON aa.reviewer_id = u_reviewer.id
  WHERE u_officer.name = 'Lisa Chen' AND aa.is_completed = true;

- Officer performance ratings:
  SELECT u.name, AVG(ar.response_number) as avg_rating
  FROM "user" u
  JOIN assessment_assignment aa ON u.id = aa.officer_id
  JOIN assessment_response ar ON aa.id = ar.assessment_assignment_id
  WHERE ar.response_number IS NOT NULL
  GROUP BY u.id, u.name;
"""

def get_database_context():
    """Get current database statistics for context"""
    from app import db
    from models import User, AssessmentPeriod, AssessmentAssignment, AssessmentResponse
    
    try:
        stats = {
            "total_officers": User.query.filter_by(role='officer', is_active=True).count(),
            "total_board_members": User.query.filter_by(role='board_member', is_active=True).count(),
            "active_periods": AssessmentPeriod.query.filter_by(is_active=True).count(),
            "current_period": None,
            "total_assignments": AssessmentAssignment.query.count(),
            "completed_assignments": AssessmentAssignment.query.filter_by(is_completed=True).count(),
            "total_responses": AssessmentResponse.query.count()
        }
        
        current_period = AssessmentPeriod.query.filter_by(is_active=True).first()
        if current_period:
            stats["current_period"] = {
                "name": current_period.name,
                "id": current_period.id,
                "start_date": current_period.start_date.isoformat(),
                "end_date": current_period.end_date.isoformat()
            }
        
        return stats
    except Exception as e:
        return {"error": f"Could not get database stats: {str(e)}"}

def execute_safe_query(sql_query):
    """Execute a safe SELECT query against the database"""
    from app import db
    
    # Security: Only allow SELECT statements
    sql_clean = sql_query.strip().upper()
    if not sql_clean.startswith('SELECT'):
        return {"error": "Only SELECT queries are allowed"}
    
    # Security: Block dangerous keywords
    dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
    for keyword in dangerous_keywords:
        if keyword in sql_clean:
            return {"error": f"Keyword '{keyword}' is not allowed"}
    
    try:
        result = db.session.execute(db.text(sql_query))
        columns = result.keys()
        rows = result.fetchall()
        
        # Convert to list of dictionaries
        data = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                row_dict[col] = row[i]
            data.append(row_dict)
        
        return {
            "success": True,
            "data": data,
            "row_count": len(data),
            "columns": list(columns)
        }
        
    except Exception as e:
        return {"error": f"Query execution failed: {str(e)}"}

def generate_sql_from_question(question, db_stats):
    """Use AI to convert natural language question to SQL"""
    try:
        prompt = f"""
        You are a SQL expert for an assessment/performance review system. Convert the user's question to a safe SELECT SQL query.

        DATABASE SCHEMA:
        {DATABASE_SCHEMA}

        CURRENT DATABASE STATS:
        {json.dumps(db_stats, indent=2)}

        USER QUESTION: {question}

        INSTRUCTIONS:
        1. Generate ONLY a SELECT query (no INSERT/UPDATE/DELETE)
        2. Use proper table joins and aliases - ALWAYS use "user" (with quotes) for user table
        3. Include relevant WHERE clauses for filtering
        4. Use appropriate aggregation functions if needed
        5. Limit results to reasonable amounts (use LIMIT if needed)
        6. Focus on the most relevant data for the question
        7. Consider the current assessment period context when relevant

        CRITICAL RULES:
        - ALWAYS use "user" (with quotes) when referencing the user table
        - Use consistent table aliases throughout the query
        - For finding reviewers: JOIN "user" u_reviewer ON aa.reviewer_id = u_reviewer.id
        - For finding officers: JOIN "user" u_officer ON aa.officer_id = u_officer.id

        COMMON PATTERNS:
        - For officer performance: FROM "user" u JOIN assessment_assignment aa ON u.id = aa.officer_id
        - For finding reviewers: FROM "user" u_officer JOIN assessment_assignment aa ON u_officer.id = aa.officer_id JOIN "user" u_reviewer ON aa.reviewer_id = u_reviewer.id
        - For ratings: JOIN assessment_response ar WHERE ar.response_number IS NOT NULL
        - For text feedback: JOIN assessment_response ar WHERE ar.response_text IS NOT NULL
        - For current period: WHERE period_id = (SELECT id FROM assessment_period WHERE is_active = true)

        Return ONLY the SQL query, no explanation:
        """

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1
        )
        
        sql_query = response.choices[0].message.content.strip()
        
        # Clean up the response
        sql_query = re.sub(r'^```sql\s*', '', sql_query)
        sql_query = re.sub(r'\s*```$', '', sql_query)
        sql_query = sql_query.strip()
        
        return sql_query
        
    except Exception as e:
        return f"Error generating SQL: {str(e)}"

def format_query_results(question, query_data, sql_query):
    """Use AI to format query results into natural language response"""
    try:
        if "error" in query_data:
            return f"I encountered an error while querying the database: {query_data['error']}"
        
        if not query_data.get("data"):
            return "I didn't find any data matching your question. The query returned no results."
        
        prompt = f"""
        Convert these database query results into a natural, conversational response for an admin user.

        ORIGINAL QUESTION: {question}
        
        SQL QUERY EXECUTED: {sql_query}
        
        QUERY RESULTS:
        {json.dumps(query_data['data'][:10], indent=2)}  # Limit to first 10 rows for AI processing
        
        Total rows: {query_data['row_count']}
        
        INSTRUCTIONS:
        1. Provide a clear, concise answer to the user's question
        2. Include specific numbers, names, and data points from the results
        3. If there are many results, summarize key insights
        4. Use a conversational, helpful tone
        5. Highlight important findings or patterns
        6. If appropriate, mention trends or notable observations
        7. Keep the response focused and actionable for an admin
        
        Format the response as plain text (no markdown):
        """

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"I found the data but had trouble formatting the response: {str(e)}"

def process_chatbot_message(message):
    """Main function to process chatbot messages"""
    try:
        # Get current database context
        db_stats = get_database_context()
        
        # Check for simple greeting or help requests
        message_lower = message.lower()
        if any(word in message_lower for word in ['hello', 'hi', 'help', 'what can you do']):
            return """Hello! I'm your Assessment AI Assistant. I can help you analyze assessment data by answering questions like:

• "What's the overall assessment score for Lisa Chen?"
• "Show me feedback themes for the latest review period"
• "Which officers have completed all their assessments?"
• "What are the average ratings by category?"
• "Who are the top-performing officers this period?"

Just ask me anything about your assessment data and I'll query the database to find the answer!"""

        # Generate SQL query from natural language
        sql_query = generate_sql_from_question(message, db_stats)
        
        if sql_query.startswith("Error"):
            return sql_query
        
        # Execute the query
        query_results = execute_safe_query(sql_query)
        
        # Format results into natural language
        response = format_query_results(message, query_results, sql_query)
        
        return response
        
    except Exception as e:
        return f"I'm sorry, I encountered an unexpected error: {str(e)}. Please try rephrasing your question."