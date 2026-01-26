# data_schema.py
"""
Data Model Schema Definitions for TDR Processor.

Provides standardized schema definitions for all output data:
- Vessel Summary
- QC Productivity  
- QC Operator Productivity
- Delay Events
- Container Details

Features:
- Schema versioning
- Column type definitions
- Validation rules
- Metric calculations (single source of truth)
- Normalization rules

Usage:
    from data_schema import SCHEMAS, validate_dataframe, normalize_qc_name
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
import pandas as pd
import logging

# Schema version - increment when changing column names or calculations
SCHEMA_VERSION = "3.0.0"


class DataType(Enum):
    """Data types for schema columns."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DATETIME = "datetime"
    BOOLEAN = "boolean"


class ErrorType(Enum):
    """Standardized error types for delay classification."""
    TERMINAL_CONVENIENCE = "Terminal Convenience"          # d - do cảng
    NON_TERMINAL_CONVENIENCE = "Non-Terminal Convenience"  # i - không do cảng (vessel, weather, etc)
    MAINTENANCE = "Maintenance"                             # m - bảo trì
    UNKNOWN = "Unknown"


@dataclass
class ColumnSchema:
    """Schema definition for a single column."""
    name: str
    data_type: DataType
    nullable: bool = True
    description: str = ""
    normalized_name: Optional[str] = None  # Alternative names to map from


@dataclass 
class TableSchema:
    """Schema definition for a data table."""
    name: str
    description: str
    columns: List[ColumnSchema]
    primary_key: List[str] = field(default_factory=list)
    
    def get_column_names(self) -> List[str]:
        """Get list of column names in order."""
        return [col.name for col in self.columns]
    
    def get_required_columns(self) -> List[str]:
        """Get list of non-nullable columns."""
        return [col.name for col in self.columns if not col.nullable]


# ============================================================================
# SCHEMA DEFINITIONS
# ============================================================================

VESSEL_SUMMARY_SCHEMA = TableSchema(
    name="vessel_summary",
    description="Summary data for each vessel visit",
    primary_key=["Filename"],
    columns=[
        ColumnSchema("Filename", DataType.STRING, nullable=False, description="Source TDR filename"),
        ColumnSchema("Vessel Name", DataType.STRING, nullable=False, description="Vessel name"),
        ColumnSchema("Voyage", DataType.STRING, nullable=False, description="Voyage number"),
        ColumnSchema("Operator", DataType.STRING, nullable=True, description="Shipping line operator"),
        ColumnSchema("Berth", DataType.STRING, nullable=True, description="Berth location"),
        ColumnSchema("ATB", DataType.DATETIME, nullable=True, description="Actual Time of Berthing"),
        ColumnSchema("ATD", DataType.DATETIME, nullable=True, description="Actual Time of Departure"),
        ColumnSchema("Report Date", DataType.DATETIME, nullable=True, description="Report generation date"),
        ColumnSchema("Portstay (hrs)", DataType.FLOAT, nullable=True, description="Total time at berth (ATD - ATB)"),
        ColumnSchema("Gross Working (hrs)", DataType.FLOAT, nullable=True, description="Total working time including delays"),
        ColumnSchema("Net Working (hrs)", DataType.FLOAT, nullable=True, description="Working time excluding non-port delays"),
        ColumnSchema("Grand Total Conts", DataType.INTEGER, nullable=True, description="Total container moves"),
        ColumnSchema("Grand Total TEUs", DataType.FLOAT, nullable=True, description="Total TEU count"),
        ColumnSchema("Vessel Moves/Portstay Hour", DataType.FLOAT, nullable=True, description="Productivity: Conts/Portstay"),
        ColumnSchema("Vessel Moves/Gross Hour", DataType.FLOAT, nullable=True, description="Productivity: Conts/Gross Working"),
        ColumnSchema("Vessel Moves/Net Hour", DataType.FLOAT, nullable=True, description="Productivity: Conts/Net Working"),
    ]
)

