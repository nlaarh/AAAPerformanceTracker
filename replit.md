# AAAPerformanceTracker

## Overview

The AAAPerformanceTracker is a Flask-based web application designed for executive performance evaluation, specifically targeting all officer assessments by board members and administrators. The system provides role-based access control, structured performance evaluations across multiple categories, and comprehensive reporting capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.
Design preference: Modern Apple/React-style interfaces with light, clean aesthetics instead of dark themes.
Form preferences: Clean, simplified evaluation forms with minimal input fields - no duplicate comment sections per question.
Matrix preferences: Simple 2D matrix with questions in rows, reviewers in columns, single score per question, short category descriptions (Finance, Strategy, Operations, Culture, External).
**Data Management**: Always create database backups before making large data changes or deletions. Use pg_dump to backup PostgreSQL database with timestamp naming convention.
**CRITICAL WARNING**: The matrix display logic in officer_reviews function is WORKING CORRECTLY and must NEVER be modified. It includes the critical fix for self-assessment display. Only modify export functions, never the core matrix logic.

## Recent Changes

- **CRITICAL FIX: Self-Assessment Matrix Display Issue (July 14, 2025)**: Successfully fixed major bug where self-assessment scores weren't displaying in officer review matrix
  - Root cause: Self-assessments use different question IDs from "Self Review For" form vs "Executive Review" form for board members
  - Solution: Modified matrix logic to include questions from BOTH reviewer and self-review forms assigned to assessment period
  - Added question text matching to map equivalent questions across different forms (same text content, different IDs)
  - Updated query to use PeriodFormAssignment with both form_type='reviewer' AND form_type='self_review'
  - Matrix now properly displays all assigned reviewers including self-assessment scores in correct columns
  - **Fixed Average Calculation**: Self-assessment scores now display in matrix but are excluded from reviewer average calculations
  - **Matrix Filtering**: Only rating questions display in matrix, text-only questions (signatures, comments, dates) are filtered out
  - **CONFIRMED WORKING**: This fix enables proper 360-degree review functionality - officer self-ratings display correctly while maintaining accurate external reviewer averages
- **Added Assessment Form Active/Inactive Status Management (July 14, 2025)**: Assessment forms now have activate/deactivate functionality with status badges and toggle buttons. Only active forms appear in assessment period form selection.
- **Updated Terminology to Use Reviewers/Reviewees (July 14, 2025)**: Changed interface terminology from role-specific (board members/officers) to flexible reviewer/reviewee terms to accommodate different role assignments
- **Enhanced Assessment Period Creation with Form Assignment (July 14, 2025)**: Assessment periods now include form selection during creation, automatically linking reviewer forms and self-assessment forms to periods
- **Fixed Missing Assessment Templates (July 14, 2025)**: Created missing template files after database restructuring
  - Added add_assessment_question.html, clone_assessment_question.html, preview_assessment_form.html, edit_assessment_question.html
  - Restored full assessment form builder functionality: add, clone, edit, preview, move, delete questions
  - Removed survey template menu from admin interface as requested
- **Complete Database Restructuring to Assessment Terminology (July 14, 2025)**: Comprehensive refactoring from "Survey" to "Assessment" terminology
  - Renamed all models: SurveyForm → AssessmentForm, SurveyQuestion → AssessmentQuestion, SurveyResponse → AssessmentResponse
  - Updated all table names and foreign key relationships with proper CASCADE handling
  - Modified admin interface to show "Assessment Templates" instead of "Survey Forms"
  - Updated all route definitions and form classes to use assessment terminology
  - Recreated database with new schema structure reflecting performance evaluation data
  - Updated forms.py with AssessmentFormForm, AssessmentQuestionForm, EditAssessmentFormTitleForm
  - Enhanced admin dashboard with assessment_forms_count and assessment_questions_count variables
  - All template references updated to point to assessment routes and terminology
