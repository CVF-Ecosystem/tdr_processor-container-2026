# tests/test_data_extractors.py
"""
Unit tests for DataExtractor class.

Uses mock openpyxl worksheets to test extraction logic
without requiring actual Excel files.
"""
import pytest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock


# ============================================================================
# FIXTURES
# ============================================================================

def make_mock_worksheet(cell_data: dict):
    """
    Create a mock openpyxl worksheet with predefined cell values.

    Args:
        cell_data: Dict mapping (row, col) tuples to cell values

    Returns:
        Mock worksheet object
    """
    ws = MagicMock()
    ws.max_row = max((r for r, c in cell_data.keys()), default=1)
    ws.max_column = max((c for r, c in cell_data.keys()), default=1)

    def cell_side_effect(row, column):
        cell = MagicMock()
        cell.value = cell_data.get((row, column))
        return cell

    ws.cell.side_effect = cell_side_effect
    return ws


@pytest.fixture
def temp_excel_file(tmp_path):
    """Create a temporary Excel file for testing."""
    excel_path = tmp_path / "test_tdr.xlsx"
    excel_path.write_bytes(b"PK\x03\x04" + b"\x00" * 100)  # Minimal ZIP signature
    return excel_path


@pytest.fixture
def mock_worksheet():
    """Create a basic mock worksheet."""
    return make_mock_worksheet({})


# ============================================================================
# TEST: DataExtractor initialization
# ============================================================================

class TestDataExtractorInit:
    def test_init_with_valid_file(self, tmp_path):
        """Test DataExtractor initializes correctly with valid file."""
        from data_extractors import DataExtractor

        excel_path = tmp_path / "valid.xlsx"
        excel_path.write_bytes(b"PK\x03\x04" + b"\x00" * 100)

        ws = MagicMock()
        ws.max_row = 10
        ws.max_column = 10

        extractor = DataExtractor(ws, excel_path)
        assert extractor.filename_str == "valid.xlsx"
        assert extractor.vessel_name is None
        assert extractor.voyage_no is None

    def test_init_with_nonexistent_file(self, tmp_path):
        """Test DataExtractor raises ValueError for non-existent file."""
        from data_extractors import DataExtractor

        nonexistent = tmp_path / "nonexistent.xlsx"
        ws = MagicMock()

        with pytest.raises(ValueError, match="File does not exist"):
            DataExtractor(ws, nonexistent)

    def test_init_with_path_traversal(self, tmp_path):
        """Test DataExtractor raises ValueError for path traversal attempts."""
        from data_extractors import DataExtractor

        traversal_path = Path("../../etc/passwd")
        ws = MagicMock()

        with pytest.raises(ValueError):
            DataExtractor(ws, traversal_path)


# ============================================================================
# TEST: Helper methods
# ============================================================================

class TestDataExtractorHelpers:
    def test_parse_moves_hour_value_int(self, tmp_path):
        """Test _parse_moves_hour_value with integer input."""
        from data_extractors import DataExtractor

        excel_path = tmp_path / "test.xlsx"
        excel_path.write_bytes(b"PK\x03\x04" + b"\x00" * 100)
        ws = MagicMock()
        ws.max_row = 1
        ws.max_column = 1

        extractor = DataExtractor(ws, excel_path)
        assert extractor._parse_moves_hour_value(42) == 42.0
        assert extractor._parse_moves_hour_value(0) == 0.0

    def test_parse_moves_hour_value_string(self, tmp_path):
        """Test _parse_moves_hour_value with string input."""
        from data_extractors import DataExtractor

        excel_path = tmp_path / "test.xlsx"
        excel_path.write_bytes(b"PK\x03\x04" + b"\x00" * 100)
        ws = MagicMock()
        ws.max_row = 1
        ws.max_column = 1

        extractor = DataExtractor(ws, excel_path)
        assert extractor._parse_moves_hour_value("35.5") == 35.5
        assert extractor._parse_moves_hour_value("35,5") == 35.5  # European decimal
        assert extractor._parse_moves_hour_value("invalid") == 0.0

    def test_get_cell_value_missing_key(self, tmp_path):
        """Test _get_cell_value returns default when key not in column_map."""
        from data_extractors import DataExtractor

        excel_path = tmp_path / "test.xlsx"
        excel_path.write_bytes(b"PK\x03\x04" + b"\x00" * 100)
        ws = MagicMock()
        ws.max_row = 1
        ws.max_column = 1

        extractor = DataExtractor(ws, excel_path)
        result = extractor._get_cell_value(1, {}, "missing_key", default_value=99)
        assert result == 99

    def test_get_cell_value_with_parse_func(self, tmp_path):
        """Test _get_cell_value applies parse function."""
        from data_extractors import DataExtractor

        excel_path = tmp_path / "test.xlsx"
        excel_path.write_bytes(b"PK\x03\x04" + b"\x00" * 100)

        ws = MagicMock()
        ws.max_row = 5
        ws.max_column = 5
        mock_cell = MagicMock()
        mock_cell.value = "42.5"
        ws.cell.return_value = mock_cell

        extractor = DataExtractor(ws, excel_path)
        result = extractor._get_cell_value(1, {"test_key": 1}, "test_key", float, 0.0)
        assert result == 42.5


