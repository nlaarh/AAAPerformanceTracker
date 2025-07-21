-- AAAPerformanceTracker Sample Data Insertion Script
-- Version: 3.0.0
-- Date: July 20, 2025
-- Purpose: Sample data for demonstration and testing

BEGIN;

-- =============================================
-- SAMPLE USERS
-- =============================================

-- Insert sample users with different roles
INSERT INTO "user" (name, email, role, password_hash, is_active) VALUES
-- Admin user
('System Administrator', 'admin@aaaperformance.com', 'admin', 'scrypt:32768:8:1$XyZ123$abcd1234efgh5678', TRUE),

-- Board members (reviewers)
('Jennifer Rodriguez', 'jennifer.rodriguez@aaaperformance.com', 'board_member', 'scrypt:32768:8:1$XyZ123$board1234hash', TRUE),
('Lisa Davis', 'lisa.davis@aaaperformance.com', 'board_member', 'scrypt:32768:8:1$XyZ123$board2345hash', TRUE),
('Michael Thompson', 'michael.thompson@aaaperformance.com', 'board_member', 'scrypt:32768:8:1$XyZ123$board3456hash', TRUE),
('Mike Chen', 'mike.chen@aaaperformance.com', 'board_member', 'scrypt:32768:8:1$XyZ123$board4567hash', TRUE),

-- Officers (reviewees)
('Emily Davis', 'emily.davis@aaaperformance.com', 'officer', 'scrypt:32768:8:1$XyZ123$officer1234hash', TRUE),
('Lisa Chen', 'lisa.chen@aaaperformance.com', 'officer', 'scrypt:32768:8:1$XyZ123$officer2345hash', TRUE),
('Robert Johnson', 'robert.johnson@aaaperformance.com', 'officer', 'scrypt:32768:8:1$XyZ123$officer3456hash', TRUE);

-- =============================================
-- LEGACY CATEGORIES (for backward compatibility)
-- =============================================

INSERT INTO category (name, description, "order", is_active) VALUES
('Financial Strategy', 'Key financial responsibilities include presenting an acceptable annual budget, achieving consistent and diversified revenue growth, maintaining and improving profitability, ensuring positive returns on investments, managing cash flow, controlling costs, providing accurate and timely financial reports.', 1, TRUE),
('Development Strategy', 'Leads creation of AAAWCNY''s strategic direction and effectively implement long-term strategies that meet the needs of the organization, associates, members and other stakeholders.', 2, TRUE),
('Operations', 'Oversees the efficient and effective operations of all departments and business lines ensuring positive operational performance and member satisfaction. Ensures adequate internal controls are in place and effectively assesses, manages and mitigates risk.', 3, TRUE),
('Talent Development & Culture', 'Develops and leads a strong executive team to drive short and long-term results to meet strategic goals and make critical, timely decisions. Creates a positive work environment for associates and promotes a culture reflecting AAAWCNY''s mission, values, and business strategies.', 4, TRUE),
('Board & External Relations', 'Forges collaborative, trusting, and transparent working relationships with the Board of Directors. Engages with the Board of Directors in establishing short-term objectives and long-term goals with regular updates on the status of operations.', 5, TRUE);

-- =============================================
-- ASSESSMENT FORMS
-- =============================================

-- Executive Review Form (for board members reviewing officers)
INSERT INTO assessment_form (title, description, is_active, is_template, created_by) VALUES
('Executive Performance Review', 'Comprehensive performance evaluation form for executive officers by board members', TRUE, FALSE, 1),
('Self Assessment Form', 'Self-evaluation form for executive officers', TRUE, FALSE, 1);

-- Get form IDs for reference
-- Executive form will be ID 1, Self assessment form will be ID 2

-- =============================================
-- ASSESSMENT QUESTIONS - EXECUTIVE REVIEW FORM
-- =============================================

INSERT INTO assessment_question (form_id, question_name, question_text, question_type, "order", is_required, settings) VALUES
-- Financial Strategy Questions
(1, 'Financial Performance', 'How effectively did the executive manage financial performance including budget achievement, revenue growth, and profitability?', 'rating', 1, TRUE, '{"min_rating": 1, "max_rating": 5, "labels": ["Poor", "Below Average", "Average", "Good", "Excellent"]}'),
(1, 'Financial Comments', 'Please provide specific comments on financial strategy performance:', 'textarea', 2, FALSE, '{"max_chars": 1000}'),