QC_PRODUCTIVITY_SCHEMA = TableSchema(
    name="qc_productivity",
    description="Productivity data per QC per vessel",
    primary_key=["Filename", "QC No."],
    columns=[
        ColumnSchema("Filename", DataType.STRING, nullable=False),
        ColumnSchema("Vessel Name", DataType.STRING, nullable=False),
        ColumnSchema("Voyage", DataType.STRING, nullable=False),
        ColumnSchema("QC No.", DataType.STRING, nullable=False, description="Normalized QC identifier (GC01, GW01, etc)"),
        ColumnSchema("Start Time", DataType.DATETIME, nullable=True),
        ColumnSchema("End Time", DataType.DATETIME, nullable=True),
        ColumnSchema("Gross working (hrs)", DataType.FLOAT, nullable=True),
        ColumnSchema("Delay times (hrs)", DataType.FLOAT, nullable=True, description="Total stop/delay time"),
        ColumnSchema("Net working (hrs)", DataType.FLOAT, nullable=True),
        ColumnSchema("Discharge Conts", DataType.INTEGER, nullable=True),
        ColumnSchema("Load Conts", DataType.INTEGER, nullable=True),
        ColumnSchema("Shifting Conts", DataType.INTEGER, nullable=True),
        ColumnSchema("Total Conts", DataType.INTEGER, nullable=True),
        ColumnSchema("Gross moves/h", DataType.FLOAT, nullable=True, description="Total Conts / Gross working"),
        ColumnSchema("Net moves/h", DataType.FLOAT, nullable=True, description="Total Conts / Net working"),
    ]
)

QC_OPERATOR_PRODUCTIVITY_SCHEMA = TableSchema(
    name="qc_operator_productivity",
    description="Operator-adjusted QC productivity (excludes non-operator delays)",
    primary_key=["Filename", "QC No."],
    columns=[
        ColumnSchema("Filename", DataType.STRING, nullable=False),
        ColumnSchema("Vessel Name", DataType.STRING, nullable=False),
        ColumnSchema("Voyage", DataType.STRING, nullable=False),
        ColumnSchema("ATB", DataType.DATETIME, nullable=True),
        ColumnSchema("ATD", DataType.DATETIME, nullable=True),
        ColumnSchema("QC No.", DataType.STRING, nullable=False),
        ColumnSchema("Start Time", DataType.DATETIME, nullable=True),
        ColumnSchema("End Time", DataType.DATETIME, nullable=True),
        ColumnSchema("Gross working (hrs)", DataType.FLOAT, nullable=True),
        ColumnSchema("Total Stop Time (hrs)", DataType.FLOAT, nullable=True, description="Non-operator delay time"),
        ColumnSchema("Net working (hrs)", DataType.FLOAT, nullable=True, description="Gross - operator-responsible delays only"),
        ColumnSchema("Discharge Conts", DataType.INTEGER, nullable=True),
        ColumnSchema("Load Conts", DataType.INTEGER, nullable=True),
        ColumnSchema("Shifting Conts", DataType.INTEGER, nullable=True),
        ColumnSchema("Total Conts", DataType.INTEGER, nullable=True),
        ColumnSchema("Gross moves/h", DataType.FLOAT, nullable=True),
        ColumnSchema("Net moves/h", DataType.FLOAT, nullable=True),
    ]
)

