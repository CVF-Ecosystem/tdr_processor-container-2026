# Contributing to TDR Processor v3.0

Thank you for your interest in contributing to TDR Processor! This guide provides everything you need to get started with development, testing, and submitting contributions.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Environment](#development-environment)
4. [Project Structure](#project-structure)
5. [Development Workflow](#development-workflow)
6. [Code Style & Standards](#code-style--standards)
7. [Testing & Coverage](#testing--coverage)
8. [Git Workflow](#git-workflow)
9. [Pull Request Process](#pull-request-process)
10. [Security Guidelines](#security-guidelines)
11. [Performance Considerations](#performance-considerations)
12. [Debugging & Profiling](#debugging--profiling)
13. [Common Tasks](#common-tasks)
14. [FAQ](#faq)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors. We pledge to:

- Respect all contributors regardless of background
- Accept constructive criticism gracefully
- Focus on code quality and collaboration
- Report unethical behavior to maintainers

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of different opinions
- Accept responsibility and apologize for mistakes
- Focus on code quality and functionality

### Enforcement

Violations will be handled by project maintainers with appropriate consequences.

---

## Getting Started

### Prerequisites

- **Python:** 3.11 or higher
- **Git:** For version control
- **pip:** Python package manager
- **Virtual Environment:** Recommended for isolation
- **OS:** Windows, macOS, or Linux

### Quick Setup (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/your-org/tdr_processor.git
cd tdr_processor

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 5. Verify installation
pytest tests/ -q
# Expected: 139 passed
```

### Verify Your Setup

```bash
# Check Python version
python --version
# Output: Python 3.11.x

# Check dependencies
pip list | grep -E "pandas|openpyxl|pytest"

# Run tests
pytest tests/ -q --tb=short
# Expected: 139 passed in ~2s
```

---

## Development Environment

### Virtual Environment Setup

**Create & Activate:**
```bash
# Create
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Deactivate (any OS)
deactivate
```

### IDE Setup

#### Visual Studio Code (Recommended)

```bash
# Install extensions
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.debugpy

# Create .vscode/settings.json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.pylintArgs": [
    "--disable=C0111",  # missing-docstring
    "--disable=C0103"   # invalid-name
  ],
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "100"],
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.python"
  }
}
```

#### PyCharm

```
Settings → Project → Python Interpreter
  ├─ Select: ./venv/bin/python (or .../venv/Scripts/python.exe on Windows)
  ├─ Enable: Pytest as test runner
  └─ Enable: Code inspection

Settings → Editor → Code Style → Python
  ├─ Spaces: 4 (indent)
  ├─ Line length: 100
  └─ Wrapping & Braces: Follow PEP 8
```

### Dependencies

```bash
# Core dependencies
pip install pandas openpyxl xlsxwriter python-dotenv

# Development dependencies
pip install -r requirements-dev.txt
# Includes: pytest, black, pylint, mypy, coverage, pytest-mock
```

---

## Project Structure

### Directory Layout

```
tdr_processor/
├── main.py                    # Primary entry point (CLI)
├── app.py                     # Desktop GUI entry point
├── config.py                  # Configuration (10 dataclasses)
├── report_processor.py        # Main processing orchestrator
├── data_extractors.py         # Data extraction logic (4 extractors)
├── dashboard.py               # Tkinter GUI
├── performance_profiler.py    # Performance profiling tool
│
├── utils/                     # Utility modules
│   ├── __init__.py
│   ├── email_notifier.py      # Email delivery (secure)
│   ├── excel_handler.py       # Excel read/write
│   ├── excel_optimizer.py     # xlsxwriter optimization
│   ├── excel_utils.py         # Excel utilities
│   ├── dataframe_utils.py     # DataFrame operations
│   ├── datetime_utils.py      # DateTime handling
│   ├── input_validator.py     # Input validation (6 validators)
│   ├── file_utils.py          # File operations
│   ├── logger_setup.py        # Logging configuration
│   ├── scheduler.py           # APScheduler integration
│   └── watcher.py             # File watcher (watchdog)
│
├── tests/                     # Test suite (139 tests)
│   ├── test_config_security.py (26 tests)
│   ├── test_coverage_expansion.py (21 tests)
│   ├── test_email_notifier.py (3 tests)
│   ├── test_excel_optimizer.py (12 tests)
│   ├── test_excel_utils.py (21 tests)
│   ├── test_file_utils.py (8 tests)
│   ├── test_report_processor.py (3 tests)
│   ├── test_scheduler.py (8 tests)
│   ├── test_security.py (24 tests)
│   └── test_watcher.py (13 tests)
│
├── data_input/                # Input directory (TDR files)
├── outputs/                   # Output directory
│   ├── data_excel/            # Generated Excel files
│   └── data_csv/              # Generated CSV files
│
├── docs/                      # Documentation
│   ├── ARCHITECTURE.md        # System design
│   ├── CONTRIBUTING.md        # This file
│   ├── SECURITY.md            # Security guidelines
│   └── README.md              # Project overview
│
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
├── pytest.ini                 # Pytest configuration
├── mypy.ini                   # Type checking configuration
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
└── TDR_Processor.spec         # PyInstaller spec for executable
```

### Key Files to Know

| File | Purpose | Size |
|------|---------|------|
| config.py | All configuration (10 dataclasses) | 500 LOC |
| report_processor.py | Main processor logic | 262 LOC |
| data_extractors.py | Data extraction (4 extractors) | 452 LOC |
| utils/email_notifier.py | Secure email delivery | 70 LOC |
| utils/excel_optimizer.py | Fast Excel export (xlsxwriter) | 93 LOC |
| performance_profiler.py | Profiling tool | 400+ LOC |
| tests/ | Test suite (139 tests) | - |

---

## Development Workflow

### Step 1: Create a Feature Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
# Or for bugfix:
git checkout -b bugfix/issue-description
```

**Branch Naming Convention:**
```
feature/short-description     # New feature
bugfix/short-description      # Bug fix
docs/short-description        # Documentation
refactor/short-description    # Code refactoring
perf/short-description        # Performance improvement
test/short-description        # Test addition
```

### Step 2: Make Changes

```bash
# Edit files, create new modules, etc.
# Ensure your code follows style guide (see below)

# Check status
git status

# Stage changes
git add .
# Or specific files:
git add utils/new_module.py tests/test_new_module.py
```

### Step 3: Write Tests

```bash
# For new feature, add tests first (TDD style)
touch tests/test_new_feature.py

# Write tests
cat > tests/test_new_feature.py << 'EOF'
import pytest
from new_module import new_function

class TestNewFeature:
    def test_basic_functionality(self):
        result = new_function(input_data)
        assert result == expected_output
    
    def test_edge_cases(self):
        # Test edge cases
        pass
    
    def test_error_handling(self):
        # Test error scenarios
        pass
EOF

# Run tests
pytest tests/test_new_feature.py -v
```

**Test Coverage Requirements:**
- New code: >80% coverage
- Existing code: maintain current coverage
- Critical functions: 100% coverage

### Step 4: Check Code Quality

```bash
# Run all tests
pytest tests/ -v

# Check type hints
mypy utils/new_module.py

# Check style (PEP 8)
pylint utils/new_module.py --disable=C0111,C0103

# Auto-format code
black utils/new_module.py

# Check coverage
pytest tests/test_new_feature.py --cov=utils.new_module --cov-report=html
```

### Step 5: Commit Changes

```bash
# Commit with descriptive message
git commit -m "feature: add new data extraction method

- Implements extraction for container details
- Adds 5 test cases (100% coverage)
- Performance: 0.1s per file
- Fixes #123"

# Best practices:
# 1. Use imperative mood ("add" not "added")
# 2. Limit first line to 50 characters
# 3. Provide detailed explanation in body
# 4. Reference related issues (#123)
# 5. One commit per logical change
```

### Step 6: Push & Create PR

```bash
# Push branch
git push origin feature/your-feature-name

# Create Pull Request on GitHub/GitLab
# Title: [FEATURE] Short description
# Description: (use PR template below)
```

---

## Code Style & Standards

### PEP 8 Compliance

**Line Length:** Maximum 100 characters

```python
# ✅ Good
result = process_data(
    input_file,
    output_file,
    config=config_object
)

# ❌ Bad
result = process_data(input_file, output_file, config=config_object, extra_param=True, another_param=False)
```

### Naming Conventions

```python
# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 10

# Variables/Functions: lower_snake_case
def process_data(input_file):
    processed_data = []
    return processed_data

# Classes: PascalCase
class ReportProcessor:
    def __init__(self):
        pass

# Private methods: _leading_underscore
def _internal_helper():
    pass

# Constants in classes: UPPER_SNAKE_CASE
class Config:
    MAX_ROWS = 1000
```

### Type Hints (Required)

```python
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# ✅ Good - Full type hints
def process_file(
    file_path: Path,
    config: Dict[str, Any],
    max_retries: int = 3
) -> Tuple[bool, str]:
    """Process a single file.
    
    Args:
        file_path: Path to input file
        config: Configuration dictionary
        max_retries: Maximum retry attempts
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    pass

# ❌ Bad - No type hints
def process_file(file_path, config, max_retries=3):
    pass
```

### Docstring Format (Google Style)

```python
def extract_vessel_info(excel_file: Path) -> Dict[str, Any]:
    """Extract vessel information from Excel file.
    
    Parses the vessel summary section of a TDR Excel file
    and extracts key vessel information including name, voyage,
    operator, and timeline data.
    
    Args:
        excel_file: Path to the Excel file
    
    Returns:
        Dictionary containing vessel information:
        {
            'vessel_name': str,
            'voyage': str,
            'operator': str,
            'report_date': datetime,
            'atb': datetime,
            'etb': datetime,
            'etd': datetime
        }
    
    Raises:
        FileNotFoundError: If excel_file doesn't exist
        ValueError: If required sheets not found
        
    Example:
        >>> vessel_data = extract_vessel_info(Path("report.xlsx"))
        >>> print(vessel_data['vessel_name'])
        'SAMPLE VESSEL'
    """
    pass
```

### Import Organization

```python
# 1. Standard library
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

# 2. Third-party libraries
import pandas as pd
import openpyxl
import pytest

# 3. Local imports
from config import get_config
from utils.email_notifier import send_notification_email
from utils.excel_handler import append_df_to_excel
```

### Error Handling

```python
# ✅ Good - Specific exceptions
try:
    df = pd.read_excel(file_path)
except FileNotFoundError as e:
    logging.error(f"File not found: {file_path}")
    raise
except ValueError as e:
    logging.error(f"Invalid Excel format: {e}")
    raise

# ❌ Bad - Bare except
try:
    df = pd.read_excel(file_path)
except:  # Too broad!
    pass

# ❌ Bad - Generic Exception
try:
    df = pd.read_excel(file_path)
except Exception:  # Still too broad
    pass
```

### Logging Best Practices

```python
import logging

logger = logging.getLogger(__name__)

# ✅ Good - Sanitized, informative
logger.info(f"Processing file: {file_path.name}")
logger.warning("Sheet not found, creating new sheet")
logger.error(f"Failed to process: {error_type.__name__}")

# ❌ Bad - Sensitive information
logger.info(f"Connecting with password: {password}")
logger.error(f"SMTP error: {full_exception_with_credentials}")

# ❌ Bad - Not informative
logger.info("Error occurred")
logger.error("Something went wrong")
```

---

## Testing & Coverage

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_email_notifier.py -v

# Run specific test class
pytest tests/test_email_notifier.py::TestEmailCredentials -v

# Run specific test
pytest tests/test_email_notifier.py::TestEmailCredentials::test_valid_credentials -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html --cov-report=term

# Run with markers
pytest tests/ -m "security" -v
```

### Test File Template

```python
# tests/test_new_feature.py
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from new_module import NewClass, new_function


class TestNewClass:
    """Test NewClass functionality."""
    
    def test_initialization(self):
        """Test basic initialization."""
        obj = NewClass(param1="value1")
        assert obj.param1 == "value1"
    
    def test_method_basic(self):
        """Test basic method functionality."""
        obj = NewClass()
        result = obj.method()
        assert result is not None
    
    def test_method_with_mock(self):
        """Test method with mocked dependency."""
        with patch('new_module.external_service') as mock_service:
            mock_service.return_value = "mocked_value"
            obj = NewClass()
            result = obj.method()
            assert result == "expected"
            mock_service.assert_called_once()
    
    def test_error_handling(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            obj = NewClass(invalid_param=True)


class TestNewFunction:
    """Test new_function functionality."""
    
    def test_basic_operation(self):
        """Test basic function operation."""
        result = new_function(input_data)
        assert result == expected_output
    
    def test_edge_case_empty_input(self):
        """Test with empty input."""
        result = new_function([])
        assert result == []
    
    def test_edge_case_large_input(self):
        """Test with large input."""
        large_input = list(range(10000))
        result = new_function(large_input)
        assert len(result) == 10000
    
    @pytest.mark.parametrize("input_val,expected", [
        (1, 2),
        (2, 4),
        (3, 6),
    ])
    def test_parametrized(self, input_val, expected):
        """Test with multiple input values."""
        assert new_function(input_val) == expected


def test_integration_with_file():
    """Integration test with file I/O."""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        # Test operations
        result = new_function(temp_path)
        assert result is not None
    finally:
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
```

### Coverage Requirements

```
✅ REQUIRED
├─ Overall: >62% (current baseline)
├─ Critical functions: 100%
├─ Security-sensitive code: 100%
├─ Public APIs: >90%
└─ Utility functions: >80%

⚠️  GOAL
├─ Target: >80% overall
├─ Focus: data_extractors.py (3% → 50%)
├─ Focus: report_processor.py (16% → 60%)
└─ Phase 4.2a: Additional coverage tests
```

### Check Coverage

```bash
# Run with coverage report
pytest tests/ --cov=. --cov-report=html

# View in browser
# Windows:
start htmlcov/index.html
# macOS:
open htmlcov/index.html
# Linux:
xdg-open htmlcov/index.html

# Check specific module
pytest tests/test_email_notifier.py --cov=utils.email_notifier --cov-report=term-missing
```

---

## Git Workflow

### Standard Git Workflow

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make commits
git add .
git commit -m "feature: implement new extractor

- Adds NewExtractor class for data extraction
- Includes 10 test cases (100% coverage)
- Performance: 0.05s per file
- Resolves #456"

# 3. Keep branch updated
git fetch origin
git rebase origin/main

# 4. Push branch
git push origin feature/my-feature

# 5. Create Pull Request on GitHub
# (Fill in PR template with details)

# 6. Address review comments
# Make changes and push again
git commit -m "review: address feedback on test coverage"
git push origin feature/my-feature

# 7. After approval, merge via PR interface
# (Maintainer merges to main)

# 8. Clean up local branch
git checkout main
git pull origin main
git branch -d feature/my-feature
```

### Useful Git Commands

```bash
# View commit history
git log --oneline -10
git log --graph --all --decorate --oneline

# See what changed
git diff HEAD~1
git diff feature/branch

# Stash temporary changes
git stash
git stash pop

# Revert a commit
git revert <commit-hash>

# Check branch status
git status
git branch -v
```

---

## Pull Request Process

### PR Title Format

```
[TYPE] Brief description

Types:
- [FEATURE] New functionality
- [BUGFIX] Bug fix
- [DOCS] Documentation changes
- [REFACTOR] Code refactoring
- [PERF] Performance improvement
- [TEST] Test additions/improvements
- [SECURITY] Security fixes
```

### PR Description Template

```markdown
## Description
Brief description of what this PR does.

## Related Issues
Fixes #123
Related to #456

## Changes Made
- Change 1 description
- Change 2 description
- Change 3 description

## Testing
- [ ] Added unit tests
- [ ] Verified coverage >80%
- [ ] Ran full test suite (139 tests pass)
- [ ] Tested with sample data

## Performance Impact
- No impact on performance
- OR: 20% improvement in Excel writing

## Security
- No security implications
- OR: Security improvements documented in PR

## Checklist
- [ ] Code follows style guidelines
- [ ] Type hints added (95%+ coverage)
- [ ] Docstrings added (Google style)
- [ ] Tests added/updated
- [ ] Coverage maintained/improved
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Commits are clean and descriptive

## Screenshots (if applicable)
[Add screenshots for UI changes]
```

### Review Process

1. **Automated Checks** (CI/CD)
   - Tests must pass (139 tests)
   - Coverage must be >62%
   - Code style must follow PEP 8
   - Type hints must be valid

2. **Code Review**
   - At least 1 maintainer review
   - Address review feedback
   - Push additional commits for fixes

3. **Approval & Merge**
   - Approved by maintainer
   - Merge via PR interface
   - Automated deployment to production

---

## Security Guidelines

### Credential Protection

```python
# ✅ CORRECT - Load from environment
from config import get_config
config = get_config()
smtp_password = config.smtp.password  # From env var

# ❌ WRONG - Hardcoded credentials
SMTP_PASSWORD = "my_secret_password"

# ❌ WRONG - In config file
[smtp]
password = my_secret_password

# ✅ CORRECT - .env.example shows template
# .env.example
TDR_SMTP_PASSWORD=your_password_here
```

### Input Validation

```python
# ✅ CORRECT - Validate all inputs
from utils.input_validator import validate_email

recipient = "user@example.com"
is_valid, error = validate_email(recipient)
if not is_valid:
    raise ValueError(f"Invalid email: {error}")

# ❌ WRONG - No validation
email = user_input  # Could be anything!
send_email(email)
```

### Error Handling

```python
# ✅ CORRECT - Sanitized error messages
try:
    result = process_data(file_path)
except Exception as e:
    logging.error(f"Processing failed: {type(e).__name__}")
    # NOT logging: f"Error: {e}" which might contain sensitive data

# ❌ WRONG - Exposing sensitive information
except Exception as e:
    logging.error(f"Database error: {e}")  # Might contain DB credentials!
```

### Dependency Security

```bash
# Check for vulnerable dependencies
pip install safety
safety check

# Keep dependencies updated
pip list --outdated
pip install --upgrade pandas openpyxl

# Use pinned versions for production
# requirements.txt
pandas==2.0.3
openpyxl==3.10.9
```

---

## Performance Considerations

### Profiling Code

```bash
# Run performance profiler
python performance_profiler.py

# View results
cat performance_reports/profile_stats.txt

# Or generate detailed report
python -m cProfile -o profile.prof main.py
python -m pstats profile.prof
# > sort cumtime
# > stats
```

### Optimization Checklist

- ✅ Use xlsxwriter for Excel writing (50-65% faster)
- ✅ Avoid repeated pandas operations
- ✅ Cache calculations for reuse
- ✅ Use generators for large datasets
- ✅ Profile before optimizing
- ✅ Test performance improvements

### Performance Targets

```
Operation              Target Time    Benchmark
────────────────────────────────────────────────
Single file process    <1.0s          0.4s avg
Excel write (10K rows) <0.3s          0.2s
Data extraction        <0.1s          0.04s
Email delivery         <5s            Variable
Startup                <0.5s          0.2s
```

---

## Debugging & Profiling

### Debug Mode

```bash
# Run with debug logging
export TDR_LOG_LEVEL=DEBUG
python main.py

# Or set in code
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

### Using Debugger

**VS Code:**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Main",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/main.py",
      "console": "integratedTerminal"
    }
  ]
}
```

**PyCharm:**
- Right-click → Run 'main.py'
- Or click Debug button (Shift+F9)

### Common Debugging Commands

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use built-in breakpoint (Python 3.7+)
breakpoint()

# Print debug info
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Variable value: {var}")

# Check types
print(type(variable))
print(variable.__class__.__name__)
```

### Profiling

```bash
# CPU profiling
python -m cProfile -s cumtime main.py | head -20

# Memory profiling
pip install memory-profiler
python -m memory_profiler main.py

# Line profiler
pip install line-profiler
kernprof -l -v main.py
```

---

## Common Tasks

### Add New Extractor

```python
# 1. Create in data_extractors.py
class MyExtractor(DataExtractor):
    """Extract my data."""
    
    def extract(self) -> Dict[str, Any]:
        """Extract data and return."""
        # Implementation
        pass

# 2. Add tests in tests/test_data_extractors.py
class TestMyExtractor:
    def test_basic_extraction(self):
        pass

# 3. Register in report_processor.py
extractors = [
    VesselExtractor(file),
    QCExtractor(file),
    MyExtractor(file),  # Add here
]

# 4. Run tests
pytest tests/test_data_extractors.py -v
```

### Add New Utility Function

```python
# 1. Create in utils/
# utils/new_utility.py
def new_utility_function(param: str) -> str:
    """Process parameter."""
    return result

# 2. Add tests in tests/test_new_utility.py
class TestNewUtility:
    def test_basic(self):
        assert new_utility_function("input") == "expected"

# 3. Export from utils/__init__.py
from .new_utility import new_utility_function

# 4. Use in code
from utils import new_utility_function
```

### Run Full Test Suite

```bash
# Run all 139 tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific category
pytest tests/test_config_security.py -v

# Run and stop on first failure
pytest tests/ -x
```

---

## FAQ

### Q: How do I set up my environment?
**A:** See [Development Environment](#development-environment) section. Quick: clone → create venv → pip install → pytest

### Q: What Python version is required?
**A:** Python 3.11 or higher. Check with `python --version`

### Q: How do I run tests?
**A:** `pytest tests/ -v` for all tests, or `pytest tests/test_specific.py -v` for specific file

### Q: What's the coverage requirement?
**A:** Current: >62% baseline. New code: >80%. Critical: 100%

### Q: How do I add type hints?
**A:** Use `from typing import ...` and annotate all function parameters and returns. Example: `def func(x: int) -> str:`

### Q: Can I hardcode credentials?
**A:** NO! Always use environment variables. See [Security Guidelines](#security-guidelines)

### Q: How do I debug an issue?
**A:** Use `breakpoint()` or `pdb.set_trace()`, enable DEBUG logging, or use profiling tools

### Q: What branch naming convention should I use?
**A:** `feature/name`, `bugfix/name`, `docs/name`, `refactor/name`, `perf/name`, `test/name`

### Q: How do I handle errors?
**A:** Use specific exceptions, log sanitized messages (no credentials), and raise appropriately

### Q: Where do I add documentation?
**A:** Docstrings in code (Google style), plus docs/ folder for architecture/contributing/security guides

### Q: How do I test with sample data?
**A:** Use data_input/ folder. Sample TDR Excel files for testing go there

### Q: What if tests fail in my environment?
**A:** Check Python version (3.11+), verify all dependencies installed, run `pip install -r requirements-dev.txt`

### Q: Can I use a different IDE?
**A:** Yes! VS Code, PyCharm, Vim, Emacs - just ensure pytest/black/mypy work in your setup

---

## Resources

### Documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design & components
- [SECURITY.md](SECURITY.md) - Security guidelines & best practices
- [README.md](README.md) - Project overview & quick start

### Tools
- **Testing:** pytest, coverage, pytest-mock
- **Code Quality:** black, pylint, mypy
- **Profiling:** cProfile, line-profiler, memory-profiler
- **VCS:** git (see [Git Workflow](#git-workflow))

### External References
- [PEP 8 Style Guide](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [pytest Documentation](https://docs.pytest.org/)

---

## Support

Have questions? Need help?

1. **Check Documentation:** See [ARCHITECTURE.md](ARCHITECTURE.md), [SECURITY.md](SECURITY.md)
2. **Search Issues:** GitHub Issues may have answers
3. **Ask in Discussions:** Use GitHub Discussions for questions
4. **Contact Maintainers:** Email or direct message

---

**Thank you for contributing to TDR Processor v3.0!**

*Document Version: 1.0*  
*Last Updated: December 2025*  
*Maintainer: TDR Processor Team*