-- Development Strategy Questions  
(1, 'Strategic Leadership', 'How effectively did the executive provide strategic direction and implement long-term strategies?', 'rating', 3, TRUE, '{"min_rating": 1, "max_rating": 5, "labels": ["Poor", "Below Average", "Average", "Good", "Excellent"]}'),
(1, 'Strategy Comments', 'Please provide specific comments on strategic leadership:', 'textarea', 4, FALSE, '{"max_chars": 1000}'),

-- Operations Questions
(1, 'Operational Excellence', 'How effectively did the executive oversee operations, risk management, and market response?', 'rating', 5, TRUE, '{"min_rating": 1, "max_rating": 5, "labels": ["Poor", "Below Average", "Average", "Good", "Excellent"]}'),
(1, 'Operations Comments', 'Please provide specific comments on operational performance:', 'textarea', 6, FALSE, '{"max_chars": 1000}'),

-- Culture Questions
(1, 'Leadership and Culture', 'How effectively did the executive develop talent, build organizational culture, and lead the team?', 'rating', 7, TRUE, '{"min_rating": 1, "max_rating": 5, "labels": ["Poor", "Below Average", "Average", "Good", "Excellent"]}'),
(1, 'Culture Comments', 'Please provide specific comments on leadership and culture development:', 'textarea', 8, FALSE, '{"max_chars": 1000}'),

-- External Relations Questions
(1, 'Board and External Relations', 'How effectively did the executive collaborate with the board and engage in external relationships?', 'rating', 9, TRUE, '{"min_rating": 1, "max_rating": 5, "labels": ["Poor", "Below Average", "Average", "Good", "Excellent"]}'),
(1, 'Relations Comments', 'Please provide specific comments on board and external relations:', 'textarea', 10, FALSE, '{"max_chars": 1000}');

-- =============================================
-- ASSESSMENT QUESTIONS - SELF ASSESSMENT FORM
-- =============================================

INSERT INTO assessment_question (form_id, question_name, question_text, question_type, "order", is_required, settings) VALUES
-- Self-Assessment Narrative Questions
(2, 'Accomplishments', 'What were your major accomplishments this year?', 'textarea', 1, TRUE, '{"max_chars": 2000}'),
(2, 'Improvement Opportunities', 'What areas do you see as opportunities for improvement?', 'textarea', 2, TRUE, '{"max_chars": 2000}'),
(2, 'Focus for 2026', 'What will be your key focus areas for 2026?', 'textarea', 3, TRUE, '{"max_chars": 2000}'),

-- Self-Rating Questions
(2, 'Financial Self-Rating', 'Rate your performance in Financial Strategy:', 'rating', 4, TRUE, '{"min_rating": 1, "max_rating": 5, "labels": ["Poor", "Below Average", "Average", "Good", "Excellent"]}'),
(2, 'Strategy Self-Rating', 'Rate your performance in Development Strategy:', 'rating', 5, TRUE, '{"min_rating": 1, "max_rating": 5, "labels": ["Poor", "Below Average", "Average", "Good", "Excellent"]}'),
(2, 'Operations Self-Rating', 'Rate your performance in Operations:', 'rating', 6, TRUE, '{"min_rating": 1, "max_rating": 5, "labels": ["Poor", "Below Average", "Average", "Good", "Excellent"]}'),
(2, 'Culture Self-Rating', 'Rate your performance in Talent Development & Culture:', 'rating', 7, TRUE, '{"min_rating": 1, "max_rating": 5, "labels": ["Poor", "Below Average", "Average", "Good", "Excellent"]}'),
(2, 'Relations Self-Rating', 'Rate your performance in Board & External Relations:', 'rating', 8, TRUE, '{"min_rating": 1, "max_rating": 5, "labels": ["Poor", "Below Average", "Average", "Good", "Excellent"]}');

-- =============================================
-- ASSESSMENT PERIODS
-- =============================================

INSERT INTO assessment_period (name, description, start_date, end_date, due_date, is_active, created_by) VALUES
('2025 Annual Executive Review', 'Annual performance review for executive leadership team', '2025-01-01', '2025-12-31', '2025-02-15', TRUE, 1),
('Q1 2025 Performance Check', 'Quarterly performance check-in', '2025-01-01', '2025-03-31', '2025-04-15', FALSE, 1);

-- =============================================
-- PERIOD FORM ASSIGNMENTS
-- =============================================

-- Assign forms to the active assessment period
INSERT INTO period_form_assignment (period_id, form_id, form_type, is_active) VALUES
(1, 1, 'reviewer', TRUE),  -- Executive Review Form for reviewers
(1, 2, 'self_review', TRUE);  -- Self Assessment Form for self-reviews

