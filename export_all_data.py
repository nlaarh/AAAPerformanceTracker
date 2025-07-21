#!/usr/bin/env python3
"""
Export all current database data to SQL insert statements
"""

import os
import sys
from datetime import datetime
from app import app, db
from models import *

def export_table_data(table_name, model_class):
    """Export data from a specific table"""
    print(f"-- Exporting {table_name} data")
    
    # Get all records
    records = model_class.query.all()
    
    if not records:
        print(f"-- No data found in {table_name}")
        return
    
    print(f"-- Found {len(records)} records in {table_name}")
    
    # Get column names
    columns = [column.name for column in model_class.__table__.columns]
    
    for record in records:
        values = []
        for column in columns:
            value = getattr(record, column)
            if value is None:
                values.append("NULL")
            elif isinstance(value, str):
                # Escape single quotes and wrap in quotes
                escaped_value = value.replace("'", "''")
                values.append(f"'{escaped_value}'")
            elif isinstance(value, bool):
                values.append("TRUE" if value else "FALSE")
            elif isinstance(value, datetime):
                values.append(f"'{value.isoformat()}'")
            else:
                values.append(str(value))
        
        columns_str = ', '.join([f'"{col}"' for col in columns])
        values_str = ', '.join(values)
        
        print(f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});")
    
    print()  # Empty line for readability

def main():
    """Export all database data"""
    
    print("-- AAAPerformanceTracker Database Export")
    print(f"-- Generated on: {datetime.now().isoformat()}")
    print("-- All current database data")
    print()
    print("BEGIN;")
    print()
    
    with app.app_context():
        # Export tables in dependency order (tables with no foreign keys first)
        
        # Core tables
        export_table_data('"user"', User)  # Note: user is a reserved keyword
        export_table_data('category', Category)
        
        # Assessment structure
        export_table_data('assessment_period', AssessmentPeriod)
        export_table_data('assessment_form', AssessmentForm)
        export_table_data('assessment_question', AssessmentQuestion)
        
        # Period configurations
        export_table_data('period_form_assignment', PeriodFormAssignment)
        export_table_data('period_reviewee', PeriodReviewee)
        export_table_data('period_reviewer', PeriodReviewer)
        
        # Assessment workflow
        export_table_data('assessment_project', AssessmentProject)
        export_table_data('assessment_assignment', AssessmentAssignment)
        export_table_data('assessment', Assessment)
        export_table_data('assessment_response', AssessmentResponse)
        export_table_data('category_rating', CategoryRating)
        
        # AI and reports (if exists)
        try:
            export_table_data('ai_report', AIReport)
        except NameError:
            print("-- ai_report table not found, skipping")
        
        # Activity logging
        export_table_data('activity_log', ActivityLog)
        export_table_data('assessment_activity_log', AssessmentActivityLog)
    
    print("COMMIT;")
    print()
    print("-- Export completed successfully")

if __name__ == "__main__":
    main()