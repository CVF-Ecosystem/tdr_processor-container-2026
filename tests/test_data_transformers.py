# tests/test_data_transformers.py
"""Unit tests for data_transformers.py — VesselTransformer, QCTransformer, DelayTransformer, ContainerTransformer."""
import pytest
from datetime import datetime
import pandas as pd

from data_transformers import (
    VesselTransformer,
    QCTransformer,
    DelayTransformer,
    ContainerTransformer,
)


# ============================================================================
# VesselTransformer
# ============================================================================

class TestVesselTransformerCalculateKPIs:
    def _base(self):
        return {
            "Break Dis (hrs)": 1.0,
            "Break Load (hrs)": 0.5,
            "Gross Working (hrs)": 10.0,
            "Grand Total Conts": 500,
            "Portstay (hrs)": 24.0,
        }

    def test_break_time_sum(self):
        info = VesselTransformer.calculate_kpis(self._base())
        assert info["Break Time (hrs)"] == pytest.approx(1.5)

    def test_net_working(self):
        info = VesselTransformer.calculate_kpis(self._base())
        assert info["Net Working (hrs)"] == pytest.approx(8.5)

    def test_net_working_never_negative(self):
        base = self._base()
        base["Break Dis (hrs)"] = 20.0
        info = VesselTransformer.calculate_kpis(base)
        assert info["Net Working (hrs)"] >= 0.0

    def test_vessel_moves_net_hour(self):
        info = VesselTransformer.calculate_kpis(self._base())
        expected = round(500 / 8.5, 1)
        assert info["Vessel Moves/Net Hour"] == pytest.approx(expected, abs=0.1)

    def test_vessel_moves_gross_hour(self):
        info = VesselTransformer.calculate_kpis(self._base())
        assert info["Vessel Moves/Gross Hour"] == pytest.approx(50.0)

    def test_vessel_moves_portstay_hour(self):
        info = VesselTransformer.calculate_kpis(self._base())
        assert info["Vessel Moves/Portstay Hour"] == pytest.approx(500 / 24.0, abs=0.1)

    def test_zero_conts_returns_zero_metrics(self):
        base = self._base()
        base["Grand Total Conts"] = 0
        info = VesselTransformer.calculate_kpis(base)
        assert info["Vessel Moves/Net Hour"] == 0.0
        assert info["Vessel Moves/Gross Hour"] == 0.0

    def test_zero_hours_returns_zero_metrics(self):
        base = self._base()
        base["Gross Working (hrs)"] = 0.0
        base["Net Working (hrs)"] = 0.0
        base["Portstay (hrs)"] = 0.0
        info = VesselTransformer.calculate_kpis(base)
        assert info["Vessel Moves/Net Hour"] == 0.0
        assert info["Vessel Moves/Gross Hour"] == 0.0


class TestVesselTransformerCalculateDurations:
    def test_portstay(self):
        atb = datetime(2024, 1, 1, 8, 0)
        atd = datetime(2024, 1, 2, 8, 0)
        info = VesselTransformer.calculate_durations({"ATB": atb, "ATD": atd})
        assert info["Portstay (hrs)"] == pytest.approx(24.0)

    def test_portstay_zero_when_atd_before_atb(self):
        atb = datetime(2024, 1, 2, 8, 0)
        atd = datetime(2024, 1, 1, 8, 0)
        info = VesselTransformer.calculate_durations({"ATB": atb, "ATD": atd})
        assert info["Portstay (hrs)"] == 0.0

    def test_portstay_none_datetimes(self):
        info = VesselTransformer.calculate_durations({"ATB": None, "ATD": None})
        assert info["Portstay (hrs)"] == 0.0

    def test_gross_working_hours(self):
        info = VesselTransformer.calculate_durations({
            "Commenced Discharge": datetime(2024, 1, 1, 6, 0),
            "Completed Loading": datetime(2024, 1, 1, 18, 0),
        })
        assert info["Gross Working (hrs)"] == pytest.approx(12.0)