-- =============================================
-- PERIOD REVIEWEES AND REVIEWERS
-- =============================================

-- Define who can be reviewed (officers)
INSERT INTO period_reviewee (period_id, user_id) VALUES
(1, 6),  -- Emily Davis
(1, 7),  -- Lisa Chen
(1, 8);  -- Robert Johnson

-- Define who can review (board members + officers for self-assessment)
INSERT INTO period_reviewer (period_id, user_id) VALUES
(1, 2),  -- Jennifer Rodriguez
(1, 3),  -- Lisa Davis  
(1, 4),  -- Michael Thompson
(1, 5),  -- Mike Chen
(1, 6),  -- Emily Davis (for self-assessment)
(1, 7),  -- Lisa Chen (for self-assessment)
(1, 8);  -- Robert Johnson (for self-assessment)

-- =============================================
-- ASSESSMENT PROJECTS (Workflow State)
-- =============================================

-- Create assessment projects for each officer
INSERT INTO assessment_project (period_id, officer_id, status, reviewer_tasks_visible) VALUES
(1, 6, 'pending_self_assessment', FALSE),  -- Emily Davis
(1, 7, 'pending_self_assessment', FALSE),  -- Lisa Chen
(1, 8, 'pending_self_assessment', FALSE);  -- Robert Johnson

-- =============================================
-- ASSESSMENT ASSIGNMENTS (Assignment Matrix)
-- =============================================

-- Self-assessments (required for all officers)
INSERT INTO assessment_assignment (period_id, officer_id, reviewer_id, is_completed, is_submitted, is_admin_approved) VALUES
(1, 6, 6, FALSE, FALSE, FALSE),  -- Emily Davis self-assessment
(1, 7, 7, FALSE, FALSE, FALSE),  -- Lisa Chen self-assessment
(1, 8, 8, FALSE, FALSE, FALSE);  -- Robert Johnson self-assessment

-- External reviewer assignments (board members reviewing officers)
INSERT INTO assessment_assignment (period_id, officer_id, reviewer_id, is_completed, is_submitted, is_admin_approved) VALUES
-- Emily Davis reviewers
(1, 6, 2, FALSE, FALSE, FALSE),  -- Jennifer Rodriguez -> Emily Davis
(1, 6, 3, FALSE, FALSE, FALSE),  -- Lisa Davis -> Emily Davis
(1, 6, 4, FALSE, FALSE, FALSE),  -- Michael Thompson -> Emily Davis

-- Lisa Chen reviewers  
(1, 7, 2, FALSE, FALSE, FALSE),  -- Jennifer Rodriguez -> Lisa Chen
(1, 7, 3, FALSE, FALSE, FALSE),  -- Lisa Davis -> Lisa Chen
(1, 7, 5, FALSE, FALSE, FALSE),  -- Mike Chen -> Lisa Chen

-- Robert Johnson reviewers
(1, 8, 3, FALSE, FALSE, FALSE),  -- Lisa Davis -> Robert Johnson
(1, 8, 4, FALSE, FALSE, FALSE),  -- Michael Thompson -> Robert Johnson
(1, 8, 5, FALSE, FALSE, FALSE);  -- Mike Chen -> Robert Johnson

-- =============================================
-- SAMPLE ASSESSMENT RESPONSES (Emily Davis Demo)
-- =============================================

-- First, create a legacy assessment for Emily Davis (self-assessment)
INSERT INTO assessment (officer_id, reviewer_id, year, overall_rating, accomplishments, improvement_opportunities, focus_for_next_year, is_self_assessment) VALUES
(6, 6, 2025, 4.2, 
'Led successful digital transformation initiative resulting in 25% efficiency improvement. Achieved budget targets with 15% revenue growth. Successfully launched new member portal increasing satisfaction scores by 30%. Strengthened board relationships through quarterly strategic updates.',
'Need to improve delegation skills and develop more robust succession planning. Should focus on expanding external partnerships and enhancing data analytics capabilities.',
'Focus on strategic partnerships, team development, and digital innovation. Implement comprehensive succession planning program and expand market presence in new regions.',
TRUE);

-- Get the assessment ID for Emily Davis self-assessment (should be ID 1)
-- Link this assessment to the assignment
UPDATE assessment_assignment SET assessment_id = 1, is_completed = TRUE, is_submitted = TRUE, is_admin_approved = TRUE, completed_at = CURRENT_TIMESTAMP, submitted_at = CURRENT_TIMESTAMP, admin_approved_at = CURRENT_TIMESTAMP, admin_approved_by = 1 WHERE period_id = 1 AND officer_id = 6 AND reviewer_id = 6;

