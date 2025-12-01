"""
Email service for sending verification emails and notifications
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Email configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)
FROM_NAME = os.getenv("FROM_NAME", "BEACON System")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


def send_email(to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
    """
    Send an email using SMTP
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email body
        text_content: Plain text fallback (optional)
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured. Email not sent.")
        return False
    
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
        message["To"] = to_email
        
        # Add text and HTML parts
        if text_content:
            part1 = MIMEText(text_content, "plain")
            message.attach(part1)
        
        part2 = MIMEText(html_content, "html")
        message.attach(part2)
        
        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(message)
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


def send_verification_email(to_email: str, name: str, verification_token: str) -> bool:
    """
    Send email verification link to user
    
    Args:
        to_email: User's email address
        name: User's name
        verification_token: Unique verification token
    
    Returns:
        bool: True if sent successfully
    """
    verification_url = f"{FRONTEND_URL}/verify-email?token={verification_token}"
    
    subject = "Verify Your Email - BEACON System"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; padding: 15px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 Welcome to BEACON!</h1>
            </div>
            <div class="content">
                <h2>Hi {name},</h2>
                <p>Thank you for registering with BEACON - your intelligent document management system.</p>
                <p>To complete your registration and activate your account, please verify your email address by clicking the button below:</p>
                <div style="text-align: center;">
                    <a href="{verification_url}" class="button">Verify Email Address</a>
                </div>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #667eea;">{verification_url}</p>
                <p><strong>This link will expire in 24 hours.</strong></p>
                <p>If you didn't create an account with BEACON, please ignore this email.</p>
                <p>Best regards,<br>The BEACON Team</p>
            </div>
            <div class="footer">
                <p>© 2024 BEACON System. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Welcome to BEACON!
    
    Hi {name},
    
    Thank you for registering with BEACON - your intelligent document management system.
    
    To complete your registration and activate your account, please verify your email address by visiting:
    {verification_url}
    
    This link will expire in 24 hours.
    
    If you didn't create an account with BEACON, please ignore this email.
    
    Best regards,
    The BEACON Team
    """
    
    return send_email(to_email, subject, html_content, text_content)


def send_verification_success_email(to_email: str, name: str) -> bool:
    """
    Send confirmation email after successful verification
    
    Args:
        to_email: User's email address
        name: User's name
    
    Returns:
        bool: True if sent successfully
    """
    subject = "Email Verified Successfully - BEACON System"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; padding: 15px 30px; background: #10b981; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✅ Email Verified!</h1>
            </div>
            <div class="content">
                <h2>Hi {name},</h2>
                <p>Great news! Your email address has been successfully verified.</p>
                <p>Your account is now pending approval from an administrator. You'll receive another email once your account has been approved and you can start using BEACON.</p>
                <p>What happens next:</p>
                <ul>
                    <li>Your account will be reviewed by an administrator</li>
                    <li>You'll receive an approval notification via email</li>
                    <li>Once approved, you can log in and start using BEACON</li>
                </ul>
                <p>Thank you for your patience!</p>
                <p>Best regards,<br>The BEACON Team</p>
            </div>
            <div class="footer">
                <p>© 2024 BEACON System. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Email Verified!
    
    Hi {name},
    
    Great news! Your email address has been successfully verified.
    
    Your account is now pending approval from an administrator. You'll receive another email once your account has been approved and you can start using BEACON.
    
    What happens next:
    - Your account will be reviewed by an administrator
    - You'll receive an approval notification via email
    - Once approved, you can log in and start using BEACON
    
    Thank you for your patience!
    
    Best regards,
    The BEACON Team
    """
    
    return send_email(to_email, subject, html_content, text_content)
