# api.py
"""
FastAPI REST API for TDR Processor.

Exposes TDR data and processing capabilities via HTTP endpoints,
enabling integration with Power BI, Excel, or other systems.

Run with:
    uvicorn api:app --host 0.0.0.0 --port 8000 --reload

API Documentation available at:
    http://localhost:8000/docs  (Swagger UI)
    http://localhost:8000/redoc (ReDoc)
"""

import hmac
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import config
import pandas as pd
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

# ============================================================================
# AUTH CONFIG
# ============================================================================

_api_key_header = APIKeyHeader(name="X-API-Token", auto_error=False)


async def _require_token(api_key: Optional[str] = Security(_api_key_header)) -> None:
    """FastAPI dependency that enforces token auth on protected endpoints."""
    auth_disabled = os.environ.get("TDR_AUTH_DISABLED", "false").lower() == "true"
    if auth_disabled:
        return
    api_token_raw = os.environ.get("TDR_API_TOKEN", "")
    if not api_key or not hmac.compare_digest(api_key, api_token_raw):
        raise HTTPException(
            status_code=401, detail="Unauthorized: API token missing or invalid."
        )


# ============================================================================
# APP INITIALIZATION
# ============================================================================

_allowed_origins_raw = os.environ.get(
    "TDR_ALLOWED_ORIGINS", "http://localhost:8503,http://127.0.0.1:8503"
)
ALLOWED_ORIGINS: List[str] = [
    o.strip() for o in _allowed_origins_raw.split(",") if o.strip()
]
API_HOST = os.environ.get("TDR_API_HOST", "127.0.0.1")