-- Add self-assessment responses using the new assessment response system
INSERT INTO assessment_response (assessment_assignment_id, question_id, response_text, response_number) VALUES
-- Emily Davis self-assessment responses (assignment_id should be 1)
(1, 11, 'This year I successfully led our digital transformation initiative, which resulted in a 25% improvement in operational efficiency across all departments. I achieved all budget targets with a 15% revenue growth, exceeding our initial projections. The launch of our new member portal has increased member satisfaction scores by 30% and reduced support ticket volume by 40%. I also strengthened our board relationships by implementing quarterly strategic update presentations that have improved transparency and alignment on organizational goals.', NULL),
(1, 12, 'I recognize that I need to improve my delegation skills to better empower my team and avoid becoming a bottleneck in decision-making processes. Additionally, I should focus on developing more robust succession planning for key leadership positions. I also see opportunities to expand our external partnerships and enhance our data analytics capabilities to drive more informed strategic decisions.', NULL),
(1, 13, 'For 2026, my key focus areas will be: 1) Building strategic partnerships to expand our market reach, 2) Implementing a comprehensive leadership development and succession planning program, 3) Driving digital innovation through advanced analytics and AI integration, 4) Expanding our presence in new regional markets, and 5) Enhancing organizational culture and employee engagement initiatives.', NULL),
(1, 14, NULL, 4),  -- Financial Self-Rating
(1, 15, NULL, 4),  -- Strategy Self-Rating
(1, 16, NULL, 4),  -- Operations Self-Rating
(1, 17, NULL, 5),  -- Culture Self-Rating
(1, 18, NULL, 4);  -- Relations Self-Rating

-- Add category ratings for Emily Davis self-assessment
INSERT INTO category_rating (assessment_id, category_id, rating) VALUES
(1, 1, 4),  -- Financial Strategy
(1, 2, 4),  -- Development Strategy
(1, 3, 4),  -- Operations
(1, 4, 5),  -- Talent Development & Culture
(1, 5, 4);  -- Board & External Relations

-- Update Emily Davis assessment project status to show self-assessment completed
UPDATE assessment_project SET 
    status = 'self_assessment_submitted',
    self_assessment_submitted_at = CURRENT_TIMESTAMP
WHERE period_id = 1 AND officer_id = 6;

-- =============================================
-- SAMPLE EXTERNAL REVIEWER ASSESSMENTS
-- =============================================

-- Jennifer Rodriguez reviewing Emily Davis
INSERT INTO assessment (officer_id, reviewer_id, year, overall_rating, is_self_assessment) VALUES
(6, 2, 2025, 4.4, FALSE);

-- Update assignment and add responses
UPDATE assessment_assignment SET assessment_id = 2, is_completed = TRUE, is_submitted = TRUE, is_admin_approved = TRUE, completed_at = CURRENT_TIMESTAMP, submitted_at = CURRENT_TIMESTAMP, admin_approved_at = CURRENT_TIMESTAMP, admin_approved_by = 1 WHERE period_id = 1 AND officer_id = 6 AND reviewer_id = 2;

INSERT INTO assessment_response (assessment_assignment_id, question_id, response_number, response_text) VALUES
-- Jennifer Rodriguez assessment of Emily Davis (assignment_id should be 4)
(4, 1, 5, NULL),  -- Financial Performance rating
(4, 2, NULL, 'Emily has demonstrated exceptional financial leadership this year. Her strategic budget management led to achieving all targets while driving 15% revenue growth. The cost optimization initiatives she implemented have improved our margins significantly.'),
(4, 3, 4, NULL),  -- Strategic Leadership rating
(4, 4, NULL, 'Emily''s strategic vision for our digital transformation has been outstanding. Her ability to align stakeholders and execute complex initiatives shows strong strategic leadership capabilities.'),
(4, 5, 4, NULL),  -- Operational Excellence rating
(4, 6, NULL, 'The operational improvements under Emily''s leadership have been substantial. The new member portal launch was executed flawlessly and the efficiency gains are measurable and significant.'),
(4, 7, 5, NULL),  -- Leadership and Culture rating
(4, 8, NULL, 'Emily has created a positive and productive work environment. Her leadership style fosters innovation and collaboration. Team morale and engagement have noticeably improved under her guidance.'),
(4, 9, 4, NULL),  -- Board and External Relations rating
(4, 10, NULL, 'Emily maintains excellent communication with the board through regular updates and transparent reporting. Her external relationship building has opened new partnership opportunities.');

