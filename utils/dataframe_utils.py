"""
utils/dataframe_utils.py - Common DataFrame transformation utilities for TDR Processor

This module provides reusable functions for DataFrame operations commonly used across
data extraction and report processing, reducing code duplication and improving
maintainability.

Type Hints: Fully type-hinted for better IDE support and type checking with mypy.
"""

import logging
from typing import Dict, Any, Optional
import pandas as pd


def apply_qc_calculations(
    dataframe: pd.DataFrame,
    delay_column: str = "Delay times (hrs)",
    containers_column: str = "Total Conts"
) -> pd.DataFrame:
    """
    Apply standard QC productivity calculations to a DataFrame.
    
    Calculates Net Working hours (Gross - Delay) and Net Moves per hour (Total Conts / Net Working).
    Creates new columns for these metrics.
    
    Args:
        dataframe: Input DataFrame with QC productivity data
        delay_column: Name of the column containing delay hours (default: "Delay times (hrs)")
        containers_column: Name of the column containing total containers (default: "Total Conts")
    
    Returns:
        DataFrame with added "Net working (hrs)" and "Net moves/h (QC)" columns
    
    Example:
        >>> df_qc = pd.DataFrame({
        ...     'Gross working (hrs)': [8.5, 7.2],
        ...     'Delay times (hrs)': [0.5, 1.0],
        ...     'Total Conts': [50, 45]
        ... })
        >>> result = apply_qc_calculations(df_qc)
        >>> result['Net working (hrs)'].tolist()
        [8.0, 6.2]
    """
    result_df = dataframe.copy()
    
    # Calculate Net working hours (Gross - Delay)
    result_df["Net working (hrs)"] = result_df.apply(
        lambda row: round(
            max(0, row.get("Gross working (hrs)", 0.0) - row.get(delay_column, 0.0)),
            2
        ),
        axis=1
    )
    
    # Calculate Net moves per hour
    result_df["Net moves/h (QC)"] = result_df.apply(
        lambda row: round(
            row[containers_column] / row["Net working (hrs)"],
            1
        ) if row["Net working (hrs)"] > 0 and row.get(containers_column, 0) > 0 else 0.0,
        axis=1
    )
    
    logging.info(f"Applied QC calculations to DataFrame with {len(result_df)} rows")
    return result_df


def calculate_vessel_kpis(vessel_info: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate vessel-level KPIs (Key Performance Indicators) from vessel information.
    
    Calculates performance metrics such as Vessel Moves per Net Hour, Gross Hour, and Portstay Hour.
    
    Args:
        vessel_info: Dictionary containing vessel information with keys:
            - 'Grand Total Conts': Total number of containers
            - 'Net Working (hrs)': Net working hours
            - 'Gross Working (hrs)': Gross working hours
            - 'Portstay (hrs)': Port stay hours
    
    Returns:
        Dictionary with calculated KPI values for:
        - 'Vessel Moves/Net Hour'
        - 'Vessel Moves/Gross Hour'
        - 'Vessel Moves/Portstay Hour'
    
    Example:
        >>> info = {
        ...     'Grand Total Conts': 500,
        ...     'Net Working (hrs)': 40.0,
        ...     'Gross Working (hrs)': 48.0,
        ...     'Portstay (hrs)': 60.0
        ... }
        >>> kpis = calculate_vessel_kpis(info)
        >>> kpis['Vessel Moves/Net Hour']
        12.5
    """
    grand_total_containers: int = vessel_info.get("Grand Total Conts", 0)
    net_working_hours: float = vessel_info.get("Net Working (hrs)", 0.0)
    gross_working_hours: float = vessel_info.get("Gross Working (hrs)", 0.0)
    portstay_hours: float = vessel_info.get("Portstay (hrs)", 0.0)
    
    kpis: Dict[str, float] = {}
    
    # Calculate Vessel Moves per Net Hour
    if net_working_hours > 0 and grand_total_containers > 0:
        kpis["Vessel Moves/Net Hour"] = round(grand_total_containers / net_working_hours, 1)
    else:
        kpis["Vessel Moves/Net Hour"] = 0.0
    
    # Calculate Vessel Moves per Gross Hour
    if gross_working_hours > 0 and grand_total_containers > 0:
        kpis["Vessel Moves/Gross Hour"] = round(grand_total_containers / gross_working_hours, 1)
    else:
        kpis["Vessel Moves/Gross Hour"] = 0.0
    
    # Calculate Vessel Moves per Portstay Hour
    if portstay_hours > 0 and grand_total_containers > 0:
        kpis["Vessel Moves/Portstay Hour"] = round(grand_total_containers / portstay_hours, 1)
    else:
        kpis["Vessel Moves/Portstay Hour"] = 0.0
    
    logging.info(f"Calculated vessel KPIs: {kpis}")
    return kpis


def format_dataframe_numeric_columns(
    dataframe: pd.DataFrame,
    numeric_columns: Optional[list[str]] = None,
    decimal_places: int = 2
) -> pd.DataFrame:
    """
    Format numeric columns in a DataFrame to specified decimal places.
    
    Rounds numeric columns to a consistent number of decimal places for better
    presentation and consistency across output files.
    
    Args:
        dataframe: Input DataFrame to format
        numeric_columns: List of column names to format. If None, formats all numeric columns
        decimal_places: Number of decimal places to round to (default: 2)
    
    Returns:
        DataFrame with formatted numeric columns
    
    Example:
        >>> df = pd.DataFrame({
        ...     'Hours': [8.123456, 7.987654],
        ...     'Moves': [123.456, 98.765]
        ... })
        >>> result = format_dataframe_numeric_columns(df)
        >>> result['Hours'].tolist()
        [8.12, 7.99]
    """
    result_df = dataframe.copy()
    
    # If no columns specified, format all numeric columns
    if numeric_columns is None:
        numeric_columns = result_df.select_dtypes(include=['number']).columns.tolist()
    
    # Round specified columns
    for col in numeric_columns:
        if col in result_df.columns:
            result_df[col] = result_df[col].round(decimal_places)
    
    logging.debug(f"Formatted {len(numeric_columns)} numeric columns to {decimal_places} decimal places")
    return result_df


def aggregate_multiple_dataframes(
    dataframes: list[pd.DataFrame],
    sort_by: Optional[str] = None,
    reset_index: bool = True
) -> pd.DataFrame:
    """
    Aggregate multiple DataFrames into a single consolidated DataFrame.
    
    Combines data from multiple source DataFrames, optionally sorting and resetting index.
    
    Args:
        dataframes: List of DataFrames to combine
        sort_by: Column name to sort the result by (optional)
        reset_index: Whether to reset the index (default: True)
    
    Returns:
        Single consolidated DataFrame
    
    Example:
        >>> df1 = pd.DataFrame({'vessel': ['A'], 'moves': [50]})
        >>> df2 = pd.DataFrame({'vessel': ['B'], 'moves': [60]})
        >>> result = aggregate_multiple_dataframes([df1, df2], sort_by='moves')
        >>> len(result)
        2
    """
    if not dataframes:
        logging.warning("No DataFrames provided for aggregation")
        return pd.DataFrame()
    
    # Concatenate all DataFrames
    combined_df = pd.concat(dataframes, ignore_index=reset_index)
    
    # Sort if requested
    if sort_by and sort_by in combined_df.columns:
        combined_df = combined_df.sort_values(by=sort_by).reset_index(drop=True)
        logging.info(f"Aggregated {len(dataframes)} DataFrames and sorted by '{sort_by}'")
    else:
        logging.info(f"Aggregated {len(dataframes)} DataFrames")
    
    return combined_df