# ============================================================================
# TEST: excel_utils functions
# ============================================================================

class TestExcelUtils:
    def test_col_letter_to_index_single(self):
        """Test column letter to index conversion for single letters."""
        from utils.excel_utils import col_letter_to_index
        assert col_letter_to_index("A") == 1
        assert col_letter_to_index("B") == 2
        assert col_letter_to_index("Z") == 26

    def test_col_letter_to_index_double(self):
        """Test column letter to index conversion for double letters."""
        from utils.excel_utils import col_letter_to_index
        assert col_letter_to_index("AA") == 27
        assert col_letter_to_index("AB") == 28
        assert col_letter_to_index("AZ") == 52

    def test_col_letter_to_index_invalid(self):
        """Test column letter to index returns None for invalid input."""
        from utils.excel_utils import col_letter_to_index
        assert col_letter_to_index("") is None
        assert col_letter_to_index("1") is None
        assert col_letter_to_index(None) is None

    def test_timedelta_to_hours(self):
        """Test timedelta to hours conversion."""
        from datetime import timedelta
        from utils.excel_utils import timedelta_to_hours
        assert timedelta_to_hours(timedelta(hours=2, minutes=30)) == 2.5
        assert timedelta_to_hours(timedelta(hours=1, minutes=15)) == 1.25
        assert timedelta_to_hours(timedelta(0)) == 0.0
        assert timedelta_to_hours("not a timedelta") == 0.0

    def test_classify_error_code_terminal(self):
        """Test error code classification for terminal convenience."""
        from utils.excel_utils import classify_error_code
        code, error_type = classify_error_code("a - crane breakdown")
        assert code == "a"
        assert error_type == "Terminal Convenience"

    def test_classify_error_code_non_terminal(self):
        """Test error code classification for non-terminal convenience."""
        from utils.excel_utils import classify_error_code
        code, error_type = classify_error_code("i - vessel delay")
        assert code == "i"
        assert error_type == "Non-Terminal Convenience"

    def test_classify_error_code_none(self):
        """Test error code classification for None input."""
        from utils.excel_utils import classify_error_code
        code, error_type = classify_error_code(None)
        assert code is None
        assert error_type == "Unknown"

    def test_parse_time_duration_string(self):
        """Test time duration parsing from string."""
        from utils.excel_utils import parse_time_duration
        assert parse_time_duration("2:30") == 2.5
        assert parse_time_duration("1:15") == 1.25
        assert parse_time_duration("0:45") == 0.75

    def test_parse_time_duration_float(self):
        """Test time duration parsing from float (Excel fraction)."""
        from utils.excel_utils import parse_time_duration
        # 0.5 = 12 hours in Excel time fraction
        result = parse_time_duration(0.5)
        assert result == 12.0

    def test_parse_excel_datetime_none(self):
        """Test parse_excel_datetime returns None for None input."""
        from utils.excel_utils import parse_excel_datetime
        assert parse_excel_datetime(None) is None

    def test_parse_excel_datetime_datetime_object(self):
        """Test parse_excel_datetime returns datetime as-is."""
        from utils.excel_utils import parse_excel_datetime
        dt = datetime(2023, 7, 15, 14, 30)
        result = parse_excel_datetime(dt)
        assert result == dt

    def test_parse_excel_datetime_date_only(self):
        """Test parse_excel_datetime with is_just_date=True."""
        from utils.excel_utils import parse_excel_datetime
        dt = datetime(2023, 7, 15, 14, 30)
        result = parse_excel_datetime(dt, is_just_date=True)
        assert result == date(2023, 7, 15)

    def test_parse_excel_datetime_string_full(self):
        """Test parse_excel_datetime with full datetime string."""
        from utils.excel_utils import parse_excel_datetime
        result = parse_excel_datetime("2023-07-15 14:30:00")
        assert isinstance(result, datetime)
        assert result.year == 2023
        assert result.month == 7
        assert result.day == 15

    def test_parse_excel_datetime_no_debug_prints(self, capsys):
        """Verify no debug print statements are executed."""
        from utils.excel_utils import parse_excel_datetime
        # Test with the value that previously triggered debug prints
        parse_excel_datetime(0.75)
        captured = capsys.readouterr()
        assert "DEBUG_FUNC" not in captured.out
        assert "DEBUG_FUNC" not in captured.err


