import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import url_for, current_app
import logging

class EmailService:
    def __init__(self):
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_username = os.environ.get('SMTP_USERNAME', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
        self.from_email = os.environ.get('FROM_EMAIL', self.smtp_username)
        self.from_name = os.environ.get('FROM_NAME', 'AAA Performance Tracker')
    
    def send_assessment_notification(self, reviewer_email, reviewer_name, officer_name, period_name, assessment_url):
        """Send assessment assignment notification email"""
        try:
            subject = f"Assessment Assignment: {officer_name} - {period_name}"
            
            # Create HTML email content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f8f9fa; }}
                    .button {{ 
                        display: inline-block; 
                        background-color: #28a745; 
                        color: white; 
                        padding: 12px 24px; 
                        text-decoration: none; 
                        border-radius: 5px;
                        margin: 20px 0;
                    }}
                    .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Assessment Assignment</h1>
                    </div>
                    <div class="content">
                        <h2>Hello {reviewer_name},</h2>
                        <p>You have been assigned to evaluate <strong>{officer_name}</strong> for the assessment period: <strong>{period_name}</strong>.</p>
                        
                        <p>Please complete your assessment by logging into the system and filling out the evaluation form. Your feedback is important for the organization's continued growth and development.</p>
                        
                        <p style="text-align: center;">
                            <a href="{assessment_url}" class="button">Start Assessment</a>
                        </p>
                        
                        <p><strong>What you need to do:</strong></p>
                        <ul>
                            <li>Click the link above to access the assessment form</li>
                            <li>Log in with your credentials</li>
                            <li>Rate the officer across 5 key performance categories</li>
                            <li>Provide detailed feedback in the text areas</li>
                            <li>Submit your completed assessment</li>
                        </ul>
                        
                        <p>If you have any questions or technical issues, please contact your administrator.</p>
                        
                        <p>Thank you for your participation in the performance evaluation process.</p>
                    </div>
                    <div class="footer">
                        <p>This is an automated message from AAA Performance Tracker.<br>
                        Please do not reply to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create plain text version
            text_content = f"""
            Assessment Assignment - {period_name}
            
            Hello {reviewer_name},
            
            You have been assigned to evaluate {officer_name} for the assessment period: {period_name}.
            
            Please complete your assessment by visiting: {assessment_url}
            
            Steps to complete:
            1. Click the link above to access the assessment form
            2. Log in with your credentials
            3. Rate the officer across 5 key performance categories
            4. Provide detailed feedback in the text areas
            5. Submit your completed assessment
            
            If you have any questions, please contact your administrator.
            
            Thank you for your participation.
            
            ---
            AAA Performance Tracker
            This is an automated message. Please do not reply.
            """
            
            return self._send_email(reviewer_email, subject, text_content, html_content)
            
        except Exception as e:
            logging.error(f"Error creating assessment notification email: {str(e)}")
            return False
    
    def send_reminder_email(self, reviewer_email, reviewer_name, officer_name, period_name, days_remaining):
        """Send reminder email for pending assessments"""
        try:
            subject = f"Reminder: Assessment Due Soon - {officer_name}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #ffc107; color: #212529; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #fff3cd; }}
                    .button {{ 
                        display: inline-block; 
                        background-color: #dc3545; 
                        color: white; 
                        padding: 12px 24px; 
                        text-decoration: none; 
                        border-radius: 5px;
                        margin: 20px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>⚠️ Assessment Reminder</h1>
                    </div>
                    <div class="content">
                        <h2>Hello {reviewer_name},</h2>
                        <p>This is a friendly reminder that you have a pending assessment for <strong>{officer_name}</strong> in the <strong>{period_name}</strong> period.</p>
                        
                        <p><strong>Time Remaining: {days_remaining} days</strong></p>
                        
                        <p>Please complete your assessment as soon as possible to ensure timely completion of the review process.</p>
                        
                        <p style="text-align: center;">
                            <a href="{current_app.config.get('BASE_URL', 'http://localhost:5000')}" class="button">Complete Assessment Now</a>
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            Assessment Reminder - {period_name}
            
            Hello {reviewer_name},
            
            This is a reminder that you have a pending assessment for {officer_name}.
            Time remaining: {days_remaining} days
            
            Please log in to complete your assessment as soon as possible.
            
            Thank you.
            
            ---
            AAA Performance Tracker
            """
            
            return self._send_email(reviewer_email, subject, text_content, html_content)
            
        except Exception as e:
            logging.error(f"Error creating reminder email: {str(e)}")
            return False
    
    def _send_email(self, to_email, subject, text_content, html_content):
        """Send email using SMTP"""
        try:
            # Skip if no SMTP configuration
            if not self.smtp_username or not self.smtp_password:
                logging.info(f"Email would be sent to {to_email}: {subject}")
                return True  # Return True for demo purposes
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logging.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logging.error(f"Error sending email to {to_email}: {str(e)}")
            return False
    
    def test_connection(self):
        """Test email configuration"""
        try:
            if not self.smtp_username or not self.smtp_password:
                return False, "SMTP credentials not configured"
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.quit()
            return True, "Email configuration is working"
            
        except Exception as e:
            return False, f"Email configuration error: {str(e)}"

# Create global email service instance
email_service = EmailService()