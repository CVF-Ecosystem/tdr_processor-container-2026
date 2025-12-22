# utils/email_notifier.py
"""
Email notification utilities for TDR Processor - SECURE IMPLEMENTATION.

Provides secure email sending functionality for automated report delivery.
Features:
- Environment variable-based credential loading (no plain text passwords)
- Input validation to prevent email injection attacks
- Sanitized error logging (no sensitive information leakage)
- Secure connection with TLS/STARTTLS
- Comprehensive error handling with generic user messages
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import Optional
from .input_validator import validate_email, validate_smtp_server, validate_smtp_port


def get_smtp_credentials() -> Optional[tuple]:
    """
    Load SMTP credentials securely from environment variables.
    
    Credentials should never be hardcoded or stored in configuration files.
    This function loads them from environment:
    - TDR_SMTP_USER: SMTP username (typically email address)
    - TDR_SMTP_PASS: SMTP password or app-specific password
    
    Returns:
        Tuple of (smtp_user, smtp_pass) if both present, None if either missing
    
    Note:
        Environment variables are created at application startup and cleared
        from memory after use. This is the most secure practice for credential
        handling in desktop applications.
    
    Example:
        >>> # Set environment variables before running application:
        >>> # export TDR_SMTP_USER="user@gmail.com"
        >>> # export TDR_SMTP_PASS="app_specific_password"
        >>> creds = get_smtp_credentials()
        >>> if creds:
        ...     user, password = creds
    """
    smtp_user = os.getenv('TDR_SMTP_USER')
    smtp_pass = os.getenv('TDR_SMTP_PASS')
    
    if not smtp_user or not smtp_pass:
        logging.warning("SMTP credentials not found in environment variables. "
                       "Please set TDR_SMTP_USER and TDR_SMTP_PASS.")
        return None
    
    return (smtp_user, smtp_pass)


def send_notification_email(smtp_server: str, smtp_port: int, smtp_user: str, smtp_pass: str,
                            recipient_email: str, subject: str, body: str) -> bool:
    """
    Send notification email via SMTP server with security hardening.
    
    Sends an email message with validation and secure credential handling.
    Uses STARTTLS for secure connection. Returns False on error without
    raising exceptions (suitable for background/scheduled operations).
    
    Args:
        smtp_server: SMTP server hostname/IP (e.g., "smtp.gmail.com") - validated
        smtp_port: SMTP server port (validated: 25, 587, or 465)
        smtp_user: SMTP authentication username (email address) - validated
        smtp_pass: SMTP authentication password - NOT LOGGED OR EXPOSED
        recipient_email: Recipient email address - validated for injection attacks
        subject: Email subject line
        body: Email body text (plain text)
    
    Returns:
        True if email sent successfully, False on error
        (No exceptions raised; all errors are logged with sanitized messages)
    
    Note:
        SECURITY:
        - Credentials are NEVER logged
        - Email parameters are validated to prevent injection attacks
        - Error messages are sanitized to prevent information disclosure
        - Exception details are NOT included in logs (may contain sensitive data)
        - Uses context manager (with statement) for proper connection cleanup
    
    Example:
        >>> success = send_notification_email(
        ...     "smtp.gmail.com", 587, "user@gmail.com", "app_password",
        ...     "recipient@example.com", "TDR Report", "Your report is ready."
        ... )
    """
    # SECURITY: Validate all inputs before use
    is_valid, error = validate_email(recipient_email)
    if not is_valid:
        logging.error(f"Invalid recipient email address: {error}")
        return False
    
    is_valid, error = validate_smtp_server(smtp_server)
    if not is_valid:
        logging.error(f"Invalid SMTP server: {error}")
        return False
    
    is_valid, error = validate_smtp_port(smtp_port)
    if not is_valid:
        logging.error(f"Invalid SMTP port: {error}")
        return False
    
    # Verify credentials provided
    if not smtp_user or not smtp_pass:
        logging.error("SMTP credentials not provided")
        return False
    
    try:
        # Log only non-sensitive information
        logging.info("[Email] Preparing to send email notification")
        
        # Create message
        message = MIMEMultipart()
        message["From"] = smtp_user
        message["To"] = recipient_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain", "utf-8"))
        
        # Create SMTP connection with TLS security
        # Use context manager to ensure proper connection cleanup
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.starttls()  # Upgrade connection to TLS
            
            # SECURITY: Don't log credentials
            server.login(smtp_user, smtp_pass)
            
            # Send email
            server.sendmail(smtp_user, recipient_email, message.as_string())
        
        # Log success without sensitive information
        logging.info("[Email] Email notification sent successfully")
        return True
    
    except smtplib.SMTPAuthenticationError:
        # SECURITY: Generic error message (don't reveal credential issue details)
        logging.error("[Email] Email delivery failed: Authentication error")
        return False
    
    except smtplib.SMTPException as e:
        # SECURITY: Log exception type only, not details (may contain sensitive data)
        logging.error(f"[Email] Email delivery failed: SMTP error ({type(e).__name__})")
        return False
    
    except TimeoutError:
        # Connection timeout - safe to log
        logging.error("[Email] Email delivery failed: Connection timeout")
        return False
    
    except Exception as e:
        # SECURITY: Log exception type and generic message, NOT the full exception
        # (which may contain credentials or sensitive data in the message)
        logging.error(f"[Email] Email delivery failed: {type(e).__name__}")
        # Do NOT use logging.exception() here - it logs full stack trace which may
        # expose sensitive information (passwords, file paths, etc.)
        return False


def send_notification_email_with_config(subject: str, body: str) -> bool:
    """Send email using configuration loaded from environment variables.
    
    This is the recommended way to send emails in the application.
    Uses SMTP and email settings loaded from environment variables via
    config.load_environment_config().
    
    Args:
        subject: Email subject line
        body: Email body text (plain text)
    
    Returns:
        True if email sent successfully, False on error or if email disabled
    
    Example:
        >>> # After config.load_environment_config() has been called:
        >>> success = send_notification_email_with_config(
        ...     "Report Ready", "Your TDR report has been processed."
        ... )
    """
    # Import here to avoid circular dependency
    from config import get_config
    
    cfg = get_config()
    
    # Check if email notifications are enabled
    if not cfg.email.enabled:
        logging.debug("[Email] Email notifications are disabled")
        return False
    
    # Verify configuration is complete
    if not cfg.email.sender or not cfg.email.recipients:
        logging.warning("[Email] Email configuration incomplete (sender or recipients missing)")
        return False
    
    # Send to each recipient
    all_success = True
    for recipient in cfg.email.recipients:
        success = send_notification_email(
            smtp_server=cfg.smtp.server,
            smtp_port=cfg.smtp.port,
            smtp_user=cfg.smtp.username,
            smtp_pass=cfg.smtp.password,
            recipient_email=recipient,
            subject=subject,
            body=body
        )
        if not success:
            all_success = False
    
    return all_success