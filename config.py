# config.py - Refactored with Dataclasses (v3.0)
# TDR Processor Configuration - Type-safe with dataclasses

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

# ============================================================================
# ENUMS - For strongly-typed categorical values
# ============================================================================

class OperationType(Enum):
    """Container operation types"""
    DISCHARGE = "Discharge"
    LOADING = "Loading"
    SHIFTING_DIS = "Shifting Dis"
    SHIFTING_LOAD = "Shifting Load"
    TOTAL_DIS = "Total Dis"
    TOTAL_LOAD = "Total Load"
    GRAND_TOTAL = "Grand Total"

class ContainerSize(Enum):
    """Standard container sizes"""
    SIZE_20 = "20"
    SIZE_40 = "40"
    SIZE_45 = "45"

class ContainerCategory(Enum):
    """Container categories"""
    FULL_DC = "Full DC"
    EMPTY_DC = "Empty DC"
    FULL_RF = "Full RF"
    EMPTY_RF = "Empty RF"

class ErrorType(Enum):
    """Delay error classification types"""
    TERMINAL_CONVENIENCE = "Terminal Convenience"
    NON_TERMINAL_CONVENIENCE = "Non-Terminal Convenience"
    FORCE_MAJEURE = "Other/Force Majeure"
    UNKNOWN = "Unknown"

# ============================================================================
# DATACLASSES - Organized configuration sections
# ============================================================================

@dataclass
class ApplicationConfig:
    """Application-level settings"""
    TITLE: str = "TDR Processor"
    VERSION: str = "3.0.0"  # v3.0.0 - Production Release
    LOG_FILENAME: str = "tdr_processor.log"
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

@dataclass
class DateTimeFormatConfig:
    """DateTime formatting configuration"""
    DATETIME_FORMAT_OUT: str = "%d/%m/%Y %H:%M"
    DATE_FORMAT_OUT: str = "%d/%m/%Y"
    TIME_FORMAT_OUT: str = "%H:%M"

@dataclass
class SheetNamesConfig:
    """Sheet names for input and output Excel files"""
    # Input sheets
    VESSEL_SUMMARY: str = "Vessel Summary"
    QC_PRODUCTIVITY: str = "QC Productivity Details"
    DELAY_DETAILS: str = "Delay Details"
    CONTAINER_SUMMARY_WIDE: str = "ContainerSummaryWide"
    CONTAINER_SUMMARY_LONG: str = "ContainerDetailsLong"
    CONTAINER_SUMMARY_LONG_ERROR: str = "ContainerDetailsLongError"
    QC_OPERATOR_PRODUCTIVITY: str = "QC Operator Productivity"

@dataclass
class OutputFilesConfig:
    """Output file names"""
    VESSEL_MASTER: str = "master_vessel_summary.xlsx"
    QC_MASTER: str = "master_qc_productivity.xlsx"
    DELAY_MASTER: str = "master_delay_details.xlsx"
    CONTAINER_MASTER_WIDE: str = "master_container_details_wide.xlsx"
    CONTAINER_MASTER_LONG: str = "master_container_details_long.xlsx"
    CONTAINER_MASTER_LONG_ERROR: str = "master_container_details_long_ERR.xlsx"
    QC_OPERATOR_MASTER: str = "master_qc_operator_productivity.xlsx"

@dataclass
class SearchParametersConfig:
    """General parameters for searching in Excel sheets"""
    MAX_ROWS_DEFAULT: int = 70
    PARTIAL_MATCH_DEFAULT: bool = True