class TestVesselTransformerValidate:
    def test_valid_vessel(self):
        info = {
            "Vessel Name": "Test Vessel",
            "Voyage": "001",
            "ATB": datetime(2024, 1, 1, 8, 0),
            "ATD": datetime(2024, 1, 2, 8, 0),
            "Portstay (hrs)": 24.0,
            "Grand Total Conts": 100,
        }
        is_valid, warnings = VesselTransformer.validate_vessel_info(info)
        assert is_valid is True
        assert len(warnings) == 0

    def test_missing_vessel_name(self):
        info = {
            "Voyage": "001",
            "ATB": datetime(2024, 1, 1, 8, 0),
            "ATD": datetime(2024, 1, 2, 8, 0),
        }
        is_valid, warnings = VesselTransformer.validate_vessel_info(info)
        assert is_valid is False
        assert any("Vessel Name" in w for w in warnings)

    def test_atd_before_atb_warning(self):
        info = {
            "Vessel Name": "V",
            "Voyage": "1",
            "ATB": datetime(2024, 1, 2),
            "ATD": datetime(2024, 1, 1),
        }
        _, warnings = VesselTransformer.validate_vessel_info(info)
        assert any("ATD" in w for w in warnings)

    def test_long_portstay_warning(self):
        info = {
            "Vessel Name": "V",
            "Voyage": "1",
            "ATB": datetime(2024, 1, 1),
            "ATD": datetime(2024, 1, 10),
            "Portstay (hrs)": 200.0,
        }
        _, warnings = VesselTransformer.validate_vessel_info(info)
        assert any("portstay" in w.lower() for w in warnings)


# ============================================================================
# QCTransformer
# ============================================================================

class TestQCTransformerNormalize:
    @pytest.mark.parametrize("raw, expected", [
        ("GC1", "GC01"),
        ("GW2", "GW02"),
        ("gc01", "GC01"),
        ("GC12", "GC12"),
        ("", ""),
        (None, ""),
    ])
    def test_normalize(self, raw, expected):
        assert QCTransformer.normalize_qc_name(raw) == expected


class TestQCTransformerMetrics:
    def test_net_working(self):
        rec = {"Gross working (hrs)": 8.0, "Delay times (hrs)": 1.5, "Total Conts": 300}
        rec = QCTransformer.calculate_qc_metrics(rec)
        assert rec["Net working (hrs)"] == pytest.approx(6.5)

    def test_net_moves_per_hour(self):
        rec = {"Gross working (hrs)": 8.0, "Delay times (hrs)": 0.0, "Total Conts": 400}
        rec = QCTransformer.calculate_qc_metrics(rec)
        assert rec["Net moves/h"] == pytest.approx(50.0)

    def test_zero_net_working_returns_zero_moves(self):
        rec = {"Gross working (hrs)": 1.0, "Delay times (hrs)": 1.0, "Total Conts": 100}
        rec = QCTransformer.calculate_qc_metrics(rec)
        assert rec["Net moves/h"] == 0.0

    def test_net_working_never_negative(self):
        rec = {"Gross working (hrs)": 1.0, "Delay times (hrs)": 5.0, "Total Conts": 100}
        rec = QCTransformer.calculate_qc_metrics(rec)
        assert rec["Net working (hrs)"] >= 0.0


class TestQCTransformerAggregateDelays:
    def test_aggregate_by_qc(self):
        records = [
            {"QC No.": "GC01", "Duration (hrs)": 1.0},
            {"QC No.": "GC01", "Duration (hrs)": 0.5},
            {"QC No.": "GW02", "Duration (hrs)": 2.0},
        ]
        result = QCTransformer.aggregate_delays_by_qc(records)
        assert result["GC01"] == pytest.approx(1.5)
        assert result["GW02"] == pytest.approx(2.0)

    def test_empty_records(self):
        assert QCTransformer.aggregate_delays_by_qc([]) == {}


# ============================================================================
# DelayTransformer
# ============================================================================

