-- AAAPerformanceTracker Database DDL Script
-- Version: 3.0.0
-- Date: July 20, 2025
-- Database: PostgreSQL 13+
-- Purpose: Complete database recreation script with all tables, indexes, and constraints

-- =============================================
-- DROP EXISTING OBJECTS (if recreating)
-- =============================================

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS assessment_activity_log CASCADE;
DROP TABLE IF EXISTS ai_generated_report CASCADE;
DROP TABLE IF EXISTS ai_analysis_cache CASCADE;
DROP TABLE IF EXISTS assessment_response CASCADE;
DROP TABLE IF EXISTS period_form_assignment CASCADE;
DROP TABLE IF EXISTS assessment_question CASCADE;
DROP TABLE IF EXISTS assessment_form CASCADE;
DROP TABLE IF EXISTS question_response CASCADE;
DROP TABLE IF EXISTS assessment_assignment CASCADE;
DROP TABLE IF EXISTS assessment_project CASCADE;
DROP TABLE IF EXISTS period_reviewee CASCADE;
DROP TABLE IF EXISTS period_reviewer CASCADE;
DROP TABLE IF EXISTS assessment_period CASCADE;
DROP TABLE IF EXISTS category_rating CASCADE;
DROP TABLE IF EXISTS assessment CASCADE;
DROP TABLE IF EXISTS category CASCADE;
DROP TABLE IF EXISTS activity_log CASCADE;
DROP TABLE IF EXISTS "user" CASCADE;

-- Drop custom types
DROP TYPE IF EXISTS assessment_status_enum CASCADE;

-- =============================================
-- CREATE CUSTOM TYPES
-- =============================================

-- Assessment workflow status enumeration
CREATE TYPE assessment_status_enum AS ENUM (
    'pending_self_assessment',
    'self_assessment_submitted',
    'awaiting_admin_review',
    'admin_review_completed',
    'awaiting_reviewer_assessments',
    'reviewer_assessments_in_progress',
    'reviewer_assessment_submitted',
    'reviewer_assessments_completed',
    'awaiting_final_admin_approval',
    'assessment_approved_by_admin',
    'results_released_to_reviewee',
    'reviewee_acknowledged_results',
    'assessment_closed'
);

-- =============================================
-- CORE USER MANAGEMENT TABLES
-- =============================================

-- User table (authentication and roles)
CREATE TABLE "user" (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'board_member', 'officer')),
    password_hash VARCHAR(256) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for user table
CREATE INDEX idx_user_email ON "user"(email);
CREATE INDEX idx_user_role ON "user"(role);
CREATE INDEX idx_user_active ON "user"(is_active);

-- =============================================
-- LEGACY ASSESSMENT SYSTEM (Backward Compatibility)
-- =============================================

-- Categories for traditional assessment
CREATE TABLE category (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    "order" INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Legacy assessment table
CREATE TABLE assessment (
    id SERIAL PRIMARY KEY,
    officer_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE NOT NULL,
    reviewer_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE NOT NULL,
    year INTEGER DEFAULT EXTRACT(year FROM CURRENT_TIMESTAMP),
    overall_rating FLOAT,
    accomplishments TEXT,
    improvement_opportunities TEXT,
    focus_for_next_year TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_self_assessment BOOLEAN DEFAULT FALSE
);

-- Category ratings for legacy assessments
CREATE TABLE category_rating (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER REFERENCES assessment(id) ON DELETE CASCADE NOT NULL,
    category_id INTEGER REFERENCES category(id) ON DELETE CASCADE NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5)
);

-- Legacy assessment indexes
CREATE INDEX idx_assessment_officer ON assessment(officer_id);
CREATE INDEX idx_assessment_reviewer ON assessment(reviewer_id);
CREATE INDEX idx_assessment_year ON assessment(year);
CREATE INDEX idx_category_rating_assessment ON category_rating(assessment_id);

-- =============================================
-- MODERN ASSESSMENT PROJECT MANAGEMENT
-- =============================================

