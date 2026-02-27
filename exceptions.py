# exceptions.py
"""
Custom exception hierarchy for TDR Processor.

Provides structured exceptions that carry context about what went wrong,
making error handling and logging more precise than generic exceptions.

Usage:
    from exceptions import ExcelParsingError, VesselInfoMissingError

    try:
        extractor.extract_vessel_info()
    except VesselInfoMissingError as e:
        logging.error(f"Missing vessel info in {e.filename}: {e.missing_fields}")
"""
from typing import List, Optional


# ============================================================================
# BASE EXCEPTION
# ============================================================================

class TDRProcessorError(Exception):
    """Base exception for all TDR Processor errors.
    
    All custom exceptions inherit from this class, allowing callers to
    catch all TDR-specific errors with a single except clause.
    """
    def __init__(self, message: str, context: Optional[dict] = None):
        super().__init__(message)
        self.context = context or {}


# ============================================================================
# FILE & I/O EXCEPTIONS
# ============================================================================

class FileProcessingError(TDRProcessorError):
    """Raised when a file cannot be read or processed."""
    def __init__(self, filename: str, reason: str):
        self.filename = filename
        self.reason = reason
        super().__init__(
            f"Cannot process file '{filename}': {reason}",
            context={"filename": filename, "reason": reason}
        )


class ExcelParsingError(FileProcessingError):
    """Raised when an Excel file cannot be parsed (corrupt, wrong format, etc.)."""
    def __init__(self, filename: str, reason: str, sheet_name: Optional[str] = None):
        self.sheet_name = sheet_name
        context_msg = f"sheet '{sheet_name}'" if sheet_name else "file"
        super().__init__(
            filename,
            f"Excel parsing failed for {context_msg}: {reason}"
        )
        self.context["sheet_name"] = sheet_name


class FileLockError(FileProcessingError):
    """Raised when a file is locked by another process (e.g., open in Excel)."""
    def __init__(self, filename: str):
        super().__init__(filename, "File is locked by another process")


class DuplicateFileError(FileProcessingError):
    """Raised when a duplicate TDR file is detected."""
    def __init__(self, filename: str, original_filename: str):
        self.original_filename = original_filename
        super().__init__(
            filename,
            f"Duplicate of '{original_filename}'"
        )
        self.context["original_filename"] = original_filename


# ============================================================================
# DATA EXTRACTION EXCEPTIONS
# ============================================================================

class DataExtractionError(TDRProcessorError):
    """Base class for data extraction failures."""
    def __init__(self, filename: str, section: str, reason: str):
        self.filename = filename
        self.section = section
        self.reason = reason
        super().__init__(
            f"Data extraction failed in '{filename}' [{section}]: {reason}",
            context={"filename": filename, "section": section, "reason": reason}
        )


class VesselInfoMissingError(DataExtractionError):
    """Raised when required vessel information cannot be found in the TDR file."""
    def __init__(self, filename: str, missing_fields: List[str]):
        self.missing_fields = missing_fields
        super().__init__(
            filename,
            "Vessel Summary",
            f"Missing required fields: {', '.join(missing_fields)}"
        )
        self.context["missing_fields"] = missing_fields


class QCDataMissingError(DataExtractionError):
    """Raised when QC productivity section cannot be found."""
    def __init__(self, filename: str, reason: str = "QC productivity header not found"):
        super().__init__(filename, "QC Productivity", reason)


class DelayDataMissingError(DataExtractionError):
    """Raised when delay details section cannot be found."""
    def __init__(self, filename: str, reason: str = "Delay times record not found"):
        super().__init__(filename, "Delay Details", reason)


class ContainerDataMissingError(DataExtractionError):
    """Raised when container summary section cannot be found."""
    def __init__(self, filename: str, reason: str = "Discharge/Load summary not found"):
        super().__init__(filename, "Container Details", reason)


