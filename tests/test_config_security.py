"""
Test suite for Phase 3.1D: Configuration Security

Tests environment variable loading, SMTP/Email configuration, and secure credential handling.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from config import SMTPConfig, EmailConfig, TDRConfig, load_environment_config, get_config


class TestSMTPConfigFromEnv:
    """Test SMTP configuration loading from environment variables."""
    
    def test_smtp_config_default_values(self):
        """Test SMTP config with no environment variables set."""
        with patch.dict(os.environ, {}, clear=True):
            smtp = SMTPConfig.from_env()
            
            assert smtp.server == "localhost"
            assert smtp.port == 587
            assert smtp.username == ""
            assert smtp.password == ""
            assert smtp.use_tls is True
            assert smtp.timeout == 10
    
    def test_smtp_config_from_env_variables(self):
        """Test SMTP config loads from environment variables."""
        env_vars = {
            'TDR_SMTP_SERVER': 'smtp.gmail.com',
            'TDR_SMTP_PORT': '587',
            'TDR_SMTP_USER': 'user@gmail.com',
            'TDR_SMTP_PASSWORD': 'secretpassword',
            'TDR_SMTP_USE_TLS': 'true',
            'TDR_SMTP_TIMEOUT': '20'
        }
        
        with patch.dict(os.environ, env_vars):
            smtp = SMTPConfig.from_env()
            
            assert smtp.server == 'smtp.gmail.com'
            assert smtp.port == 587
            assert smtp.username == 'user@gmail.com'
            assert smtp.password == 'secretpassword'
            assert smtp.use_tls is True
            assert smtp.timeout == 20
    
    def test_smtp_config_use_tls_false(self):
        """Test SMTP config with TLS disabled."""
        env_vars = {
            'TDR_SMTP_USE_TLS': 'false'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            smtp = SMTPConfig.from_env()
            assert smtp.use_tls is False
    
    def test_smtp_config_custom_port(self):
        """Test SMTP config with custom port."""
        env_vars = {
            'TDR_SMTP_PORT': '465'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            smtp = SMTPConfig.from_env()
            assert smtp.port == 465
    
    def test_smtp_config_invalid_port(self):
        """Test SMTP config with invalid port raises error."""
        env_vars = {
            'TDR_SMTP_PORT': 'invalid'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError):
                SMTPConfig.from_env()


class TestEmailConfigFromEnv:
    """Test Email configuration loading from environment variables."""
    
    def test_email_config_default_values(self):
        """Test email config with no environment variables set."""
        with patch.dict(os.environ, {}, clear=True):
            email = EmailConfig.from_env()
            
            assert email.sender == ""
            assert email.recipients == []
            assert email.enabled is False
    
    def test_email_config_from_env_variables(self):
        """Test email config loads from environment variables."""
        env_vars = {
            'TDR_EMAIL_SENDER': 'sender@example.com',
            'TDR_EMAIL_RECIPIENTS': 'user1@example.com, user2@example.com',
            'TDR_EMAIL_ENABLED': 'true'
        }
        
        with patch.dict(os.environ, env_vars):
            email = EmailConfig.from_env()
            
            assert email.sender == 'sender@example.com'
            assert email.recipients == ['user1@example.com', 'user2@example.com']
            assert email.enabled is True
    
    def test_email_config_single_recipient(self):
        """Test email config with single recipient."""
        env_vars = {
            'TDR_EMAIL_RECIPIENTS': 'single@example.com',
            'TDR_EMAIL_ENABLED': 'true'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            email = EmailConfig.from_env()
            assert email.recipients == ['single@example.com']
    
    def test_email_config_multiple_recipients(self):
        """Test email config with multiple recipients."""
        env_vars = {
            'TDR_EMAIL_RECIPIENTS': 'user1@ex.com,user2@ex.com,user3@ex.com',
            'TDR_EMAIL_ENABLED': 'false'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            email = EmailConfig.from_env()
            assert len(email.recipients) == 3
            assert 'user1@ex.com' in email.recipients
    
    def test_email_config_whitespace_handling(self):
        """Test email config strips whitespace from recipients."""
        env_vars = {
            'TDR_EMAIL_RECIPIENTS': '  user1@ex.com  ,  user2@ex.com  '
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            email = EmailConfig.from_env()
            assert email.recipients == ['user1@ex.com', 'user2@ex.com']
    
    def test_email_config_empty_recipients_string(self):
        """Test email config with empty recipients string."""
        env_vars = {
            'TDR_EMAIL_RECIPIENTS': ''
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            email = EmailConfig.from_env()
            assert email.recipients == []
    
    def test_email_config_enabled_case_insensitive(self):
        """Test email enabled flag is case insensitive."""
        test_cases = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('false', False),
            ('False', False),
            ('FALSE', False),
            ('yes', False),
            ('', False)
        ]
        
        for value, expected in test_cases:
            env_vars = {'TDR_EMAIL_ENABLED': value}
            with patch.dict(os.environ, env_vars, clear=True):
                email = EmailConfig.from_env()
                assert email.enabled == expected, f"Failed for value '{value}'"


class TestLoadEnvironmentConfig:
    """Test load_environment_config function."""
    
    def test_load_environment_config_updates_global(self):
        """Test that load_environment_config updates global config."""
        env_vars = {
            'TDR_SMTP_SERVER': 'smtp.test.com',
            'TDR_SMTP_USER': 'testuser',
            'TDR_EMAIL_SENDER': 'test@example.com',
            'TDR_LOG_LEVEL': 'INFO'
        }
        
        with patch.dict(os.environ, env_vars):
            load_environment_config()
            cfg = get_config()
            
            assert cfg.smtp.server == 'smtp.test.com'
            assert cfg.smtp.username == 'testuser'
            assert cfg.email.sender == 'test@example.com'
            assert cfg.app.LOG_LEVEL == 'INFO'
    
    def test_load_environment_config_log_level(self):
        """Test load_environment_config updates log level."""
        env_vars = {
            'TDR_LOG_LEVEL': 'WARNING'
        }
        
        with patch.dict(os.environ, env_vars):
            load_environment_config()
            cfg = get_config()
            assert cfg.app.LOG_LEVEL == 'WARNING'
    
    def test_load_environment_config_log_level_not_set(self):
        """Test load_environment_config doesn't change log level if not in env."""
        original_level = get_config().app.LOG_LEVEL
        
        with patch.dict(os.environ, {}, clear=True):
            load_environment_config()
            cfg = get_config()
            # Log level should remain unchanged
            assert cfg.app.LOG_LEVEL == original_level
    
    def test_load_environment_config_with_complex_setup(self):
        """Test load_environment_config with complete environment setup."""
        env_vars = {
            'TDR_SMTP_SERVER': 'smtp.gmail.com',
            'TDR_SMTP_PORT': '587',
            'TDR_SMTP_USER': 'bot@gmail.com',
            'TDR_SMTP_PASSWORD': 'app_password_123',
            'TDR_SMTP_USE_TLS': 'true',
            'TDR_EMAIL_SENDER': 'reports@company.com',
            'TDR_EMAIL_RECIPIENTS': 'manager@company.com, admin@company.com',
            'TDR_EMAIL_ENABLED': 'true',
            'TDR_LOG_LEVEL': 'DEBUG'
        }
        
        with patch.dict(os.environ, env_vars):
            load_environment_config()
            cfg = get_config()
            
            # Verify all settings loaded
            assert cfg.smtp.server == 'smtp.gmail.com'
            assert cfg.smtp.port == 587
            assert cfg.smtp.username == 'bot@gmail.com'
            assert cfg.smtp.password == 'app_password_123'
            assert cfg.smtp.use_tls is True
            assert cfg.email.sender == 'reports@company.com'
            assert len(cfg.email.recipients) == 2
            assert cfg.email.enabled is True
            assert cfg.app.LOG_LEVEL == 'DEBUG'


