import pandas as pd
import os
import sqlite3

file_path = r"d:\UNG DUNG AI\TOOL AI 2026\CVF-Workspace\tdr_processor-container-2026\outputs\data_excel\master_vessel_summary.xlsx"
if os.path.exists(file_path):
    try:
        df = pd.read_excel(file_path)
        if "Vessel Name" in df.columns:
            # Remove " (DEMO)" suffix (case insensitive)
            original_names = df["Vessel Name"].unique()
            df["Vessel Name"] = (
                df["Vessel Name"]
                .astype(str)
                .str.replace(r"\s*\(DEMO\)", "", case=False, regex=True)
            )
            new_names = df["Vessel Name"].unique()

            # Save back to Excel
            df.to_excel(file_path, index=False)
            print("Cleaned master_vessel_summary.xlsx. Vessel names updated.")
            print(f"Sample changes: {original_names[:3]} -> {new_names[:3]}")
        else:
            print("Vessel Name column not found.")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("File not found.")

# Also need to clean the SQLite DB to avoid waiting for re-process
db_path = r"d:\UNG DUNG AI\TOOL AI 2026\CVF-Workspace\tdr_processor-container-2026\outputs\tdr_master.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE vessel_summary SET [Vessel Name] = REPLACE([Vessel Name], ' (DEMO)', '') WHERE [Vessel Name] LIKE '% (DEMO)%';"
        )
        conn.execute(
            "UPDATE vessel_summary SET [Vessel Name] = REPLACE([Vessel Name], '(DEMO)', '') WHERE [Vessel Name] LIKE '%(DEMO)%';"
        )
        conn.execute(
            "UPDATE delay_events SET [Vessel Name] = REPLACE([Vessel Name], ' (DEMO)', '') WHERE [Vessel Name] LIKE '% (DEMO)%';"
        )
        conn.execute(
            "UPDATE qc_productivity SET [Vessel Name] = REPLACE([Vessel Name], ' (DEMO)', '') WHERE [Vessel Name] LIKE '% (DEMO)%';"
        )
        conn.execute(
            "UPDATE container_details_wide SET [Vessel Name] = REPLACE([Vessel Name], ' (DEMO)', '') WHERE [Vessel Name] LIKE '% (DEMO)%';"
        )
        conn.commit()
        print("Cleaned SQLite database.")
    except Exception as e:
        print(f"DB Error: {e}")
    conn.close()