app = FastAPI(
    title="TDR Processor API",
    description="REST API for accessing and processing Terminal Daily Report (TDR) data",
    version=config.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS restricted to configured origins (default: localhost dashboard only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    auth_disabled = os.environ.get("TDR_AUTH_DISABLED", "false").lower() == "true"
    api_token_raw = os.environ.get("TDR_API_TOKEN", "")
    if not auth_disabled and not api_token_raw:
        raise RuntimeError(
            "[TDR API] TDR_API_TOKEN environment variable is not set. "
            "Set it before starting the server, or set TDR_AUTH_DISABLED=true for local dev."
        )


# ============================================================================
# PYDANTIC MODELS (Request/Response)
# ============================================================================


class ProcessingRequest(BaseModel):
    """Request body for triggering file processing."""

    overwrite: bool = False
    check_duplicates: bool = True
    input_dir: Optional[str] = None
    output_dir: Optional[str] = None


class ProcessingResult(BaseModel):
    """Response from processing operation."""

    message: str
    processed_count: int
    skipped_count: int
    duplicate_count: int = 0
    time_taken: float = 0.0
    errors: List[str] = []


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    timestamp: str
    data_summary: Dict[str, Any] = {}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _get_db():
    """Get database instance (lazy initialization), always using the canonical DB path."""
    try:
        from utils.database import TDRDatabase

        return TDRDatabase(Path("outputs/tdr_master.db"))
    except Exception as e:
        logging.warning(f"[API] Database not available: {e}. Falling back to CSV.")
        return None


_csv_cache = {}


def _load_csv_data(csv_name: str):
    """Load data from CSV file as fallback when DB is not available, with mtime-based caching."""
    import pandas as pd

    csv_path = Path("outputs/data_csv") / csv_name
    if not csv_path.exists():
        return None

    try:
        mtime = csv_path.stat().st_mtime
    except OSError:
        mtime = 0.0

    cache_entry = _csv_cache.get(csv_name)
    if cache_entry and cache_entry["mtime"] == mtime:
        return cache_entry["df"].copy()

    try:
        df = pd.read_csv(csv_path)
        _csv_cache[csv_name] = {"mtime": mtime, "df": df}
        return df.copy()
    except Exception as e:
        logging.error(f"[API] Error loading CSV {csv_name}: {e}")
        if cache_entry:
            return cache_entry["df"].copy()
        return None


def _load_table_df(table_name: str, csv_name: str) -> pd.DataFrame:
    """Load table from SQLite database, falling back to CSV if empty or on error."""
    import pandas as pd
    db = _get_db()
    if db:
        try:
            with db._get_connection() as conn:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)  # nosec B608
                if not df.empty:
                    return df
        except Exception as e:
            logging.warning(f"[API] Error loading {table_name} from DB: {e}. Falling back to CSV.")
    
    # Fallback to CSV
    df_csv = _load_csv_data(csv_name)
    if df_csv is not None:
        return df_csv
    return pd.DataFrame()


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================


@app.get("/health", response_model=HealthResponse, tags=["Status"])
async def health_check():
    """
    Health check endpoint (public — does not expose sensitive data).
    """
    summary = {}
    import pandas as pd

    db = _get_db()
    db_has_data = False
    if db:
        try:
            summary = db.get_summary_stats()
            if summary.get("vessel_count", 0) > 0:
                db_has_data = True
        except Exception:
            pass

    if not db_has_data:
        # Fallback to CSV files counts & stats
        try:
            df_vessel = _load_csv_data("vessel_summary.csv")
            df_qc = _load_csv_data("qc_productivity.csv")
            df_delay = _load_csv_data("delay_details.csv")
            df_cont = _load_csv_data("container_details_long.csv")

            vessel_count = len(df_vessel) if df_vessel is not None else 0
            qc_count = len(df_qc) if df_qc is not None else 0
            delay_count = len(df_delay) if df_delay is not None else 0
            container_count = len(df_cont) if df_cont is not None else 0

            date_from = None
            date_to = None
            if df_vessel is not None and not df_vessel.empty:
                col_report_date = "Report Date" if "Report Date" in df_vessel.columns else "report_date"
                if col_report_date in df_vessel.columns:
                    dates = pd.to_datetime(df_vessel[col_report_date], errors="coerce").dropna()
                    if not dates.empty:
                        date_from = dates.min().strftime("%Y-%m-%d")
                        date_to = dates.max().strftime("%Y-%m-%d")

            summary = {
                "vessel_count": vessel_count,
                "qc_records": qc_count,
                "delay_records": delay_count,
                "container_records": container_count,
                "date_from": date_from,
                "date_to": date_to,
                "db_path": str(db.db_path) if db else "outputs/tdr_master.db",
                "schema_version": "1.0.0",
            }
        except Exception as e:
            logging.error(f"[API] Error generating CSV fallback stats: {e}")
            csv_dir = Path("outputs/data_csv")
            if csv_dir.exists():
                summary["csv_files"] = [f.name for f in csv_dir.glob("*.csv")]

    return HealthResponse(
        status="healthy",
        version=config.APP_VERSION,
        timestamp=datetime.now().isoformat(),
        data_summary=summary,
    )


@app.get("/", tags=["Status"])
async def root():
    """API root - redirects to documentation."""
    return {"message": "TDR Processor API", "docs": "/docs", "health": "/health"}


# ============================================================================
# VESSEL ENDPOINTS
# ============================================================================


@app.get("/api/vessels", tags=["Vessels"], dependencies=[Depends(_require_token)])
async def get_vessels(
    operator: Optional[str] = Query(
        None, description="Filter by shipping line operator"
    ),
    berth: Optional[str] = Query(None, description="Filter by berth location"),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    limit: int = Query(
        10000,
        ge=1,
        le=100000,
        description="Maximum records to return",
    ),
):
    """
    Get vessel summary data with optional filters.

    Returns vessel performance metrics including portstay, working hours,
    container counts, and productivity rates.
    """
    import pandas as pd

    db = _get_db()
    df = None
    if db:
        try:
            df = db.query_vessels(
                operator=operator,
                berth=berth,
                date_from=date_from,
                date_to=date_to,
                limit=limit,
            )
        except Exception as e:
            logging.warning(f"[API] Error querying vessels from DB: {e}. Falling back to CSV.")
    if df is None or df.empty:
        df = _load_csv_data("vessel_summary.csv")
        if df is None:
            raise HTTPException(status_code=404, detail="No vessel data available")
        if operator:
            col_op = "Operator" if "Operator" in df.columns else "operator"
            df = df[df[col_op] == operator]
        if berth:
            col_berth = "Berth" if "Berth" in df.columns else "berth"
            df = df[df[col_berth] == berth]
        df = df.head(limit)

    return {
        "count": len(df),
        "data": df.where(pd.notna(df), None).to_dict(orient="records"),
    }


@app.get(
    "/api/vessels/{filename}", tags=["Vessels"], dependencies=[Depends(_require_token)]
)
async def get_vessel_by_filename(filename: str):
    """Get a specific vessel record by TDR filename."""
    import pandas as pd

    db = _get_db()
    df = None
    if db:
        try:
            df = db.query_vessels(limit=10000)
            if not df.empty:
                df = (
                    df[df["filename"] == filename]
                    if "filename" in df.columns
                    else df[df["Filename"] == filename]
                )
        except Exception as e:
            logging.warning(f"[API] Error querying vessels from DB: {e}. Falling back to CSV.")
    if df is None or df.empty:
        df = _load_csv_data("vessel_summary.csv")
        if df is None:
            raise HTTPException(status_code=404, detail="No vessel data available")
        col = "Filename" if "Filename" in df.columns else "filename"
        df = df[df[col] == filename]

    if df.empty:
        raise HTTPException(status_code=404, detail=f"Vessel '{filename}' not found")

    return df.where(pd.notna(df), None).to_dict(orient="records")[0]


# ============================================================================
# QC PRODUCTIVITY ENDPOINTS
# ============================================================================


@app.get(
    "/api/qc-productivity",
    tags=["QC Productivity"],
    dependencies=[Depends(_require_token)],
)
async def get_qc_productivity(
    filename: Optional[str] = Query(None, description="Filter by TDR filename"),
    qc_no: Optional[str] = Query(None, description="Filter by QC number (e.g., GC01)"),
    limit: int = Query(500, ge=1, le=10000),
):
    """Get QC crane productivity data."""
    import pandas as pd

    db = _get_db()
    df = None
    if db:
        try:
            df = db.query_qc_productivity(filename=filename, qc_no=qc_no, limit=limit)
        except Exception as e:
            logging.warning(f"[API] Error querying QC productivity from DB: {e}. Falling back to CSV.")
    if df is None or df.empty:
        df = _load_csv_data("qc_productivity.csv")
        if df is None:
            raise HTTPException(
                status_code=404, detail="No QC productivity data available"
            )
        if filename:
            col = "Filename" if "Filename" in df.columns else "filename"
            df = df[df[col] == filename]
        df = df.head(limit)

    return {
        "count": len(df),
        "data": df.where(pd.notna(df), None).to_dict(orient="records"),
    }


# ============================================================================
# DELAY ANALYSIS ENDPOINTS
# ============================================================================


@app.get("/api/delays", tags=["Delay Analysis"], dependencies=[Depends(_require_token)])
async def get_delays(
    filename: Optional[str] = Query(None, description="Filter by TDR filename"),
    error_type: Optional[str] = Query(None, description="Filter by error type"),
    limit: int = Query(1000, ge=1, le=50000),
):
    """Get delay event records."""
    import pandas as pd

    db = _get_db()
    df = None
    if db:
        try:
            df = db.query_delay_details(
                filename=filename, error_type=error_type, limit=limit
            )
        except Exception as e:
            logging.warning(f"[API] Error querying delay details from DB: {e}. Falling back to CSV.")
    if df is None or df.empty:
        df = _load_csv_data("delay_details.csv")
        if df is None:
            raise HTTPException(status_code=404, detail="No delay data available")
        if filename:
            col = "Filename" if "Filename" in df.columns else "filename"
            df = df[df[col] == filename]
        df = df.head(limit)

    return {
        "count": len(df),
        "data": df.where(pd.notna(df), None).to_dict(orient="records"),
    }


@app.get(
    "/api/delays/summary",
    tags=["Delay Analysis"],
    dependencies=[Depends(_require_token)],
)
async def get_delay_summary():
    """Get aggregated delay statistics by error type."""

    df = _load_table_df("delay_details", "delay_details.csv")
    if df.empty:
        raise HTTPException(status_code=404, detail="No delay data available")

    error_col = "Error Type" if "Error Type" in df.columns else "error_type"
    duration_col = (
        "Duration (hrs)" if "Duration (hrs)" in df.columns else "duration_hrs"
    )

    if error_col in df.columns and duration_col in df.columns:
        summary = (
            df.groupby(error_col)[duration_col]
            .agg(total_hours="sum", count="count", avg_hours="mean")
            .round(2)
            .reset_index()
        )
        return summary.to_dict(orient="records")

    return []


# ============================================================================
# CONTAINER ENDPOINTS
# ============================================================================


@app.get(
    "/api/containers",
    tags=["Container Details"],
    dependencies=[Depends(_require_token)],
)
async def get_containers(
    filename: Optional[str] = Query(None, description="Filter by TDR filename"),
    operation_type: Optional[str] = Query(None, description="Filter by operation type"),
    limit: int = Query(1000, ge=1, le=50000),
):
    """Get container detail records."""
    import pandas as pd

    df = _load_table_df("container_details", "container_details_long.csv")
    if df.empty:
        raise HTTPException(status_code=404, detail="No container data available")

    if filename:
        col = "Filename" if "Filename" in df.columns else "filename"
        df = df[df[col] == filename]
    if operation_type:
        op_col = "OperationType" if "OperationType" in df.columns else "operation_type"
        if op_col in df.columns:
            df = df[df[op_col] == operation_type]

    df = df.head(limit)
    return {
        "count": len(df),
        "data": df.where(pd.notna(df), None).to_dict(orient="records"),
    }


# ============================================================================
# PROCESSING ENDPOINTS
# ============================================================================

_processing_status: Dict[str, Any] = {"running": False, "last_result": None}


@app.post(
    "/api/process",
    response_model=ProcessingResult,
    tags=["Processing"],
    dependencies=[Depends(_require_token)],
)
async def trigger_processing(
    request: ProcessingRequest,
    background_tasks: BackgroundTasks,
):
    """
    Trigger TDR file processing.

    Processes all Excel files in the input directory and updates the database.
    Returns immediately with status; processing runs in background.
    """
    if _processing_status["running"]:
        raise HTTPException(
            status_code=409, detail="Processing already in progress. Please wait."
        )

    from core_processor import auto_process_input_folder

    input_dir = Path(request.input_dir) if request.input_dir else None
    output_dir = Path(request.output_dir) if request.output_dir else None

    _processing_status["running"] = True

    try:
        result = auto_process_input_folder(
            input_dir=input_dir,
            output_dir=output_dir,
            overwrite=request.overwrite,
            check_duplicates=request.check_duplicates,
        )
        _processing_status["last_result"] = result
        return ProcessingResult(
            message=result.get("message", "Processing complete"),
            processed_count=result.get("processed_count", 0),
            skipped_count=result.get("skipped_count", 0),
            duplicate_count=result.get("duplicate_count", 0),
            time_taken=result.get("time_taken", 0.0),
            errors=result.get("errors", []),
        )
    except Exception as e:
        logging.error(f"[API] Processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        _processing_status["running"] = False


@app.get(
    "/api/process/status", tags=["Processing"], dependencies=[Depends(_require_token)]
)
async def get_processing_status():
    """Get current processing status and last result."""
    return {
        "running": _processing_status["running"],
        "last_result": _processing_status["last_result"],
    }


# ============================================================================
# EXPORT ENDPOINTS
# ============================================================================


@app.get("/api/export/{table}", tags=["Export"], dependencies=[Depends(_require_token)])
async def export_csv(
    table: str,
    background_tasks: BackgroundTasks,
):
    """
    Download a data table as CSV file.

    Available tables: vessel_summary, qc_productivity, delay_details,
    container_details_long, qc_operator_productivity
    """
    table_to_csv = {
        "vessel_summary": "vessel_summary.csv",
        "qc_productivity": "qc_productivity.csv",
        "qc_operator_productivity": "qc_operator_productivity.csv",
        "delay_details": "delay_details.csv",
        "container_details": "container_details_long.csv",
    }

    if table not in table_to_csv:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown table '{table}'. Available: {list(table_to_csv.keys())}",
        )

    csv_path = Path("outputs/data_csv") / table_to_csv[table]
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail=f"No data available for '{table}'")

    return FileResponse(
        path=str(csv_path),
        media_type="text/csv",
        filename=table_to_csv[table],
    )


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================


