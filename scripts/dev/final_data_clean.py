import pandas as pd
import os
import sqlite3
import glob

# Paths
base_path = (
    r"d:\UNG DUNG AI\TOOL AI 2026\CVF-Workspace\tdr_processor-container-2026\outputs"
)
excel_path = os.path.join(base_path, "data_excel", "master_vessel_summary.xlsx")
db_path = os.path.join(base_path, "tdr_master.db")
csv_dir = os.path.join(base_path, "data_csv")


def clean_series(s):
    return s.astype(str).str.replace(r"\s*\(DEMO\)", "", case=False, regex=True)


# 1. Clean Excel
if os.path.exists(excel_path):
    try:
        df = pd.read_excel(excel_path)
        if "Vessel Name" in df.columns:
            df["Vessel Name"] = clean_series(df["Vessel Name"])
            df.to_excel(excel_path, index=False)
            print("Excel cleaned.")
    except Exception as e:
        print(f"Excel Error: {e}")

# 2. Clean CSVs
if os.path.exists(csv_dir):
    for csv_file in glob.glob(os.path.join(csv_dir, "*.csv")):
        try:
            # Detect separator - some might be semicolon
            df = pd.read_csv(csv_file, nrows=1)
            sep = "," if len(df.columns) > 1 else ";"
            df = pd.read_csv(csv_file, sep=sep)

            # Look for columns that might have vessel names
            vessel_cols = [c for c in df.columns if "Vessel" in c]
            if vessel_cols:
                for col in vessel_cols:
                    df[col] = clean_series(df[col])
                df.to_csv(csv_file, index=False, sep=sep)
                print(f"CSV cleaned: {os.path.basename(csv_file)}")
        except Exception as e:
            print(f"CSV Error ({os.path.basename(csv_file)}): {e}")

# 3. Clean SQLite
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        # Find all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cursor.fetchall()]

        for table in tables:
            # Find columns with 'vessel' in name
            cursor.execute(f"PRAGMA table_info({table})")  # nosec B608
            cols = [r[1] for r in cursor.fetchall() if "vessel" in r[1].lower()]

            for col in cols:
                # Use standard SQL REPLACE
                cursor.execute(
                    f"UPDATE [{table}] SET [{col}] = REPLACE([{col}], ' (DEMO)', '') WHERE [{col}] LIKE '% (DEMO)%';"  # nosec B608
                )
                cursor.execute(
                    f"UPDATE [{table}] SET [{col}] = REPLACE([{col}], '(DEMO)', '') WHERE [{col}] LIKE '%(DEMO)%';"  # nosec B608
                )

        conn.commit()
        print("Database cleaned.")
    except Exception as e:
        print(f"DB Error: {e}")
    finally:
        conn.close()
