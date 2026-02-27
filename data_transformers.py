# data_transformers.py
"""
Data transformation and business logic layer for TDR Processor.

This module separates business logic (calculations, normalization, enrichment)
from the Excel I/O layer (data_extractors.py).

Architecture:
    data_extractors.py  → Raw data extraction from Excel (I/O layer)
    data_transformers.py → Calculations, normalization, enrichment (business logic)
    report_processor.py → Orchestration, aggregation, persistence

Benefits:
    - Business logic can be unit tested without Excel files
    - Changing Excel format only affects data_extractors.py
    - Calculations are centralized and reusable

Usage:
    from data_transformers import VesselTransformer, QCTransformer, DelayTransformer

    vessel_info = extractor.extract_vessel_info()
    vessel_info = VesselTransformer.calculate_kpis(vessel_info)
"""
import logging
import re
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from utils.excel_utils import timedelta_to_hours


# ============================================================================
# VESSEL TRANSFORMER
# ============================================================================

class VesselTransformer:
    """
    Business logic transformations for vessel summary data.

    All methods are static - no state required.
    """

    @staticmethod
    def calculate_kpis(vessel_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate vessel-level KPI metrics from raw extracted data.

        Computes:
        - Break Time (hrs) = Break Dis + Break Load
        - Net Working (hrs) = Gross Working - Break Time
        - Vessel Moves/Net Hour
        - Vessel Moves/Gross Hour
        - Vessel Moves/Portstay Hour

        Args:
            vessel_info: Raw vessel info dict from DataExtractor.extract_vessel_info()

        Returns:
            vessel_info dict with KPI fields added/updated
        """
        # Break time
        vessel_info["Break Time (hrs)"] = round(
            vessel_info.get("Break Dis (hrs)", 0.0) + vessel_info.get("Break Load (hrs)", 0.0),
            2
        )

        # Net working = Gross - Break
        gross_working = vessel_info.get("Gross Working (hrs)", 0.0)
        break_time = vessel_info.get("Break Time (hrs)", 0.0)
        vessel_info["Net Working (hrs)"] = round(max(0.0, gross_working - break_time), 2)

        # Productivity metrics
        grand_total_conts = vessel_info.get("Grand Total Conts", 0)
        net_working = vessel_info.get("Net Working (hrs)", 0.0)
        portstay = vessel_info.get("Portstay (hrs)", 0.0)

        vessel_info["Vessel Moves/Net Hour"] = (
            round(grand_total_conts / net_working, 1)
            if net_working > 0 and grand_total_conts > 0 else 0.0
        )
        vessel_info["Vessel Moves/Gross Hour"] = (
            round(grand_total_conts / gross_working, 1)
            if gross_working > 0 and grand_total_conts > 0 else 0.0
        )
        vessel_info["Vessel Moves/Portstay Hour"] = (
            round(grand_total_conts / portstay, 1)
            if portstay > 0 and grand_total_conts > 0 else 0.0
        )

        return vessel_info

    @staticmethod
    def calculate_durations(vessel_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate time durations from datetime fields.

        Computes:
        - Portstay (hrs) = ATD - ATB
        - Discharge Duration (hrs) = Completed Discharge - Commenced Discharge
        - Load Duration (hrs) = Completed Loading - Commenced Loading
        - Gross Working (hrs) = Last Op - First Op

        Args:
            vessel_info: Vessel info dict with datetime fields

        Returns:
            vessel_info dict with duration fields added
        """
        atb = vessel_info.get("ATB")
        atd = vessel_info.get("ATD")
        cd = vessel_info.get("Commenced Discharge")
        completed_discharge = vessel_info.get("Completed Discharge")
        cl = vessel_info.get("Commenced Loading")
        completed_loading = vessel_info.get("Completed Loading")

        # Portstay
        vessel_info["Portstay (hrs)"] = (
            timedelta_to_hours(atd - atb)
            if all(isinstance(x, datetime) for x in [atd, atb]) and atd > atb
            else 0.0
        )

        # Discharge duration
        vessel_info["Discharge Duration (hrs)"] = (
            timedelta_to_hours(completed_discharge - cd)
            if all(isinstance(x, datetime) for x in [completed_discharge, cd]) and completed_discharge > cd
            else 0.0
        )

        # Load duration
        vessel_info["Load Duration (hrs)"] = (
            timedelta_to_hours(completed_loading - cl)
            if all(isinstance(x, datetime) for x in [completed_loading, cl]) and completed_loading > cl
            else 0.0
        )

        # Gross working = last op - first op
        first_op = min(
            filter(None, [cd, cl]),
            default=None,
            key=lambda x: x if isinstance(x, datetime) else datetime.max
        )
        last_op = max(
            filter(None, [completed_discharge, completed_loading]),
            default=None,
            key=lambda x: x if isinstance(x, datetime) else datetime.min
        )
        vessel_info["Gross Working (hrs)"] = (
            timedelta_to_hours(last_op - first_op)
            if all(isinstance(x, datetime) for x in [last_op, first_op]) and last_op > first_op
            else 0.0
        )

        return vessel_info

    @staticmethod
    def validate_vessel_info(vessel_info: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate vessel info for required fields and data quality.

        Args:
            vessel_info: Vessel info dict to validate

        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        required_fields = ["Vessel Name", "Voyage", "ATB", "ATD"]

        for field in required_fields:
            if not vessel_info.get(field):
                warnings.append(f"Missing required field: {field}")

        atb = vessel_info.get("ATB")
        atd = vessel_info.get("ATD")
        if isinstance(atb, datetime) and isinstance(atd, datetime):
            if atd <= atb:
                warnings.append(f"ATD ({atd}) is not after ATB ({atb})")
            portstay = vessel_info.get("Portstay (hrs)", 0)
            if portstay > 168:  # More than 7 days
                warnings.append(f"Unusually long portstay: {portstay:.1f} hours")

        grand_total = vessel_info.get("Grand Total Conts", 0)
        if grand_total < 0:
            warnings.append(f"Negative container count: {grand_total}")

        is_valid = len([w for w in warnings if "Missing required" in w]) == 0
        return is_valid, warnings


# ============================================================================
# QC TRANSFORMER
# ============================================================================

class QCTransformer:
    """
    Business logic transformations for QC productivity data.
    """

    @staticmethod
    def normalize_qc_name(name: str) -> str:
        """
        Normalize QC name to standard format 'XX00'.

        Examples:
            GC1 -> GC01
            GW2 -> GW02
            gc01 -> GC01

        Args:
            name: Raw QC name

        Returns:
            Normalized QC name
        """
        if not isinstance(name, str):
            return ""
        name = name.strip().upper()
        letters = ''.join(re.findall(r'[A-Z]', name))
        numbers = ''.join(re.findall(r'\d', name))
        if letters and numbers:
            return f"{letters}{int(numbers):02d}"
        return name

    @staticmethod
    def calculate_qc_metrics(qc_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate QC productivity metrics.

        Computes:
        - Net working (hrs) = Gross working - Delay times
        - Net moves/h = Total Conts / Net working
        - Gross moves/h = Total Conts / Gross working

        Args:
            qc_record: Raw QC record dict

        Returns:
            qc_record with calculated metrics
        """
        gross_w = qc_record.get("Gross working (hrs)", 0.0) or 0.0
        delay_t = qc_record.get("Delay times (hrs)", 0.0) or 0.0
        total_c = qc_record.get("Total Conts", 0) or 0

        net_w = round(max(0.0, gross_w - delay_t), 2)
        qc_record["Net working (hrs)"] = net_w

        qc_record["Net moves/h"] = (
            round(total_c / net_w, 1) if net_w > 0 and total_c > 0 else 0.0
        )
        qc_record["Gross moves/h"] = (
            round(total_c / gross_w, 1) if gross_w > 0 and total_c > 0 else 0.0
        )

        return qc_record

    @staticmethod
    def calculate_operator_metrics(
        qc_record: Dict[str, Any],
        actual_delay_hours: float
    ) -> Dict[str, Any]:
        """
        Calculate operator-adjusted QC metrics using actual delay from delay table.

        The operator metric uses actual stop times from the delay details table
        (not the reported delay from the QC productivity table) for more accurate
        operator performance assessment.

        Args:
            qc_record: QC record dict
            actual_delay_hours: Total actual delay hours from delay details table

        Returns:
            qc_record with operator-adjusted metrics
        """
        gross_w = qc_record.get("Gross working (hrs)", 0.0) or 0.0
        total_c = qc_record.get("Total Conts", 0) or 0

        qc_record["Total Stop Time (hrs)"] = actual_delay_hours
        net_w = round(max(0.0, gross_w - actual_delay_hours), 2)
        qc_record["Net working (hrs)"] = net_w

        qc_record["Net moves/h"] = (
            round(total_c / net_w, 1) if net_w > 0 and total_c > 0 else 0.0
        )

        return qc_record

    @staticmethod
    def aggregate_delays_by_qc(delay_records: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Aggregate total delay hours per QC from delay detail records.

        Args:
            delay_records: List of delay event dicts

        Returns:
            Dict mapping normalized QC name to total delay hours
        """
        if not delay_records:
            return {}

        df = pd.DataFrame(delay_records)
        if "QC No." not in df.columns or "Duration (hrs)" not in df.columns:
            return {}

        df["QC_Normalized"] = df["QC No."].apply(QCTransformer.normalize_qc_name)
        return df.groupby("QC_Normalized")["Duration (hrs)"].sum().to_dict()


# ============================================================================
# DELAY TRANSFORMER
# ============================================================================

class DelayTransformer:
    """
    Business logic transformations for delay event data.
    """

    @staticmethod
    def classify_error(error_code_and_remark: Optional[str]) -> Tuple[Optional[str], str]:
        """
        Classify delay error code into error type.

        Args:
            error_code_and_remark: Raw error code/remark string

        Returns:
            Tuple of (error_code, error_type)
        """
        from utils.excel_utils import classify_error_code
        return classify_error_code(error_code_and_remark)

    @staticmethod
    def calculate_duration(
        from_time: Optional[datetime],
        to_time: Optional[datetime],
        reported_hours: float = 0.0,
        mismatch_threshold: float = 0.02
    ) -> Tuple[float, Optional[datetime], Optional[datetime]]:
        """
        Calculate delay duration, handling overnight spans.

        Prefers reported hours from file; falls back to calculated.
        Logs warning if mismatch exceeds threshold.

        Args:
            from_time: Delay start datetime
            to_time: Delay end datetime
            reported_hours: Hours reported in the TDR file
            mismatch_threshold: Acceptable difference between reported and calculated

        Returns:
            Tuple of (duration_hours, adjusted_from_time, adjusted_to_time)
        """
        dur_calc = 0.0
        from_f, to_f = from_time, to_time

        if isinstance(from_time, datetime) and isinstance(to_time, datetime):
            tmp_f, tmp_t = from_time, to_time
            # Handle overnight spans
            if tmp_t < tmp_f:
                tmp_t += timedelta(days=1)
            if tmp_t > tmp_f:
                dur_calc = timedelta_to_hours(tmp_t - tmp_f)
            from_f, to_f = tmp_f, tmp_t

        # Use reported hours if available, otherwise calculated
        dur_use = reported_hours if reported_hours > 0 else dur_calc

        # Log mismatch warning
        if reported_hours > 0 and dur_calc > 0:
            if abs(reported_hours - dur_calc) > mismatch_threshold:
                logging.warning(
                    f"Duration mismatch: reported={reported_hours:.2f}h, "
                    f"calculated={dur_calc:.2f}h. Using reported."
                )
                dur_use = reported_hours

        return dur_use, from_f, to_f

    @staticmethod
    def summarize_by_error_type(delay_records: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Summarize total delay hours by error type.

        Args:
            delay_records: List of delay event dicts

        Returns:
            Dict mapping error type to total hours
        """
        if not delay_records:
            return {}

        df = pd.DataFrame(delay_records)
        if "Error Type" not in df.columns or "Duration (hrs)" not in df.columns:
            return {}

        return df.groupby("Error Type")["Duration (hrs)"].sum().round(2).to_dict()


# ============================================================================
# CONTAINER TRANSFORMER
# ============================================================================

class ContainerTransformer:
    """
    Business logic transformations for container detail data.
    """

    @staticmethod
    def calculate_teus(container_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate TEU equivalents for container records.

        TEU calculation:
        - 20ft container = 1 TEU
        - 40ft container = 2 TEUs
        - 45ft container = 2 TEUs

        Args:
            container_records: List of container detail dicts

        Returns:
            container_records with TEU field added
        """
        teu_multipliers = {"20": 1, "40": 2, "45": 2}

        for record in container_records:
            size = str(record.get("ContainerSize", "20"))
            quantity = record.get("Quantity", 0) or 0
            multiplier = teu_multipliers.get(size, 1)
            record["TEUs"] = quantity * multiplier

        return container_records

    @staticmethod
    def pivot_to_wide_format(df_long: pd.DataFrame) -> pd.DataFrame:
        """
        Pivot container data from long to wide format.

        Long format: one row per (operation, category, size)
        Wide format: one row per operation, columns for each category/size combo

        Args:
            df_long: DataFrame in long format

        Returns:
            DataFrame in wide format
        """
        if df_long.empty:
            return pd.DataFrame()

        try:
            df_long = df_long.copy()
            df_long["ContainerTypeSize"] = (
                df_long["ContainerCategory"] + "_" + df_long["ContainerSize"].astype(str)
            )

            base_cols = [
                col for col in ["Filename", "Vessel Name", "Voyage", "OperationType", "Port"]
                if col in df_long.columns
            ]

            df_wide = pd.pivot_table(
                df_long,
                values="Quantity",
                index=base_cols,
                columns="ContainerTypeSize",
                aggfunc="sum",
                fill_value=0
            ).reset_index()

            # Add total columns
            quantity_cols = [col for col in df_wide.columns if col not in base_cols]
            if quantity_cols:
                df_wide["Total Conts"] = df_wide[quantity_cols].sum(axis=1)
                df_wide["Total TEUs"] = sum(
                    df_wide[col] * (1 if "_20" in col else 2)
                    for col in quantity_cols
                )

            return df_wide

        except Exception as e:
            logging.error(f"ContainerTransformer.pivot_to_wide_format failed: {e}", exc_info=True)
            return pd.DataFrame()