DELAY_EVENTS_SCHEMA = TableSchema(
    name="delay_events",
    description="Individual delay/stop events from delay times record",
    primary_key=["Filename", "QC No.", "From Time"],
    columns=[
        ColumnSchema("Filename", DataType.STRING, nullable=False),
        ColumnSchema("Vessel Name", DataType.STRING, nullable=False),
        ColumnSchema("Voyage", DataType.STRING, nullable=False),
        ColumnSchema("QC No.", DataType.STRING, nullable=False, description="Normalized QC name"),
        ColumnSchema("Stop Category", DataType.STRING, nullable=True, description="Stop-1, Stop-2, Stop-3"),
        ColumnSchema("From Time", DataType.DATETIME, nullable=True, description="Delay start time"),
        ColumnSchema("To Time", DataType.DATETIME, nullable=True, description="Delay end time"),
        ColumnSchema("Duration (hrs)", DataType.FLOAT, nullable=False, description="Delay duration in hours"),
        ColumnSchema("Error Code", DataType.STRING, nullable=True, description="d, i, or m"),
        ColumnSchema("Error Type", DataType.STRING, nullable=True, description="Terminal/Non-Terminal Convenience"),
        ColumnSchema("Remark", DataType.STRING, nullable=True, description="Original remark text"),
    ]
)

CONTAINER_DETAILS_SCHEMA = TableSchema(
    name="container_details",
    description="Container operation details (long format)",
    primary_key=["Filename", "QC No.", "Operation", "Size", "Category"],
    columns=[
        ColumnSchema("Filename", DataType.STRING, nullable=False),
        ColumnSchema("Vessel Name", DataType.STRING, nullable=False),
        ColumnSchema("Voyage", DataType.STRING, nullable=False),
        ColumnSchema("QC No.", DataType.STRING, nullable=False),
        ColumnSchema("Operation", DataType.STRING, nullable=False, description="Discharge/Load/Shifting"),
        ColumnSchema("Size", DataType.STRING, nullable=False, description="20/40/45"),
        ColumnSchema("Category", DataType.STRING, nullable=False, description="Full/Empty"),
        ColumnSchema("Conts", DataType.INTEGER, nullable=True, description="Container count"),
        ColumnSchema("TEUs", DataType.FLOAT, nullable=True, description="TEU equivalent"),
    ]
)


# Collection of all schemas
SCHEMAS: Dict[str, TableSchema] = {
    "vessel_summary": VESSEL_SUMMARY_SCHEMA,
    "qc_productivity": QC_PRODUCTIVITY_SCHEMA,
    "qc_operator_productivity": QC_OPERATOR_PRODUCTIVITY_SCHEMA,
    "delay_events": DELAY_EVENTS_SCHEMA,
    "container_details": CONTAINER_DETAILS_SCHEMA,
}


# ============================================================================
# NORMALIZATION FUNCTIONS
# ============================================================================

def normalize_qc_name(qc_name: Any) -> str:
    """
    Normalize QC names to standard format.
    
    Examples:
        GC1 -> GC01
        gw2 -> GW02
        QC 3 -> QC03
        
    Args:
        qc_name: Raw QC name
        
    Returns:
        Normalized QC name (uppercase, zero-padded number)
    """
    if pd.isna(qc_name) or not qc_name:
        return ""
    
    name = str(qc_name).strip().upper()
    
    # Remove spaces
    name = name.replace(" ", "")
    
    # Handle patterns like GC1 -> GC01
    import re
    match = re.match(r'^([A-Z]+)(\d+)$', name)
    if match:
        prefix, number = match.groups()
        return f"{prefix}{int(number):02d}"
    
    return name


def normalize_error_code(code: Any) -> str:
    """
    Normalize error codes to standard format.
    
    Args:
        code: Raw error code (d, i, m, or description)
        
    Returns:
        Normalized single-character code
    """
    if pd.isna(code) or not code:
        return ""
    
    code_str = str(code).strip().lower()
    
    # Already single character
    if code_str in ('d', 'i', 'm'):
        return code_str
    
    # Map descriptions to codes
    if 'terminal' in code_str and 'non' not in code_str:
        return 'd'
    elif 'non-terminal' in code_str or 'non terminal' in code_str:
        return 'i'
    elif 'maintenance' in code_str:
        return 'm'
    
    return code_str[:1] if code_str else ""


