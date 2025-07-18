# AAAPerformanceTracker - Railway Deployment Guide

## Overview
AAAPerformanceTracker is a comprehensive Flask-based web application for CEO and executive performance evaluation featuring 360-degree review capabilities, role-based access control, and AI-powered performance analysis.

## Recent Deployment Fixes (July 18, 2025)
✅ **Fixed Deployment Timeout Issues**: Resolved 3 consecutive deployment failures
✅ **Lazy Database Initialization**: Optimized startup process for production
✅ **Health Check Endpoint**: Added `/health` for monitoring
✅ **Enhanced Gunicorn Configuration**: Production-ready settings with 300s timeout
✅ **SQLAlchemy Warnings**: Resolved relationship conflicts

## Quick Railway Deployment

### 1. Environment Variables Required
```
DATABASE_URL=postgresql://...  # Your PostgreSQL database URL
OPENAI_API_KEY=sk-...         # Your OpenAI API key
SESSION_SECRET=your-secret-key # Flask session secret
```

### 2. Railway Configuration
The application is configured to run with:
- **Port**: 5000 (configured in gunicorn.conf.py)
- **Build Command**: `pip install -r requirements.txt` (automatic)
- **Start Command**: `gunicorn --config gunicorn.conf.py wsgi:application`

### 3. Database Setup
The application uses PostgreSQL and will automatically:
- Create all required tables on first startup
- Initialize default data (categories, questions, admin user)
- Handle migrations through SQLAlchemy

### 4. Health Check
Railway can monitor the application health at:
- **Health Endpoint**: `/health`
- **Expected Response**: `{"status": "healthy", "database": "connected"}`

## Key Files for Deployment

### Production Entry Points
- `wsgi.py` - Production WSGI entry point
- `gunicorn.conf.py` - Production server configuration
- `main.py` - Development entry point

### Core Application
- `app.py` - Flask application factory with lazy initialization
- `models.py` - Database models and relationships
- `routes.py` - All application routes and logic

### Configuration
- `pyproject.toml` - Python dependencies
- `startup.py` - Production initialization script
- `deployment_health_check.py` - Deployment verification

## Application Features
- **Role-Based Access**: Admin, Board Member, Officer roles
- **Assessment Management**: Create and manage evaluation periods
- **360-Degree Reviews**: Comprehensive reviewer assignment matrix
- **AI-Powered Analysis**: OpenAI GPT-4o integration for performance insights
- **PDF Reports**: Comprehensive assessment reports with AI analysis
- **Activity Logging**: Complete audit trail
- **Excel Export/Import**: Assessment forms and data management

## Default Admin Access
- **Email**: `admin@company.com`
- **Password**: `admin123`

## Support
- Health check confirms 85 routes registered
- All deployment timeout issues resolved
- Production-ready with enhanced error handling and logging