@app.get(
    "/api/analytics/kpi", tags=["Analytics"], dependencies=[Depends(_require_token)]
)
async def get_kpi_summary(
    kpi_target: float = Query(45.0, description="KPI target moves/hour"),
):
    """
    Get KPI performance summary.

    Returns vessels above/below KPI target and overall statistics.
    """

    df = _load_table_df("vessel_summary", "vessel_summary.csv")
    if df.empty:
        raise HTTPException(status_code=404, detail="No vessel data available")

    # Calculate net moves/h
    conts_col = "Grand Total Conts" if "Grand Total Conts" in df.columns else None
    net_col = "Net Working (hrs)" if "Net Working (hrs)" in df.columns else None

    if conts_col and net_col:
        df["net_moves_h"] = (
            (df[conts_col] / df[net_col])
            .replace([float("inf"), float("-inf")], 0)
            .fillna(0)
            .round(1)
        )

        above_kpi = df[df["net_moves_h"] >= kpi_target]
        below_kpi = df[df["net_moves_h"] < kpi_target]

        return {
            "kpi_target": kpi_target,
            "total_vessels": len(df),
            "above_kpi": len(above_kpi),
            "below_kpi": len(below_kpi),
            "avg_net_moves_h": round(df["net_moves_h"].mean(), 2),
            "max_net_moves_h": round(df["net_moves_h"].max(), 2),
            "min_net_moves_h": round(df["net_moves_h"].min(), 2),
            "kpi_achievement_rate": round(len(above_kpi) / len(df) * 100, 1)
            if len(df) > 0
            else 0,
        }

    return {"error": "Required columns not available"}