- **Enhanced Question Editing Interface and Date Picker Implementation (July 13, 2025)**: Complete form editing improvements
  - Changed edit question button text to "Update Question" instead of "Add Question" for better UX
  - Updated default max characters for long text (textarea) to 2000 instead of 500
  - Added smart character limit defaults: 500 for short text, 2000 for long text with automatic detection
  - Enhanced form interface with helpful text showing character limits for different question types
  - Added date selection widget with Bootstrap datepicker for date field types
  - Created form title editing functionality allowing admins to change survey form names and descriptions
  - Added "Title" button to survey forms management page for quick form name changes
  - Implemented comprehensive date picker support across all question management templates
- **Comprehensive Assessment Period Deletion System with Dependency Analysis (July 14, 2025)**: Complete administrative control over assessment periods
  - Added comprehensive dependency checking system showing all related data that will be deleted
  - Created detailed confirmation modal with visual dependency breakdown (assignments, assessments, survey responses, form assignments, involved users)
  - Implemented safe deletion process requiring exact text confirmation "DELETE PERIOD" for security
  - Built comprehensive backend deletion handling with proper cascade deletion of all related data
  - Added real-time dependency analysis with loading states and error handling
  - Enhanced admin interface with red delete button and visual warning system
  - Integrated comprehensive activity logging for all deletion attempts and completions
  - Deletion process removes: assignments, assessments, question responses, category ratings, survey responses, form assignments
- **Enhanced Form Assignment System with Reviewer/Self-Review Distinction (July 14, 2025)**: Complete form type management implementation
  - Added form_type field to PeriodFormAssignment model to distinguish between 'reviewer' and 'self_review' forms
  - Updated AssignFormToPeriodForm to include separate selection fields for reviewer forms and self-review forms
  - Created enhanced assignment interface with side-by-side form selection for different user types
  - Database migration completed to add form_type column with default 'reviewer' value
  - Enhanced assignment template with clear visual distinction between reviewer and self-review forms
  - Activity logging integrated for comprehensive form assignment tracking
  - Form assignment validation ensures at least one form type is selected
  - Admins can now specify which forms board members use vs which forms officers use for self-assessment
- **Streamlined Admin Interface by Removing Survey Templates (July 14, 2025)**: Simplified survey management
  - Removed survey template functionality from admin interface for cleaner user experience
  - Updated admin dashboard to show only total survey forms instead of separate template count
  - Streamlined survey forms management to focus on active forms creation and editing
  - Enhanced admin tab interface with single "Survey Forms" section instead of confusing template/forms distinction
- **Fixed Self-Assessment Access and Assignment Badge Counter (July 13, 2025)**: Resolved critical access issues for officer self-assessments
  - Fixed evaluate_officer route to allow officers to access their own self-assessment forms
  - Corrected assignment badge counter to show only relevant tasks per user role (officers see self-assessments, reviewers see review tasks)
  - Updated My Assignments page to clearly distinguish self-assessments vs external reviews with proper labels
  - Enhanced assignment creation logic to automatically include all user types as potential reviewers while maintaining self-assessment creation for officers
- **User Activation/Deactivation System with Comprehensive Data Management (July 13, 2025)**: Complete user lifecycle management implementation
  - Added `is_active` boolean field to User model for user status management
  - Implemented user activation/deactivation with pause/play icons in user management interface
  - Enhanced delete user functionality with detailed dependency analysis and confirmation system
  - Created comprehensive user dependency checking showing assessments, assignments, and question responses
  - Added critical confirmation requirement ("DELETE ALL DATA") for user deletion with detailed warnings
  - Implemented comprehensive activity logging for all user management operations (activation, deactivation, deletion attempts)
  - Inactive users excluded from assignment creation and login access while preserving historical data
  - Enhanced login security to block inactive users with appropriate warning messages
  - Status toggle functionality with informative confirmation dialogs explaining impact
- **Excel-Based Export/Import System with Password Management (July 13, 2025)**: Complete administrative functionality overhaul
  - Converted all export/import functionality from JSON to Excel format for better usability
  - Enhanced admin user management with secure password visibility and copy-to-clipboard features
  - Implemented professional Excel exports with formatted headers, auto-sized columns, and multiple sheets
  - Created comprehensive import system that updates existing records and inserts new ones
  - Added modal interface for secure password viewing with security warnings
  - Integrated export/import dropdown menus in both User Management and Questions administration
  - Excel exports include proper styling with blue headers and optimized column widths
  - Import validation with detailed error reporting and transaction rollback protection