-- Assessment periods (projects)
CREATE TABLE assessment_period (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    due_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES "user"(id) ON DELETE RESTRICT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Period reviewee selection
CREATE TABLE period_reviewee (
    id SERIAL PRIMARY KEY,
    period_id INTEGER REFERENCES assessment_period(id) ON DELETE CASCADE NOT NULL,
    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Period reviewer selection
CREATE TABLE period_reviewer (
    id SERIAL PRIMARY KEY,
    period_id INTEGER REFERENCES assessment_period(id) ON DELETE CASCADE NOT NULL,
    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Assessment project workflow state
CREATE TABLE assessment_project (
    id SERIAL PRIMARY KEY,
    period_id INTEGER REFERENCES assessment_period(id) ON DELETE CASCADE NOT NULL,
    officer_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE NOT NULL,
    
    -- Workflow Status
    status assessment_status_enum DEFAULT 'pending_self_assessment' NOT NULL,
    
    -- Phase Timestamps
    self_assessment_submitted_at TIMESTAMP WITH TIME ZONE,
    admin_review_completed_at TIMESTAMP WITH TIME ZONE,
    reviewer_assessments_released_at TIMESTAMP WITH TIME ZONE,
    final_approval_at TIMESTAMP WITH TIME ZONE,
    results_released_at TIMESTAMP WITH TIME ZONE,
    reviewee_acknowledged_at TIMESTAMP WITH TIME ZONE,
    
    -- Admin Control
    admin_approved_by INTEGER REFERENCES "user"(id) ON DELETE RESTRICT,
    admin_notes TEXT,
    reviewer_tasks_visible BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Assessment assignment matrix (core assignment logic)
CREATE TABLE assessment_assignment (
    id SERIAL PRIMARY KEY,
    period_id INTEGER REFERENCES assessment_period(id) ON DELETE CASCADE NOT NULL,
    officer_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE NOT NULL,
    reviewer_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE NOT NULL,
    is_completed BOOLEAN DEFAULT FALSE,
    is_notified BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Staged Approval Workflow
    is_submitted BOOLEAN DEFAULT FALSE,
    submitted_at TIMESTAMP WITH TIME ZONE,
    is_admin_approved BOOLEAN DEFAULT FALSE,
    admin_approved_at TIMESTAMP WITH TIME ZONE,
    admin_approved_by INTEGER REFERENCES "user"(id) ON DELETE RESTRICT,
    admin_notes TEXT,
    
    -- Link to legacy assessment
    assessment_id INTEGER REFERENCES assessment(id) ON DELETE SET NULL,
    
    -- Business rule: One reviewer per officer per period
    UNIQUE(period_id, officer_id, reviewer_id)
);

-- =============================================
-- ASSESSMENT FORM BUILDER SYSTEM
-- =============================================

-- Dynamic assessment forms
CREATE TABLE assessment_form (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_template BOOLEAN DEFAULT FALSE,
    created_by INTEGER REFERENCES "user"(id) ON DELETE RESTRICT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Dynamic assessment questions
CREATE TABLE assessment_question (
    id SERIAL PRIMARY KEY,
    form_id INTEGER REFERENCES assessment_form(id) ON DELETE CASCADE NOT NULL,
    question_name VARCHAR(200) NOT NULL,
    question_text TEXT NOT NULL,
    question_type VARCHAR(20) NOT NULL CHECK (question_type IN 
        ('rating', 'text', 'textarea', 'checkbox', 'dropdown', 'multiple_choice', 'boolean', 'date')),
    "order" INTEGER DEFAULT 0,
    is_required BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    settings TEXT, -- JSON for type-specific configurations
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Form assignment to periods
CREATE TABLE period_form_assignment (
    id SERIAL PRIMARY KEY,
    period_id INTEGER REFERENCES assessment_period(id) ON DELETE CASCADE NOT NULL,
    form_id INTEGER REFERENCES assessment_form(id) ON DELETE CASCADE NOT NULL,
    form_type VARCHAR(20) NOT NULL DEFAULT 'reviewer' CHECK (form_type IN ('reviewer', 'self_review')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Assessment responses (modern form responses)
CREATE TABLE assessment_response (
    id SERIAL PRIMARY KEY,
    assessment_assignment_id INTEGER REFERENCES assessment_assignment(id) ON DELETE CASCADE NOT NULL,
    question_id INTEGER REFERENCES assessment_question(id) ON DELETE CASCADE NOT NULL,
    response_text TEXT,
    response_number FLOAT,
    response_boolean BOOLEAN,
    response_date DATE,
    response_json TEXT, -- For complex responses (arrays, objects)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Legacy question responses (backward compatibility)
CREATE TABLE question_response (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER REFERENCES assessment(id) ON DELETE CASCADE NOT NULL,
    question_id INTEGER REFERENCES assessment_question(id) ON DELETE CASCADE NOT NULL,
    response_text TEXT,
    response_rating INTEGER,
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- AI INTEGRATION TABLES
-- =============================================

-- AI analysis cache for performance
CREATE TABLE ai_analysis_cache (
    id SERIAL PRIMARY KEY,
    officer_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE NOT NULL,
    period_id INTEGER REFERENCES assessment_period(id) ON DELETE CASCADE NOT NULL,
    question_id INTEGER REFERENCES assessment_question(id) ON DELETE CASCADE,
    analysis_type VARCHAR(20) NOT NULL CHECK (analysis_type IN ('question', 'overall')),
    
    -- Analysis Results
    summary TEXT,
    themes TEXT, -- JSON array of themes
    sentiment VARCHAR(20),
    executive_summary TEXT,
    major_themes TEXT, -- JSON array for overall themes
    overall_sentiment VARCHAR(20),
    
    -- Cache Metadata
    content_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- AI generated comprehensive reports
CREATE TABLE ai_generated_report (
    id SERIAL PRIMARY KEY,
    officer_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE NOT NULL,
    period_id INTEGER REFERENCES assessment_period(id) ON DELETE CASCADE NOT NULL,
    report_title VARCHAR(200),
    summary_text TEXT,
    report_data TEXT, -- Complete AI analysis as JSON
    pdf_data BYTEA, -- Stored PDF binary data
    pdf_filename VARCHAR(200),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    generated_by INTEGER REFERENCES "user"(id) ON DELETE RESTRICT NOT NULL,
    created_by INTEGER REFERENCES "user"(id) ON DELETE RESTRICT NOT NULL,
    
    -- Report Statistics
    total_reviewers INTEGER DEFAULT 0,
    average_rating FLOAT DEFAULT 0.0,
    total_questions INTEGER DEFAULT 0,
    
    -- Business rule: One report per officer per period
    UNIQUE(officer_id, period_id)
);

-- =============================================
-- ACTIVITY LOGGING & AUDIT TRAIL
-- =============================================

-- General system activity log
CREATE TABLE activity_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE NOT NULL,
    action VARCHAR(100) NOT NULL,
    description TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Assessment-specific activity logging
CREATE TABLE assessment_activity_log (
    id SERIAL PRIMARY KEY,
    
    -- Event Classification
    event_type VARCHAR(50) NOT NULL,
    event_category VARCHAR(30) NOT NULL CHECK (event_category IN 
        ('assignment', 'submission', 'approval', 'notification', 'workflow', 'access')),
    
    -- Assessment Context
    officer_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE NOT NULL,
    period_id INTEGER REFERENCES assessment_period(id) ON DELETE CASCADE NOT NULL,
    reviewer_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
    assignment_id INTEGER REFERENCES assessment_assignment(id) ON DELETE CASCADE,
    
    -- Event Details
    description TEXT NOT NULL,
    event_status VARCHAR(20) DEFAULT 'completed' CHECK (event_status IN 
        ('completed', 'pending', 'failed', 'cancelled')),
    event_data TEXT, -- JSON for additional event data
    
    -- Actor Information
    actor_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    
    -- Timing
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- PERFORMANCE OPTIMIZATION INDEXES
-- =============================================

-- Assessment Period Indexes
CREATE INDEX idx_assessment_period_active ON assessment_period(is_active);
CREATE INDEX idx_assessment_period_dates ON assessment_period(start_date, end_date);
CREATE INDEX idx_assessment_period_created_by ON assessment_period(created_by);

-- Assessment Assignment Indexes
CREATE INDEX idx_assignment_period ON assessment_assignment(period_id);
CREATE INDEX idx_assignment_officer ON assessment_assignment(officer_id);
CREATE INDEX idx_assignment_reviewer ON assessment_assignment(reviewer_id);
CREATE INDEX idx_assignment_completed ON assessment_assignment(is_completed);
CREATE INDEX idx_assignment_submitted ON assessment_assignment(is_submitted);
CREATE INDEX idx_assignment_approved ON assessment_assignment(is_admin_approved);
CREATE INDEX idx_assignment_unique_combo ON assessment_assignment(period_id, officer_id, reviewer_id);

-- Assessment Project Indexes
CREATE INDEX idx_project_period ON assessment_project(period_id);
CREATE INDEX idx_project_officer ON assessment_project(officer_id);
CREATE INDEX idx_project_status ON assessment_project(status);
CREATE INDEX idx_project_workflow_combo ON assessment_project(period_id, officer_id);

-- Assessment Form Builder Indexes
CREATE INDEX idx_form_active ON assessment_form(is_active);
CREATE INDEX idx_form_template ON assessment_form(is_template);
CREATE INDEX idx_form_created_by ON assessment_form(created_by);
CREATE INDEX idx_question_form ON assessment_question(form_id);
CREATE INDEX idx_question_order ON assessment_question("order");
CREATE INDEX idx_question_type ON assessment_question(question_type);
CREATE INDEX idx_question_active ON assessment_question(is_active);

-- Assessment Response Indexes
CREATE INDEX idx_response_assignment ON assessment_response(assessment_assignment_id);
CREATE INDEX idx_response_question ON assessment_response(question_id);
CREATE INDEX idx_response_assignment_question ON assessment_response(assessment_assignment_id, question_id);

-- Period Selection Indexes
CREATE INDEX idx_period_reviewee_period ON period_reviewee(period_id);
CREATE INDEX idx_period_reviewee_user ON period_reviewee(user_id);
CREATE INDEX idx_period_reviewer_period ON period_reviewer(period_id);
CREATE INDEX idx_period_reviewer_user ON period_reviewer(user_id);

-- Form Assignment Indexes
CREATE INDEX idx_form_assignment_period ON period_form_assignment(period_id);
CREATE INDEX idx_form_assignment_form ON period_form_assignment(form_id);
CREATE INDEX idx_form_assignment_type ON period_form_assignment(form_type);

-- AI Integration Indexes
CREATE INDEX idx_ai_cache_officer_period ON ai_analysis_cache(officer_id, period_id);
CREATE INDEX idx_ai_cache_question ON ai_analysis_cache(question_id);
CREATE INDEX idx_ai_cache_type ON ai_analysis_cache(analysis_type);
CREATE INDEX idx_ai_cache_hash ON ai_analysis_cache(content_hash);
CREATE INDEX idx_ai_report_officer_period ON ai_generated_report(officer_id, period_id);

-- Activity Log Indexes
CREATE INDEX idx_activity_user ON activity_log(user_id);
CREATE INDEX idx_activity_timestamp ON activity_log(timestamp DESC);
CREATE INDEX idx_activity_action ON activity_log(action);
CREATE INDEX idx_assessment_activity_officer ON assessment_activity_log(officer_id);
CREATE INDEX idx_assessment_activity_period ON assessment_activity_log(period_id);
CREATE INDEX idx_assessment_activity_timestamp ON assessment_activity_log(timestamp DESC);
CREATE INDEX idx_assessment_activity_event_type ON assessment_activity_log(event_type);
CREATE INDEX idx_assessment_activity_category ON assessment_activity_log(event_category);

-- =============================================
-- FOREIGN KEY CONSTRAINTS VERIFICATION
-- =============================================

-- Verify all foreign key constraints are properly created
-- This section documents the key relationships for reference:

-- User relationships:
-- - assessment.officer_id -> user.id
-- - assessment.reviewer_id -> user.id
-- - assessment_period.created_by -> user.id
-- - assessment_assignment.officer_id -> user.id
-- - assessment_assignment.reviewer_id -> user.id
-- - assessment_project.officer_id -> user.id
-- - All activity logs reference user.id

-- Assessment workflow relationships:
-- - assessment_assignment.period_id -> assessment_period.id
-- - assessment_project.period_id -> assessment_period.id
-- - assessment_assignment.assessment_id -> assessment.id (nullable)

-- Form builder relationships:
-- - assessment_question.form_id -> assessment_form.id
-- - period_form_assignment.period_id -> assessment_period.id
-- - period_form_assignment.form_id -> assessment_form.id
-- - assessment_response.question_id -> assessment_question.id
-- - assessment_response.assessment_assignment_id -> assessment_assignment.id

-- =============================================
-- BUSINESS RULE CONSTRAINTS
-- =============================================

-- Additional constraints to enforce business rules:

-- Ensure assessment assignments are unique per period
ALTER TABLE assessment_assignment 
ADD CONSTRAINT check_assignment_unique 
CHECK (period_id IS NOT NULL AND officer_id IS NOT NULL AND reviewer_id IS NOT NULL);

-- Ensure ratings are within valid range for legacy assessments
ALTER TABLE category_rating 
ADD CONSTRAINT check_rating_range 
CHECK (rating >= 1 AND rating <= 5);

-- Ensure valid user roles
ALTER TABLE "user" 
ADD CONSTRAINT check_user_role 
CHECK (role IN ('admin', 'board_member', 'officer'));

-- Ensure valid assessment period dates
ALTER TABLE assessment_period 
ADD CONSTRAINT check_period_dates 
CHECK (end_date >= start_date);

-- Ensure valid question types
ALTER TABLE assessment_question 
ADD CONSTRAINT check_question_type 
CHECK (question_type IN ('rating', 'text', 'textarea', 'checkbox', 'dropdown', 'multiple_choice', 'boolean', 'date'));

-- Ensure valid form types in period assignments
ALTER TABLE period_form_assignment 
ADD CONSTRAINT check_form_type 
CHECK (form_type IN ('reviewer', 'self_review'));

-- =============================================
-- PERFORMANCE TUNING CONFIGURATIONS
-- =============================================

-- Optimize PostgreSQL for assessment data
-- These are recommended postgresql.conf settings for production:

-- shared_buffers = 256MB                    # 25% of system RAM
-- effective_cache_size = 1GB                # 75% of system RAM  
-- work_mem = 4MB                            # For sorting and grouping
-- maintenance_work_mem = 64MB               # For maintenance operations
-- random_page_cost = 1.1                   # For SSD storage
-- effective_io_concurrency = 200           # For SSD storage
-- max_connections = 100                    # Adjust based on load
-- shared_preload_libraries = 'pg_stat_statements'  # For query analysis

-- =============================================
-- COMPLETION VERIFICATION
-- =============================================

-- Verify table creation
SELECT schemaname, tablename, tableowner 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;

-- Verify indexes
SELECT indexname, tablename, indexdef 
FROM pg_indexes 
WHERE schemaname = 'public' 
ORDER BY tablename, indexname;

-- Verify foreign key constraints
SELECT tc.table_name, kcu.column_name, ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name;

-- =============================================
-- SCRIPT COMPLETION SUMMARY
-- =============================================

-- Tables Created: 18 main tables + supporting tables
-- Indexes Created: 40+ performance optimization indexes  
-- Constraints: Foreign key constraints + business rule constraints
-- Custom Types: assessment_status_enum for workflow management
-- Features: Complete audit trail, modern form builder, AI integration
-- Compatibility: Maintains backward compatibility with legacy assessment system

-- This script creates a production-ready database schema for the AAAPerformanceTracker
-- system with full functionality including modern assessment workflow, AI integration,
-- comprehensive logging, and performance optimization.

COMMIT;