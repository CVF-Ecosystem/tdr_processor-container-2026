# utils/database.py
"""
SQLite database layer for TDR Processor.

Replaces Excel master files with a proper relational database for:
- Faster queries (no need to load entire Excel files)
- Concurrent read access
- No file corruption risk
- Easy backup and migration
- SQL-based filtering and aggregation

Usage:
    from utils.database import TDRDatabase

    db = TDRDatabase()
    db.upsert_vessel_summary(df_vessel)
    vessels = db.query_vessels(operator="EVERGREEN", limit=50)
"""
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import pandas as pd

from exceptions import DatabaseConnectionError, DatabaseWriteError

# Default database path
DEFAULT_DB_PATH = Path("outputs/tdr_data.db")

# Schema version - increment when changing table structure
SCHEMA_VERSION = "1.0.0"

# SQL DDL for all tables
_CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT NOT NULL,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vessel_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL UNIQUE,
    vessel_name TEXT,
    voyage TEXT,
    operator TEXT,
    berth TEXT,
    report_date TEXT,
    atb TEXT,
    atd TEXT,
    gangway_secured TEXT,
    commenced_discharge TEXT,
    completed_discharge TEXT,
    commenced_loading TEXT,
    completed_loading TEXT,
    all_ops_completed TEXT,
    break_time_hrs REAL DEFAULT 0.0,
    discharge_hrs REAL DEFAULT 0.0,
    loading_hrs REAL DEFAULT 0.0,
    total_working_hrs REAL DEFAULT 0.0,
    portstay_hrs REAL DEFAULT 0.0,
    gross_working_hrs REAL DEFAULT 0.0,
    net_working_hrs REAL DEFAULT 0.0,
    grand_total_conts INTEGER DEFAULT 0,
    grand_total_teus REAL DEFAULT 0.0,
    vessel_moves_per_portstay_hour REAL DEFAULT 0.0,
    vessel_moves_per_gross_hour REAL DEFAULT 0.0,
    vessel_moves_per_net_hour REAL DEFAULT 0.0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS qc_productivity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    vessel_name TEXT,
    voyage TEXT,
    atb TEXT,
    atd TEXT,
    qc_no TEXT NOT NULL,
    start_time TEXT,
    end_time TEXT,
    gross_working_hrs REAL DEFAULT 0.0,
    delay_times_hrs REAL DEFAULT 0.0,
    net_working_hrs REAL DEFAULT 0.0,
    discharge_conts INTEGER DEFAULT 0,
    load_conts INTEGER DEFAULT 0,
    shifting_conts INTEGER DEFAULT 0,
    total_conts INTEGER DEFAULT 0,
    gross_moves_h REAL DEFAULT 0.0,
    net_moves_h REAL DEFAULT 0.0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(filename, qc_no)
);

CREATE TABLE IF NOT EXISTS qc_operator_productivity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    vessel_name TEXT,
    voyage TEXT,
    atb TEXT,
    atd TEXT,
    qc_no TEXT NOT NULL,
    start_time TEXT,
    end_time TEXT,
    gross_working_hrs REAL DEFAULT 0.0,
    total_stop_time_hrs REAL DEFAULT 0.0,
    net_working_hrs REAL DEFAULT 0.0,
    discharge_conts INTEGER DEFAULT 0,
    load_conts INTEGER DEFAULT 0,
    shifting_conts INTEGER DEFAULT 0,
    total_conts INTEGER DEFAULT 0,
    gross_moves_h REAL DEFAULT 0.0,
    net_moves_h REAL DEFAULT 0.0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(filename, qc_no)
);

CREATE TABLE IF NOT EXISTS delay_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    vessel_name TEXT,
    voyage TEXT,
    qc_no TEXT,
    stop_category TEXT,
    from_time TEXT,
    to_time TEXT,
    duration_hrs REAL DEFAULT 0.0,
    error_code TEXT,
    error_type TEXT,
    remark TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS container_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    vessel_name TEXT,
    voyage TEXT,
    operation_type TEXT,
    port TEXT,
    container_category TEXT,
    container_size TEXT,
    quantity INTEGER DEFAULT 0,
    row_total_conts_from_tdr INTEGER DEFAULT 0,
    row_teus_from_tdr INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_vessel_operator ON vessel_summary(operator);