@dataclass
class VesselInfoConfig:
    """Vessel information extraction configuration"""
    MAX_SEARCH_ROWS: int = 35
    LABELS: Dict[str, str] = field(default_factory=lambda: {
        "Vessel Name": "Vessel:", "Voyage": "Voyage:", "Operator": "Operator:",
        "Berth": "Berth:", "Report Date_str": "Date:", "ETB_str": "ETB:",
        "ATB_str": "ATB:", "ETD_str": "ETD:", "Gangway Secured_str": "Gangway secured:",
        "Commenced Discharge_str": "Commenced discharge:",
        "Completed Discharge_str": "Completed discharge:",
        "Commenced Loading_str": "Commenced loading:",
        "Completed Loading_str": "Completed loading:",
        "Lashing Finished_str": "Lashing finished:", "ATD_str": "ATD:"
    })
    
    LABEL_COL_LETTERS: Dict[str, str] = field(default_factory=lambda: {
        "Vessel Name": 'B', "Voyage": 'B', "Operator": 'B', "Berth": 'H',
        "Report Date_str": 'L', "ETB_str": 'H', "ATB_str": 'L', "ETD_str": 'H',
        "Gangway Secured_str": 'L', "Commenced Discharge_str": 'B',
        "Completed Discharge_str": 'B', "Commenced Loading_str": 'B',
        "Completed Loading_str": 'B', "Lashing Finished_str": 'B', "ATD_str": 'B'
    })
    
    VALUE_COL_LETTERS: Dict[str, str] = field(default_factory=lambda: {
        "Vessel Name": 'E', "Voyage": 'E', "Operator": 'E', "Berth": 'I',
        "Report Date_str": 'O', "ETB_str": 'I', "ATB_str": 'O', "ETD_str": 'I',
        "Gangway Secured_str": 'O', "Commenced Discharge_str": 'E',
        "Completed Discharge_str": 'E', "Commenced Loading_str": 'E',
        "Completed Loading_str": 'E', "Lashing Finished_str": 'E', "ATD_str": 'E'
    })
    
    BREAK_TIME_SUMMARY_LABEL: str = "Break Time"
    BREAK_TIME_DISCHARGE_COL: str = 'E'
    BREAK_TIME_LOADING_COL: str = 'K'

@dataclass
class QCProductivityConfig:
    """QC productivity extraction configuration"""
    CRANES_HEADER: str = "CRANES PRODUCTIVITY"
    MAX_SEARCH_ROWS: int = 50
    HEADER_ROW_1_OFFSET: int = 1
    HEADER_ROW_2_OFFSET: int = 2
    DATA_START_FROM_H1: int = 2
    DATA_START_FROM_H2: int = 1
    
    HEADER_VARIANTS: Dict[str, List[str]] = field(default_factory=lambda: {
        "qc_no": ["qc no.", "qcno", "qc"],
        "start_time": ["start", "start time"],
        "end_time": ["end", "end time"],
        "gross_working_reported": ["gross working", "grosswork", "gross working (hrs)"],
        "delay_times_reported": ["delay times", "delay time", "delay times (hrs)"],
        "net_working_reported": ["net working", "network", "net working (hrs)"],
        "total_conts_qc_reported": ["total (conts)", "total conts", "total", "conts"],
        "gross_moves_h_reported": ["gross moves/h", "grossmoves/h", "gross m/h"],
        "net_moves_h_reported": ["net moves/h", "netmoves/h", "net m/h"],
        "dis_conts": ["dis.", "discharge", "disch"],
        "load_conts": ["load", "loading"],
        "shifting_conts": ["shifting", "shift"]
    })
    
    IDENTIFIERS: List[str] = field(default_factory=lambda: ["GW", "GC"])

@dataclass
class DelayDetailsConfig:
    """Delay details extraction configuration"""
    TIMES_RECORD_LABEL: str = "* Delay times record:"
    QC_NO_LABEL: str = "QC No."
    MAX_SEARCH_ROWS: int = 60
    HEADER_ROW_OFFSET: int = 1
    QC_IDENTIFIERS: List[str] = field(default_factory=lambda: ["GW", "GC"])
    
    QC_COLUMN_BLOCKS: List[Dict[str, str]] = field(default_factory=lambda: [
        {"name_col_letter": 'C', "from_col_letter": 'C', "to_col_letter": 'D', 
         "hours_col_letter": 'E', "error_remark_col_letter": 'F'},
        {"name_col_letter": 'G', "from_col_letter": 'G', "to_col_letter": 'H', 
         "hours_col_letter": 'I', "error_remark_col_letter": 'J'},
        {"name_col_letter": 'K', "from_col_letter": 'K', "to_col_letter": 'L', 
         "hours_col_letter": 'N', "error_remark_col_letter": 'O'}
    ])
    
    STOP_CATEGORIES: Dict[str, Dict] = field(default_factory=lambda: {
        "Stop-1": {"label": "Stop - 1", "rows_to_check": 4, 
                   "sub_header_texts": ["from", "to", "hours"]},
        "Stop-2": {"label": "Stop - 2", "rows_to_check": 4, 
                   "sub_header_texts": ["from", "to", "hours"]},
        "Stop-3": {"label": "Stop - 3", "rows_to_check": 4, 
                   "sub_header_texts": ["from", "to", "hours"]},
    })
    
    MAX_SEARCH_ROWS_STOP_LABEL: int = 20
    TOTAL_STOP_LABEL: str = "total stop"
    DURATION_MISMATCH_THRESHOLD: float = 0.02

