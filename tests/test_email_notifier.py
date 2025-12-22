import pytest
from utils.email_notifier import send_notification_email

# Test gửi email với cấu hình sai (nên trả về False, không raise exception)
# SECURITY: Email notifier now returns False instead of raising exceptions
# for better error handling in background/scheduled operations
def test_send_notification_email_invalid_config():
    # Invalid SMTP server should return False without raising exception
    result = send_notification_email(
        smtp_server="invalid..server",  # Invalid format (consecutive dots)
        smtp_port=587,
        smtp_user="invalid@example.com",
        smtp_pass="wrongpass",
        recipient_email="recipient@example.com",
        subject="Test",
        body="Test body"
    )
    assert result is False  # Should return False for invalid config

# Test email validation
def test_send_notification_email_invalid_recipient():
    # Invalid recipient email should return False
    result = send_notification_email(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        smtp_user="valid@gmail.com",
        smtp_pass="password",
        recipient_email="invalid.email.no.at",  # Invalid email format
        subject="Test",
        body="Test body"
    )
    assert result is False  # Should return False for invalid recipient