- **Fixed Excel Export and Optimized Matrix Layout (July 13, 2025)**: Resolved critical export issues and enhanced user interface
  - Fixed Excel export internal server error caused by dictionary objects being written directly to cells
  - Converted AI summary data to proper text format for Excel compatibility
  - Reduced reviewer column widths from 6% to 4% for more compact layout
  - Expanded AI analysis column from 55% to 62% for detailed insights display
  - Reverted CSS colors to light blue badges with better text visibility
  - Simplified overall AI summary prompts for faster, more reliable responses
  - Enhanced theme display with consistent styling throughout the matrix
- **Question Clone Feature for Rapid Development (July 13, 2025)**: Added question cloning functionality to speed up form creation
  - Clone button added to question management interface with green clone icon
  - Pre-populates form with all original question data including settings and options
  - Automatically adds "Copy of" prefix to question name for easy identification
  - Maintains all question type settings (rating scales, options, text limits)
  - Places cloned question at the end of the form for immediate editing
- **Simplified Survey Question Structure (July 13, 2025)**: Streamlined question design to use only Question Label and Question Text fields
  - Removed Long Description field for cleaner, focused question creation
  - Updated form structure: Question Label (required) → Question Text (required)
  - Question Label serves as the primary identifier, Question Text contains the actual question
  - Enhanced templates to display question labels prominently in listings and previews
  - Database schema updated to support simplified two-field structure
- **Complete Matrix Export Functionality with All Reviewers (July 13, 2025)**: Full matrix export system with all assigned reviewers
  - Fixed PDF and Excel exports to show ALL assigned reviewers, not just completed assessments
  - Updated export logic to match web matrix display exactly with empty cells for pending reviews
  - Added Excel export with professional formatting, color-coded ratings, and comprehensive AI analysis
  - Both exports now use AssessmentAssignment table to include all assigned reviewers
  - Export files show complete matrix as displayed on web page with proper reviewer counts
- **Matrix Display Shows All Assigned Reviewers (July 13, 2025)**: Complete reviewer visibility in performance matrix
  - Updated officer review matrix to display ALL assigned reviewers from AssessmentAssignment table
  - Shows empty cells (—) for reviewers who haven't submitted evaluations yet
  - Fixed reviewer count to reflect total assignments rather than completed assessments only
  - Matrix now provides complete picture of review process including pending submissions
  - Enhanced visibility of evaluation status for comprehensive progress tracking
- **Comprehensive Activity Logging System with Advanced Filtering (July 13, 2025)**: Complete activity monitoring solution
  - Implemented comprehensive activity logging throughout the entire application
  - Added logging for all major user activities: dashboard access, data viewing, evaluation actions, user management
  - Created dedicated admin activity logs page with advanced filtering capabilities (user, action type, date range)
  - Built real-time activity monitoring with IP address and user agent tracking
  - Added CSV export functionality for activity logs with applied filters
  - Enhanced user management page with live activity feed and user statistics
  - Integrated activity logs menu item in admin navigation for easy access
  - Implemented pagination for large activity log datasets with 50 entries per page
  - Added color-coded activity badges and browser detection for better visualization
- **Clean Simplified Matrix with Total Average (July 13, 2025)**: Streamlined performance matrix with comprehensive scoring
  - Removed duplicate rows by filtering out questions without responses
  - Added total average score row showing overall performance across all questions
  - Individual reviewer averages calculated and displayed with color coding
  - Overall matrix average prominently displayed for quick assessment
  - Short category names (Finance, Strategy, Operations, Culture, External) for clean display
- **AI-Powered Officer Review Matrix (July 13, 2025)**: Comprehensive performance analysis with artificial intelligence
  - Created detailed officer review matrix with questions in rows and reviewers in columns
  - Implemented score visualization at intersections with color-coded ratings
  - Added automatic average calculation for each question and overall performance
  - Integrated OpenAI GPT-4o for intelligent feedback analysis and insights
  - Built AI-powered executive summary with themes, strengths, and development priorities
  - Created question-level AI analysis with sentiment detection and improvement recommendations
  - Added responsive matrix design with sticky headers and modal popups for detailed feedback
  - Implemented comprehensive performance visualization with leadership readiness assessment
