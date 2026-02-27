# utils/credential_manager.py
"""
Secure credential management for TDR Processor.

Provides secure storage and retrieval of sensitive credentials using:
1. Windows Credential Manager (via keyring library) - preferred
2. Environment variables - fallback
3. Session-only storage - for testing without persistence

NEVER stores passwords in plain text files.
"""
import os
import logging
from typing import Optional, Tuple

# Service name for keyring storage
SERVICE_NAME = "TDR_Processor"
SMTP_USER_KEY = "smtp_user"
SMTP_PASS_KEY = "smtp_pass"

# Try to import keyring, but don't fail if not available
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    logging.warning("keyring library not available. Using environment variables only.")


def save_smtp_credentials(smtp_user: str, smtp_pass: str) -> bool:
    """
    Securely save SMTP credentials.
    
    Uses Windows Credential Manager (keyring) if available,
    otherwise sets environment variables for current session only.
    
    Args:
        smtp_user: SMTP username (email address)
        smtp_pass: SMTP password or app-specific password
        
    Returns:
        True if saved successfully, False otherwise
    """
    if not smtp_user or not smtp_pass:
        logging.warning("Cannot save empty credentials")
        return False
    
    try:
        if KEYRING_AVAILABLE:
            # Save to Windows Credential Manager (secure, persistent)
            keyring.set_password(SERVICE_NAME, SMTP_USER_KEY, smtp_user)
            keyring.set_password(SERVICE_NAME, SMTP_PASS_KEY, smtp_pass)
            logging.info("SMTP credentials saved to Windows Credential Manager")
            return True
        else:
            # Fallback: Set environment variables (session only)
            os.environ['TDR_SMTP_USER'] = smtp_user
            os.environ['TDR_SMTP_PASS'] = smtp_pass
            logging.info("SMTP credentials set for current session (env vars)")
            return True
    except Exception as e:
        logging.error(f"Failed to save credentials: {type(e).__name__}")
        return False


def get_smtp_credentials() -> Optional[Tuple[str, str]]:
    """
    Retrieve SMTP credentials securely.
    
    Checks in order:
    1. Environment variables (TDR_SMTP_USER, TDR_SMTP_PASS)
    2. Windows Credential Manager (keyring)
    
    Returns:
        Tuple of (smtp_user, smtp_pass) if found, None otherwise
    """
    # First check environment variables (highest priority - allows override)
    env_user = os.getenv('TDR_SMTP_USER')
    env_pass = os.getenv('TDR_SMTP_PASS')
    
    if env_user and env_pass:
        return (env_user, env_pass)
    
    # Then check keyring
    if KEYRING_AVAILABLE:
        try:
            kr_user = keyring.get_password(SERVICE_NAME, SMTP_USER_KEY)
            kr_pass = keyring.get_password(SERVICE_NAME, SMTP_PASS_KEY)
            
            if kr_user and kr_pass:
                return (kr_user, kr_pass)
        except Exception as e:
            logging.debug(f"Keyring retrieval error: {type(e).__name__}")
    
    return None


def delete_smtp_credentials() -> bool:
    """
    Remove stored SMTP credentials.
    
    Clears both environment variables and keyring storage.
    
    Returns:
        True if deletion successful, False otherwise
    """
    try:
        # Clear environment variables
        if 'TDR_SMTP_USER' in os.environ:
            del os.environ['TDR_SMTP_USER']
        if 'TDR_SMTP_PASS' in os.environ:
            del os.environ['TDR_SMTP_PASS']
        
        # Clear keyring
        if KEYRING_AVAILABLE:
            try:
                keyring.delete_password(SERVICE_NAME, SMTP_USER_KEY)
            except keyring.errors.PasswordDeleteError:
                pass  # Already deleted or never existed
            try:
                keyring.delete_password(SERVICE_NAME, SMTP_PASS_KEY)
            except keyring.errors.PasswordDeleteError:
                pass
        
        logging.info("SMTP credentials cleared")
        return True
    except Exception as e:
        logging.error(f"Failed to delete credentials: {type(e).__name__}")
        return False


def has_stored_credentials() -> bool:
    """
    Check if SMTP credentials are stored (without retrieving them).
    
    Returns:
        True if credentials exist, False otherwise
    """
    return get_smtp_credentials() is not None


def get_credential_storage_info() -> str:
    """
    Get information about how credentials are stored.

    Returns:
        Human-readable string describing storage method and backend.
        Uses platform-appropriate terminology (keyring supports Windows
        Credential Manager, macOS Keychain, and Linux Secret Service).
    """
    if os.getenv('TDR_SMTP_USER') and os.getenv('TDR_SMTP_PASS'):
        return "Environment Variables"

    if KEYRING_AVAILABLE:
        try:
            if keyring.get_password(SERVICE_NAME, SMTP_USER_KEY):
                return "System Secure Storage (Keyring)"
        except Exception:
            pass

    return "Not Configured"


def test_smtp_connection(smtp_server: str, smtp_port: int, 
                         smtp_user: str, smtp_pass: str) -> Tuple[bool, str]:
    """
    Test SMTP connection with provided credentials.
    
    Does NOT save credentials - only tests the connection.
    
    Args:
        smtp_server: SMTP server hostname
        smtp_port: SMTP port
        smtp_user: Username to test
        smtp_pass: Password to test
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    import smtplib
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
        return (True, "Connection successful! Credentials are valid.")
    except smtplib.SMTPAuthenticationError:
        return (False, "Authentication failed. Check username/password.")
    except smtplib.SMTPConnectError:
        return (False, f"Cannot connect to {smtp_server}:{smtp_port}")
    except smtplib.SMTPException as e:
        return (False, f"SMTP error: {str(e)[:50]}")
    except Exception as e:
        return (False, f"Connection error: {type(e).__name__}")
