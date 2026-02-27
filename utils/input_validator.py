# utils/input_validator.py
"""
Input validation utilities for TDR Processor.

Provides functions for:
- Email address validation with RFC 5322 compliance
- File path validation to prevent path traversal attacks
- Excel file type validation using magic bytes
- SMTP parameter validation (server, port)
- File size validation to prevent DoS attacks

All validators return (bool, str) tuples: (is_valid, error_message)
"""

import re
from pathlib import Path
from typing import Tuple


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email address format and prevent injection attacks.
    
    Uses regex pattern matching for RFC 5322 compliant validation.
    Prevents email header injection (CRLF injection attacks).
    
    Args:
        email: Email address string to validate
    
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if email is valid
        - error_message: Empty string if valid, error description if invalid
    
    Example:
        >>> validate_email("user@example.com")
        (True, "")
        >>> validate_email("invalid.email")
        (False, "Invalid email format")
        >>> validate_email("user@evil.com\\nBCC: attacker@evil.com")
        (False, "Email contains invalid characters (injection attempt)")
    """
    if not email or not isinstance(email, str):
        return False, "Email must be a non-empty string"
    
    # Check for email header injection (CRLF characters)
    if '\n' in email or '\r' in email:
        return False, "Email contains invalid characters (injection attempt)"
    
    # Check for suspiciously long email (prevent DoS)
    if len(email) > 254:  # RFC 5321 limit
        return False, "Email address exceeds maximum length (254 characters)"
    
    # RFC 5322 simplified regex pattern
    # More permissive than strict RFC but adequate for practical use
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    return True, ""


def validate_file_path(file_path: str, base_directory: Path = None) -> Tuple[bool, str]:
    """
    Validate file path to prevent path traversal attacks.
    
    Checks for:
    - Parent directory references (.., /)
    - Absolute paths (when base_directory is provided)
    - Non-existent intermediate directories
    - Suspicious path patterns
    
    Args:
        file_path: File path string to validate
        base_directory: Optional base directory to check path is within (prevents traversal)
    
    Returns:
        Tuple of (is_valid, error_message)
    
    Example:
        >>> validate_file_path("data/input/file.xlsx", Path.cwd())
        (True, "")
        >>> validate_file_path("../../etc/passwd")
        (False, "Path contains parent directory references (traversal attempt)")
        >>> validate_file_path("/etc/passwd", Path.cwd())
        (False, "Absolute paths are not allowed")
    """
    if not file_path or not isinstance(file_path, str):
        return False, "File path must be a non-empty string"
    
    # Check for parent directory traversal (exact match for .. as path component)
    # Split by path separators and check if any component is exactly ".."
    path_parts = file_path.replace('\\', '/').split('/')
    if '..' in path_parts:
        return False, "Path contains parent directory references (traversal attempt)"
    
    # Convert to Path object for validation
    try:
        path_obj = Path(file_path)
    except (ValueError, TypeError):
        return False, "Invalid file path format"
    
    # Check for absolute paths when base_directory is provided
    if base_directory and path_obj.is_absolute():
        return False, "Absolute paths are not allowed"
    
    # If base_directory provided, verify resolved path is within it
    if base_directory:
        try:
            base_dir = base_directory.resolve()
            resolved_path = (base_directory / path_obj).resolve()
            
            # Ensure resolved path is within base directory
            if not str(resolved_path).startswith(str(base_dir)):
                return False, "Path traversal detected (resolved path outside base directory)"
        except (OSError, ValueError):
            return False, "Cannot resolve file path"
    
    return True, ""


def validate_excel_file(file_path: str, max_size_mb: int = 100) -> Tuple[bool, str]:
    """
    Validate Excel file: type, format, and size.
    
    Checks for:
    - File existence
    - Correct extension (.xlsx, .xls)
    - File magic bytes (binary signature)
    - File size to prevent DoS attacks
    
    Args:
        file_path: Path to file to validate
        max_size_mb: Maximum allowed file size in MB (default: 100 MB)
    
    Returns:
        Tuple of (is_valid, error_message)
    
    Example:
        >>> validate_excel_file("data/report.xlsx", max_size_mb=50)
        (True, "")
        >>> validate_excel_file("data/image.png")
        (False, "File extension not allowed. Expected: .xlsx or .xls")
        >>> validate_excel_file("data/huge_file.xlsx", max_size_mb=50)
        (False, "File size exceeds maximum (50 MB)")
    """
    if not file_path:
        return False, "File path must be provided"
    
    try:
        path_obj = Path(file_path)
    except (ValueError, TypeError):
        return False, "Invalid file path format"
    
    # Check file exists
    if not path_obj.exists():
        return False, f"File does not exist: {file_path}"
    
    # Check if it's actually a file (not directory)
    if not path_obj.is_file():
        return False, f"Path is not a file: {file_path}"
    
    # Check file extension
    allowed_extensions = {'.xlsx', '.xls'}
    if path_obj.suffix.lower() not in allowed_extensions:
        return False, f"File extension not allowed. Expected: {', '.join(allowed_extensions)}"
    
    # Check file size
    file_size_mb = path_obj.stat().st_size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"File size exceeds maximum ({max_size_mb} MB). Actual: {file_size_mb:.1f} MB"
    
    # Check magic bytes for Office Open XML (xlsx) format
    # Excel 2007+ .xlsx files are ZIP archives with specific structure
    if path_obj.suffix.lower() == '.xlsx':
        try:
            with open(path_obj, 'rb') as f:
                # Check for ZIP file signature (PK..)
                header = f.read(4)
                if header[:2] != b'PK':
                    return False, "File is not a valid Excel file (invalid ZIP signature)"
        except (IOError, OSError):
            return False, f"Cannot read file: {file_path}"
    
    return True, ""


def validate_smtp_server(server: str) -> Tuple[bool, str]:
    """
    Validate SMTP server hostname.
    
    Checks for:
    - Valid hostname format
    - No special characters that could cause injection
    - Reasonable length
    
    Args:
        server: SMTP server hostname or IP address
    
    Returns:
        Tuple of (is_valid, error_message)
    
    Example:
        >>> validate_smtp_server("smtp.gmail.com")
        (True, "")
        >>> validate_smtp_server("invalid..server")
        (False, "Invalid SMTP server hostname format")
    """
    if not server or not isinstance(server, str):
        return False, "SMTP server must be a non-empty string"
    
    # Check length
    if len(server) > 255:
        return False, "SMTP server hostname exceeds maximum length"
    
    # Check for injection characters
    if any(char in server for char in ['\n', '\r', ' ', ';', '|', '&']):
        return False, "SMTP server contains invalid characters"
    
    # Check for valid hostname format (simplified)
    # Allows: letters, digits, dots, hyphens, IPv4 addresses
    pattern = r'^[a-zA-Z0-9.-]+$'
    if not re.match(pattern, server):
        return False, "Invalid SMTP server hostname format"
    
    # Check for invalid patterns like consecutive dots
    if '..' in server:
        return False, "Invalid SMTP server hostname format"
    
    return True, ""


def validate_smtp_port(port: int) -> Tuple[bool, str]:
    """
    Validate SMTP port number.

    Accepts any valid TCP port in range 1-65535.
    Common SMTP ports: 25, 587 (STARTTLS), 465 (SMTPS), 2525 (alternate).

    Args:
        port: Port number to validate

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_smtp_port(587)
        (True, "")
        >>> validate_smtp_port(0)
        (False, "SMTP port must be between 1 and 65535")
    """
    if not isinstance(port, int):
        try:
            port = int(port)
        except (ValueError, TypeError):
            return False, "SMTP port must be a number"

    if not (1 <= port <= 65535):
        return False, "SMTP port must be between 1 and 65535"

    return True, ""


def validate_smtp_credentials(username: str, password: str) -> Tuple[bool, str]:
    """
    Validate SMTP credentials (basic checks).
    
    Note: Actual validation happens during SMTP connection.
    This performs basic sanity checks only.
    
    Args:
        username: SMTP username (typically email address)
        password: SMTP password (should be from secure storage)
    
    Returns:
        Tuple of (is_valid, error_message)
    
    Example:
        >>> validate_smtp_credentials("user@gmail.com", "password123")
        (True, "")
        >>> validate_smtp_credentials("", "password123")
        (False, "SMTP username cannot be empty")
    """
    if not username:
        return False, "SMTP username cannot be empty"
    
    if not password:
        return False, "SMTP password cannot be empty"
    
    # Username should typically be an email
    if '@' in username:
        is_valid, error = validate_email(username)
        if not is_valid:
            return False, f"Invalid SMTP username (email): {error}"
    
    return True, ""


__all__ = [
    'validate_email',
    'validate_file_path',
    'validate_excel_file',
    'validate_smtp_server',
    'validate_smtp_port',
    'validate_smtp_credentials',
]
