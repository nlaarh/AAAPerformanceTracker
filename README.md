# AAAPerformanceTracker

A comprehensive Flask-based web application for CEO and executive performance evaluation featuring 360-degree review capabilities, role-based access control, and AI-powered performance analysis.

## Features

### 🎯 Core Functionality
- **360-Degree Performance Reviews**: Complete evaluation system with self-assessment and external reviewer feedback
- **Role-Based Access Control**: Admin, Board Member, and Officer roles with appropriate permissions
- **Assessment Period Management**: Flexible assessment cycles with customizable forms
- **AI-Powered Analysis**: GPT-4o integration for intelligent performance insights and feedback summaries

### 📊 Matrix Display System
- **Self-Assessment Integration**: Officers can complete self-evaluations that display alongside external reviews
- **Smart Question Matching**: Maps equivalent questions across different form types
- **Rating-Only Matrix**: Clean display filtering out text-only questions (signatures, comments, dates)
- **Accurate Calculations**: Self-assessment scores display but are excluded from reviewer averages

### 🔧 Assessment Form Builder
- **Dynamic Question Types**: Rating scales, text fields, dropdowns, checkboxes, and more
- **Form Templates**: Reusable assessment forms for different evaluation scenarios
- **Question Management**: Add, edit, clone, and reorder questions with rich formatting options
- **Form Assignment**: Assign different forms to reviewers vs. self-assessment

### 📈 Advanced Features
- **Comprehensive Reporting**: PDF and Excel exports with AI analysis
- **Activity Logging**: Complete audit trail of user actions and system events
- **User Management**: Excel import/export, password management, activation/deactivation
- **Database Backups**: Built-in backup and restore functionality

## Technology Stack

### Backend
- **Flask**: Python web framework with SQLAlchemy ORM
- **PostgreSQL**: Primary database with connection pooling
- **OpenAI GPT-4o**: AI-powered performance analysis
- **Flask-Login**: Authentication and session management
- **WTForms**: Form validation and rendering

### Frontend
- **Bootstrap 5**: Modern responsive UI framework
- **Jinja2**: Template engine with custom filters
- **Chart.js**: Interactive performance visualizations
- **Font Awesome**: Professional icon library

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/AAAPerformanceTracker.git
cd AAAPerformanceTracker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export DATABASE_URL="postgresql://user:password@localhost/database"
export OPENAI_API_KEY="your-openai-api-key"
export SESSION_SECRET="your-secret-key"
```

4. Initialize the database:
```bash
python main.py
```

5. Access the application:
- Open http://localhost:5000 in your browser
- Login with admin credentials (created during initialization)

## Usage

### For Administrators
- Create assessment periods and assign forms
- Manage users and their roles
- View comprehensive performance reports
- Export data and generate insights

### For Board Members
- Complete officer evaluations
- Access assigned review tasks
- View performance matrices

### For Officers
- Complete self-assessments
- View personal performance reviews
- Access feedback and development insights

## Key Features Implemented

### Matrix Display System (Working)
- ✅ Self-assessment scores display correctly in matrix
- ✅ Question text matching across different form types
- ✅ Rating-only questions in matrix display
- ✅ Proper calculation logic excluding self-assessment from averages
- ✅ Clean, professional matrix layout

### Assessment Form Builder
- ✅ Dynamic question types with validation
- ✅ Form templates and duplication
- ✅ Question management (add, edit, clone, reorder)
- ✅ Form assignment to assessment periods

### User Management
- ✅ Excel import/export functionality
- ✅ Password management and visibility
- ✅ User activation/deactivation
- ✅ Role-based access control

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue in the GitHub repository.

---

**Built with Flask, PostgreSQL, and OpenAI GPT-4o**