# ============================================================================
# TEST: input_validator
# ============================================================================

class TestInputValidator:
    def test_validate_email_valid(self):
        """Test email validation with valid email."""
        from utils.input_validator import validate_email
        is_valid, error = validate_email("user@example.com")
        assert is_valid is True
        assert error == ""

    def test_validate_email_invalid(self):
        """Test email validation with invalid email."""
        from utils.input_validator import validate_email
        is_valid, error = validate_email("not-an-email")
        assert is_valid is False
        assert error != ""

    def test_validate_email_injection(self):
        """Test email validation blocks injection attempts."""
        from utils.input_validator import validate_email
        is_valid, error = validate_email("user@evil.com\nBCC: attacker@evil.com")
        assert is_valid is False

    def test_validate_smtp_port_valid(self):
        """Test SMTP port validation with valid ports."""
        from utils.input_validator import validate_smtp_port
        assert validate_smtp_port(587)[0] is True
        assert validate_smtp_port(465)[0] is True
        assert validate_smtp_port(25)[0] is True
        assert validate_smtp_port(2525)[0] is True  # Common alternate port

    def test_validate_smtp_port_invalid(self):
        """Test SMTP port validation with invalid ports."""
        from utils.input_validator import validate_smtp_port
        assert validate_smtp_port(0)[0] is False
        assert validate_smtp_port(65536)[0] is False
        assert validate_smtp_port(-1)[0] is False

    def test_validate_file_path_traversal(self):
        """Test file path validation blocks path traversal."""
        from utils.input_validator import validate_file_path
        is_valid, error = validate_file_path("../../etc/passwd")
        assert is_valid is False
        assert "traversal" in error.lower()

    def test_validate_excel_file_valid(self, tmp_path):
        """Test Excel file validation with valid file."""
        from utils.input_validator import validate_excel_file
        excel_path = tmp_path / "test.xlsx"
        # Write valid ZIP/XLSX magic bytes
        excel_path.write_bytes(b"PK\x03\x04" + b"\x00" * 100)
        is_valid, error = validate_excel_file(str(excel_path))
        assert is_valid is True

    def test_validate_excel_file_wrong_extension(self, tmp_path):
        """Test Excel file validation rejects wrong extension."""
        from utils.input_validator import validate_excel_file
        txt_path = tmp_path / "test.txt"
        txt_path.write_text("not excel")
        is_valid, error = validate_excel_file(str(txt_path))
        assert is_valid is False


# ============================================================================
# TEST: file_utils
# ============================================================================

class TestFileUtils:
    def test_setup_project_directories(self, tmp_path):
        """Test project directory creation."""
        from utils.file_utils import setup_project_directories
        dirs = ["data_input", "outputs", "backup"]
        result = setup_project_directories(tmp_path, dirs)
        assert result is True
        for d in dirs:
            assert (tmp_path / d).exists()

    def test_backup_file_creates_backup(self, tmp_path):
        """Test backup_file creates a timestamped backup."""
        from utils.file_utils import backup_file
        source = tmp_path / "test_file.xlsx"
        source.write_text("test content")

        # Change to tmp_path to use relative backup dir
        import os
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        try:
            backup_file(source)
            backup_dirs = list((tmp_path / "backup").glob("backup_*"))
            assert len(backup_dirs) > 0
            backup_files = list(backup_dirs[0].glob("*.xlsx"))
            assert len(backup_files) > 0
        finally:
            os.chdir(original_dir)

    def test_backup_file_nonexistent(self, tmp_path):
        """Test backup_file handles non-existent file gracefully."""
        from utils.file_utils import backup_file
        nonexistent = tmp_path / "nonexistent.xlsx"
        # Should not raise any exception
        backup_file(nonexistent)