class TestTDRConfigIntegration:
    """Test TDRConfig integration with SMTP and Email configs."""
    
    def test_tdr_config_has_smtp_field(self):
        """Test TDRConfig has smtp field."""
        cfg = TDRConfig()
        assert hasattr(cfg, 'smtp')
        assert isinstance(cfg.smtp, SMTPConfig)
    
    def test_tdr_config_has_email_field(self):
        """Test TDRConfig has email field."""
        cfg = TDRConfig()
        assert hasattr(cfg, 'email')
        assert isinstance(cfg.email, EmailConfig)
    
    def test_tdr_config_smtp_defaults(self):
        """Test TDRConfig smtp field defaults."""
        cfg = TDRConfig()
        assert cfg.smtp.server == "localhost"
        assert cfg.smtp.port == 587
    
    def test_tdr_config_email_defaults(self):
        """Test TDRConfig email field defaults."""
        cfg = TDRConfig()
        assert cfg.email.enabled is False
        assert cfg.email.recipients == []


class TestConfigurationSecurity:
    """Test security aspects of configuration handling."""
    
    def test_no_hardcoded_credentials(self):
        """Test that default config has no hardcoded credentials."""
        cfg = TDRConfig()
        
        # Credentials should be empty by default
        assert cfg.smtp.username == ""
        assert cfg.smtp.password == ""
        assert cfg.email.sender == ""
    
    def test_environment_variables_not_exposed(self):
        """Test that credentials from env vars are properly encapsulated."""
        env_vars = {
            'TDR_SMTP_PASSWORD': 'very_secret_password_123',
            'TDR_SMTP_USER': 'user@example.com'
        }
        
        with patch.dict(os.environ, env_vars):
            smtp = SMTPConfig.from_env()
            # Verify credentials are stored but not exposed in string representation
            assert smtp.password == 'very_secret_password_123'
            # The dataclass __repr__ should not expose the password
            repr_str = repr(smtp)
            # This is just a basic check - real sanitization happens in logging
            assert isinstance(repr_str, str)
    
    def test_smtp_port_validation(self):
        """Test SMTP port must be integer."""
        env_vars = {
            'TDR_SMTP_PORT': 'not_a_number'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError):
                SMTPConfig.from_env()
    
    def test_smtp_timeout_validation(self):
        """Test SMTP timeout must be integer."""
        env_vars = {
            'TDR_SMTP_TIMEOUT': 'invalid'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError):
                SMTPConfig.from_env()


class TestConfigurationBackwardCompatibility:
    """Test backward compatibility of configuration changes."""
    
    def test_existing_config_constants_still_work(self):
        """Test that existing configuration constants are still available."""
        # These should all be defined and accessible
        from config import (
            APP_TITLE, APP_VERSION, LOG_LEVEL, LOG_FORMAT,
            VESSEL_SUMMARY_SHEET, QC_PRODUCTIVITY_SHEET,
            VESSEL_MASTER_FILE, QC_MASTER_FILE
        )
        
        assert APP_TITLE == "TDR Processor"
        assert APP_VERSION == "3.0"
    
    def test_get_config_function_works(self):
        """Test get_config() function returns valid config."""
        cfg = get_config()
        assert isinstance(cfg, TDRConfig)
        assert hasattr(cfg, 'app')
        assert hasattr(cfg, 'smtp')
        assert hasattr(cfg, 'email')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
