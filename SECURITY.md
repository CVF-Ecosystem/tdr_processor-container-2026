# Security Guide for TDR Processor v3.0

**Version:** 3.0.0  
**Last Updated:** December 2025  
**Status:** Production-Ready

---

## Table of Contents

1. [Security Overview](#security-overview)
2. [Credential Management](#credential-management)
3. [Input Validation](#input-validation)
4. [File Security](#file-security)
5. [Configuration Security](#configuration-security)
6. [Logging & Error Handling](#logging--error-handling)
7. [Security Best Practices](#security-best-practices)
8. [Vulnerability Reporting](#vulnerability-reporting)
9. [FAQ](#faq)

---

## Security Overview

TDR Processor v3.0 implements comprehensive security hardening to prevent common web and desktop application vulnerabilities:

### Security Features

- ✅ **Credential Protection**: Environment variable-based credential management (no plain text passwords)
- ✅ **Input Validation**: Comprehensive validation for email, file paths, and SMTP parameters
- ✅ **Path Traversal Prevention**: Prevents directory traversal attacks (`../../../etc/passwd`)
- ✅ **Email Injection Prevention**: Prevents CRLF injection and BCC/CC header manipulation
- ✅ **File Type Validation**: Ensures only Excel files (.xlsx/.xls) are processed
- ✅ **File Size Limits**: Prevents DoS attacks from extremely large files
- ✅ **Error Sanitization**: Error messages never expose sensitive information
- ✅ **Secure Logging**: Credentials and sensitive data never logged
- ✅ **OWASP Compliance**: Addresses OWASP Top 10 vulnerabilities

### Vulnerability Coverage

| OWASP | Vulnerability | Mitigation |
|-------|---|---|
| A01:2021 | Broken Access Control | Path traversal validation, file access control |
| A02:2021 | Cryptographic Failures | Environment variable credentials, secure connections |
| A04:2021 | Insecure Design | Input validation layer, secure defaults |

---

## Credential Management

### ⚠️ CRITICAL: Never Store Passwords in Code or Config Files

Credentials should ALWAYS be loaded from environment variables.

### Setup Instructions

#### Windows (Command Prompt)
```cmd
set TDR_SMTP_USER=your-email@gmail.com
set TDR_SMTP_PASS=your-app-password
python main.py
```

#### Windows (PowerShell)
```powershell
$env:TDR_SMTP_USER="your-email@gmail.com"
$env:TDR_SMTP_PASS="your-app-password"
python main.py
```

#### Linux/macOS (Bash/Zsh)
```bash
export TDR_SMTP_USER="your-email@gmail.com"
export TDR_SMTP_PASS="your-app-password"
python main.py
```

#### Windows (Batch File)
Create `run_tdr.bat`:
```batch
@echo off
setlocal
set TDR_SMTP_USER=your-email@gmail.com
set TDR_SMTP_PASS=your-app-password
python main.py
pause
```

#### Docker/Container Environment
```dockerfile
ENV TDR_SMTP_USER=your-email@gmail.com
ENV TDR_SMTP_PASS=your-app-password
```

#### Systemd Service
Create `/etc/systemd/system/tdr-processor.service`:
```ini
[Service]
Type=simple
User=tdr
WorkingDirectory=/opt/tdr-processor
ExecStart=/usr/bin/python main.py
Environment="TDR_SMTP_USER=your-email@gmail.com"
Environment="TDR_SMTP_PASS=your-app-password"
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### Gmail Setup (Recommended for Testing)

1. **Enable 2-Factor Authentication**
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Create App Password**
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer"
   - Copy the 16-character password

3. **Configure TDR Processor**
   ```
   TDR_SMTP_USER=your-email@gmail.com
   TDR_SMTP_PASS=xyzw abcd efgh ijkl  (16-character app password, spaces removed)
   ```

4. **SMTP Settings in Application**
   - Server: `smtp.gmail.com`
   - Port: `587` (STARTTLS)
   - User: Your Gmail address

### Office 365 Setup

1. **Requirements**
   - Active Office 365 subscription
   - Optional: Create an app-specific password in Azure AD

2. **Configure TDR Processor**
   ```
   TDR_SMTP_USER=your-email@yourcompany.com
   TDR_SMTP_PASS=your-office-password
   ```

3. **SMTP Settings in Application**
   - Server: `smtp.office365.com`
   - Port: `587` (STARTTLS)
   - User: Your Office 365 email address

### Custom SMTP Server

1. **Get Configuration from Your Email Provider**
   - SMTP Server hostname
   - Port (typically 25, 587, or 465)
   - Authentication method (STARTTLS, SMTPS, plain)

2. **Configure TDR Processor**
   ```
   TDR_SMTP_USER=your-username
   TDR_SMTP_PASS=your-password
   ```

3. **SMTP Settings in Application**
   - Enter server hostname and port from your provider

---

## Input Validation

All user inputs are validated before processing to prevent injection and DoS attacks.

### Email Validation

**What is validated:**
- Email format (RFC 5322 compliance)
- Maximum length (254 characters)
- Injection characters (CRLF, newlines)

**Examples:**
```python
# VALID
validate_email("user@example.com")           # ✅ Valid
validate_email("john.doe+tag@example.co.uk") # ✅ Valid with subdomain

# INVALID
validate_email("invalid.email")               # ❌ No @ symbol
validate_email("user@")                       # ❌ No domain
validate_email("user@example.com\nBCC: x")   # ❌ CRLF injection
validate_email("a" * 300 + "@example.com")   # ❌ Too long
```

### File Path Validation

**What is validated:**
- Parent directory references (`..`)
- Absolute path access (when base directory specified)
- Path resolution within allowed directory

**Examples:**
```python
# VALID
validate_file_path("data/input/file.xlsx")   # ✅ Relative path
validate_file_path("file.xlsx")               # ✅ Simple filename

# INVALID - Path Traversal Attempts
validate_file_path("../../etc/passwd")        # ❌ Parent directory reference
validate_file_path("../../../sensitive.xlsx") # ❌ Multiple level traversal
validate_file_path("/etc/passwd")             # ❌ Absolute path (with base_dir)
validate_file_path("data/../../../etc/passwd")# ❌ Hidden traversal
```

### File Type Validation

**What is validated:**
- File extension (.xlsx or .xls only)
- File existence and readability
- File size (default: max 100 MB)
- ZIP file signature (for .xlsx format)

**Examples:**
```python
# VALID
validate_excel_file("data/report.xlsx")      # ✅ Valid Excel file
validate_excel_file("data/report.xls")       # ✅ Valid Excel file

# INVALID
validate_excel_file("data/image.png")        # ❌ Wrong extension
validate_excel_file("data/script.exe")       # ❌ Executable file
validate_excel_file("nonexistent.xlsx")      # ❌ File doesn't exist
validate_excel_file("huge_file.xlsx")        # ❌ File too large (>100MB)
```

### SMTP Parameter Validation

**What is validated:**
- Server hostname format (prevents injection)
- Port number (only 25, 587, 465 allowed)
- Credentials present and non-empty

**Examples:**
```python
# VALID SERVERS
validate_smtp_server("smtp.gmail.com")       # ✅ Valid hostname
validate_smtp_server("192.168.1.1")          # ✅ Valid IP address
validate_smtp_server("mail.company.com")     # ✅ Custom server

# INVALID SERVERS
validate_smtp_server("smtp..gmail.com")      # ❌ Consecutive dots
validate_smtp_server("smtp.gmail.com\nADD")  # ❌ Injection attempt

# VALID PORTS
validate_smtp_port(25)                       # ✅ Standard SMTP
validate_smtp_port(587)                      # ✅ STARTTLS (recommended)
validate_smtp_port(465)                      # ✅ SMTPS

# INVALID PORTS
validate_smtp_port(80)                       # ❌ HTTP port
validate_smtp_port(8080)                     # ❌ Web server port
```

---

## File Security

### Excel File Processing

All Excel files are validated before processing:

1. **File Path Validation** - Prevents access to files outside intended directory
2. **File Type Validation** - Ensures file is actually an Excel document
3. **File Size Validation** - Prevents processing of extremely large files
4. **File Accessibility** - Checks file is not locked by another process

### Data Directory Structure

```
TDR Processor/
├── data_input/        # Place input files here
├── data_csv/          # Exported CSV files
├── data_excel/        # Exported Excel files
├── outputs/           # Final reports
├── templates/         # Report templates
├── backup/            # Automatic backups
└── logs/              # Application logs
```

### File Access Control

- ✅ Only Excel files (.xlsx, .xls) are accepted
- ✅ Files locked by other processes are skipped with warning
- ✅ Input files are not modified (read-only processing)
- ✅ Output files are created in designated output directory
- ✅ Automatic backups before processing

---

## Configuration Security

### .env File Protection

The `.env` file contains sensitive credentials and should be protected:

**On Linux/macOS:**
```bash
# Set restrictive permissions
chmod 600 .env

# Verify permissions
ls -la .env
# Output should be: -rw------- (owner read/write only)
```

**On Windows:**
```powershell
# Set NTFS permissions to deny all except owner
icacls .env /inheritance:r /grant:r "%username%:F"
```

### Version Control (.gitignore)

Ensure `.env` file is NOT committed to version control:

```
# .gitignore
.env
.env.local
.env.*.local
*.log
__pycache__/
.pytest_cache/
build/
dist/
*.egg-info/
```

### Configuration Hierarchy

Configuration is loaded in this order (later overrides earlier):

1. **Hardcoded defaults** (in code)
2. **Configuration file** (app_settings.json)
3. **Environment variables** (TDR_* variables)
4. **User input** (UI dialogs)

**Security Note:** Credentials should ONLY be in environment variables, never in any file.

---

## Logging & Error Handling

### What Gets Logged

**SAFE to log:**
- Operation names and status
- File names (not full paths)
- Timestamps
- Success/failure indicators

**NEVER logged:**
- Passwords or credentials
- Email addresses (when not necessary)
- Full file paths (only filenames)
- Exception stack traces
- Exception details (exception type only)

### Example Logs

```
✅ GOOD
[INFO] Email notification sent successfully
[WARNING] File locked: report.xlsx
[ERROR] File validation failed: File does not exist

❌ BAD
[ERROR] SMTP authentication failed for user@gmail.com with password xyz123
[ERROR] Exception: login(user@gmail.com, password) - smtplib.SMTPAuthenticationError
[ERROR] Full traceback: ... (contains sensitive data)
```

### Error Messages for Users

- Generic messages (don't reveal implementation details)
- Actionable guidance when possible
- No technical details that could aid attackers

**Examples:**
```
✅ User-friendly
- "Email delivery failed: Authentication error"
- "File validation failed: Invalid file format"
- "Cannot access file: Permission denied"

❌ Too technical
- "SMTP login failed: Invalid credentials for user@gmail.com"
- "File contains non-ZIP data at offset 0x00"
- "Path traversal detected: /etc/passwd is outside base directory"
```

---

## Security Best Practices

### For Users

1. **Credential Management**
   - ✅ Use app-specific passwords (not account password)
   - ✅ Store credentials in environment variables only
   - ✅ Rotate credentials regularly
   - ✅ Never share .env file
   - ❌ Don't hardcode passwords in config files
   - ❌ Don't commit credentials to version control

2. **File Handling**
   - ✅ Keep input files in designated `data_input/` directory
   - ✅ Regularly backup your data
   - ✅ Monitor output files for accuracy
   - ✅ Close Excel files before processing
   - ❌ Don't process files from untrusted sources
   - ❌ Don't modify input files while processing

3. **System Security**
   - ✅ Keep Python and libraries updated
   - ✅ Use strong system passwords
   - ✅ Enable antivirus/malware protection
   - ✅ Monitor logs regularly
   - ❌ Don't run as administrator unless necessary
   - ❌ Don't disable security warnings

4. **Access Control**
   - ✅ Restrict access to application directory
   - ✅ Use appropriate file permissions
   - ✅ Limit user accounts with access
   - ✅ Use separate accounts for production
   - ❌ Don't share login credentials
   - ❌ Don't give unnecessary permissions

### For Developers

1. **Code Review**
   - ✅ Review all credential handling code
   - ✅ Check for hardcoded passwords
   - ✅ Verify input validation is applied
   - ✅ Ensure error messages don't leak info
   - ✅ Test with malicious inputs

2. **Testing**
   - ✅ Write security tests (36+ security tests included)
   - ✅ Test path traversal attempts
   - ✅ Test injection attacks
   - ✅ Test with invalid/oversized files
   - ✅ Run penetration tests

3. **Dependency Management**
   - ✅ Keep dependencies updated
   - ✅ Monitor for security vulnerabilities
   - ✅ Use dependency scanners (pip-audit, safety)
   - ✅ Review new dependencies before adding
   - ❌ Don't use deprecated libraries
   - ❌ Don't add unnecessary dependencies

4. **Deployment**
   - ✅ Use environment variables for credentials
   - ✅ Set appropriate file permissions
   - ✅ Enable logging and monitoring
   - ✅ Keep systems patched
   - ✅ Have incident response plan
   - ❌ Don't expose credentials in CI/CD logs
   - ❌ Don't commit sensitive files

---

## Vulnerability Reporting

### Security Issues Found?

If you discover a security vulnerability, please report it responsibly:

1. **DO NOT** post it publicly or in issues
2. **Contact** the development team via private channel
3. **Include** detailed reproduction steps
4. **Wait** for confirmation and fix
5. **Coordinate** on disclosure timeline

### What to Include in Report

- Vulnerability description
- Affected version(s)
- Step-by-step reproduction
- Proof-of-concept code (if safe)
- Potential impact
- Suggested remediation
- Your contact information (if you want credit)

### Security Update Process

1. **Acknowledgment** - Team responds within 48 hours
2. **Assessment** - Severity and impact determined
3. **Development** - Fix developed in secure branch
4. **Testing** - Security tests verify fix
5. **Release** - Patched version released
6. **Announcement** - CVE and advisory issued
7. **Follow-up** - Coordinate with reporters

---

## FAQ

### Q: Should I use my real Gmail password?

**A:** No! Use an App Password instead:
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer"
3. Generate a 16-character password
4. Use that in TDR_SMTP_PASS

### Q: Is .env file committed to version control?

**A:** No! It's in .gitignore. Always:
- Create your own .env from .env.example
- Keep .env local only
- Never commit to repository

### Q: What if I don't want to use email notifications?

**A:** Just leave TDR_SMTP_USER and TDR_SMTP_PASS unset:
- Email sending will be skipped
- No error messages
- Application runs normally

### Q: Can I use the app without internet?

**A:** Yes! Email notifications require internet, but core functionality works offline:
- ✅ File processing works offline
- ✅ Report generation works offline
- ❌ Email sending requires internet

### Q: How often should I rotate credentials?

**A:** Recommended schedule:
- Production: Every 90 days
- Development/Testing: As needed
- After staff changes: Immediately
- After suspected compromise: Immediately

### Q: What if credentials are compromised?

**A:** Immediately:
1. Change password in email provider
2. Reset app-specific password if using Gmail
3. Update TDR_SMTP_PASS environment variable
4. Check logs for unauthorized access
5. Review recent emails from suspicious sources

### Q: How are files validated?

**A:** Three-layer validation:
1. **Path validation** - Check for traversal attacks
2. **Type validation** - Verify Excel format
3. **Content validation** - Check file integrity

### Q: Can I increase the 100 MB file size limit?

**A:** Yes, modify this code in utils/input_validator.py:
```python
is_valid, error = validate_excel_file(file_path, max_size_mb=200)  # 200 MB limit
```

### Q: Where are logs stored?

**A:** Logs stored in project directory:
- `tdr_processor.log` - Main application log
- Check application UI for log messages

### Q: How do I enable debug logging?

**A:** Set environment variable:
```bash
# Or in Windows:
set TDR_LOG_LEVEL=DEBUG
```

### Q: Is there a GUI for credential setup?

**A:** Partially - SMTP settings in UI, but credentials must be from environment for security.

---

## References

- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [OWASP Credential Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Credential_Storage_Cheat_Sheet.html)
- [OWASP Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal)
- [OWASP Email Injection](https://owasp.org/www-community/attacks/Email_Injection)
- [CWE-22: Path Traversal](https://cwe.mitre.org/data/definitions/22.html)
- [CWE-200: Information Exposure](https://cwe.mitre.org/data/definitions/200.html)

---

**For more information, see:**
- [PHASE_3_SECURITY_AUDIT_REPORT.md](PHASE_3_SECURITY_AUDIT_REPORT.md) - Security audit findings
- [PHASE_3_IMPLEMENTATION_REPORT.md](PHASE_3_IMPLEMENTATION_REPORT.md) - Implementation details
- [utils/input_validator.py](utils/input_validator.py) - Validation functions source code