@app.get(
    "/api/analytics/operators",
    tags=["Analytics"],
    dependencies=[Depends(_require_token)],
)
async def get_operator_performance():
    """Get performance statistics grouped by shipping line operator."""

    df = _load_table_df("vessel_summary", "vessel_summary.csv")
    if df.empty:
        raise HTTPException(status_code=404, detail="No vessel data available")

    op_col = "Operator" if "Operator" in df.columns else None
    if not op_col:
        raise HTTPException(status_code=400, detail="Operator column not found")

    conts_col = "Grand Total Conts" if "Grand Total Conts" in df.columns else None
    net_col = "Net Working (hrs)" if "Net Working (hrs)" in df.columns else None

    if conts_col and net_col:
        df["net_moves_h"] = (
            (df[conts_col] / df[net_col])
            .replace([float("inf"), float("-inf")], 0)
            .fillna(0)
        )

    agg_cols: Dict[str, Any] = (
        {"net_moves_h": ["mean", "count"]} if "net_moves_h" in df.columns else {}
    )
    if "Portstay (hrs)" in df.columns:
        agg_cols["Portstay (hrs)"] = "mean"

    if agg_cols:
        result = df.groupby(op_col).agg(agg_cols).round(2).reset_index()
        result.columns = ["_".join(c).strip("_") for c in result.columns]
        return result.to_dict(orient="records")

    return []


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # nosec B104 — API_HOST defaults to 127.0.0.1; Docker compose sets 0.0.0.0
    uvicorn.run(app, host=API_HOST, port=8000, reload=True)