class HeaderNotFoundError(DataExtractionError):
    """Raised when a required header label cannot be located in the worksheet."""
    def __init__(self, filename: str, header_label: str, section: str):
        self.header_label = header_label
        super().__init__(
            filename,
            section,
            f"Header label '{header_label}' not found in worksheet"
        )
        self.context["header_label"] = header_label


# ============================================================================
# VALIDATION EXCEPTIONS
# ============================================================================

class ValidationError(TDRProcessorError):
    """Raised when data fails validation checks."""
    def __init__(self, field: str, value, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(
            f"Validation failed for field '{field}' (value={value!r}): {reason}",
            context={"field": field, "value": str(value), "reason": reason}
        )


class InvalidFilePathError(ValidationError):
    """Raised when a file path fails security validation (e.g., path traversal)."""
    def __init__(self, path: str, reason: str):
        super().__init__("file_path", path, reason)


class InvalidEmailError(ValidationError):
    """Raised when an email address fails format validation."""
    def __init__(self, email: str, reason: str):
        super().__init__("email", email, reason)


class InvalidSMTPConfigError(ValidationError):
    """Raised when SMTP configuration is invalid."""
    def __init__(self, field: str, value, reason: str):
        super().__init__(f"smtp.{field}", value, reason)


# ============================================================================
# PROCESSING EXCEPTIONS
# ============================================================================

class ProcessingError(TDRProcessorError):
    """Raised when the processing pipeline encounters an unrecoverable error."""
    def __init__(self, message: str, processed_count: int = 0, failed_count: int = 0):
        self.processed_count = processed_count
        self.failed_count = failed_count
        super().__init__(
            message,
            context={"processed_count": processed_count, "failed_count": failed_count}
        )


class ConcurrentProcessingError(ProcessingError):
    """Raised when processing is already in progress and a concurrent request is made."""
    def __init__(self):
        super().__init__(
            "Processing already in progress. Please wait for the current operation to complete."
        )


class OutputWriteError(TDRProcessorError):
    """Raised when output files cannot be written."""
    def __init__(self, output_path: str, reason: str):
        self.output_path = output_path
        self.reason = reason
        super().__init__(
            f"Cannot write output to '{output_path}': {reason}",
            context={"output_path": output_path, "reason": reason}
        )


# ============================================================================
# DATABASE EXCEPTIONS
# ============================================================================

class DatabaseError(TDRProcessorError):
    """Base class for database-related errors."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when the database cannot be connected to."""
    def __init__(self, db_path: str, reason: str):
        self.db_path = db_path
        super().__init__(
            f"Cannot connect to database '{db_path}': {reason}",
            context={"db_path": db_path, "reason": reason}
        )


class DatabaseWriteError(DatabaseError):
    """Raised when data cannot be written to the database."""
    def __init__(self, table: str, reason: str):
        self.table = table
        super().__init__(
            f"Cannot write to table '{table}': {reason}",
            context={"table": table, "reason": reason}
        )


# ============================================================================
# CONFIGURATION EXCEPTIONS
# ============================================================================

class ConfigurationError(TDRProcessorError):
    """Raised when application configuration is invalid or missing."""
    def __init__(self, config_key: str, reason: str):
        self.config_key = config_key
        super().__init__(
            f"Configuration error for '{config_key}': {reason}",
            context={"config_key": config_key, "reason": reason}
        )


__all__ = [
    # Base
    'TDRProcessorError',
    # File & I/O
    'FileProcessingError', 'ExcelParsingError', 'FileLockError', 'DuplicateFileError',
    # Data Extraction
    'DataExtractionError', 'VesselInfoMissingError', 'QCDataMissingError',
    'DelayDataMissingError', 'ContainerDataMissingError', 'HeaderNotFoundError',
    # Validation
    'ValidationError', 'InvalidFilePathError', 'InvalidEmailError', 'InvalidSMTPConfigError',
    # Processing
    'ProcessingError', 'ConcurrentProcessingError', 'OutputWriteError',
    # Database
    'DatabaseError', 'DatabaseConnectionError', 'DatabaseWriteError',
    # Configuration
    'ConfigurationError',
]
