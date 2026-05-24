"""
TDR Processor Dashboard — Flask API Server
==========================================
Serves dashboard.html and exposes /api/meta + /api/data endpoints backed by
the existing SQLite database (outputs/tdr_master.db) or CSV fallbacks.

Run:  python dashboard_api.py
Open: http://localhost:8503
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, send_from_directory

# ─── Config ──────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
DB_PATH    = BASE_DIR / os.environ.get("TDR_DB_PATH", "outputs/tdr_master.db")
CSV_DIR    = BASE_DIR / "outputs" / "data_csv"
PORT       = int(os.environ.get("TDR_DASH_PORT", "8503"))
KPI_TARGET = int(os.environ.get("TDR_KPI_TARGET", "45"))
APP_VERSION = "v1.0"

VESSEL_COLORS = [
    "#3B82F6", "#10B981", "#F59E0B", "#EF4444",
    "#8B5CF6", "#06B6D4", "#EC4899", "#14B8A6", "#F97316",
]

_CSV_MAP = {
    "vessel_summary":          "vessel_summary.csv",
    "qc_productivity":         "qc_productivity.csv",
    "qc_operator_productivity":"qc_operator_productivity.csv",
    "delay_events":            "delay_details.csv",
    "delay_details":           "delay_details.csv",
}

app = Flask(__name__, static_url_path="")


import functools
import time

# Secure API Token
API_TOKEN = os.environ.get("TDR_API_TOKEN", "admin123")
IP_LIMITS = {}  # {ip: [timestamps]} for lightweight rate limiting

def require_token(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        from flask import request
        token = request.headers.get("X-API-Token") or request.args.get("token")
        if token != API_TOKEN:
            return jsonify({"error": "Unauthorized", "message": "API Access Token is missing or invalid."}), 401
        return f(*args, **kwargs)
    return decorated


def rate_limit():
    from flask import request
    ip = request.remote_addr
    now = time.time()
    # clean up old timestamps (> 60 seconds)
    timestamps = [t for t in IP_LIMITS.get(ip, []) if now - t < 60]
    if len(timestamps) >= 60:  # limit to 60 requests per minute
        return jsonify({"error": "Too Many Requests", "message": "Rate limit exceeded. Max 60 requests per minute."}), 429
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
            df = pd.read_sql(f"SELECT * FROM {table}", con)  # noqa: S608
            con.close()
            if not df.empty:
                return df
        except Exception as e:
            print(f"[DB] {table}: {e}")
    # CSV fallback
    csv_name = _CSV_MAP.get(table)
    if csv_name:
        csv_path = CSV_DIR / csv_name
        if csv_path.exists():
            try:
                return pd.read_csv(csv_path)
            except Exception as e:
                print(f"[CSV] {csv_path.name}: {e}")
    return pd.DataFrame()


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
    v_str = str(vessel).strip()
    voy_str = str(voyage).strip()
    mask = (df["Vessel Name"].astype(str).str.strip() == v_str) & (df["Voyage"].astype(str).str.strip() == voy_str)
    return df[mask][col].fillna(0).sum()


# ─── Build helpers ────────────────────────────────────────────────────────────
def _build_vessels(df_vessel: pd.DataFrame, df_qc: pd.DataFrame) -> list:
    if df_vessel.empty:
        return []
    cranes_map: dict = {}
    if not df_qc.empty and "Vessel Name" in df_qc.columns and "QC No." in df_qc.columns:
        qc_df = df_qc.copy()
        qc_df["Voyage"] = qc_df["Voyage"].astype(str).str.strip()
        cranes_map = qc_df.groupby(["Vessel Name", "Voyage"])["QC No."].nunique().to_dict()

    vessels = []
    for i, row in df_vessel.iterrows():
        name    = _safe(row.get("Vessel Name"), "Unknown")
        voyage  = _safe(row.get("Voyage"), "—")
        voyage_str = str(voyage).strip()
        atb_raw = _safe(row.get("ATB"))
        atd_raw = _safe(row.get("ATD"))
        status  = "Berthed" if not atd_raw else "Completed"
        vessels.append({
            "id":       i + 1,
            "name":     name,
            "voyage":   voyage,
            "op":       _safe(row.get("Operator"), "—"),
            "berth":    _safe(row.get("Berth"), "—"),
            "ata":      _fmt_time(atb_raw),
            "atd":      _fmt_time(atd_raw),
            "portstay": _safe(_to_float(row.get("Portstay (hrs)"))),
            "gross":    _to_float(row.get("Gross Working (hrs)")),
            "net":      _to_float(row.get("Net Working (hrs)")),
            "cranes":   cranes_map.get((name, voyage_str), 1),
            "ci":       _to_float(row.get("Vessel Moves/Portstay Hour")),
            "gmph":     _to_float(row.get("Vessel Moves/Gross Hour")),
            "nmph":     _to_float(row.get("Vessel Moves/Net Hour")),
            "dis":      _to_int(_sum_qc(df_qc, name, voyage_str, "Discharge Conts")),
            "load":     _to_int(_sum_qc(df_qc, name, voyage_str, "Load Conts")),
            "shift":    _to_int(_sum_qc(df_qc, name, voyage_str, "Shifting Conts")),
            "conts":    _to_int(row.get("Grand Total Conts")),
            "teus":     _to_int(row.get("Grand Total TEUs")),
            "st":       status,
        })
    return vessels


def _build_qc(df_qc: pd.DataFrame) -> list:
    """Aggregate QC productivity per (QC No., Vessel Name) pair."""
    result = []
    if df_qc.empty:
        return result

    group_cols = ["QC No.", "Vessel Name"]
    sum_cols = {
        "Gross working (hrs)": "gH",
        "Net working (hrs)":   "nH",
        "Delay times (hrs)":   "dH",
        "Discharge Conts":     "dis",
        "Load Conts":          "load",
        "Shifting Conts":      "sh",
        "Total Conts":         "tot",
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
        gH  = _to_float(row.get("Gross working (hrs)"))
        nH  = _to_float(row.get("Net working (hrs)"))
        tot = _to_int(row.get("Total Conts"))
        gmh = round(tot / gH, 1) if gH > 0 else 0.0
        nmh = round(tot / nH, 1) if nH > 0 else 0.0
        result.append({
            "qc":    _safe(row.get("QC No."), "—"),
            "vessel":_safe(row.get("Vessel Name"), "—"),
            "gH":    round(gH, 2),
            "nH":    round(nH, 2),
            "dH":    round(_to_float(row.get("Delay times (hrs)")), 2),
            "dis":   _to_int(row.get("Discharge Conts")),
            "load":  _to_int(row.get("Load Conts")),
            "sh":    _to_int(row.get("Shifting Conts")),
            "tot":   tot,
            "gmh":   gmh,
            "nmh":   nmh,
        })
    return result


def _build_qc_operator(df_qc_op: pd.DataFrame) -> list:
    """Aggregate QC operator-adjusted productivity per (QC No., Vessel Name) pair."""
    result = []
    if df_qc_op.empty:
        return result

    group_cols = ["QC No.", "Vessel Name"]
    sum_cols = {
        "Gross working (hrs)": "gH",
        "Net working (hrs)":   "nH",
        "Total Stop Time (hrs)": "dH",
        "Discharge Conts":     "dis",
        "Load Conts":          "load",
        "Shifting Conts":      "sh",
        "Total Conts":         "tot",
    }
    agg_map = {col: "sum" for col in sum_cols if col in df_qc_op.columns}
    if not agg_map:
        return result

    try:
        grp = df_qc_op.groupby(group_cols, as_index=False).agg(agg_map)
    except Exception:
        grp = df_qc_op

    for _, row in grp.iterrows():
        gH  = _to_float(row.get("Gross working (hrs)"))
        nH  = _to_float(row.get("Net working (hrs)"))
        tot = _to_int(row.get("Total Conts"))
        gmh = round(tot / gH, 1) if gH > 0 else 0.0
        nmh = round(tot / nH, 1) if nH > 0 else 0.0
        result.append({
            "qc":    _safe(row.get("QC No."), "—"),
            "vessel":_safe(row.get("Vessel Name"), "—"),
            "gH":    round(gH, 2),
            "nH":    round(nH, 2),
            "dH":    round(_to_float(row.get("Total Stop Time (hrs)")), 2),
            "dis":   _to_int(row.get("Discharge Conts")),
            "load":  _to_int(row.get("Load Conts")),
            "sh":    _to_int(row.get("Shifting Conts")),
            "tot":   tot,
            "gmh":   gmh,
            "nmh":   nmh,
        })
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
            end   = _time_to_float(row.get("End Time"))
            vessel = _safe(row.get("Vessel Name"), "")
            if start is not None and end is not None:
                if end > start:
                    segs.append({
                        "v":    vessel,
                        "from": round(start, 2),
                        "to":   round(end, 2),
                        "col":  v_color.get(vessel, "#3B82F6"),
                    })
                else:
                    segs.append({
                        "v":    vessel,
                        "from": round(start, 2),
                        "to":   24.0,
                        "col":  v_color.get(vessel, "#3B82F6"),
                    })
                    segs.append({
                        "v":    vessel,
                        "from": 0.0,
                        "to":   round(end, 2),
                        "col":  v_color.get(vessel, "#3B82F6"),
                    })
        if segs:
            timeline.append({"qc": qc, "segs": segs})
    return timeline


def _build_berths(df_vessel: pd.DataFrame, cranes_map: dict) -> list:
    if df_vessel.empty or "Berth" not in df_vessel.columns:
        return []
    df = df_vessel.copy()
    all_berths = sorted(df["Berth"].dropna().unique().tolist())
    berths = []
    for b in all_berths:
        rows = df[df["Berth"] == b]
        if rows.empty:
            berths.append({"id": b, "vessel": None, "op": None, "status": "Available",
                           "cranes": 0, "pct": 0, "conts": 0, "atb": None})
        else:
            row = rows.sort_values("ATB", ascending=False).iloc[0]
            name    = _safe(row.get("Vessel Name"), "")
            voyage  = _safe(row.get("Voyage"), "")
            voyage_str = str(voyage).strip()
            gross   = _to_float(row.get("Gross Working (hrs)"))
            portstay= _to_float(row.get("Portstay (hrs)"))
            pct     = int(min(99, (gross / max(portstay, 1)) * 100)) if portstay > 0 else 0
            berths.append({
                "id":     b,
                "vessel": name,
                "op":     _safe(row.get("Operator")),
                "status": "Berthed",
                "cranes": cranes_map.get((name, voyage_str), 1),
                "pct":    pct,
                "conts":  _to_int(row.get("Grand Total Conts")),
                "atb":    _fmt_time(row.get("ATB")),
            })
    return berths


def _build_delays(df_delay: pd.DataFrame) -> list:
    """Build delay event list.
    The 'Remark' column sometimes contains only the Error Code letter (data quality issue).
    Fallback priority: Remark (if meaningful) → Stop Category → Error Type short.
    """
    result = []
    if df_delay.empty:
        return result
    for i, row in df_delay.iterrows():
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
        result.append({
            "id":     i + 1,
            "vessel": _safe(row.get("Vessel Name"), "—"),
            "qc":     _safe(row.get("QC No."), "—"),
            "from":   _fmt_time(row.get("From Time")) or "—",
            "to":     _fmt_time(row.get("To Time")) or "—",
            "dur":    _to_float(row.get("Duration (hrs)")),
            "code":   code,
            "type":   _safe(row.get("Error Type"), "Terminal Convenience"),
            "cat":    stop_cat,
            "rmk":    rmk,
        })
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
        result.append({
            "op":  row["Operator"],
            "nmh": round(_to_float(row[col]), 1),
            "col": VESSEL_COLORS[len(result) % len(VESSEL_COLORS)],
        })
    return result


def _build_sparklines(df_vessel: pd.DataFrame, df_delay: pd.DataFrame) -> dict:
    empty = {"v": [0]*8, "t": [0]*8, "ps": [0]*8, "nw": [0]*8,
             "nm": [0]*8, "dl": [0]*8, "de": [0]*8, "dh": [0]*8}
    if df_vessel.empty:
        return empty

    def _lst(df, col):
        if col not in df.columns:
            return [0]*8
        vals = df[col].fillna(0).tolist()
        vals = vals[-8:] if len(vals) >= 8 else [0]*(8-len(vals)) + vals
        return [round(_to_float(v), 1) for v in vals]

    sp = {
        "v":  [0]*8,
        "t":  _lst(df_vessel, "Grand Total TEUs"),
        "ps": _lst(df_vessel, "Portstay (hrs)"),
        "nw": _lst(df_vessel, "Net Working (hrs)"),
        "nm": _lst(df_vessel, "Vessel Moves/Net Hour"),
        "dl": [0]*8, "de": [0]*8, "dh": [0]*8,
    }
    n = min(len(df_vessel), 8)
    sp["v"] = [0]*(8-n) + [1]*n

    if not df_delay.empty and "Duration (hrs)" in df_delay.columns:
        sp["dh"] = _lst(df_delay, "Duration (hrs)")
        sp["dl"] = _lst(df_delay, "Duration (hrs)")
        sp["de"] = [0]*(8-min(len(df_delay), 8)) + [1]*min(len(df_delay), 8)

    return sp


def _build_feed(df_vessel: pd.DataFrame, df_delay: pd.DataFrame, df_qc: pd.DataFrame) -> list:
    now = datetime.now().strftime("%H:%M:%S")
    feed = []
    if not df_vessel.empty:
        feed.append({"t": now, "lv": "SUCCESS",
                     "m": f"[DB] vessel_summary loaded — {len(df_vessel)} records"})
    if not df_qc.empty:
        col = "Net moves/h"
        avg = df_qc[col].mean() if col in df_qc.columns else 0
        feed.append({"t": now, "lv": "INFO",
                     "m": f"[Extractor] QC productivity: {len(df_qc)} records · avg nmh {avg:.1f}"})
    if not df_delay.empty:
        total = df_delay["Duration (hrs)"].sum() if "Duration (hrs)" in df_delay.columns else 0
        feed.append({"t": now, "lv": "INFO",
                     "m": f"[Extractor] Delay events: {len(df_delay)} events · {total:.2f}h total"})
    if df_vessel.empty and df_qc.empty:
        feed.append({"t": now, "lv": "WARN",
                     "m": "[DB] No data found — run TDR processing first"})
    feed.append({"t": now, "lv": "INFO",
                 "m": f"[API] Dashboard ready — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"})
    return feed


# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "dashboard.html")


@app.route("/assets/<path:fn>")
def assets(fn):
    return send_from_directory(BASE_DIR / "assets", fn)


@app.route("/api/meta")
@require_token
def api_meta():
    df = _load_table("vessel_summary")
    mn = mx = report_date = ""
    vessel_count = 0
    if not df.empty:
        vessel_count = len(df)
        if "Report Date" in df.columns:
            dates = pd.to_datetime(df["Report Date"], errors="coerce").dropna()
            if not dates.empty:
                mn          = dates.min().strftime("%Y-%m-%d")
                mx          = dates.max().strftime("%Y-%m-%d")
                report_date = dates.max().strftime("%Y-%m-%d")
    return jsonify({
        "version":     APP_VERSION,
        "kpiTarget":   KPI_TARGET,
        "dbStatus":    "healthy" if DB_PATH.exists() else "csv_fallback",
        "vesselCount": vessel_count,
        "reportDate":  report_date,
        "dateRange":   {"min": mn, "max": mx},
    })


_API_CACHE = {
    "timestamp": 0.0,
    "data": None
}


@app.route("/api/cache/clear")
@require_token
def api_cache_clear():
    """Force-clear the in-memory API cache (debug/admin use)."""
    global _API_CACHE
    _API_CACHE["data"] = None
    _API_CACHE["timestamp"] = 0.0
    return jsonify({"ok": True, "message": "Cache cleared. Next /api/data call will recompute."})


@app.route("/api/data")
@require_token
def api_data():
    global _API_CACHE
    now = time.time()
    if _API_CACHE["data"] is not None and (now - _API_CACHE["timestamp"]) < 30.0:
        return jsonify(_API_CACHE["data"])

    df_vessel = _load_table("vessel_summary")
    df_qc     = _load_table("qc_productivity")
    df_qc_op  = _load_table("qc_operator_productivity")
    df_delay  = _load_table("delay_events")
    if df_delay.empty:
        df_delay = _load_table("delay_details")

    cranes_map: dict = {}
    if not df_qc.empty and "Vessel Name" in df_qc.columns and "QC No." in df_qc.columns:
        qc_df = df_qc.copy()
        qc_df["Voyage"] = qc_df["Voyage"].astype(str).str.strip()
        cranes_map = qc_df.groupby(["Vessel Name", "Voyage"])["QC No."].nunique().to_dict()

    vessels    = _build_vessels(df_vessel, df_qc)
    qc_data    = _build_qc(df_qc)
    qc_op_data = _build_qc_operator(df_qc_op)
    timeline   = _build_qc_timeline(df_qc)
    berths     = _build_berths(df_vessel, cranes_map)
    delays     = _build_delays(df_delay)
    operators  = _build_operators(df_vessel)
    spark      = _build_sparklines(df_vessel, df_delay)
    feed       = _build_feed(df_vessel, df_delay, df_qc)

    report_date = ""
    if not df_vessel.empty and "Report Date" in df_vessel.columns:
        dates = pd.to_datetime(df_vessel["Report Date"], errors="coerce").dropna()
        if not dates.empty:
            report_date = dates.max().strftime("%Y-%m-%d")

    data = {
        "vessels":    vessels,
        "qc":         qc_data,
        "qcOperator": qc_op_data,
        "qcTimeline": timeline,
        "berths":     berths,
        "delays":     delays,
        "operators":  operators,
        "spark":      spark,
        "feed":       feed,
        "meta": {
            "kpiTarget":       KPI_TARGET,
            "version":         APP_VERSION,
            "dbStatus":        "healthy" if DB_PATH.exists() else "csv_fallback",
            "reportDate":      report_date,
            "vesselCount":     len(vessels),
            "qcCount":         len(qc_data),
            "qcOperatorCount": len(qc_op_data),
            "delayCount":      len(delays),
        },
    }

    _API_CACHE["data"] = data
    _API_CACHE["timestamp"] = now
    return jsonify(data)


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[TDR Dashboard] http://localhost:{PORT}")
    if not DB_PATH.exists():
        print(f"[WARN] Database not found: {DB_PATH}")
        csv_found = any((CSV_DIR / f).exists() for f in _CSV_MAP.values())
        print(f"[INFO] CSV fallback {'available' if csv_found else 'NOT available — run TDR processing first'}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