def classify_error_type(error_code: str) -> str:
    """
    Get full error type description from code.
    
    Args:
        error_code: Single character code (d, i, m)
        
    Returns:
        Full error type description
    """
    code = normalize_error_code(error_code)
    
    mapping = {
        'd': ErrorType.TERMINAL_CONVENIENCE.value,
        'i': ErrorType.NON_TERMINAL_CONVENIENCE.value,
        'm': ErrorType.MAINTENANCE.value,
    }
    
    return mapping.get(code, ErrorType.UNKNOWN.value)


# ============================================================================
# METRIC CALCULATIONS (Single Source of Truth)
# ============================================================================

def calculate_net_working_hours(gross_hours: float, delay_hours: float) -> float:
    """
    Calculate net working hours.
    
    Formula: Net = max(0, Gross - Delays)
    
    Args:
        gross_hours: Total working hours
        delay_hours: Total delay/stop hours
        
    Returns:
        Net working hours (never negative)
    """
    if pd.isna(gross_hours) or pd.isna(delay_hours):
        return 0.0
    return max(0.0, gross_hours - delay_hours)


def calculate_moves_per_hour(total_conts: int, working_hours: float) -> float:
    """
    Calculate moves per hour productivity metric.
    
    Formula: Moves/h = Total Conts / Working Hours (when hours > 0)
    
    Args:
        total_conts: Total container moves
        working_hours: Working hours (net or gross)
        
    Returns:
        Moves per hour (0 if hours is 0 or invalid)
    """
    if pd.isna(total_conts) or pd.isna(working_hours) or working_hours <= 0:
        return 0.0
    return round(total_conts / working_hours, 2)


def calculate_portstay_hours(atb: Any, atd: Any) -> float:
    """
    Calculate portstay duration.
    
    Formula: Portstay = ATD - ATB (in hours)
    
    Args:
        atb: Actual Time of Berthing (datetime)
        atd: Actual Time of Departure (datetime)
        
    Returns:
        Portstay in hours
    """
    if pd.isna(atb) or pd.isna(atd):
        return 0.0
    
    try:
        atb_dt = pd.to_datetime(atb)
        atd_dt = pd.to_datetime(atd)
        delta = atd_dt - atb_dt
        return round(delta.total_seconds() / 3600, 2)
    except Exception:
        return 0.0


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_dataframe(df: pd.DataFrame, schema: TableSchema) -> Dict[str, Any]:
    """
    Validate a DataFrame against a schema.
    
    Args:
        df: DataFrame to validate
        schema: TableSchema to validate against
        
    Returns:
        Dict with:
            - valid: bool
            - missing_columns: List of missing required columns
            - extra_columns: List of columns not in schema
            - type_errors: List of type mismatch errors
    """
    result = {
        "valid": True,
        "missing_columns": [],
        "extra_columns": [],
        "type_errors": [],
        "null_violations": []
    }
    
    schema_cols = set(schema.get_column_names())
    df_cols = set(df.columns)
    
    # Check missing columns
    result["missing_columns"] = list(schema_cols - df_cols)
    
    # Check extra columns (warning, not error)
    result["extra_columns"] = list(df_cols - schema_cols)
    
    # Check required columns for nulls
    for col in schema.columns:
        if not col.nullable and col.name in df.columns:
            null_count = df[col.name].isna().sum()
            if null_count > 0:
                result["null_violations"].append(f"{col.name}: {null_count} null values")
    
    # Determine validity
    result["valid"] = len(result["missing_columns"]) == 0 and len(result["null_violations"]) == 0
    
    return result


def get_schema_info() -> Dict[str, Any]:
    """
    Get information about all schemas.
    
    Returns:
        Dict with schema version and table info
    """
    return {
        "version": SCHEMA_VERSION,
        "tables": {
            name: {
                "description": schema.description,
                "columns": schema.get_column_names(),
                "primary_key": schema.primary_key
            }
            for name, schema in SCHEMAS.items()
        }
    }