class TestDelayTransformerDuration:
    def test_uses_reported_hours_when_available(self):
        from_t = datetime(2024, 1, 1, 8, 0)
        to_t = datetime(2024, 1, 1, 10, 0)
        dur, _, _ = DelayTransformer.calculate_duration(from_t, to_t, reported_hours=2.0)
        assert dur == pytest.approx(2.0)

    def test_falls_back_to_calculated_when_no_reported(self):
        from_t = datetime(2024, 1, 1, 8, 0)
        to_t = datetime(2024, 1, 1, 10, 30)
        dur, _, _ = DelayTransformer.calculate_duration(from_t, to_t, reported_hours=0.0)
        assert dur == pytest.approx(2.5)

    def test_handles_overnight_span(self):
        from_t = datetime(2024, 1, 1, 23, 0)
        to_t = datetime(2024, 1, 1, 1, 0)
        dur, _, _ = DelayTransformer.calculate_duration(from_t, to_t, reported_hours=0.0)
        assert dur == pytest.approx(2.0)

    def test_none_datetimes_returns_zero(self):
        dur, _, _ = DelayTransformer.calculate_duration(None, None, reported_hours=0.0)
        assert dur == 0.0


class TestDelayTransformerSummarize:
    def test_summarize_by_error_type(self):
        records = [
            {"Error Type": "Terminal Convenience", "Duration (hrs)": 1.0},
            {"Error Type": "Terminal Convenience", "Duration (hrs)": 0.5},
            {"Error Type": "Force Majeure", "Duration (hrs)": 2.0},
        ]
        result = DelayTransformer.summarize_by_error_type(records)
        assert result["Terminal Convenience"] == pytest.approx(1.5)
        assert result["Force Majeure"] == pytest.approx(2.0)

    def test_empty_records(self):
        assert DelayTransformer.summarize_by_error_type([]) == {}


# ============================================================================
# ContainerTransformer
# ============================================================================

class TestContainerTransformerTEUs:
    def test_20ft_is_1_teu(self):
        records = [{"ContainerSize": "20", "Quantity": 10}]
        result = ContainerTransformer.calculate_teus(records)
        assert result[0]["TEUs"] == 10

    def test_40ft_is_2_teus(self):
        records = [{"ContainerSize": "40", "Quantity": 5}]
        result = ContainerTransformer.calculate_teus(records)
        assert result[0]["TEUs"] == 10

    def test_45ft_is_2_teus(self):
        records = [{"ContainerSize": "45", "Quantity": 3}]
        result = ContainerTransformer.calculate_teus(records)
        assert result[0]["TEUs"] == 6

    def test_unknown_size_defaults_to_1(self):
        records = [{"ContainerSize": "99", "Quantity": 4}]
        result = ContainerTransformer.calculate_teus(records)
        assert result[0]["TEUs"] == 4

    def test_mixed_sizes(self):
        records = [
            {"ContainerSize": "20", "Quantity": 10},
            {"ContainerSize": "40", "Quantity": 5},
        ]
        result = ContainerTransformer.calculate_teus(records)
        assert result[0]["TEUs"] == 10
        assert result[1]["TEUs"] == 10


class TestContainerTransformerPivot:
    def _make_df(self):
        return pd.DataFrame([
            {"Filename": "f1", "Vessel Name": "V", "Voyage": "1",
             "OperationType": "Discharge", "Port": "ABC",
             "ContainerCategory": "Full DC", "ContainerSize": "20", "Quantity": 100},
            {"Filename": "f1", "Vessel Name": "V", "Voyage": "1",
             "OperationType": "Discharge", "Port": "ABC",
             "ContainerCategory": "Empty DC", "ContainerSize": "40", "Quantity": 50},
        ])

    def test_pivot_creates_columns(self):
        df_long = self._make_df()
        df_wide = ContainerTransformer.pivot_to_wide_format(df_long)
        assert not df_wide.empty
        assert "Full DC_20" in df_wide.columns
        assert "Empty DC_40" in df_wide.columns

    def test_pivot_total_conts(self):
        df_long = self._make_df()
        df_wide = ContainerTransformer.pivot_to_wide_format(df_long)
        assert "Total Conts" in df_wide.columns
        assert df_wide["Total Conts"].iloc[0] == 150

    def test_pivot_empty_df(self):
        result = ContainerTransformer.pivot_to_wide_format(pd.DataFrame())
        assert result.empty
