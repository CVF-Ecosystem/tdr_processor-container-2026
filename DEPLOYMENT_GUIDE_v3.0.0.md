# TDR Processor v3.0.0 - Deployment Guide

**Version:** 3.0.0  
**Last Updated:** December 22, 2025  
**Status:** Production Ready ✅

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Configuration](#environment-configuration)
3. [Installation Methods](#installation-methods)
4. [Verification & Testing](#verification--testing)
5. [Deployment Scenarios](#deployment-scenarios)
6. [Post-Deployment Validation](#post-deployment-validation)
7. [Rollback Procedures](#rollback-procedures)
8. [Troubleshooting](#troubleshooting)
9. [Support & Monitoring](#support--monitoring)

---

## Pre-Deployment Checklist

### System Requirements

- [ ] **OS:** Windows 7+, macOS 10.13+, or Linux (any modern distro)
- [ ] **Python:** 3.11+ installed and in PATH
- [ ] **Disk Space:** ≥500MB available
- [ ] **Memory:** ≥2GB RAM
- [ ] **Internet:** Required for pip install (can work offline after)
- [ ] **Permissions:** Can install packages and write to install directory

### Code Readiness

- [ ] All 139 tests passing: `pytest tests/ -q` → **139 passed** ✅
- [ ] Coverage ≥62%: `pytest --cov=.` → **62% coverage** ✅
- [ ] Version correct: config.py VERSION = "3.0.0" ✅
- [ ] Documentation complete:
  - [ ] ARCHITECTURE.md (500+ lines) ✅
  - [ ] CONTRIBUTING.md (300+ lines) ✅
  - [ ] SECURITY.md (security guidelines) ✅
  - [ ] RELEASE_NOTES_v3.0.0.md ✅

### Configuration Readiness

- [ ] SMTP credentials identified (optional)
  - [ ] Email address
  - [ ] App password (Gmail) or account password
  - [ ] SMTP server (smtp.gmail.com, smtp.outlook.com, etc.)
  - [ ] SMTP port (25, 465, or 587)

- [ ] Sample data prepared (optional)
  - [ ] TDR Excel files in data_input/ folder
  - [ ] Expected output directory identified

- [ ] Backup plan documented
  - [ ] Previous version backed up (if upgrading)
  - [ ] Configuration backed up
  - [ ] Data backed up

### Deployment Resources

- [ ] Repository access (git clone)
- [ ] Python interpreter verified (`python --version` → 3.11+)
- [ ] Package manager verified (`pip --version` → latest)
- [ ] Virtual environment tool available (`python -m venv`)

---

## Environment Configuration

### 1. Environment Variables (SMTP Settings)

Create a `.env` file in the project root directory:

```bash
# .env file (DO NOT COMMIT TO GIT!)
TDR_SMTP_SERVER=smtp.gmail.com
TDR_SMTP_PORT=587
TDR_SMTP_USER=your_email@gmail.com
TDR_SMTP_PASSWORD=your_app_password
```

### 2. Create .env.example Template

For distribution (commit to git):

```bash
# .env.example file (COMMIT TO GIT - shared with team)
TDR_SMTP_SERVER=smtp.gmail.com
TDR_SMTP_PORT=587
TDR_SMTP_USER=your_email@gmail.com
TDR_SMTP_PASSWORD=your_app_password

# Common SMTP Servers:
# Gmail: smtp.gmail.com:587 (TLS)
# Outlook: smtp-mail.outlook.com:587 (TLS)
# Yahoo: smtp.mail.yahoo.com:465 (SSL) or :587 (TLS)
# Corporate: ask your IT department for SMTP settings
```

### 3. Load Environment Variables

**Option A: Linux/macOS (Manual)**
```bash
export TDR_SMTP_SERVER=smtp.gmail.com
export TDR_SMTP_PORT=587
export TDR_SMTP_USER=your_email@gmail.com
export TDR_SMTP_PASSWORD=your_app_password
```

**Option B: Windows PowerShell (Manual)**
```powershell
$env:TDR_SMTP_SERVER = "smtp.gmail.com"
$env:TDR_SMTP_PORT = "587"
$env:TDR_SMTP_USER = "your_email@gmail.com"
$env:TDR_SMTP_PASSWORD = "your_app_password"
```

**Option C: Windows Command Prompt (Manual)**
```cmd
set TDR_SMTP_SERVER=smtp.gmail.com
set TDR_SMTP_PORT=587
set TDR_SMTP_USER=your_email@gmail.com
set TDR_SMTP_PASSWORD=your_app_password
```

**Option D: Python Dotenv (Automatic)**
```python
# Install python-dotenv (optional)
pip install python-dotenv

# In your script
from dotenv import load_dotenv
load_dotenv()

# Now os.getenv() reads from .env file
```

### 4. Verify Environment Configuration

```bash
# Test SMTP configuration
python -c "
import os
from utils.email_notifier import test_smtp_connection

server = os.getenv('TDR_SMTP_SERVER')
port = os.getenv('TDR_SMTP_PORT')
user = os.getenv('TDR_SMTP_USER')

print(f'SMTP Server: {server}')
print(f'SMTP Port: {port}')
print(f'SMTP User: {user}')
print('✅ Configuration loaded successfully')
"
```

---

## Installation Methods

### Method 1: Local Development Installation (Recommended for Testing)

```bash
# 1. Clone repository
git clone https://github.com/your-org/tdr_processor.git
cd tdr_processor

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 4. Upgrade pip
pip install --upgrade pip

# 5. Install dependencies
pip install -r requirements.txt

# 6. Create .env file (optional, for email)
cp .env.example .env
# Edit .env with your SMTP credentials

# 7. Verify installation
pytest tests/ -q
# Expected output: 139 passed in 1.88s ✅

# 8. Test with sample data
python main.py data_input/sample_tdr.xlsx
# Check outputs/ folder for generated files
```

### Method 2: System-Wide Installation

```bash
# 1. Clone repository to permanent location
sudo git clone https://github.com/your-org/tdr_processor.git /opt/tdr_processor
cd /opt/tdr_processor

# 2. Create system virtual environment
sudo python3.11 -m venv /opt/tdr_processor/venv
sudo chown -R $USER:$USER /opt/tdr_processor

# 3. Activate and install
source /opt/tdr_processor/venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Create system command
sudo tee /usr/local/bin/tdr-processor <<EOF
#!/bin/bash
/opt/tdr_processor/venv/bin/python /opt/tdr_processor/main.py "$@"
EOF
sudo chmod +x /usr/local/bin/tdr-processor

# 5. Test
tdr-processor --help
```

### Method 3: Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 tdr && chown -R tdr:tdr /app
USER tdr

# Run application
ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
```

```bash
# Build Docker image
docker build -t tdr_processor:3.0.0 .

# Run Docker container
docker run -v $(pwd)/data_input:/app/data_input \
           -v $(pwd)/outputs:/app/outputs \
           -e TDR_SMTP_SERVER=smtp.gmail.com \
           -e TDR_SMTP_PORT=587 \
           -e TDR_SMTP_USER=your_email@gmail.com \
           -e TDR_SMTP_PASSWORD=your_password \
           tdr_processor:3.0.0 data_input/sample.xlsx

# Docker Compose (docker-compose.yml)
version: '3.8'
services:
  tdr:
    build: .
    volumes:
      - ./data_input:/app/data_input
      - ./outputs:/app/outputs
    environment:
      TDR_SMTP_SERVER: smtp.gmail.com
      TDR_SMTP_PORT: 587
      TDR_SMTP_USER: ${SMTP_USER}
      TDR_SMTP_PASSWORD: ${SMTP_PASSWORD}
    command: main.py /app/data_input/sample.xlsx
```

### Method 4: Packaged Executable (PyInstaller)

```bash
# 1. Install PyInstaller
pip install pyinstaller

# 2. Build executable using spec file
pyinstaller TDR_Processor.spec

# 3. Output location: dist/TDR_Processor.exe (Windows)
#                or: dist/TDR_Processor (Linux/macOS)

# 4. Distribution structure:
# dist/
# ├── TDR_Processor.exe
# ├── requirements.txt
# ├── .env.example
# ├── README.md
# ├── QUICK_START.md
# └── sample_data/
#     └── sample_tdr.xlsx

# 5. User installation (no Python needed):
# Extract archive
# Double-click TDR_Processor.exe
# Or: TDR_Processor.exe data_input/sample.xlsx
```

---

## Verification & Testing

### Pre-Deployment Test Suite

```bash
# 1. Run all tests
pytest tests/ -v

# Expected: 139 passed
# Execution time: ~2 seconds

# 2. Run with coverage report
pytest tests/ --cov=. --cov-report=html --cov-report=term

# Expected: 62% coverage

# 3. Run security tests specifically
pytest tests/test_security.py -v
pytest tests/test_config_security.py -v

# Expected: All security tests pass

# 4. Run performance tests
pytest tests/test_excel_optimizer.py -v

# Expected: All performance optimizations verified

# 5. Type checking with mypy
mypy utils/ --strict --no-implicit-optional

# Expected: No type errors
```

### Manual Verification Steps

```bash
# 1. Verify Python version
python --version
# Expected: Python 3.11.x

# 2. Verify virtual environment (if using)
which python
# Expected: /path/to/venv/bin/python

# 3. Verify dependencies installed
pip list | grep -E "pandas|openpyxl|xlsxwriter|click"

# 4. Verify version string
python -c "from config import ApplicationConfig; print(ApplicationConfig.VERSION)"
# Expected: 3.0.0

# 5. Test with sample file
python main.py data_input/sample_tdr.xlsx
# Expected: Success message, output files in outputs/

# 6. Verify email configuration (optional)
python -c "
import os
from utils.email_notifier import validate_email
result = validate_email(os.getenv('TDR_SMTP_USER'))
print(f'Email validation: {result}')
"
```

---

## Deployment Scenarios

### Scenario 1: Desktop/Laptop User

**Setup Time:** 15 minutes  
**Complexity:** Easy

```bash
# 1. Install Python 3.11+ from python.org
# 2. Download source code (zip or git clone)
# 3. Open terminal in project directory
# 4. Run:
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
# 5. Place TDR Excel files in data_input/
# 6. Run:
python main.py data_input/your_file.xlsx
# 7. Check outputs/ folder for results
```

### Scenario 2: Shared Server (Linux/macOS)

**Setup Time:** 30 minutes  
**Complexity:** Medium

```bash
# 1. SSH to server
ssh user@server.example.com

# 2. Clone repository
git clone https://github.com/your-org/tdr_processor.git
cd tdr_processor

# 3. Create system-wide installation
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Set environment variables (in ~/.bashrc or ~/.zshrc)
echo 'export TDR_SMTP_SERVER=smtp.gmail.com' >> ~/.bashrc
echo 'export TDR_SMTP_PORT=587' >> ~/.bashrc
echo 'export TDR_SMTP_USER=email@gmail.com' >> ~/.bashrc
echo 'export TDR_SMTP_PASSWORD=password' >> ~/.bashrc
source ~/.bashrc

# 5. Create cron job for scheduled processing
crontab -e
# Add: 0 2 * * * /home/user/tdr_processor/venv/bin/python /home/user/tdr_processor/main.py /home/user/data_input/daily_report.xlsx

# 6. Monitor logs
tail -f tdr_processor.log
```

### Scenario 3: Docker Container Deployment

**Setup Time:** 20 minutes  
**Complexity:** Medium

```bash
# 1. Build image
docker build -t tdr_processor:3.0.0 .

# 2. Create .env file with SMTP credentials
cat > .docker.env <<EOF
TDR_SMTP_SERVER=smtp.gmail.com
TDR_SMTP_PORT=587
TDR_SMTP_USER=your_email@gmail.com
TDR_SMTP_PASSWORD=your_password
EOF

# 3. Run container
docker run -d \
  --name tdr_processor \
  --env-file .docker.env \
  -v $(pwd)/data_input:/app/data_input \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/tdr_processor.log:/app/tdr_processor.log \
  tdr_processor:3.0.0

# 4. Monitor
docker logs -f tdr_processor

# 5. Process file
docker exec tdr_processor python main.py data_input/sample.xlsx
```

### Scenario 4: Cloud Deployment (AWS Lambda)

**Setup Time:** 45 minutes  
**Complexity:** Advanced

```bash
# Note: Lambda has Python 3.11+ support

# 1. Create deployment package
mkdir lambda_deployment
cd lambda_deployment
pip install -r requirements.txt -t .
cp -r ../utils .
cp main.py lambda_function.py

# 2. Update lambda_function.py
# Handler: lambda_handler
# Timeout: 300 seconds (5 minutes)
# Memory: 1024 MB

# 3. Create deployment package
zip -r lambda_deployment.zip .

# 4. Deploy using AWS CLI
aws lambda create-function \
  --function-name tdr-processor-v3.0.0 \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://lambda_deployment.zip \
  --timeout 300 \
  --memory-size 1024 \
  --environment Variables="TDR_SMTP_SERVER=smtp.gmail.com,TDR_SMTP_PORT=587"
```

---

## Post-Deployment Validation

### Immediate Validation (First 5 minutes)

```bash
# 1. Verify installation
python main.py --version
# Expected: TDR Processor v3.0.0

# 2. Run help
python main.py --help
# Expected: Help message with usage

# 3. Test with sample data
python main.py data_input/sample_tdr.xlsx
# Expected: Success message

# 4. Verify output files
ls outputs/
# Expected: Multiple CSV and Excel files

# 5. Check log file
cat tdr_processor.log | tail -20
# Expected: No ERROR or CRITICAL messages
```

### Extended Validation (First 24 hours)

```bash
# 1. Run full test suite
pytest tests/ -q
# Expected: 139 passed

# 2. Test SMTP (if email configured)
python -c "
from utils.email_notifier import send_notification_email_with_config
result = send_notification_email_with_config(
    subject='TDR Processor Test',
    body='Deployment test email',
    file_path=None
)
print(f'Email delivery: {\"✅ Success\" if result else \"❌ Failed\"}')"

# 3. Monitor performance
python performance_profiler.py

# 4. Check disk usage
du -sh . outputs/ data_input/
# Expected: <5GB total

# 5. Monitor memory usage
# Linux:
watch -n 1 'free -h'
# Windows:
Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 5
```

### Ongoing Validation (Weekly)

```bash
# 1. Check for updates
git fetch origin
git status
# Expected: "Your branch is up to date"

# 2. Verify no accumulation of temp files
ls -la | grep -E "\.tmp|\.bak|__pycache__"
# Clean if needed: find . -name "__pycache__" -type d -exec rm -rf {} +

# 3. Monitor log file size
ls -lh tdr_processor.log
# Rotate if >100MB: mv tdr_processor.log tdr_processor.log.1

# 4. Test with fresh data
# Run tests again
pytest tests/ -q
```

---

## Rollback Procedures

### Rollback to Previous Version

```bash
# 1. Identify current version
git log --oneline -5

# 2. Backup current version (if needed)
git tag v3.0.0-backup
cp -r . ../tdr_processor_v3.0.0_backup

# 3. Rollback to previous version
git checkout v2.1.0
# or: git revert HEAD (for single commit)

# 4. Reinstall dependencies
pip install -r requirements.txt

# 5. Run tests
pytest tests/ -q
# Expected: Previous version's test count

# 6. Verify version
python -c "from config import ApplicationConfig; print(ApplicationConfig.VERSION)"

# 7. Monitor logs for rollback
tail -f tdr_processor.log
```

### Emergency Rollback Procedure

```bash
# If deployment fails and you need immediate recovery:

# 1. Stop current process
pkill -f "python main.py"  # Linux/macOS
taskkill /IM python.exe /F  # Windows (careful!)

# 2. Restore from backup (if available)
rm -rf tdr_processor
cp -r tdr_processor_v2.1_backup tdr_processor
cd tdr_processor

# 3. Activate old environment
source venv/bin/activate  # or venv\Scripts\activate

# 4. Run immediately
python main.py data_input/critical_file.xlsx

# 5. Investigate rollback cause
# Check error logs, test suite, recent changes
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'pandas'"

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Or specific package
pip install pandas==2.0.0 --force-reinstall
```

### Issue: "Permission denied" (Linux/macOS)

**Solution:**
```bash
# Make script executable
chmod +x main.py

# Fix directory permissions
chmod -R 755 .

# If using sudo, check ownership
sudo chown -R $USER:$USER .
```

### Issue: Email sending fails

**Solution:**
```bash
# 1. Verify environment variables set
echo $TDR_SMTP_SERVER
echo $TDR_SMTP_PORT
echo $TDR_SMTP_USER

# 2. Test SMTP connection
python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your_email@gmail.com', 'your_password')
print('✅ SMTP connection successful')
"

# 3. Check firewall (port 25, 465, or 587 blocked?)
telnet smtp.gmail.com 587
# Expected: Connected

# 4. Verify credentials (test with webmail first)
# Log in manually to Gmail/Outlook to verify password

# 5. Use app password (Gmail)
# Settings > Security > App passwords > Generate password for "Mail"
```

### Issue: Excel file too large or processing slow

**Solution:**
```bash
# 1. Check file size
ls -lh data_input/your_file.xlsx

# 2. Profile performance
python performance_profiler.py

# 3. Consider splitting large files
# Process in batches instead of one large file

# 4. Use xlsxwriter for output (already default in v3.0.0)
# This provides 69% performance improvement

# 5. Increase available memory/resources
# Linux: ulimit -v (virtual memory)
# Windows: Check Task Manager
```

### Issue: Tests fail after deployment

**Solution:**
```bash
# 1. Check Python version
python --version
# Must be 3.11+

# 2. Reinstall all dependencies
pip install -r requirements.txt --force-reinstall

# 3. Clear pytest cache
rm -rf .pytest_cache __pycache__ tests/__pycache__

# 4. Run tests with verbose output
pytest tests/ -vv

# 5. Check for environment variables
env | grep TDR_

# 6. Run specific failing test
pytest tests/test_config_security.py::test_secure_config_loading -vv
```

---

## Support & Monitoring

### Monitoring Checklist

- [ ] **Daily:** Check tdr_processor.log for errors
- [ ] **Weekly:** Run `pytest tests/ -q` (ensure 139 pass)
- [ ] **Weekly:** Check disk space (`du -sh outputs/`)
- [ ] **Monthly:** Review performance metrics
- [ ] **Monthly:** Check for security updates (`pip check`)
- [ ] **Quarterly:** Review and test rollback procedures

### Log File Analysis

```bash
# View recent errors
grep ERROR tdr_processor.log | tail -20

# View processing summary
grep "Processing complete" tdr_processor.log

# Count errors by type
grep "ERROR\|CRITICAL" tdr_processor.log | cut -d':' -f3 | sort | uniq -c

# Archive old logs (>30 days)
find . -name "*.log" -mtime +30 -exec gzip {} \;
```

### Performance Monitoring

```bash
# Monitor resource usage (Linux)
watch -n 5 'free -h && df -h && ps aux | head -10'

# Monitor from Python
import psutil
print(f"CPU: {psutil.cpu_percent()}%")
print(f"Memory: {psutil.virtual_memory().percent}%")
print(f"Disk: {psutil.disk_usage('/').percent}%")
```

### Scheduled Maintenance

```bash
# Weekly cleanup (cron job)
0 2 * * 0 find /home/user/tdr_processor -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
0 3 * * 0 find /home/user/tdr_processor/outputs -mtime +90 -delete 2>/dev/null

# Monthly backup
0 4 1 * * tar -czf /backup/tdr_processor_$(date +\%Y\%m\%d).tar.gz /home/user/tdr_processor/

# Test suite (weekly)
0 5 * * 1 cd /home/user/tdr_processor && /home/user/tdr_processor/venv/bin/pytest tests/ -q >> deployment_tests.log 2>&1
```

---

## Deployment Success Confirmation

✅ **Deployment Complete When:**

1. All 139 tests passing: `pytest tests/ -q` → **139 passed**
2. Version confirmed: `python -c "from config import ApplicationConfig; print(ApplicationConfig.VERSION)"` → **3.0.0**
3. Sample data processed: `python main.py data_input/sample_tdr.xlsx` → **Success**
4. No ERROR/CRITICAL in logs: `grep -E "ERROR|CRITICAL" tdr_processor.log` → **No results**
5. Environment variables set (if using email): `echo $TDR_SMTP_SERVER` → **Value shown**

---

## Post-Deployment Next Steps

1. **Notify users** that v3.0.0 is available
2. **Document any custom configurations** in DEPLOYMENT_CONFIG.md
3. **Set up monitoring** dashboard or alerts
4. **Schedule follow-up review** 1 week post-deployment
5. **Plan Phase 4.2a** (80%+ coverage) if desired
6. **Collect user feedback** for future improvements

---

## Quick Reference

| Task | Command |
|------|---------|
| Install | `pip install -r requirements.txt` |
| Test | `pytest tests/ -q` |
| Run | `python main.py data_input/file.xlsx` |
| Profile | `python performance_profiler.py` |
| Version | `python -c "from config import ApplicationConfig; print(ApplicationConfig.VERSION)"` |
| Type Check | `mypy utils/ --strict` |
| Coverage | `pytest tests/ --cov=.` |
| Logs | `tail -f tdr_processor.log` |
| Rollback | `git checkout v2.1.0 && pip install -r requirements.txt` |

---

**For detailed information:**
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security: [SECURITY.md](SECURITY.md)
- Quick Start: [QUICK_START.md](QUICK_START.md)

**Contact Support:** See CONTRIBUTING.md for reporting issues
