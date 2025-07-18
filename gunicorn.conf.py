# Gunicorn configuration for production deployment
import os

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = 1
worker_class = "sync"
worker_connections = 1000
timeout = 300  # Increased timeout for deployment stability
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
graceful_timeout = 120  # Graceful shutdown timeout

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "aaaperformancetracker"

# Server mechanics
daemon = False
pidfile = None  # Disable PID file to prevent conflicts
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None

# Application
preload_app = True

# Health check - enable for deployment monitoring
def when_ready(server):
    """Called just after the server is started"""
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    """Called just after a worker has been exited on SIGINT or SIGQUIT"""
    worker.log.info("Worker received INT or QUIT signal")

def on_exit(server):
    """Called just before exiting gunicorn"""
    server.log.info("Shutting down: Master")