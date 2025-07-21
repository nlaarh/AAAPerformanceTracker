# AAAPerformanceTracker Deployment & Setup Guide
## Complete Production Deployment Documentation
**Version:** 3.0.0  
**Date:** July 20, 2025  
**Target:** Production Environment Setup

---

## Table of Contents
1. [Quick Start Guide](#quick-start-guide)
2. [System Requirements](#system-requirements)
3. [Database Setup](#database-setup)
4. [Application Deployment](#application-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Production Deployment Options](#production-deployment-options)
7. [Post-Deployment Verification](#post-deployment-verification)
8. [Maintenance & Monitoring](#maintenance--monitoring)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start Guide

### For Railway Deployment (Recommended)

```bash
# 1. Clone repository from GitHub
git clone https://github.com/nlaarh/AAAPerformanceTracker.git
cd AAAPerformanceTracker

# 2. Deploy to Railway
# Visit railway.app, connect GitHub repo, set environment variables

# 3. Configure environment variables in Railway dashboard:
DATABASE_URL=postgresql://user:pass@host:port/db
OPENAI_API_KEY=sk-your-openai-key
SESSION_SECRET=your-random-secret-key
```

### For Local Development

```bash
# 1. Clone and setup
git clone https://github.com/nlaarh/AAAPerformanceTracker.git
cd AAAPerformanceTracker

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Setup environment variables
export DATABASE_URL="postgresql://localhost/aaaperformance"
export OPENAI_API_KEY="sk-your-openai-key"  
export SESSION_SECRET="your-secret-key"

# 4. Initialize database
python -c "from app import init_database; init_database()"

# 5. Start application
python main.py
```

---

## System Requirements

### Minimum Requirements
- **Python:** 3.11 or higher
- **Memory:** 512MB RAM minimum, 2GB recommended
- **Storage:** 1GB minimum for application and database
- **Database:** PostgreSQL 13+ (production) or SQLite (development)
- **Network:** HTTPS support for production

### Recommended Production Environment
- **Memory:** 4GB RAM
- **Storage:** 10GB SSD storage
- **CPU:** 2 cores minimum
- **Database:** PostgreSQL 15+ with connection pooling
- **Load Balancer:** Nginx or similar for static file serving

### Required Python Packages
```txt
flask>=3.1.1
flask-sqlalchemy>=3.1.1
flask-login>=0.6.3
flask-wtf>=1.2.2
wtforms>=3.2.1
werkzeug>=3.1.3
psycopg2-binary>=2.9.10
sqlalchemy>=2.0.41
openai>=1.95.1
reportlab>=4.4.2
openpyxl>=3.1.5
plotly>=6.2.0
matplotlib>=3.10.3
seaborn>=0.13.2
pandas>=2.3.1
requests>=2.32.4
sendgrid>=6.12.4
email-validator>=2.2.0
gunicorn>=23.0.0
```

---

## Database Setup

### Option 1: PostgreSQL (Production Recommended)

#### Install PostgreSQL
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS with Homebrew
brew install postgresql
brew services start postgresql

# CentOS/RHEL
sudo yum install postgresql postgresql-server
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Create Database and User
```sql
-- Connect as postgres user
sudo -u postgres psql

-- Create database and user
CREATE DATABASE aaaperformance;
CREATE USER aaauser WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE aaaperformance TO aaauser;

-- Grant schema permissions
\c aaaperformance
GRANT ALL ON SCHEMA public TO aaauser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO aaauser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO aaauser;

\q
```

#### Execute DDL Script
```bash
# Run the complete database creation script
psql -h localhost -U aaauser -d aaaperformance -f DATABASE_DDL_SCRIPT.sql

# Load sample data (optional)
psql -h localhost -U aaauser -d aaaperformance -f SAMPLE_DATA.sql
```

### Option 2: Cloud Database Services

#### Railway PostgreSQL
```bash
# Railway automatically provisions PostgreSQL
# DATABASE_URL provided automatically in environment
# No manual setup required
```

#### AWS RDS PostgreSQL
```bash
# Create RDS instance through AWS Console
# Security group: Allow port 5432 from application servers
# Parameter group: Optimize for performance
# DATABASE_URL format: postgresql://username:password@host:port/database
```

#### Google Cloud SQL
```bash
# Create Cloud SQL PostgreSQL instance
# Enable Cloud SQL Admin API
# Create database user and password
# Whitelist application IP addresses
```

### Database Performance Optimization

#### PostgreSQL Configuration (postgresql.conf)
```ini
# Memory Configuration
shared_buffers = 256MB                    # 25% of system RAM
effective_cache_size = 1GB                # 75% of system RAM
work_mem = 4MB                           # For sorting and grouping
maintenance_work_mem = 64MB              # For maintenance operations

# Storage Configuration  
random_page_cost = 1.1                  # For SSD storage
effective_io_concurrency = 200          # For SSD storage

# Connection Configuration
max_connections = 100                    # Adjust based on load
shared_preload_libraries = 'pg_stat_statements'  # Query analysis

# Logging Configuration
log_statement = 'mod'                    # Log modifications
log_min_duration_statement = 1000       # Log slow queries (1s+)
```

---

## Application Deployment

### Production WSGI Configuration (gunicorn.conf.py)
```python
# gunicorn.conf.py
import os

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2

# Application
preload_app = True
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'aaaperformancetracker'

# SSL (if using SSL termination at application level)
# keyfile = '/path/to/ssl/key.pem'
# certfile = '/path/to/ssl/cert.pem'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
```

### systemd Service File (Linux)
```ini
# /etc/systemd/system/aaaperformance.service
[Unit]
Description=AAA Performance Tracker
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/aaaperformancetracker
Environment=PATH=/opt/aaaperformancetracker/venv/bin
Environment=DATABASE_URL=postgresql://user:pass@localhost/aaaperformance
Environment=OPENAI_API_KEY=sk-your-openai-key
Environment=SESSION_SECRET=your-session-secret
ExecStart=/opt/aaaperformancetracker/venv/bin/gunicorn --config gunicorn.conf.py main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable aaaperformance
sudo systemctl start aaaperformance
sudo systemctl status aaaperformance
```

### Nginx Reverse Proxy Configuration
```nginx
# /etc/nginx/sites-available/aaaperformance
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Application proxy
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;
    }

    # Static files (if serving from nginx)
    location /static {
        alias /opt/aaaperformancetracker/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security - block access to sensitive files
    location ~ /\. {
        deny all;
    }
    
    location ~ \.(sql|env|conf|ini)$ {
        deny all;
    }
}
```

---

## Environment Configuration

### Required Environment Variables
```bash
# Database Configuration
DATABASE_URL="postgresql://username:password@host:port/database"

# AI Integration (Required)
OPENAI_API_KEY="sk-your-openai-api-key-here"

# Security (Required)
SESSION_SECRET="your-random-secret-key-minimum-32-characters"

# Optional: Email Integration
SENDGRID_API_KEY="SG.your-sendgrid-api-key"

# Optional: Development Settings
ENVIRONMENT="production"  # or "development"
FLASK_ENV="production"
```

### Environment Variable Generation
```bash
# Generate secure session secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Or using openssl
openssl rand -base64 32
```

### .env File Template (Development)
```bash
# .env file for local development
DATABASE_URL=postgresql://localhost/aaaperformance_dev
OPENAI_API_KEY=sk-your-openai-api-key
SESSION_SECRET=your-development-secret-key
ENVIRONMENT=development
FLASK_ENV=development
```

---

## Production Deployment Options

### Option 1: Railway (Recommended for Quick Deployment)

#### Setup Steps
1. **Connect GitHub Repository**
   ```bash
   # Push code to GitHub
   git remote add origin https://github.com/yourusername/AAAPerformanceTracker.git
   git push -u origin main
   ```

2. **Deploy on Railway**
   - Visit [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your AAAPerformanceTracker repository
   - Railway auto-detects Python and provisions PostgreSQL

3. **Configure Environment Variables**
   ```bash
   # Set in Railway dashboard:
   OPENAI_API_KEY=sk-your-openai-key
   SESSION_SECRET=your-secret-key
   # DATABASE_URL is automatically provided
   ```

4. **Custom Domain (Optional)**
   - Add custom domain in Railway settings
   - Configure DNS CNAME record

#### Railway Configuration Files
```toml
# railway.toml
[build]
builder = "NIXPACKS"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### Option 2: Heroku

#### Setup Steps
```bash
# Install Heroku CLI and login
heroku login

# Create Heroku app
heroku create your-app-name

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev

# Set environment variables
heroku config:set OPENAI_API_KEY=sk-your-openai-key
heroku config:set SESSION_SECRET=your-secret-key

# Deploy
git push heroku main
```

#### Procfile
```
web: gunicorn --config gunicorn.conf.py main:app
release: python -c "from app import init_database; init_database()"
```

### Option 3: DigitalOcean App Platform

#### app.yaml Configuration
```yaml
name: aaaperformance
services:
- name: web
  source_dir: /
  github:
    repo: yourusername/AAAPerformanceTracker
    branch: main
  run_command: gunicorn --config gunicorn.conf.py main:app
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: OPENAI_API_KEY
    value: sk-your-openai-key
  - key: SESSION_SECRET
    value: your-secret-key
  health_check:
    http_path: /health
databases:
- name: aaaperformance-db
  engine: PG
  version: "15"
```

### Option 4: AWS EC2 with Docker

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000

CMD ["gunicorn", "--config", "gunicorn.conf.py", "main:app"]
```

#### docker-compose.yml
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/aaaperformance
      - OPENAI_API_KEY=sk-your-openai-key
      - SESSION_SECRET=your-secret-key
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: aaaperformance
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./DATABASE_DDL_SCRIPT.sql:/docker-entrypoint-initdb.d/01-schema.sql
      - ./SAMPLE_DATA.sql:/docker-entrypoint-initdb.d/02-data.sql
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
```

---

## Post-Deployment Verification

### Health Check Verification
```bash
# Test health endpoint
curl -f https://your-domain.com/health

# Expected response:
# {"status": "healthy", "database": "connected"}
```

### Application Functionality Test
```bash
# Test login page
curl -I https://your-domain.com/login

# Test static files
curl -I https://your-domain.com/static/css/modern.css

# Test admin access (after login)
curl -c cookies.txt -d "email=admin@aaaperformance.com&password=admin123" https://your-domain.com/login
curl -b cookies.txt https://your-domain.com/admin
```

### Database Verification
```sql
-- Connect to database and verify tables
\dt

-- Check user count
SELECT role, COUNT(*) FROM "user" GROUP BY role;

-- Check assessment periods
SELECT name, is_active, start_date, end_date FROM assessment_period;

-- Verify assessment forms
SELECT title, is_active FROM assessment_form;
```

### Performance Testing
```bash
# Install Apache Bench for load testing
sudo apt install apache2-utils

# Test concurrent users
ab -n 100 -c 10 -H "Accept-Encoding: gzip,deflate" https://your-domain.com/

# Test login performance
ab -n 50 -c 5 -p login_data.txt -T application/x-www-form-urlencoded https://your-domain.com/login
```

---

## Maintenance & Monitoring

### Database Backup Script
```bash
#!/bin/bash
# backup_database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"
DB_NAME="aaaperformance"
DB_USER="aaauser"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
pg_dump -h localhost -U $DB_USER -d $DB_NAME -f $BACKUP_DIR/aaaperformance_backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/aaaperformance_backup_$DATE.sql

# Remove backups older than 30 days
find $BACKUP_DIR -name "aaaperformance_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: aaaperformance_backup_$DATE.sql.gz"
```

### Monitoring Script
```python
#!/usr/bin/env python3
# monitor.py

import requests
import smtplib
from email.mime.text import MIMEText
import time
import logging

def check_health():
    try:
        response = requests.get('https://your-domain.com/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'healthy':
                return True, 'System healthy'
        return False, f'Health check failed: {response.status_code}'
    except Exception as e:
        return False, f'Health check error: {str(e)}'

def send_alert(message):
    # Configure email alerts
    sender = 'monitoring@your-domain.com'
    receiver = 'admin@your-domain.com'
    
    msg = MIMEText(f'AAAPerformanceTracker Alert: {message}')
    msg['Subject'] = 'System Alert'
    msg['From'] = sender
    msg['To'] = receiver
    
    # Send email (configure SMTP settings)
    # smtp_server.send_message(msg)

if __name__ == "__main__":
    healthy, message = check_health()
    if not healthy:
        send_alert(message)
        logging.error(message)
    else:
        logging.info(message)
```

### Log Rotation Configuration
```
# /etc/logrotate.d/aaaperformance
/var/log/aaaperformance/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload aaaperformance
    endscript
}
```

### Automated Updates Script
```bash
#!/bin/bash
# update_application.sh

# Stop service
sudo systemctl stop aaaperformance

# Backup current version
cp -r /opt/aaaperformancetracker /opt/backup_$(date +%Y%m%d_%H%M%S)

# Pull latest changes
cd /opt/aaaperformancetracker
git pull origin main

# Install dependencies
/opt/aaaperformancetracker/venv/bin/pip install -r requirements.txt

# Run database migrations if needed
/opt/aaaperformancetracker/venv/bin/python -c "from app import init_database; init_database()"

# Start service
sudo systemctl start aaaperformance

# Verify health
sleep 10
curl -f http://localhost:5000/health
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Database Connection Errors
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database permissions
sudo -u postgres psql -c "\du"

# Test connection
psql -h localhost -U aaauser -d aaaperformance -c "SELECT 1;"

# Check connection limits
sudo -u postgres psql -c "SHOW max_connections;"
```

#### 2. Application Won't Start
```bash
# Check Python version
python3 --version

# Check dependencies
pip list | grep -E "(flask|sqlalchemy|psycopg2)"

# Check logs
sudo journalctl -u aaaperformance -f

# Check port availability
sudo netstat -tlnp | grep :5000
```

#### 3. Performance Issues
```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check database size
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::text)) AS size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::text) DESC;
```

#### 4. SSL/TLS Issues
```bash
# Check certificate validity
openssl x509 -in /path/to/cert.pem -text -noout

# Test SSL connection
openssl s_client -connect your-domain.com:443

# Check certificate chain
curl -vI https://your-domain.com
```

#### 5. Memory Issues
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Check swap usage
swapon --show

# Monitor in real-time
top -p $(pgrep -f gunicorn)
```

### Debugging Configuration

#### Enable Debug Logging
```python
# Add to app.py for debugging
import logging
logging.basicConfig(level=logging.DEBUG)

# Database query logging
app.config['SQLALCHEMY_ECHO'] = True
```

#### Application Logs Analysis
```bash
# Monitor application logs
tail -f /var/log/aaaperformance/app.log

# Search for errors
grep -i error /var/log/aaaperformance/app.log

# Analyze access patterns
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -nr
```

### Recovery Procedures

#### Database Recovery
```bash
# Restore from backup
gunzip aaaperformance_backup_YYYYMMDD_HHMMSS.sql.gz
psql -h localhost -U aaauser -d aaaperformance -f aaaperformance_backup_YYYYMMDD_HHMMSS.sql
```

#### Application Recovery
```bash
# Rollback to previous version
sudo systemctl stop aaaperformance
rm -rf /opt/aaaperformancetracker
mv /opt/backup_YYYYMMDD_HHMMSS /opt/aaaperformancetracker
sudo systemctl start aaaperformance
```

---

## Security Checklist

### Pre-Production Security Review
- [ ] Change all default passwords
- [ ] Configure HTTPS with valid SSL certificates
- [ ] Set secure session configuration
- [ ] Enable database connection encryption
- [ ] Configure firewall rules
- [ ] Set up automated security updates
- [ ] Review and configure CORS settings
- [ ] Enable rate limiting
- [ ] Configure security headers
- [ ] Set up monitoring and alerting
- [ ] Backup and recovery procedures tested
- [ ] Penetration testing completed

### Production Security Configuration
```python
# Security settings for production
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24),
    SECRET_KEY=os.environ.get('SESSION_SECRET'),
    WTF_CSRF_ENABLED=True,
    WTF_CSRF_TIME_LIMIT=None
)
```

---

**Support Information:**
- **Documentation:** This deployment guide
- **Repository:** https://github.com/nlaarh/AAAPerformanceTracker
- **Issues:** GitHub Issues for bug reports and feature requests
- **Updates:** Check repository for latest releases and updates

---

*This guide provides comprehensive deployment instructions for the AAAPerformanceTracker system. Follow the appropriate section based on your deployment target and requirements.*