# ============================================================================
# TEST: data_schema
# ============================================================================

class TestDataSchema:
    def test_normalize_qc_name_gc1(self):
        """Test QC name normalization GC1 -> GC01."""
        from data_schema import normalize_qc_name
        assert normalize_qc_name("GC1") == "GC01"
        assert normalize_qc_name("GW2") == "GW02"
        assert normalize_qc_name("gc1") == "GC01"

    def test_normalize_qc_name_already_normalized(self):
        """Test QC name normalization for already-normalized names."""
        from data_schema import normalize_qc_name
        assert normalize_qc_name("GC01") == "GC01"
        assert normalize_qc_name("GW10") == "GW10"

    def test_normalize_qc_name_empty(self):
        """Test QC name normalization for empty/None input."""
        from data_schema import normalize_qc_name
        assert normalize_qc_name("") == ""
        assert normalize_qc_name(None) == ""

    def test_calculate_net_working_hours(self):
        """Test net working hours calculation."""
        from data_schema import calculate_net_working_hours
        assert calculate_net_working_hours(10.0, 2.0) == 8.0
        assert calculate_net_working_hours(5.0, 6.0) == 0.0  # Never negative
        assert calculate_net_working_hours(None, 2.0) == 0.0

    def test_calculate_moves_per_hour(self):
        """Test moves per hour calculation."""
        from data_schema import calculate_moves_per_hour
        assert calculate_moves_per_hour(100, 2.0) == 50.0
        assert calculate_moves_per_hour(0, 2.0) == 0.0
        assert calculate_moves_per_hour(100, 0) == 0.0  # No division by zero

    def test_validate_dataframe_valid(self):
        """Test DataFrame validation with valid data."""
        import pandas as pd
        from data_schema import validate_dataframe, VESSEL_SUMMARY_SCHEMA

        df = pd.DataFrame([{
            "Filename": "test.xlsx",
            "Vessel Name": "TEST VESSEL",
            "Voyage": "001E",
        }])
        result = validate_dataframe(df, VESSEL_SUMMARY_SCHEMA)
        assert "valid" in result

    def test_error_type_enum_consistency(self):
        """Test ErrorType enum values are consistent between config and data_schema."""
        from data_schema import ErrorType as SchemaErrorType
        from config import ErrorType as ConfigErrorType

        # Values should match
        assert SchemaErrorType.TERMINAL_CONVENIENCE.value == ConfigErrorType.TERMINAL_CONVENIENCE.value
        assert SchemaErrorType.NON_TERMINAL_CONVENIENCE.value == ConfigErrorType.NON_TERMINAL_CONVENIENCE.value
        assert SchemaErrorType.UNKNOWN.value == ConfigErrorType.UNKNOWN.value


# ============================================================================
# TEST: exceptions
# ============================================================================

class TestExceptions:
    def test_excel_parsing_error(self):
        """Test ExcelParsingError carries context."""
        from exceptions import ExcelParsingError
        err = ExcelParsingError("test.xlsx", "Invalid format", sheet_name="Sheet1")
        assert err.filename == "test.xlsx"
        assert err.sheet_name == "Sheet1"
        assert "test.xlsx" in str(err)

    def test_vessel_info_missing_error(self):
        """Test VesselInfoMissingError carries missing fields."""
        from exceptions import VesselInfoMissingError
        err = VesselInfoMissingError("test.xlsx", ["Vessel Name", "ATB"])
        assert err.filename == "test.xlsx"
        assert "Vessel Name" in err.missing_fields
        assert "ATB" in err.missing_fields

    def test_concurrent_processing_error(self):
        """Test ConcurrentProcessingError message."""
        from exceptions import ConcurrentProcessingError
        err = ConcurrentProcessingError()
        assert "already in progress" in str(err).lower()

    def test_exception_hierarchy(self):
        """Test all exceptions inherit from TDRProcessorError."""
        from exceptions import (
            TDRProcessorError, ExcelParsingError, VesselInfoMissingError,
            DatabaseError, ValidationError, ProcessingError
        )
        assert issubclass(ExcelParsingError, TDRProcessorError)
        assert issubclass(VesselInfoMissingError, TDRProcessorError)
        assert issubclass(DatabaseError, TDRProcessorError)
        assert issubclass(ValidationError, TDRProcessorError)
        assert issubclass(ProcessingError, TDRProcessorError)
