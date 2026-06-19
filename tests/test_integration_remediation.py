import os
import sqlite3
from pathlib import Path

import pandas as pd

# Insert root folder to path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Disable authentication globally during test suite imports to prevent collection crash
os.environ["TDR_AUTH_DISABLED"] = "true"

from utils.database import TDRDatabase  # noqa: E402
from api import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from dashboard_api import _normalize_vessel_columns  # noqa: E402


def test_database_dynamic_column_resolution(tmp_path):
    """Test that TDRDatabase resolves columns correctly even with space-separated capitalized headers."""
    db_file = tmp_path / "test_tdr.db"

    # Create DB with raw vessel_summary schema (containing spaces/capitalized fields)
    conn = sqlite3.connect(db_file)
    conn.execute("""
        CREATE TABLE vessel_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Filename TEXT UNIQUE,
            [Vessel Name] TEXT,
            Voyage TEXT,
            Operator TEXT,
            Berth TEXT,
            [Report Date] TEXT
        )
    """)
    conn.execute("""
        INSERT INTO vessel_summary (Filename, [Vessel Name], Voyage, Operator, Berth, [Report Date])
        VALUES ('test_file.xlsx', 'MAERSK TEST', '2301E', 'MAERSK', 'B1', '2023-07-10')
    """)
    conn.commit()
    conn.close()

    # Instantiate TDRDatabase pointing to this test file
    db = TDRDatabase(db_path=db_file)

    # Check column resolution helper
    with db._get_connection() as c:
        assert db._resolve_column(c, "vessel_summary", "operator") == "[Operator]"
        assert db._resolve_column(c, "vessel_summary", "berth") == "[Berth]"
        assert db._resolve_column(c, "vessel_summary", "report_date") == "[Report Date]"

    # Test query_vessels works without crashing and applies correct filtering
    res = db.query_vessels(operator="MAERSK", limit=10)
    assert not res.empty
    assert res.iloc[0]["Vessel Name"] == "MAERSK TEST"

    # Test get_summary_stats works and correctly reads report_date
    stats = db.get_summary_stats()
    assert stats["vessel_count"] == 1
    assert stats["date_from"] == "2023-07-10"
    assert stats["date_to"] == "2023-07-10"


def test_fastapi_token_authorization(monkeypatch):
    """Test FastAPI authentication defaults and secure endpoint protection."""
    # Enforce authentication requirement
    monkeypatch.setenv("TDR_API_TOKEN", "secure_test_token_123")
    monkeypatch.setenv("TDR_AUTH_DISABLED", "false")

    client = TestClient(app)

    # Protected endpoint: /api/vessels
    # Case 1: Missing Token
    response = client.get("/api/vessels")
    assert response.status_code == 401

    # Case 2: Wrong Token
    response = client.get("/api/vessels", headers={"X-API-Token": "wrong_token"})
    assert response.status_code == 401

    # Case 3: Correct Token
    response = client.get(
        "/api/vessels", headers={"X-API-Token": "secure_test_token_123"}
    )
    # It might return 500 or 200 depending on DB file presence, but not 401
    assert response.status_code != 401

    # Protected endpoint: /api/process/status
    response = client.get("/api/process/status")
    assert response.status_code == 401


def test_fastapi_auth_disabled(monkeypatch):
    """Test FastAPI when authentication is explicitly disabled for local development."""
    monkeypatch.setenv("TDR_AUTH_DISABLED", "true")

    client = TestClient(app)

    response = client.get("/api/process/status")
    assert response.status_code == 200


def test_frontend_compiled_bundle_exists():
    """Verify that the frontend compiled static assets bundle exists and contains transpiled React code."""
    workspace_dir = Path(__file__).resolve().parent.parent
    bundle_path = workspace_dir / "assets" / "dashboard.js"

    assert bundle_path.exists(), "assets/dashboard.js does not exist!"
    assert bundle_path.stat().st_size > 0, "assets/dashboard.js is empty!"

    with open(bundle_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert (
            "React.createElement" in content
        ), "compiled bundle does not contain transpiled React.createElement elements!"
        assert (
            "react/jsx-dev-runtime" not in content
        ), "compiled bundle contains dev dependencies (jsx-dev-runtime) instead of classic React runtime!"


def test_dashboard_removes_legacy_demo_vessel_suffix():
    frame = pd.DataFrame(
        {
            "Vessel Name": ["NEWSUN GREEN 03 (DEMO)", "BIEN DONG STAR"],
            "Vessel Operator": ["VMC", "VMC"],
            "Vessel Moves/Net Hour": [42.5, 50.0],
        }
    )

    cleaned = _normalize_vessel_columns(frame)

    assert cleaned["Vessel Name"].tolist() == ["NEWSUN GREEN 03", "BIEN DONG STAR"]
    assert cleaned["Vessel Operator"].tolist() == ["VMC", "VMC"]
    assert cleaned["Vessel Moves/Net Hour"].tolist() == [42.5, 50.0]


def test_empty_db_fallback(tmp_path, monkeypatch):
    """Verify that when the database exists but has empty tables, api.py falls back to CSV."""
    monkeypatch.setenv("TDR_AUTH_DISABLED", "true")

    db_file = tmp_path / "empty_tdr.db"
    from utils.database import TDRDatabase
    db = TDRDatabase(db_path=db_file)

    import api
    monkeypatch.setattr(api, "_get_db", lambda: db)

    from fastapi.testclient import TestClient
    client = TestClient(api.app)

    # 1. Test /health endpoint fallback
    response = client.get("/health")
    assert response.status_code == 200
    res_data = response.json()
    summary = res_data["data_summary"]
    assert summary["vessel_count"] > 0

    # 2. Test /api/vessels endpoint fallback
    response = client.get("/api/vessels?limit=5")
    assert response.status_code == 200
    res_vessels = response.json()
    assert res_vessels["count"] > 0
    assert len(res_vessels["data"]) > 0
