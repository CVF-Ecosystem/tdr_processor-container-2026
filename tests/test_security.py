# tests/test_security.py
"""
Security test cases for TDR Processor Phase 3.

Tests for:
- Input validation (email, file paths, SMTP parameters)
- Path traversal prevention
- Email injection prevention
- File type validation
- Credential handling
"""

import pytest
from pathlib import Path
from utils.input_validator import (
    validate_email, validate_file_path, validate_excel_file,
    validate_smtp_server, validate_smtp_port, validate_smtp_credentials
)


class TestEmailValidation:
    """Test email address validation"""
    
    def test_valid_email(self):
        """Valid email addresses should pass"""
        is_valid, error = validate_email("user@example.com")
        assert is_valid is True
        assert error == ""
    
    def test_valid_email_complex(self):
        """Valid email with complex format"""
        is_valid, error = validate_email("john.doe+tag@example.co.uk")
        assert is_valid is True
        assert error == ""
    
    def test_invalid_email_no_at(self):
        """Email without @ should fail"""
        is_valid, error = validate_email("userexample.com")
        assert is_valid is False
        assert "Invalid email format" in error
    
    def test_invalid_email_no_domain(self):
        """Email without domain should fail"""
        is_valid, error = validate_email("user@")
        assert is_valid is False
        assert "Invalid email format" in error
    
    def test_email_injection_crlf(self):
        """CRLF injection in email should be blocked"""
        is_valid, error = validate_email("user@example.com\nBCC: attacker@evil.com")
        assert is_valid is False
        assert "injection attempt" in error.lower()
    
    def test_email_injection_newline(self):
        """Newline injection should be blocked"""
        is_valid, error = validate_email("user@example.com\nCC: attacker@evil.com")
        assert is_valid is False
        assert "invalid characters" in error.lower()
    
    def test_email_too_long(self):
        """Extremely long email should be rejected"""
        long_email = "a" * 300 + "@example.com"
        is_valid, error = validate_email(long_email)
        assert is_valid is False
        assert "exceeds maximum length" in error.lower()
    
    def test_empty_email(self):
        """Empty email should fail"""
        is_valid, error = validate_email("")
        assert is_valid is False
        assert "non-empty" in error.lower()


class TestFilePathValidation:
    """Test file path validation to prevent traversal attacks"""
    
    def test_valid_relative_path(self):
        """Valid relative path should pass"""
        is_valid, error = validate_file_path("data/input/file.xlsx")
        assert is_valid is True
        assert error == ""
    
    def test_path_traversal_parent_ref(self):
        """Path traversal attempt with .. should be blocked"""
        is_valid, error = validate_file_path("../../etc/passwd")
        assert is_valid is False
        assert "parent directory" in error.lower()
    
    def test_path_traversal_multiple_levels(self):
        """Multiple levels of traversal should be blocked"""
        is_valid, error = validate_file_path("../../../sensitive.xlsx")
        assert is_valid is False
        assert "parent directory" in error.lower()
    
    def test_absolute_path_blocked(self):
        """Absolute paths should be blocked when base_directory provided"""
        is_valid, error = validate_file_path("/etc/passwd", base_directory=Path.cwd())
        assert is_valid is False
        # Can be either "Absolute paths" or "Path traversal detected"
        assert ("Absolute paths" in error or "Path traversal" in error)
    
    def test_path_with_dot_dot_variant(self):
        """Encoded or variant parent directory references should be blocked"""
        is_valid, error = validate_file_path("data/../../../etc/passwd")
        assert is_valid is False
        assert "parent directory" in error.lower()
    
    def test_empty_path(self):
        """Empty path should fail"""
        is_valid, error = validate_file_path("")
        assert is_valid is False
        assert "non-empty" in error.lower()


class TestExcelFileValidation:
    """Test Excel file validation"""
    
    def test_invalid_extension_txt(self, tmp_path):
        """TXT file should be rejected"""
        # Create a temporary .txt file
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Some text content")
        
        is_valid, error = validate_excel_file(str(txt_file))
        assert is_valid is False
        assert "extension not allowed" in error.lower()
    
    def test_invalid_extension_exe(self, tmp_path):
        """Executable file should be rejected"""
        # Create a temporary .exe file
        exe_file = tmp_path / "test.exe"
        exe_file.write_bytes(b"fake exe content")
        
        is_valid, error = validate_excel_file(str(exe_file))
        assert is_valid is False
        assert "extension not allowed" in error.lower()
    
    def test_nonexistent_file(self):
        """Non-existent file should be rejected"""
        is_valid, error = validate_excel_file("nonexistent_file_12345.xlsx")
        assert is_valid is False
        assert "does not exist" in error.lower()
    
    def test_empty_file_path(self):
        """Empty file path should be rejected"""
        is_valid, error = validate_excel_file("")
        assert is_valid is False
        assert "must be provided" in error.lower()
    
    def test_xlsx_extension_case_insensitive(self, tmp_path):
        """XLSX extension should work in uppercase"""
        # Create a temporary .XLSX file
        xlsx_file = tmp_path / "test.XLSX"
        xlsx_file.write_bytes(b"PK\x03\x04")  # ZIP file header
        
        is_valid, error = validate_excel_file(str(xlsx_file))
        # Should pass extension check
        assert "extension not allowed" not in error.lower()