- **Matrix-Based Assignment Interface (July 13, 2025)**: Revolutionary assignment creation with visual matrix layout
  - Created interactive matrix interface with reviewees in rows and reviewers in columns
  - Implemented checkbox-based selection system for intuitive assignment creation
  - Added automatic self-assessment checkbox pre-selection on diagonal intersections
  - Built comprehensive assignment management with existing assignment detection
  - Enhanced interface with Select All Self, Select All, and Clear All functionality
  - Added real-time selection counting and form validation
  - Integrated sticky headers and responsive design for large assignment matrices
- **Restructured Navigation with Beautiful Dashboard Visualizations (July 13, 2025)**: Complete navigation and visualization overhaul
  - Restructured navigation menu with Dashboard, Assessments, My Assignments, and Admin sections
  - Created beautiful admin dashboard with Chart.js visualizations and eye-catching progress charts
  - Built assessment management page with current/past period tabs and advanced filtering
  - Added role-based navigation where Dashboard and Assessments are admin-only
  - Implemented real-time metrics cards, progress bars, and monthly trend charts
  - Enhanced filtering capabilities by officer, reviewer, assignment period, and status
  - Added comprehensive progress tracking with completion rates and visual indicators
- **Clean Admin Interface with Tabbed Navigation (July 13, 2025)**: Complete overhaul of admin interface
  - Created new tabbed admin console with three main sections: Assessment Management, Survey Templates, User Management
  - Replaced old admin dashboard with modern card-based layout and organized navigation
  - Added dropdown admin menu in navigation bar for cleaner header design
  - Improved visual organization with color-coded statistics cards and quick action buttons
  - Enhanced user experience with Bootstrap tabs and clean responsive design
- **Privacy-Enhanced Evaluation System (July 11, 2025)**: Implemented role-based form visibility for detailed feedback sections
  - Detailed feedback section (accomplishments, improvement opportunities, focus areas) now only visible for self-assessments
  - External reviewers see only the question-based evaluation form without personal feedback fields
  - Enhanced privacy protection for self-reflection content
- **Dynamic Question-Based Evaluation System (July 11, 2025)**: Complete transformation to configurable assessment framework
  - Implemented dynamic question generation from database with individual scoring and comments
  - Created QuestionResponse model to store detailed responses for each question
  - Built question-based evaluation form grouped by categories with rating scales, text, and textarea inputs
  - Added individual comment fields for each question to capture detailed feedback
  - Updated backend processing to handle individual question responses and maintain category compatibility
  - Created test review assignments for admin user to demonstrate functionality
  - Enhanced admin reviewer capabilities with self-assignment and task management
- **360° Review Management System (July 11, 2025)**: Complete overhaul of assignment and review management
  - Created modern assignment matrix interface showing reviewer-officer combinations
  - Implemented dedicated reviewer dashboard with pending and completed tasks
  - Added visual progress tracking with completion rates and status badges
  - Built comprehensive assignment management with real-time preview
  - Enhanced admin interface with quick stats and matrix overview
  - Created intuitive reviewer workflow similar to modern 360 review platforms
- **Ultra-modern clean design overhaul (July 11, 2025)**: Complete website redesign with contemporary 2025 aesthetics
  - Replaced all dark themes with bright, clean white and light gray backgrounds
  - Implemented modern Inter font family for improved readability
  - Added subtle gradients, soft shadows, and smooth hover animations
  - Created clean card-based layouts with rounded corners and minimal borders
  - Updated navigation to light theme with professional blue accents
  - Redesigned badges with soft colors and rounded corners
  - Implemented modern button styles with hover effects and proper spacing
  - Enhanced table design with clean borders and subtle hover states
- **Fixed critical template errors (July 11, 2025)**: Resolved None attribute errors in assessment periods and user management
  - Added safety checks for None created_at values to prevent crashes
  - Applied consistent modern design across all admin pages