CREATE INDEX IF NOT EXISTS idx_vessel_berth ON vessel_summary(berth);
CREATE INDEX IF NOT EXISTS idx_vessel_report_date ON vessel_summary(report_date);
CREATE INDEX IF NOT EXISTS idx_qc_filename ON qc_productivity(filename);
CREATE INDEX IF NOT EXISTS idx_delay_filename ON delay_details(filename);
CREATE INDEX IF NOT EXISTS idx_container_filename ON container_details(filename);
"""


class TDRDatabase:
    """
    SQLite database interface for TDR Processor data.

    Provides methods to store and query all TDR data tables.
    Uses WAL mode for better concurrent read performance.

    Example:
        db = TDRDatabase()
        db.upsert_vessel_summary(df)
        vessels = db.query_vessels(operator="EVERGREEN")
    """

    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file. Created if not exists.

        Raises:
            DatabaseConnectionError: If database cannot be opened.
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Test connection
            with self._get_connection() as conn:
                conn.execute("PRAGMA journal_mode=WAL")  # Better concurrent reads
                conn.execute("PRAGMA foreign_keys=ON")
                self._initialize_schema(conn)
            logging.info(f"[Database] Connected to SQLite database: {self.db_path}")
        except Exception as e:
            raise DatabaseConnectionError(str(db_path), str(e)) from e

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connections with auto-commit/rollback."""
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _initialize_schema(self, conn: sqlite3.Connection) -> None:
        """Create tables if they don't exist and record schema version."""
        conn.executescript(_CREATE_TABLES_SQL)

        # Record schema version if not already present
        existing = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                (SCHEMA_VERSION, datetime.now().isoformat())
            )
        logging.debug(f"[Database] Schema initialized (version {SCHEMA_VERSION})")

    def _df_to_db(self, conn: sqlite3.Connection, df: pd.DataFrame,
                  table: str, if_exists: str = "append") -> int:
        """Write DataFrame to database table. Returns rows written."""
        if df.empty:
            return 0
        # Convert datetime columns to ISO strings for SQLite compatibility
        df_copy = df.copy()
        for col in df_copy.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
            df_copy[col] = df_copy[col].dt.strftime("%Y-%m-%d %H:%M:%S")
        df_copy.to_sql(table, conn, if_exists=if_exists, index=False)
        return len(df_copy)

    # =========================================================================
    # UPSERT METHODS
    # =========================================================================

    def upsert_vessel_summary(self, df: pd.DataFrame) -> int:
        """
        Insert or update vessel summary records.

        Uses filename as unique key - existing records are replaced.

        Args:
            df: DataFrame with vessel summary data

        Returns:
            Number of records upserted

        Raises:
            DatabaseWriteError: If write fails
        """
        if df.empty:
            return 0
        try:
            with self._get_connection() as conn:
                # Delete existing records for these filenames first (upsert pattern)
                filenames = df["Filename"].tolist() if "Filename" in df.columns else []
                if filenames:
                    placeholders = ",".join("?" * len(filenames))
                    conn.execute(
                        f"DELETE FROM vessel_summary WHERE filename IN ({placeholders})",
                        filenames
                    )
                count = self._df_to_db(conn, df, "vessel_summary")
                logging.info(f"[Database] Upserted {count} vessel summary records")
                return count
        except Exception as e:
            raise DatabaseWriteError("vessel_summary", str(e)) from e

    def upsert_qc_productivity(self, df: pd.DataFrame) -> int:
        """Insert or update QC productivity records."""
        if df.empty:
            return 0
        try:
            with self._get_connection() as conn:
                filenames = df["Filename"].tolist() if "Filename" in df.columns else []
                if filenames:
                    placeholders = ",".join("?" * len(filenames))
                    conn.execute(
                        f"DELETE FROM qc_productivity WHERE filename IN ({placeholders})",
                        filenames
                    )
                count = self._df_to_db(conn, df, "qc_productivity")
                logging.info(f"[Database] Upserted {count} QC productivity records")
                return count
        except Exception as e:
            raise DatabaseWriteError("qc_productivity", str(e)) from e

    def upsert_qc_operator_productivity(self, df: pd.DataFrame) -> int:
        """Insert or update QC operator productivity records."""
        if df.empty:
            return 0
        try:
            with self._get_connection() as conn:
                filenames = df["Filename"].tolist() if "Filename" in df.columns else []
                if filenames:
                    placeholders = ",".join("?" * len(filenames))
                    conn.execute(
                        f"DELETE FROM qc_operator_productivity WHERE filename IN ({placeholders})",
                        filenames
                    )
                count = self._df_to_db(conn, df, "qc_operator_productivity")
                logging.info(f"[Database] Upserted {count} QC operator productivity records")
                return count
        except Exception as e:
            raise DatabaseWriteError("qc_operator_productivity", str(e)) from e

    def upsert_delay_details(self, df: pd.DataFrame) -> int:
        """Insert or update delay detail records."""
        if df.empty:
            return 0
        try:
            with self._get_connection() as conn:
                filenames = df["Filename"].tolist() if "Filename" in df.columns else []
                if filenames:
                    placeholders = ",".join("?" * len(filenames))
                    conn.execute(
                        f"DELETE FROM delay_details WHERE filename IN ({placeholders})",
                        filenames
                    )
                count = self._df_to_db(conn, df, "delay_details")
                logging.info(f"[Database] Upserted {count} delay detail records")
                return count
        except Exception as e:
            raise DatabaseWriteError("delay_details", str(e)) from e

    def upsert_container_details(self, df: pd.DataFrame) -> int:
        """Insert or update container detail records."""
        if df.empty:
            return 0
        try:
            with self._get_connection() as conn:
                filenames = df["Filename"].tolist() if "Filename" in df.columns else []
                if filenames:
                    placeholders = ",".join("?" * len(filenames))
                    conn.execute(
                        f"DELETE FROM container_details WHERE filename IN ({placeholders})",
                        filenames
                    )
                count = self._df_to_db(conn, df, "container_details")
                logging.info(f"[Database] Upserted {count} container detail records")
                return count
        except Exception as e:
            raise DatabaseWriteError("container_details", str(e)) from e

    # =========================================================================
    # QUERY METHODS
    # =========================================================================

    def query_vessels(
        self,
        operator: Optional[str] = None,
        berth: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Query vessel summary data with optional filters.

        Args:
            operator: Filter by shipping line operator
            berth: Filter by berth location
            date_from: Filter by report date (ISO format: YYYY-MM-DD)
            date_to: Filter by report date (ISO format: YYYY-MM-DD)
            limit: Maximum number of records to return

        Returns:
            DataFrame with vessel summary data
        """
        conditions: List[str] = []
        params: List[Any] = []

        if operator:
            conditions.append("operator = ?")
            params.append(operator)
        if berth:
            conditions.append("berth = ?")
            params.append(berth)
        if date_from:
            conditions.append("report_date >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("report_date <= ?")
            params.append(date_to)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT * FROM vessel_summary {where_clause} ORDER BY report_date DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            return pd.read_sql_query(sql, conn, params=params)

    def query_qc_productivity(
        self,
        filename: Optional[str] = None,
        qc_no: Optional[str] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """Query QC productivity data."""
        conditions: List[str] = []
        params: List[Any] = []

        if filename:
            conditions.append("filename = ?")
            params.append(filename)
        if qc_no:
            conditions.append("qc_no = ?")
            params.append(qc_no)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT * FROM qc_productivity {where_clause} LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            return pd.read_sql_query(sql, conn, params=params)

    def query_delay_details(
        self,
        filename: Optional[str] = None,
        error_type: Optional[str] = None,
        limit: int = 5000
    ) -> pd.DataFrame:
        """Query delay detail records."""
        conditions: List[str] = []
        params: List[Any] = []

        if filename:
            conditions.append("filename = ?")
            params.append(filename)
        if error_type:
            conditions.append("error_type = ?")
            params.append(error_type)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT * FROM delay_details {where_clause} LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            return pd.read_sql_query(sql, conn, params=params)

    def get_processed_filenames(self) -> set:
        """
        Get set of all filenames already in the database.

        Used to skip already-processed files.

        Returns:
            Set of filename strings
        """
        with self._get_connection() as conn:
            rows = conn.execute("SELECT filename FROM vessel_summary").fetchall()
            return {row["filename"] for row in rows}

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get high-level statistics about stored data.

        Returns:
            Dict with counts and date ranges
        """
        with self._get_connection() as conn:
            vessel_count = conn.execute("SELECT COUNT(*) FROM vessel_summary").fetchone()[0]
            qc_count = conn.execute("SELECT COUNT(*) FROM qc_productivity").fetchone()[0]
            delay_count = conn.execute("SELECT COUNT(*) FROM delay_details").fetchone()[0]
            container_count = conn.execute("SELECT COUNT(*) FROM container_details").fetchone()[0]

            date_range = conn.execute(
                "SELECT MIN(report_date), MAX(report_date) FROM vessel_summary"
            ).fetchone()

        return {
            "vessel_count": vessel_count,
            "qc_records": qc_count,
            "delay_records": delay_count,
            "container_records": container_count,
            "date_from": date_range[0],
            "date_to": date_range[1],
            "db_path": str(self.db_path),
            "schema_version": SCHEMA_VERSION,
        }

    def export_to_csv(self, output_dir: Path) -> Dict[str, int]:
        """
        Export all tables to CSV files (for backward compatibility).

        Args:
            output_dir: Directory to write CSV files

        Returns:
            Dict mapping table name to row count exported
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        tables = {
            "vessel_summary": "vessel_summary.csv",
            "qc_productivity": "qc_productivity.csv",
            "qc_operator_productivity": "qc_operator_productivity.csv",
            "delay_details": "delay_details.csv",
            "container_details": "container_details_long.csv",
        }
        counts = {}
        with self._get_connection() as conn:
            for table, csv_name in tables.items():
                df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                csv_path = output_dir / csv_name
                df.to_csv(csv_path, index=False, encoding="utf-8-sig")
                counts[table] = len(df)
                logging.info(f"[Database] Exported {len(df)} rows from '{table}' to {csv_name}")
        return counts

    def vacuum(self) -> None:
        """Compact the database file to reclaim space."""
        with self._get_connection() as conn:
            conn.execute("VACUUM")
        logging.info("[Database] VACUUM completed")