@dataclass
class ContainerDetailsConfig:
    """Container details extraction configuration"""
    DISCHARGE_LOAD_SUMMARY_LABEL: str = "DISCHARGE/LOAD SUMMARY"
    MAX_SEARCH_ROWS: int = 50
    CATEGORY_ROW_OFFSET: int = 1
    SIZE_ROW_OFFSET: int = 2
    DATA_START_ROW_OFFSET: int = 3
    MAX_DATA_ROWS: int = 30
    
    DEFAULT_CATEGORY_BY_COL: Dict[str, str] = field(default_factory=lambda: {
        'C': "Full DC", 'F': "Empty DC", 'I': "Full RF", 'K': "Empty RF"
    })
    
    CATEGORIES_ORDER: List[str] = field(default_factory=lambda: 
        ["Full DC", "Empty DC", "Full RF", "Empty RF"])
    SIZES_ORDER: List[str] = field(default_factory=lambda: ["20", "40", "45"])
    
    CATEGORY_COL_RANGES: List[tuple] = field(default_factory=lambda: [
        ('C', 'E', "Full DC"),
        ('F', 'H', "Empty DC"),
        ('I', 'J', "Full RF"),
        ('K', 'M', "Empty RF")
    ])
    
    TOTAL_CONTS_COL: str = 'N'
    TEUS_COL: str = 'O'
    GRAND_TOTAL_LABEL: str = "Grand Total"

@dataclass
class DelayErrorConfig:
    """Delay error classification configuration"""
    ERROR_CODE_CLASSIFICATION: Dict[str, List[str]] = field(default_factory=lambda: {
        "Terminal Convenience": list('abcdefgh'),
        "Non-Terminal Convenience": list('ijklmn')
    })
    FORCE_MAJEURE_KEYWORDS: List[str] = field(default_factory=lambda: 
        ["weather", "bất khả kháng", "thời tiết"])
    UNKNOWN_TYPE: str = "Unknown"

@dataclass
class SMTPConfig:
    """SMTP configuration loaded from environment variables.
    
    Environment variables:
    - TDR_SMTP_SERVER: SMTP server hostname (default: localhost)
    - TDR_SMTP_PORT: SMTP server port (default: 587)
    - TDR_SMTP_USER: SMTP username
    - TDR_SMTP_PASSWORD: SMTP password
    - TDR_SMTP_USE_TLS: Use TLS (true/false, default: true)
    - TDR_SMTP_TIMEOUT: Connection timeout in seconds (default: 10)
    """
    server: str = "localhost"
    port: int = 587
    username: str = ""
    password: str = ""
    use_tls: bool = True
    timeout: int = 10
    
    @classmethod
    def from_env(cls) -> 'SMTPConfig':
        """Load SMTP configuration from environment variables.
        
        Returns:
            SMTPConfig: Configuration loaded from environment or defaults
        """
        return cls(
            server=os.getenv('TDR_SMTP_SERVER', 'localhost'),
            port=int(os.getenv('TDR_SMTP_PORT', '587')),
            username=os.getenv('TDR_SMTP_USER', ''),
            password=os.getenv('TDR_SMTP_PASSWORD', ''),
            use_tls=os.getenv('TDR_SMTP_USE_TLS', 'true').lower() == 'true',
            timeout=int(os.getenv('TDR_SMTP_TIMEOUT', '10'))
        )