class TestSMTPValidation:
    """Test SMTP parameter validation"""
    
    def test_valid_smtp_server(self):
        """Valid SMTP server should pass"""
        is_valid, error = validate_smtp_server("smtp.gmail.com")
        assert is_valid is True
        assert error == ""
    
    def test_valid_smtp_server_ip(self):
        """Valid SMTP server with IP should pass"""
        is_valid, error = validate_smtp_server("192.168.1.1")
        assert is_valid is True
        assert error == ""
    
    def test_invalid_smtp_server_consecutive_dots(self):
        """SMTP server with consecutive dots should fail"""
        is_valid, error = validate_smtp_server("smtp..gmail.com")
        assert is_valid is False
        assert "Invalid" in error
    
    def test_invalid_smtp_server_spaces(self):
        """SMTP server with spaces should fail"""
        is_valid, error = validate_smtp_server("smtp. gmail.com")
        assert is_valid is False
        assert "invalid characters" in error.lower()
    
    def test_invalid_smtp_server_injection(self):
        """SMTP server with newline injection should fail"""
        is_valid, error = validate_smtp_server("smtp.gmail.com\nADD HEADER")
        assert is_valid is False
        assert "invalid characters" in error.lower()
    
    def test_valid_smtp_port_587(self):
        """SMTP port 587 (STARTTLS) should be valid"""
        is_valid, error = validate_smtp_port(587)
        assert is_valid is True
        assert error == ""
    
    def test_valid_smtp_port_465(self):
        """SMTP port 465 (SMTPS) should be valid"""
        is_valid, error = validate_smtp_port(465)
        assert is_valid is True
        assert error == ""
    
    def test_valid_smtp_port_25(self):
        """SMTP port 25 should be valid"""
        is_valid, error = validate_smtp_port(25)
        assert is_valid is True
        assert error == ""
    
    def test_invalid_smtp_port_80(self):
        """Port 80 should not be valid for SMTP"""
        is_valid, error = validate_smtp_port(80)
        assert is_valid is False
        assert "Invalid SMTP port" in error
    
    def test_invalid_smtp_port_string(self):
        """String port number should be converted or fail"""
        is_valid, error = validate_smtp_port("587")
        # Should either convert or fail gracefully
        assert is_valid is True  # Conversion should work
    
    def test_invalid_smtp_port_non_numeric(self):
        """Non-numeric port should fail"""
        is_valid, error = validate_smtp_port("abc")
        assert is_valid is False
        assert "must be a number" in error.lower()


class TestSMTPCredentialsValidation:
    """Test SMTP credentials validation"""
    
    def test_valid_credentials(self):
        """Valid username and password should pass"""
        is_valid, error = validate_smtp_credentials("user@gmail.com", "password123")
        assert is_valid is True
        assert error == ""
    
    def test_missing_username(self):
        """Missing username should fail"""
        is_valid, error = validate_smtp_credentials("", "password123")
        assert is_valid is False
        assert "username cannot be empty" in error.lower()
    
    def test_missing_password(self):
        """Missing password should fail"""
        is_valid, error = validate_smtp_credentials("user@gmail.com", "")
        assert is_valid is False
        assert "password cannot be empty" in error.lower()
    
    def test_both_missing(self):
        """Both missing should fail"""
        is_valid, error = validate_smtp_credentials("", "")
        assert is_valid is False
        assert "username cannot be empty" in error.lower()


class TestSecurityIntegration:
    """Integration tests for security measures"""
    
    def test_path_traversal_prevention(self):
        """Comprehensive path traversal prevention"""
        dangerous_paths = [
            "../../data/sensitive.xlsx",
            "../../../etc/passwd",
            "data/../../../etc/passwd",
            "/etc/passwd",
            "\\windows\\system32\\config",
        ]
        for path in dangerous_paths:
            is_valid, error = validate_file_path(path, base_directory=Path.cwd())
            assert is_valid is False, f"Path traversal not blocked: {path}"
    
    def test_email_injection_prevention(self):
        """Comprehensive email injection prevention"""
        dangerous_emails = [
            "user@example.com\nBCC: attacker@evil.com",
            "user@example.com\nCC: attacker@evil.com",
            "user@example.com\rCC: attacker@evil.com",
            "user@example.com\r\nCC: attacker@evil.com",
        ]
        for email in dangerous_emails:
            is_valid, error = validate_email(email)
            assert is_valid is False, f"Email injection not blocked: {email}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
