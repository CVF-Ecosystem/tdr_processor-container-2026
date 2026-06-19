"""
TDR Processor Dashboard — Flask API Server
==========================================
Serves dashboard.html and exposes /api/meta + /api/data endpoints backed by
the existing SQLite database (outputs/tdr_master.db) or CSV fallbacks.

Run:  python dashboard_api.py
Open: http://localhost:8503

Auth: Set TDR_API_TOKEN env var before running.
      For local dev without token: TDR_AUTH_DISABLED=true
"""

import functools
import hmac
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, send_from_directory

from config import APP_VERSION
from data_schema import find_tdr_datetime_issues, normalize_vessel_name

# ─── Config ──────────────────────────────────────────────────────────────────
APP_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
WORK_DIR = Path(os.environ.get("TDR_WORKDIR", Path.cwd()))
DB_PATH_RAW = os.environ.get("TDR_DB_PATH")
DB_PATH = Path(DB_PATH_RAW) if DB_PATH_RAW else WORK_DIR / "outputs" / "tdr_master.db"
if not DB_PATH.is_absolute():
    DB_PATH = WORK_DIR / DB_PATH
CSV_DIR = WORK_DIR / "outputs" / "data_csv"
PORT = int(os.environ.get("TDR_DASH_PORT", "8503"))
KPI_TARGET = int(os.environ.get("TDR_KPI_TARGET", "45"))
# TDR_DASH_HOST defaults to 127.0.0.1 for safe local execution.
# Docker compose overrides this to 0.0.0.0 for container networking.
DASH_HOST = os.environ.get("TDR_DASH_HOST", "127.0.0.1")

VESSEL_COLORS = [
    "#3B82F6",
    "#10B981",
    "#F59E0B",
    "#EF4444",
    "#8B5CF6",
    "#06B6D4",
    "#EC4899",
    "#14B8A6",
    "#F97316",
]

_CSV_MAP = {
    "vessel_summary": "vessel_summary.csv",
    "qc_productivity": "qc_productivity.csv",
    "qc_operator_productivity": "qc_operator_productivity.csv",
    "delay_events": "delay_details.csv",
    "delay_details": "delay_details.csv",
    "container_details_wide": "container_details_wide.csv",
}

app = Flask(__name__, static_url_path="")

# ─── Auth ─────────────────────────────────────────────────────────────────────
IP_LIMITS = {}  # {ip: [timestamps]} for lightweight rate limiting

_AUTH_CHECK_DONE = False


@app.before_request
def check_auth_config():
    global _AUTH_CHECK_DONE
    # Skip check for static frontend files if any, but since it's a small app we check all endpoints
    if not _AUTH_CHECK_DONE:
        auth_disabled = os.environ.get("TDR_AUTH_DISABLED", "false").lower() == "true"
        api_token_raw = os.environ.get("TDR_API_TOKEN", "")
        if not auth_disabled and not api_token_raw:
            raise RuntimeError(
                "[TDR Dashboard] TDR_API_TOKEN environment variable is not set. "
                "Set it before starting the server, or set TDR_AUTH_DISABLED=true for local dev."
            )
        _AUTH_CHECK_DONE = True