INSERT INTO category_rating (assessment_id, category_id, rating) VALUES
(2, 1, 5), (2, 2, 4), (2, 3, 4), (2, 4, 5), (2, 5, 4);

-- =============================================
-- ACTIVITY LOG SAMPLES
-- =============================================

INSERT INTO activity_log (user_id, action, description, ip_address, timestamp) VALUES
(1, 'login', 'Admin user logged into system', '192.168.1.100', CURRENT_TIMESTAMP - INTERVAL '1 day'),
(1, 'create_assessment_period', 'Created 2025 Annual Executive Review period', '192.168.1.100', CURRENT_TIMESTAMP - INTERVAL '1 day'),
(6, 'login', 'Emily Davis logged in to complete self-assessment', '192.168.1.101', CURRENT_TIMESTAMP - INTERVAL '2 hours'),
(6, 'submit_assessment', 'Emily Davis submitted self-assessment', '192.168.1.101', CURRENT_TIMESTAMP - INTERVAL '2 hours'),
(1, 'approve_assessment', 'Admin approved Emily Davis self-assessment', '192.168.1.100', CURRENT_TIMESTAMP - INTERVAL '1 hour'),
(2, 'submit_assessment', 'Jennifer Rodriguez submitted review of Emily Davis', '192.168.1.102', CURRENT_TIMESTAMP - INTERVAL '30 minutes');

-- =============================================
-- ASSESSMENT ACTIVITY LOG SAMPLES
-- =============================================

INSERT INTO assessment_activity_log (event_type, event_category, officer_id, period_id, reviewer_id, assignment_id, description, actor_id, timestamp) VALUES
('assignment_created', 'assignment', 6, 1, 6, 1, 'Self-assessment assignment created for Emily Davis', 1, CURRENT_TIMESTAMP - INTERVAL '1 day'),
('assignment_created', 'assignment', 6, 1, 2, 4, 'External reviewer assignment created: Jennifer Rodriguez -> Emily Davis', 1, CURRENT_TIMESTAMP - INTERVAL '1 day'),
('self_assessment_submitted', 'submission', 6, 1, 6, 1, 'Emily Davis submitted self-assessment', 6, CURRENT_TIMESTAMP - INTERVAL '2 hours'),
('admin_approved_self_assessment', 'approval', 6, 1, 6, 1, 'Admin approved Emily Davis self-assessment', 1, CURRENT_TIMESTAMP - INTERVAL '1 hour'),
('reviewer_assessment_submitted', 'submission', 6, 1, 2, 4, 'Jennifer Rodriguez submitted assessment of Emily Davis', 2, CURRENT_TIMESTAMP - INTERVAL '30 minutes');

COMMIT;

-- =============================================
-- DATA VERIFICATION QUERIES
-- =============================================

-- Verify users created
SELECT name, email, role, is_active FROM "user" ORDER BY role, name;

-- Verify assessment periods  
SELECT name, start_date, end_date, is_active FROM assessment_period;

-- Verify assignment matrix
SELECT 
    ap.name as period_name,
    officer.name as officer_name,
    reviewer.name as reviewer_name,
    aa.is_completed,
    aa.is_admin_approved
FROM assessment_assignment aa
JOIN assessment_period ap ON aa.period_id = ap.id
JOIN "user" officer ON aa.officer_id = officer.id  
JOIN "user" reviewer ON aa.reviewer_id = reviewer.id
ORDER BY ap.name, officer.name, reviewer.name;

-- Verify assessment responses
SELECT 
    ar.id,
    officer.name as officer_name,
    reviewer.name as reviewer_name,
    aq.question_name,
    ar.response_text,
    ar.response_number
FROM assessment_response ar
JOIN assessment_assignment aa ON ar.assessment_assignment_id = aa.id
JOIN "user" officer ON aa.officer_id = officer.id
JOIN "user" reviewer ON aa.reviewer_id = reviewer.id  
JOIN assessment_question aq ON ar.question_id = aq.id
ORDER BY officer.name, reviewer.name, aq."order";

-- Verify activity logs
SELECT 
    u.name,
    al.action,
    al.description,
    al.timestamp
FROM activity_log al
JOIN "user" u ON al.user_id = u.id
ORDER BY al.timestamp DESC
LIMIT 10;