@dataclass
class EmailConfig:
    """Email configuration loaded from environment variables.
    
    Environment variables:
    - TDR_EMAIL_SENDER: Sender email address
    - TDR_EMAIL_RECIPIENTS: Recipient emails (comma-separated)
    - TDR_EMAIL_ENABLED: Enable email notifications (true/false)
    """
    sender: str = ""
    recipients: List[str] = field(default_factory=list)
    enabled: bool = False
    
    @classmethod
    def from_env(cls) -> 'EmailConfig':
        """Load email configuration from environment variables.
        
        Returns:
            EmailConfig: Configuration loaded from environment or defaults
        """
        recipients_str = os.getenv('TDR_EMAIL_RECIPIENTS', '')
        recipients = [r.strip() for r in recipients_str.split(',') if r.strip()]
        
        return cls(
            sender=os.getenv('TDR_EMAIL_SENDER', ''),
            recipients=recipients,
            enabled=os.getenv('TDR_EMAIL_ENABLED', 'false').lower() == 'true'
        )

# ============================================================================
# SINGLETON CONFIGURATION INSTANCE
# ============================================================================

@dataclass
class TDRConfig:
    """Complete TDR Processor configuration"""
    app: ApplicationConfig = field(default_factory=ApplicationConfig)
    datetime_formats: DateTimeFormatConfig = field(default_factory=DateTimeFormatConfig)
    sheets: SheetNamesConfig = field(default_factory=SheetNamesConfig)
    output_files: OutputFilesConfig = field(default_factory=OutputFilesConfig)
    search_params: SearchParametersConfig = field(default_factory=SearchParametersConfig)
    vessel_info: VesselInfoConfig = field(default_factory=VesselInfoConfig)
    qc_productivity: QCProductivityConfig = field(default_factory=QCProductivityConfig)
    delay_details: DelayDetailsConfig = field(default_factory=DelayDetailsConfig)
    container_details: ContainerDetailsConfig = field(default_factory=ContainerDetailsConfig)
    delay_error: DelayErrorConfig = field(default_factory=DelayErrorConfig)
    smtp: SMTPConfig = field(default_factory=SMTPConfig)  # New: SMTP configuration
    email: EmailConfig = field(default_factory=EmailConfig)  # New: Email configuration

# ============================================================================
# ENVIRONMENT VARIABLE LOADING FUNCTION (NEW - Phase 3.1D)
# ============================================================================