def require_token(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        from flask import request

        auth_disabled = os.environ.get("TDR_AUTH_DISABLED", "false").lower() == "true"
        if auth_disabled:
            return f(*args, **kwargs)
        token = request.headers.get("X-API-Token") or request.args.get("token", "")
        api_token_raw = os.environ.get("TDR_API_TOKEN", "")
        # Constant-time comparison to prevent timing attacks
        if not token or not hmac.compare_digest(token, api_token_raw):
            return jsonify(
                {
                    "error": "Unauthorized",
                    "message": "API Access Token is missing or invalid.",
                }
            ), 401
        return f(*args, **kwargs)

    return decorated


def rate_limit():
    from flask import request

    ip = request.remote_addr
    now = time.time()
    # clean up old timestamps (> 60 seconds)
    timestamps = [t for t in IP_LIMITS.get(ip, []) if now - t < 60]
    if len(timestamps) >= 60:  # limit to 60 requests per minute
        return jsonify(
            {
                "error": "Too Many Requests",
                "message": "Rate limit exceeded. Max 60 requests per minute.",
            }
        ), 429
    timestamps.append(now)
    IP_LIMITS[ip] = timestamps
    return None


@app.before_request
def before_request_hooks():
    from flask import request

    if request.path.startswith("/api/"):
        limit_res = rate_limit()
        if limit_res:
            return limit_res


# ─── DB helpers ───────────────────────────────────────────────────────────────
def _load_table(table: str) -> pd.DataFrame:
    """Load table from SQLite; fall back to CSV if needed."""
    if DB_PATH.exists():
        try:
            con = sqlite3.connect(DB_PATH, check_same_thread=False)
            # Enable WAL mode and synchronous normal to prevent race conditions
            con.execute("PRAGMA journal_mode=WAL;")
            con.execute("PRAGMA synchronous=NORMAL;")
            df = pd.read_sql(f"SELECT * FROM {table}", con)  # nosec B608 # noqa: S608
            con.close()
            if not df.empty:
                return _normalize_vessel_columns(df)
        except Exception as e:
            print(f"[DB] {table}: {e}")
    # CSV fallback
    csv_name = _CSV_MAP.get(table)
    if csv_name:
        csv_path = CSV_DIR / csv_name
        if csv_path.exists():
            try:
                return _normalize_vessel_columns(pd.read_csv(csv_path))
            except Exception as e:
                print(f"[CSV] {csv_path.name}: {e}")
    return pd.DataFrame()


def _normalize_vessel_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize legacy vessel labels read from existing databases and CSVs."""
    vessel_columns = [
        col
        for col in df.columns
        if str(col).strip().lower() in {"vessel", "vessel name"}
    ]
    for column in vessel_columns:
        df[column] = df[column].map(normalize_vessel_name)
    return df


def _filter_invalid_vessel_dates(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict]]:
    """Exclude implausible vessel dates and return actionable issue details."""
    if df.empty:
        return df, []

    valid_indices = []
    quality_issues = []
    for index, row in df.iterrows():
        issues = find_tdr_datetime_issues(row.to_dict())
        if not issues:
            valid_indices.append(index)
            continue

        quality_issues.append(
            {
                "filename": _safe(row.get("Filename"), "—"),
                "vessel": _safe(row.get("Vessel Name"), "—"),
                "voyage": _safe(row.get("Voyage"), "—"),
                "issues": issues,
            }
        )

    return df.loc[valid_indices].copy(), quality_issues


def _safe(v, default=None):
    if v is None:
        return default
    try:
        if pd.isna(v):
            return default
    except Exception:
        pass
    return v


def _to_float(v, default=0.0) -> float:
    try:
        f = float(v)
        return default if pd.isna(f) else f
    except Exception:
        return default


def _to_int(v, default=0) -> int:
    try:
        f = float(v)
        return default if pd.isna(f) else int(f)
    except Exception:
        return default


def _fmt_time(s) -> str | None:
    """Extract YYYY-MM-DD HH:MM from datetime string."""
    if not s or str(s) in ("None", "nan", "NaT", ""):
        return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s[:19], fmt).strftime("%Y-%m-%d %H:%M")
        except Exception:
            pass
    return s


def _time_to_float(s) -> float | None:
    """Convert HH:MM or datetime string to float hours (0-24)."""
    if not s or str(s) in ("None", "nan", "NaT", ""):
        return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            dt = datetime.strptime(s[:19], fmt)
            return dt.hour + dt.minute / 60
        except Exception:
            pass
    parts = s.replace(":", " ").split()
    if len(parts) >= 2:
        try:
            return int(parts[0]) + int(parts[1]) / 60
        except Exception:
            pass
    return None


def _sum_qc(df_qc: pd.DataFrame, vessel: str, voyage: str, col: str) -> float:
    if df_qc.empty or col not in df_qc.columns:
        return 0
    df = df_qc
    v_str = vessel.strip()
    voy_str = voyage.strip()
    mask = (df["Vessel Name"].astype(str).str.strip() == v_str) & (
        df["Voyage"].astype(str).str.strip() == voy_str
    )
    return df[mask][col].fillna(0).sum()


# ─── Build helpers ────────────────────────────────────────────────────────────
def _build_vessels(df_vessel: pd.DataFrame, df_qc: pd.DataFrame) -> list:
    if df_vessel.empty:
        return []
    df_vessel, _ = _filter_invalid_vessel_dates(df_vessel)
    if df_vessel.empty:
        return []
    cranes_map: dict = {}
    if not df_qc.empty and "Vessel Name" in df_qc.columns and "QC No." in df_qc.columns:
        qc_df = df_qc.copy()
        qc_df["Voyage"] = qc_df["Voyage"].astype(str).str.strip()
        cranes_map = (
            qc_df.groupby(["Vessel Name", "Voyage"])["QC No."].nunique().to_dict()
        )

    vessels = []
    for idx, (i, row) in enumerate(df_vessel.iterrows(), start=1):
        name = _safe(row.get("Vessel Name"), "Unknown")
        voyage = _safe(row.get("Voyage"), "—")
        voyage_str = str(voyage).strip()
        atb_raw = _safe(row.get("ATB"))
        atd_raw = _safe(row.get("ATD"))
        status = "Berthed" if not atd_raw else "Completed"
        vessels.append(
            {
                "id": idx,
                "name": name,
                "voyage": voyage,
                "op": _safe(row.get("Operator"), "—"),
                "berth": _safe(row.get("Berth"), "—"),
                "ata": _fmt_time(atb_raw),
                "atd": _fmt_time(atd_raw),
                "portstay": _safe(_to_float(row.get("Portstay (hrs)"))),
                "gross": _to_float(row.get("Gross Working (hrs)")),
                "net": _to_float(row.get("Net Working (hrs)")),
                "cranes": cranes_map.get((name, voyage_str), 1),
                "ci": _to_float(row.get("Vessel Moves/Portstay Hour")),
                "gmph": _to_float(row.get("Vessel Moves/Gross Hour")),
                "nmph": _to_float(row.get("Vessel Moves/Net Hour")),
                "dis": _to_int(_sum_qc(df_qc, name, voyage_str, "Discharge Conts")),
                "load": _to_int(_sum_qc(df_qc, name, voyage_str, "Load Conts")),
                "shift": _to_int(_sum_qc(df_qc, name, voyage_str, "Shifting Conts")),
                "conts": _to_int(row.get("Grand Total Conts")),
                "teus": _to_int(row.get("Grand Total TEUs")),
                "st": status,
            }
        )
    return vessels


def _build_qc(df_qc: pd.DataFrame) -> list:
    """Aggregate QC productivity per (QC No., Vessel Name) pair."""
    result = []
    if df_qc.empty:
        return result

    group_cols = ["QC No.", "Vessel Name"]
    sum_cols = {
        "Gross working (hrs)": "gH",
        "Net working (hrs)": "nH",
        "Delay times (hrs)": "dH",
        "Discharge Conts": "dis",
        "Load Conts": "load",
        "Shifting Conts": "sh",
        "Total Conts": "tot",
    }
    # Only aggregate existing columns
    agg_map = {col: "sum" for col in sum_cols if col in df_qc.columns}
    if not agg_map:
        return result

    try:
        grp = df_qc.groupby(group_cols, as_index=False).agg(agg_map)
    except Exception:
        grp = df_qc  # fallback to raw rows

    for _, row in grp.iterrows():
        gH = _to_float(row.get("Gross working (hrs)"))
        nH = _to_float(row.get("Net working (hrs)"))
        tot = _to_int(row.get("Total Conts"))
        gmh = round(tot / gH, 1) if gH > 0 else 0.0
        nmh = round(tot / nH, 1) if nH > 0 else 0.0
        result.append(
            {
                "qc": _safe(row.get("QC No."), "—"),
                "vessel": _safe(row.get("Vessel Name"), "—"),
                "gH": round(gH, 2),
                "nH": round(nH, 2),
                "dH": round(_to_float(row.get("Delay times (hrs)")), 2),
                "dis": _to_int(row.get("Discharge Conts")),
                "load": _to_int(row.get("Load Conts")),
                "sh": _to_int(row.get("Shifting Conts")),
                "tot": tot,
                "gmh": gmh,
                "nmh": nmh,
            }
        )
    return result


def _build_qc_operator(df_qc_op: pd.DataFrame) -> list:
    """Aggregate QC operator-adjusted productivity per (QC No., Vessel Name) pair."""
    result = []
    if df_qc_op.empty:
        return result

    group_cols = ["QC No.", "Vessel Name"]
    sum_cols = {
        "Gross working (hrs)": "gH",
        "Net working (hrs)": "nH",
        "Total Stop Time (hrs)": "dH",
        "Discharge Conts": "dis",
        "Load Conts": "load",
        "Shifting Conts": "sh",
        "Total Conts": "tot",
    }
    agg_map = {col: "sum" for col in sum_cols if col in df_qc_op.columns}
    if not agg_map:
        return result

    try:
        grp = df_qc_op.groupby(group_cols, as_index=False).agg(agg_map)
    except Exception:
        grp = df_qc_op

    for _, row in grp.iterrows():
        gH = _to_float(row.get("Gross working (hrs)"))
        nH = _to_float(row.get("Net working (hrs)"))
        tot = _to_int(row.get("Total Conts"))
        gmh = round(tot / gH, 1) if gH > 0 else 0.0
        nmh = round(tot / nH, 1) if nH > 0 else 0.0
        result.append(
            {
                "qc": _safe(row.get("QC No."), "—"),
                "vessel": _safe(row.get("Vessel Name"), "—"),
                "gH": round(gH, 2),
                "nH": round(nH, 2),
                "dH": round(_to_float(row.get("Total Stop Time (hrs)")), 2),
                "dis": _to_int(row.get("Discharge Conts")),
                "load": _to_int(row.get("Load Conts")),
                "sh": _to_int(row.get("Shifting Conts")),
                "tot": tot,
                "gmh": gmh,
                "nmh": nmh,
            }
        )
    return result


def _build_qc_timeline(df_qc: pd.DataFrame) -> list:
    if df_qc.empty or "QC No." not in df_qc.columns:
        return []
    vessels = df_qc["Vessel Name"].dropna().unique().tolist()
    v_color = {v: VESSEL_COLORS[i % len(VESSEL_COLORS)] for i, v in enumerate(vessels)}
    timeline = []
    for qc, grp in df_qc.groupby("QC No."):
        segs = []
        for _, row in grp.sort_values("Start Time", na_position="last").iterrows():
            start = _time_to_float(row.get("Start Time"))
            end = _time_to_float(row.get("End Time"))
            vessel = _safe(row.get("Vessel Name"), "")
            if start is not None and end is not None:
                if end > start:
                    segs.append(
                        {
                            "v": vessel,
                            "from": round(start, 2),
                            "to": round(end, 2),
                            "col": v_color.get(vessel, "#3B82F6"),
                        }
                    )
                else:
                    segs.append(
                        {
                            "v": vessel,
                            "from": round(start, 2),
                            "to": 24.0,
                            "col": v_color.get(vessel, "#3B82F6"),
                        }
                    )
                    segs.append(
                        {
                            "v": vessel,
                            "from": 0.0,
                            "to": round(end, 2),
                            "col": v_color.get(vessel, "#3B82F6"),
                        }
                    )
        if segs:
            timeline.append({"qc": qc, "segs": segs})
    return timeline


def _build_berths(df_vessel: pd.DataFrame, cranes_map: dict) -> list:
    if df_vessel.empty or "Berth" not in df_vessel.columns:
        return []

    df, _ = _filter_invalid_vessel_dates(df_vessel)
    if df.empty:
        return []

    df["ATB_dt"] = pd.to_datetime(df["ATB"], errors="coerce")

    all_berths = sorted(df["Berth"].dropna().unique().tolist())
    berths = []

    for b in all_berths:
        rows = df[df["Berth"] == b]
        if rows.empty:
            berths.append(
                {
                    "id": b,
                    "vessel": None,
                    "op": None,
                    "status": "Available",
                    "cranes": 0,
                    "pct": 0,
                    "conts": 0,
                    "atb": None,
                }
            )
        else:
            # Take the latest valid vessel that arrived at this berth.
            row = rows.sort_values("ATB_dt", ascending=False).iloc[0]
            name = _safe(row.get("Vessel Name"), "")
            voyage = _safe(row.get("Voyage"), "")
            voyage_str = str(voyage).strip()
            gross = _to_float(row.get("Gross Working (hrs)"))
            portstay = _to_float(row.get("Portstay (hrs)"))
            pct = int(min(99, (gross / max(portstay, 1)) * 100)) if portstay > 0 else 0
            berths.append(
                {
                    "id": b,
                    "vessel": name,
                    "op": _safe(row.get("Operator")),
                    "status": "Berthed",
                    "cranes": cranes_map.get((name, voyage_str), 1),
                    "pct": pct,
                    "conts": _to_int(row.get("Grand Total Conts")),
                    "atb": _fmt_time(row.get("ATB")),
                }
            )
    return berths


def _build_delays(df_delay: pd.DataFrame) -> list:
    """Build delay event list.
    The 'Remark' column sometimes contains only the Error Code letter (data quality issue).
    Fallback priority: Remark (if meaningful) → Stop Category → Error Type short.
    """
    result = []
    if df_delay.empty:
        return result
    for idx, (i, row) in enumerate(df_delay.iterrows(), start=1):
        code = _safe(row.get("Error Code"), "d")
        raw_rmk = _safe(row.get("Remark"), "")
        stop_cat = _safe(row.get("Stop Category"), "")
        # Remark is meaningless if it is identical to the error code (single letter)
        if raw_rmk and raw_rmk.strip() != code.strip():
            rmk = raw_rmk
        elif stop_cat:
            rmk = stop_cat
        else:
            rmk = _safe(row.get("Error Type"), "")
        result.append(
            {
                "id": idx,
                "vessel": _safe(row.get("Vessel Name"), "—"),
                "qc": _safe(row.get("QC No."), "—"),
                "from": _fmt_time(row.get("From Time")) or "—",
                "to": _fmt_time(row.get("To Time")) or "—",
                "dur": _to_float(row.get("Duration (hrs)")),
                "code": code,
                "type": _safe(row.get("Error Type"), "Terminal Convenience"),
                "cat": stop_cat,
                "rmk": rmk,
            }
        )
    return result


def _build_operators(df_vessel: pd.DataFrame) -> list:
    if df_vessel.empty or "Operator" not in df_vessel.columns:
        return []
    col = "Vessel Moves/Net Hour"
    if col not in df_vessel.columns:
        return []
    grp = df_vessel.groupby("Operator")[col].mean().reset_index()
    grp = grp.dropna().sort_values(col, ascending=False)
    result = []
    for _, row in grp.iterrows():
        result.append(
            {
                "op": row["Operator"],
                "nmh": round(_to_float(row[col]), 1),
                "col": VESSEL_COLORS[len(result) % len(VESSEL_COLORS)],
            }
        )
    return result


def _build_sparklines(df_vessel: pd.DataFrame, df_delay: pd.DataFrame) -> dict:
    empty = {
        "v": [0] * 8,
        "t": [0] * 8,
        "ps": [0] * 8,
        "nw": [0] * 8,
        "nm": [0] * 8,
        "dl": [0] * 8,
        "de": [0] * 8,
        "dh": [0] * 8,
    }
    if df_vessel.empty:
        return empty

    def _lst(df, col):
        if col not in df.columns:
            return [0] * 8
        vals = df[col].fillna(0).tolist()
        vals = vals[-8:] if len(vals) >= 8 else [0] * (8 - len(vals)) + vals
        return [round(_to_float(v), 1) for v in vals]

    sp = {
        "v": [0] * 8,
        "t": _lst(df_vessel, "Grand Total TEUs"),
        "ps": _lst(df_vessel, "Portstay (hrs)"),
        "nw": _lst(df_vessel, "Net Working (hrs)"),
        "nm": _lst(df_vessel, "Vessel Moves/Net Hour"),
        "dl": [0] * 8,
        "de": [0] * 8,
        "dh": [0] * 8,
    }
    n = min(len(df_vessel), 8)
    sp["v"] = [0] * (8 - n) + [1] * n

    if not df_delay.empty and "Duration (hrs)" in df_delay.columns:
        sp["dh"] = _lst(df_delay, "Duration (hrs)")
        sp["dl"] = _lst(df_delay, "Duration (hrs)")
        sp["de"] = [0] * (8 - min(len(df_delay), 8)) + [1] * min(len(df_delay), 8)

    return sp


def _build_market_stats(df_vessel: pd.DataFrame, df_cont: pd.DataFrame) -> list:
    if df_cont.empty:
        return []

    # 1. Prepare Columns for granular result
    # We want a record for each Vessel/Voyage containing all the mix stats

    # Status Mix columns
    full_cols = [c for c in df_cont.columns if "Full" in c or "Laden" in c]
    empty_cols = [c for c in df_cont.columns if "Empty" in c]

    # Size Mix columns
    s20 = [c for c in df_cont.columns if "_20" in c]
    s40 = [c for c in df_cont.columns if "_40" in c]
    s45 = [c for c in df_cont.columns if "_45" in c]

    # Aggregate at Vessel/Voyage/OperationType level
    # This is small enough to send (usually ~2-4 rows per vessel: Imp/Exp)
    df_cont["Full"] = df_cont[full_cols].sum(axis=1)
    df_cont["Empty"] = df_cont[empty_cols].sum(axis=1)
    df_cont["s20"] = df_cont[s20].sum(axis=1)
    df_cont["s40"] = df_cont[s40].sum(axis=1)
    df_cont["s45"] = df_cont[s45].sum(axis=1)

    # Keep only necessary columns
    needed = [
        "Vessel Name",
        "Voyage",
        "OperationType",
        "Total Conts",
        "Full",
        "Empty",
        "s20",
        "s40",
        "s45",
    ]
    res = df_cont[needed].copy()

    # Merge with Vessel metadata for filtering
    if not df_vessel.empty:
        v_meta = df_vessel[["Vessel Name", "Voyage", "Report Date", "Operator"]].copy()
        v_meta["Voyage"] = v_meta["Voyage"].astype(str).str.strip()
        res["Voyage"] = res["Voyage"].astype(str).str.strip()

        merged = res.merge(v_meta, on=["Vessel Name", "Voyage"], how="left")
        merged["Report Date"] = pd.to_datetime(
            merged["Report Date"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")
        return merged.fillna("").to_dict("records")

    return res.fillna("").to_dict("records")


def _build_feed(
    df_vessel: pd.DataFrame,
    df_delay: pd.DataFrame,
    df_qc: pd.DataFrame,
    date_quality_issues: list[dict] | None = None,
) -> list:
    now = datetime.now().strftime("%H:%M:%S")
    feed = []
    if not df_vessel.empty:
        feed.append(
            {
                "t": now,
                "lv": "SUCCESS",
                "m": f"[DB] vessel_summary loaded — {len(df_vessel)} records",
            }
        )
    if not df_qc.empty:
        col = "Net moves/h"
        avg = df_qc[col].mean() if col in df_qc.columns else 0
        feed.append(
            {
                "t": now,
                "lv": "INFO",
                "m": f"[Extractor] QC productivity: {len(df_qc)} records · avg nmh {avg:.1f}",
            }
        )
    if not df_delay.empty:
        total = (
            df_delay["Duration (hrs)"].sum()
            if "Duration (hrs)" in df_delay.columns
            else 0
        )
        feed.append(
            {
                "t": now,
                "lv": "INFO",
                "m": f"[Extractor] Delay events: {len(df_delay)} events · {total:.2f}h total",
            }
        )
    if df_vessel.empty and df_qc.empty:
        feed.append(
            {
                "t": now,
                "lv": "WARN",
                "m": "[DB] No data found — run TDR processing first",
            }
        )
    for item in (date_quality_issues or [])[:10]:
        details = ", ".join(
            f"{issue['field']}={issue['value']} ({issue['reason']})"
            for issue in item["issues"]
        )
        feed.append(
            {
                "t": now,
                "lv": "WARN",
                "m": (
                    f"[Data Quality] {item['filename']} · {item['vessel']} "
                    f"· voyage {item['voyage']}: {details}"
                ),
            }
        )
    feed.append(
        {
            "t": now,
            "lv": "INFO",
            "m": f"[API] Dashboard ready — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        }
    )
    return feed


# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(APP_DIR, "dashboard.html")


@app.route("/assets/<path:fn>")
def assets(fn):
    return send_from_directory(APP_DIR / "assets", fn)


@app.route("/api/meta")
@require_token
def api_meta():
    df = _load_table("vessel_summary")
    df, date_quality_issues = _filter_invalid_vessel_dates(df)
    mn = mx = report_date = ""
    vessel_count = 0
    if not df.empty:
        vessel_count = len(df)
        if "Report Date" in df.columns:
            dates = pd.to_datetime(df["Report Date"], errors="coerce").dropna()
            if not dates.empty:
                mn = dates.min().strftime("%Y-%m-%d")
                mx = dates.max().strftime("%Y-%m-%d")
                report_date = dates.max().strftime("%Y-%m-%d")
    return jsonify(
        {
            "version": APP_VERSION,
            "kpiTarget": KPI_TARGET,
            "dbStatus": "healthy" if DB_PATH.exists() else "csv_fallback",
            "vesselCount": vessel_count,
            "dataQualityIssueCount": len(date_quality_issues),
            "reportDate": report_date,
            "dateRange": {"min": mn, "max": mx},
        }
    )


_API_CACHE = {"timestamp": 0.0, "data": None}


@app.route("/api/cache/clear")
@require_token
def api_cache_clear():
    """Force-clear the in-memory API cache (debug/admin use)."""
    global _API_CACHE
    _API_CACHE["data"] = None
    _API_CACHE["timestamp"] = 0.0
    return jsonify(
        {"ok": True, "message": "Cache cleared. Next /api/data call will recompute."}
    )


@app.route("/api/data")
@require_token
def api_data():
    global _API_CACHE
    now = time.time()
    if _API_CACHE["data"] is not None and (now - _API_CACHE["timestamp"]) < 30.0:
        return jsonify(_API_CACHE["data"])

    df_vessel = _load_table("vessel_summary")
    df_vessel, date_quality_issues = _filter_invalid_vessel_dates(df_vessel)
    df_qc = _load_table("qc_productivity")
    df_qc_op = _load_table("qc_operator_productivity")
    df_cont = _load_table("container_details_wide")  # New table
    df_delay = _load_table("delay_events")
    if df_delay.empty:
        df_delay = _load_table("delay_details")

    cranes_map: dict = {}
    if not df_qc.empty and "Vessel Name" in df_qc.columns and "QC No." in df_qc.columns:
        qc_df = df_qc.copy()
        qc_df["Voyage"] = qc_df["Voyage"].astype(str).str.strip()
        cranes_map = (
            qc_df.groupby(["Vessel Name", "Voyage"])["QC No."].nunique().to_dict()
        )

    vessels = _build_vessels(df_vessel, df_qc)
    qc_data = _build_qc(df_qc)
    qc_op_data = _build_qc_operator(df_qc_op)
    timeline = _build_qc_timeline(df_qc)
    berths = _build_berths(df_vessel, cranes_map)
    delays = _build_delays(df_delay)
    operators = _build_operators(df_vessel)
    spark = _build_sparklines(df_vessel, df_delay)
    feed = _build_feed(df_vessel, df_delay, df_qc, date_quality_issues)
    market = _build_market_stats(df_vessel, df_cont)  # New stats

    report_date = ""
    if not df_vessel.empty and "Report Date" in df_vessel.columns:
        dates = pd.to_datetime(df_vessel["Report Date"], errors="coerce").dropna()
        if not dates.empty:
            report_date = dates.max().strftime("%Y-%m-%d")

    data = {
        "vessels": vessels,
        "qc": qc_data,
        "qcOperator": qc_op_data,
        "qcTimeline": timeline,
        "berths": berths,
        "delays": delays,
        "operators": operators,
        "market": market,  # New data
        "spark": spark,
        "feed": feed,
        "dataQualityIssues": date_quality_issues,
        "meta": {
            "kpiTarget": KPI_TARGET,
            "version": APP_VERSION,
            "dbStatus": "healthy" if DB_PATH.exists() else "csv_fallback",
            "reportDate": report_date,
            "vesselCount": len(vessels),
            "qcCount": len(qc_data),
            "qcOperatorCount": len(qc_op_data),
            "delayCount": len(delays),
            "dataQualityIssueCount": len(date_quality_issues),
        },
    }

    _API_CACHE["data"] = data
    _API_CACHE["timestamp"] = now
    return jsonify(data)


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[TDR Dashboard] http://{DASH_HOST}:{PORT}")
    if not DB_PATH.exists():
        print(f"[WARN] Database not found: {DB_PATH}")
        csv_found = any((CSV_DIR / f).exists() for f in _CSV_MAP.values())
        print(
            f"[INFO] CSV fallback {'available' if csv_found else 'NOT available — run TDR processing first'}"
        )
    app.run(host=DASH_HOST, port=PORT, debug=False)  # nosec B104 — host set via env, Docker overrides to 0.0.0.0
