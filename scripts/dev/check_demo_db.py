import sqlite3
import os

db_path = r"d:\UNG DUNG AI\TOOL AI 2026\CVF-Workspace\tdr_processor-container-2026\outputs\tdr_master.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT DISTINCT [Vessel Name] FROM vessel_summary WHERE [Vessel Name] LIKE '%DEMO%';"
        )
        rows = cursor.fetchall()
        if rows:
            print("Found DEMO in vessel_summary:")
            for r in rows:
                print(f"  - {r[0]}")
        else:
            print("DEMO not found in vessel_summary.")
    except Exception as e:
        print(f"Error: {e}")
    conn.close()
else:
    print(f"DB not found at {db_path}")