def load_environment_config() -> None:
    """Load and apply environment variable configuration.

    This function should be called early in application initialization
    to override default configuration with environment variables.
    Also updates backward-compatibility module-level constants so that
    code importing LOG_LEVEL etc. directly gets the env-var values.

    Supported environment variables:
    - TDR_SMTP_SERVER: SMTP server hostname
    - TDR_SMTP_PORT: SMTP server port
    - TDR_SMTP_USER: SMTP username
    - TDR_SMTP_PASSWORD: SMTP password
    - TDR_SMTP_USE_TLS: Use TLS (true/false)
    - TDR_SMTP_TIMEOUT: Connection timeout
    - TDR_EMAIL_SENDER: Sender email address
    - TDR_EMAIL_RECIPIENTS: Recipient emails (comma-separated)
    - TDR_EMAIL_ENABLED: Enable email notifications
    - TDR_LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    global _config, LOG_LEVEL

    # Load SMTP configuration from environment
    smtp_config = SMTPConfig.from_env()
    _config.smtp = smtp_config

    # Load email configuration from environment
    email_config = EmailConfig.from_env()
    _config.email = email_config

    # Load log level from environment if specified and update backward-compat constant
    log_level = os.getenv('TDR_LOG_LEVEL')
    if log_level:
        _config.app.LOG_LEVEL = log_level
        LOG_LEVEL = log_level  # Keep backward-compat constant in sync

# ============================================================================
# BACKWARD COMPATIBILITY LAYER
# ============================================================================
# The following section maintains backward compatibility with existing code
# that imports constants directly. This allows gradual migration.

_config = TDRConfig()

# Application Settings
APP_TITLE = _config.app.TITLE
APP_VERSION = _config.app.VERSION
LOG_FILENAME = _config.app.LOG_FILENAME
LOG_LEVEL = _config.app.LOG_LEVEL
LOG_FORMAT = _config.app.LOG_FORMAT
LOG_DATE_FORMAT = _config.app.LOG_DATE_FORMAT

# DateTime Formats
DATETIME_FORMAT_OUT = _config.datetime_formats.DATETIME_FORMAT_OUT
DATE_FORMAT_OUT = _config.datetime_formats.DATE_FORMAT_OUT
TIME_FORMAT_OUT = _config.datetime_formats.TIME_FORMAT_OUT

# Sheet Names
VESSEL_SUMMARY_SHEET = _config.sheets.VESSEL_SUMMARY
QC_PRODUCTIVITY_SHEET = _config.sheets.QC_PRODUCTIVITY
DELAY_DETAILS_SHEET = _config.sheets.DELAY_DETAILS
CONTAINER_SUMMARY_WIDE_SHEET = _config.sheets.CONTAINER_SUMMARY_WIDE
CONTAINER_SUMMARY_LONG_SHEET = _config.sheets.CONTAINER_SUMMARY_LONG
CONTAINER_SUMMARY_LONG_ERROR_SHEET = _config.sheets.CONTAINER_SUMMARY_LONG_ERROR
QC_OPERATOR_PRODUCTIVITY_SHEET = _config.sheets.QC_OPERATOR_PRODUCTIVITY

# Output Files
VESSEL_MASTER_FILE = _config.output_files.VESSEL_MASTER
QC_MASTER_FILE = _config.output_files.QC_MASTER
DELAY_MASTER_FILE = _config.output_files.DELAY_MASTER
CONTAINER_MASTER_WIDE_FILE = _config.output_files.CONTAINER_MASTER_WIDE
CONTAINER_MASTER_LONG_FILE = _config.output_files.CONTAINER_MASTER_LONG
CONTAINER_MASTER_LONG_ERROR_FILE = _config.output_files.CONTAINER_MASTER_LONG_ERROR
QC_OPERATOR_MASTER_FILE = _config.output_files.QC_OPERATOR_MASTER

# Search Parameters
MAX_SEARCH_ROWS_DEFAULT = _config.search_params.MAX_ROWS_DEFAULT
PARTIAL_MATCH_DEFAULT = _config.search_params.PARTIAL_MATCH_DEFAULT

# Vessel Info
MAX_SEARCH_ROWS_VESSEL_INFO = _config.vessel_info.MAX_SEARCH_ROWS
VESSEL_INFO_LABELS = _config.vessel_info.LABELS
VESSEL_INFO_LABEL_COL_LETTERS = _config.vessel_info.LABEL_COL_LETTERS
VESSEL_INFO_VALUE_COL_LETTERS = _config.vessel_info.VALUE_COL_LETTERS
LABEL_BREAK_TIME_SUMMARY_VESSEL = _config.vessel_info.BREAK_TIME_SUMMARY_LABEL
BREAK_TIME_DISCHARGE_COL_LETTER = _config.vessel_info.BREAK_TIME_DISCHARGE_COL
BREAK_TIME_LOADING_COL_LETTER = _config.vessel_info.BREAK_TIME_LOADING_COL

# QC Productivity
LABEL_CRANES_PRODUCTIVITY = _config.qc_productivity.CRANES_HEADER
MAX_SEARCH_ROWS_QC_HEADER = _config.qc_productivity.MAX_SEARCH_ROWS
QC_HEADER_ROW_1_OFFSET = _config.qc_productivity.HEADER_ROW_1_OFFSET
QC_HEADER_ROW_2_OFFSET = _config.qc_productivity.HEADER_ROW_2_OFFSET
QC_DATA_START_ROW_OFFSET_FROM_H1 = _config.qc_productivity.DATA_START_FROM_H1
QC_DATA_START_ROW_OFFSET_FROM_H2 = _config.qc_productivity.DATA_START_FROM_H2
QC_PRODUCTIVITY_HEADER_VARIANTS = _config.qc_productivity.HEADER_VARIANTS
QC_IDENTIFIERS_IN_DATA = _config.qc_productivity.IDENTIFIERS

# Delay Details
LABEL_DELAY_TIMES_RECORD = _config.delay_details.TIMES_RECORD_LABEL
LABEL_QC_NO_IN_DELAY_HEADER = _config.delay_details.QC_NO_LABEL
MAX_SEARCH_ROWS_DELAY_HEADER = _config.delay_details.MAX_SEARCH_ROWS
DELAY_QC_HEADER_ROW_OFFSET = _config.delay_details.HEADER_ROW_OFFSET
DELAY_QC_IDENTIFIERS_IN_HEADER = _config.delay_details.QC_IDENTIFIERS
DELAY_QC_COLUMN_BLOCKS = _config.delay_details.QC_COLUMN_BLOCKS
DELAY_STOP_CATEGORIES = _config.delay_details.STOP_CATEGORIES
MAX_SEARCH_ROWS_DELAY_STOP_LABEL = _config.delay_details.MAX_SEARCH_ROWS_STOP_LABEL
LABEL_TOTAL_STOP_IN_DELAY_TABLE = _config.delay_details.TOTAL_STOP_LABEL
DELAY_ERROR_CODE_CLASSIFICATION = _config.delay_error.ERROR_CODE_CLASSIFICATION
DELAY_ERROR_FORCE_MAJEURE_KEYWORDS = _config.delay_error.FORCE_MAJEURE_KEYWORDS
DELAY_ERROR_UNKNOWN_TYPE = _config.delay_error.UNKNOWN_TYPE
DELAY_DURATION_MISMATCH_THRESHOLD = _config.delay_details.DURATION_MISMATCH_THRESHOLD

# Container Details
LABEL_DISCHARGE_LOAD_SUMMARY = _config.container_details.DISCHARGE_LOAD_SUMMARY_LABEL
MAX_SEARCH_ROWS_CONTAINER_HEADER = _config.container_details.MAX_SEARCH_ROWS
CONTAINER_SUMMARY_CAT_ROW_OFFSET = _config.container_details.CATEGORY_ROW_OFFSET
CONTAINER_SUMMARY_SIZE_ROW_OFFSET = _config.container_details.SIZE_ROW_OFFSET
CONTAINER_SUMMARY_DATA_START_ROW_OFFSET = _config.container_details.DATA_START_ROW_OFFSET
MAX_ROWS_TO_READ_CONTAINER_DATA = _config.container_details.MAX_DATA_ROWS
CONTAINER_DEFAULT_CATEGORY_NAMES_BY_START_COL = _config.container_details.DEFAULT_CATEGORY_BY_COL
CONTAINER_CATEGORIES_IN_ORDER = _config.container_details.CATEGORIES_ORDER
CONTAINER_SIZES_IN_ORDER = _config.container_details.SIZES_ORDER
CONTAINER_CATEGORY_COL_RANGES_DEF = _config.container_details.CATEGORY_COL_RANGES
CONTAINER_SUMMARY_ROW_TOTAL_CONTS_COL_LETTER = _config.container_details.TOTAL_CONTS_COL
CONTAINER_SUMMARY_ROW_TEUS_COL_LETTER = _config.container_details.TEUS_COL
LABEL_GRAND_TOTAL_IN_CONTAINER_SUMMARY = _config.container_details.GRAND_TOTAL_LABEL

# Operation Types
OP_DISCHARGE = OperationType.DISCHARGE.value
OP_LOADING = OperationType.LOADING.value
OP_SHIFTING_DIS = OperationType.SHIFTING_DIS.value
OP_SHIFTING_LOAD = OperationType.SHIFTING_LOAD.value
OP_TOTAL_DIS = OperationType.TOTAL_DIS.value
OP_TOTAL_LOAD = OperationType.TOTAL_LOAD.value
OP_GRAND_TOTAL = OperationType.GRAND_TOTAL.value
PORT_ALL = "All"

# Container Wide Format Configuration (used by report_processor.py for pivot)
CONTAINER_WIDE_BASE_COLS = [
    'Filename', 'Vessel Name', 'Voyage', 'OperationType', 'Port'
]
CONTAINER_WIDE_TOTAL_COLS_SUFFIX = ['Total Conts', 'Total TEUs']

# Operation type sort order for container wide format
OPERATION_TYPE_SORT_ORDER = {
    OperationType.DISCHARGE.value: 1,
    OperationType.LOADING.value: 2,
    OperationType.SHIFTING_DIS.value: 3,
    OperationType.SHIFTING_LOAD.value: 4,
    OperationType.TOTAL_DIS.value: 5,
    OperationType.TOTAL_LOAD.value: 6,
    OperationType.GRAND_TOTAL.value: 7,
}

# Output Column Mapping & Order (for DataFrame rename and column selection)
VESSEL_COL_RENAMES_OUTPUT = {}  # Empty mapping - no renaming needed
VESSEL_COLS_OUTPUT_ORDER = [
    'Filename', 'Vessel Name', 'Voyage', 'Operator', 'Berth', 'Report Date', 'ATB', 'ATD',
    'Gangway Secured', 'Commenced Discharge', 'Commenced Loading', 'Completed Discharge',
    'Completed Loading', 'All Operations Completed', 'Break time (hrs)', 'Discharge (hrs)',
    'Loading (hrs)', 'Total working (hrs)', 'Portstay (hrs)', 'Gross Working (hrs)', 
    'Net Working (hrs)', 'Grand Total Conts', 'Grand Total TEUs',
    'Vessel Moves/Portstay Hour', 'Vessel Moves/Gross Hour', 'Vessel Moves/Net Hour'
]

VESSEL_DATETIME_COLS_FORMAT = ['Report Date', 'ATB', 'ATD', 'Gangway Secured', 'Commenced Discharge', 
                                'Commenced Loading', 'Completed Discharge', 'Completed Loading', 
                                'All Operations Completed']

QC_COL_RENAMES_OUTPUT = {}  # Empty mapping - no renaming needed
QC_COLS_OUTPUT_ORDER = [
    'Filename', 'Vessel Name', 'Voyage', 'ATB', 'ATD', 'QC No.', 'Start Time', 'End Time',
    'Gross working (hrs)', 'Delay times (hrs)', 'Net working (hrs)', 'Discharge Conts',
    'Load Conts', 'Shifting Conts', 'Total Conts', 'Gross moves/h', 'Net moves/h'
]

QC_TIME_COLS_FORMAT = ['Start Time', 'End Time']

QC_OPERATOR_COL_RENAMES_OUTPUT = {}  # Empty mapping - no renaming needed

DELAY_DETAILS_COLS_OUTPUT_ORDER = [
    'Filename', 'Vessel Name', 'Voyage', 'QC No.', 'Stop Category',
    'From Time', 'To Time', 'Duration (hrs)', 'Error Code', 'Error Type', 'Remark'
]

DELAY_DATETIME_COLS_FORMAT = ['From Time', 'To Time']

# ============================================================================
# PUBLIC API
# ============================================================================

def get_config() -> TDRConfig:
    """Get the complete TDR configuration object for new code"""
    return _config

__all__ = [
    # Dataclasses
    'TDRConfig', 'ApplicationConfig', 'DateTimeFormatConfig',
    'SheetNamesConfig', 'OutputFilesConfig', 'SearchParametersConfig',
    'VesselInfoConfig', 'QCProductivityConfig', 'DelayDetailsConfig',
    'ContainerDetailsConfig', 'DelayErrorConfig', 'SMTPConfig', 'EmailConfig',
    # Enums
    'OperationType', 'ContainerSize', 'ContainerCategory', 'ErrorType',
    # Functions
    'get_config', 'load_environment_config',
    # Backward compatibility constants (all old constants)
    'APP_TITLE', 'APP_VERSION', 'LOG_FILENAME', 'LOG_LEVEL', 'LOG_FORMAT',
    'LOG_DATE_FORMAT', 'DATETIME_FORMAT_OUT', 'DATE_FORMAT_OUT', 'TIME_FORMAT_OUT',
    'VESSEL_SUMMARY_SHEET', 'QC_PRODUCTIVITY_SHEET', 'DELAY_DETAILS_SHEET',
    'CONTAINER_SUMMARY_WIDE_SHEET', 'CONTAINER_SUMMARY_LONG_SHEET',
    'CONTAINER_SUMMARY_LONG_ERROR_SHEET', 'QC_OPERATOR_PRODUCTIVITY_SHEET',
    'VESSEL_MASTER_FILE', 'QC_MASTER_FILE', 'DELAY_MASTER_FILE',
    'CONTAINER_MASTER_WIDE_FILE', 'CONTAINER_MASTER_LONG_FILE',
    'CONTAINER_MASTER_LONG_ERROR_FILE', 'QC_OPERATOR_MASTER_FILE',
    'MAX_SEARCH_ROWS_DEFAULT', 'PARTIAL_MATCH_DEFAULT',
    'MAX_SEARCH_ROWS_VESSEL_INFO', 'VESSEL_INFO_LABELS',
    'VESSEL_INFO_LABEL_COL_LETTERS', 'VESSEL_INFO_VALUE_COL_LETTERS',
    'LABEL_BREAK_TIME_SUMMARY_VESSEL', 'BREAK_TIME_DISCHARGE_COL_LETTER',
    'BREAK_TIME_LOADING_COL_LETTER', 'LABEL_CRANES_PRODUCTIVITY',
    'MAX_SEARCH_ROWS_QC_HEADER', 'QC_HEADER_ROW_1_OFFSET', 'QC_HEADER_ROW_2_OFFSET',
    'QC_DATA_START_ROW_OFFSET_FROM_H1', 'QC_DATA_START_ROW_OFFSET_FROM_H2',
    'QC_PRODUCTIVITY_HEADER_VARIANTS', 'QC_IDENTIFIERS_IN_DATA',
    'LABEL_DELAY_TIMES_RECORD', 'LABEL_QC_NO_IN_DELAY_HEADER',
    'MAX_SEARCH_ROWS_DELAY_HEADER', 'DELAY_QC_HEADER_ROW_OFFSET',
    'DELAY_QC_IDENTIFIERS_IN_HEADER', 'DELAY_QC_COLUMN_BLOCKS',
    'DELAY_STOP_CATEGORIES', 'MAX_SEARCH_ROWS_DELAY_STOP_LABEL',
    'LABEL_TOTAL_STOP_IN_DELAY_TABLE', 'DELAY_ERROR_CODE_CLASSIFICATION',
    'DELAY_ERROR_FORCE_MAJEURE_KEYWORDS', 'DELAY_ERROR_UNKNOWN_TYPE',
    'DELAY_DURATION_MISMATCH_THRESHOLD', 'LABEL_DISCHARGE_LOAD_SUMMARY',
    'MAX_SEARCH_ROWS_CONTAINER_HEADER', 'CONTAINER_SUMMARY_CAT_ROW_OFFSET',
    'CONTAINER_SUMMARY_SIZE_ROW_OFFSET', 'CONTAINER_SUMMARY_DATA_START_ROW_OFFSET',
    'MAX_ROWS_TO_READ_CONTAINER_DATA', 'CONTAINER_DEFAULT_CATEGORY_NAMES_BY_START_COL',
    'CONTAINER_CATEGORIES_IN_ORDER', 'CONTAINER_SIZES_IN_ORDER',
    'CONTAINER_CATEGORY_COL_RANGES_DEF', 'CONTAINER_SUMMARY_ROW_TOTAL_CONTS_COL_LETTER',
    'CONTAINER_SUMMARY_ROW_TEUS_COL_LETTER', 'LABEL_GRAND_TOTAL_IN_CONTAINER_SUMMARY',
    'OP_DISCHARGE', 'OP_LOADING', 'OP_SHIFTING_DIS', 'OP_SHIFTING_LOAD',
    'OP_TOTAL_DIS', 'OP_TOTAL_LOAD', 'OP_GRAND_TOTAL', 'PORT_ALL',
    'VESSEL_COL_RENAMES_OUTPUT', 'VESSEL_COLS_OUTPUT_ORDER', 'VESSEL_DATETIME_COLS_FORMAT',
    'QC_COL_RENAMES_OUTPUT', 'QC_COLS_OUTPUT_ORDER', 'QC_TIME_COLS_FORMAT',
    'QC_OPERATOR_COL_RENAMES_OUTPUT', 'DELAY_DETAILS_COLS_OUTPUT_ORDER', 'DELAY_DATETIME_COLS_FORMAT'
]