- Updated default assessment categories to match CEO performance evaluation framework:
  - Financial Strategy: Comprehensive financial management including budgeting, revenue growth, profitability, investments, cash flow, and financial reporting
  - Development Strategy: Strategic direction creation and long-term strategy implementation for all stakeholders
  - Operations: Efficient operations oversight, risk management, market response, marketing strategies, and technology ROI
  - Talent Development, Organizational Structure & Culture: Executive team development, succession planning, culture building, and community reputation
  - Board & External Relations: Board collaboration, goal setting, meeting productivity, and community leadership

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database ORM**: SQLAlchemy with Flask-SQLAlchemy extension
- **Authentication**: Flask-Login for session management
- **Form Handling**: WTForms with Flask-WTF for CSRF protection
- **Password Security**: Werkzeug for password hashing
- **Report Generation**: ReportLab for PDF generation

### Frontend Architecture
- **Template Engine**: Jinja2 (Flask's default)
- **CSS Framework**: Bootstrap 5 with dark theme
- **Icons**: Font Awesome 6.0
- **JavaScript**: Vanilla JS with Bootstrap components
- **Responsive Design**: Mobile-first approach using Bootstrap grid system

### Database Design
- **Primary Database**: SQLite (configurable to PostgreSQL via DATABASE_URL)
- **Connection Pooling**: Configured with pool_recycle and pool_pre_ping
- **Schema Management**: SQLAlchemy declarative base with automatic table creation

## Key Components

### Models (models.py)
- **User**: Handles authentication and role management (admin, board_member, officer)
- **Category**: Defines evaluation categories with descriptions and ordering
- **Assessment**: Stores performance evaluations with ratings and feedback
- **CategoryRating**: Links assessments to specific category scores

### Forms (forms.py)
- **LoginForm**: User authentication
- **AssessmentForm**: Performance evaluation with text fields
- **CategoryRatingForm**: Individual category scoring
- **UserForm**: User management for administrators

### Routes (routes.py)
- Role-based routing with access control decorators
- Dashboard views customized by user role
- Assessment creation and management endpoints
- Report generation and data export functionality

### Utilities (utils.py)
- **admin_required**: Decorator for administrative access control
- **PDF generation**: ReportLab-based report creation
- **CSV export**: Data export functionality
- **Database initialization**: Default data seeding

## Data Flow

1. **Authentication Flow**:
   - Users log in via email/password
   - Flask-Login manages session state
   - Role-based redirects to appropriate dashboards

2. **Assessment Flow**:
   - Board members access officer evaluation forms
   - Category ratings (1-5 scale) + narrative feedback
   - Data persists to Assessment and CategoryRating tables
   - Officers can view their own assessment results

3. **Reporting Flow**:
   - Admins access aggregated performance data
   - PDF reports generated via ReportLab
   - CSV export for external analysis

## External Dependencies

### Python Packages
- **Flask**: Web framework and core functionality
- **SQLAlchemy**: Database ORM and migrations
- **WTForms**: Form validation and rendering
- **ReportLab**: PDF report generation
- **Werkzeug**: Security utilities and WSGI middleware

### Frontend Dependencies
- **Bootstrap 5**: UI framework loaded via CDN
- **Font Awesome**: Icon library
- **Custom CSS**: Application-specific styling

### Infrastructure
- **ProxyFix**: Handles reverse proxy headers
- **Environment Variables**: Configuration management for secrets and database URLs

## Deployment Strategy

### Development Setup
- **Entry Point**: main.py runs Flask development server
- **Debug Mode**: Enabled for development with hot reload
- **Database**: SQLite for local development

### Production Considerations
- **Database**: Configurable via DATABASE_URL environment variable
- **Session Security**: SECRET_KEY required for production
- **Proxy Support**: ProxyFix middleware for reverse proxy deployment
- **Connection Pooling**: Configured for production database connections

### Security Features
- **CSRF Protection**: WTForms integration
- **Password Hashing**: Werkzeug secure password storage
- **Role-Based Access**: Decorator-enforced permission system
- **Session Management**: Flask-Login secure session handling

### Scaling Considerations
- **Database**: Ready for PostgreSQL migration
- **Static Assets**: CDN-hosted external dependencies
- **Session Storage**: Currently in-memory, scalable to Redis/database
- **File Storage**: Local filesystem for reports (could migrate to cloud storage)