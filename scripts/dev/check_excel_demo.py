import pandas as pd
import os

file_path = r"d:\UNG DUNG AI\TOOL AI 2026\CVF-Workspace\tdr_processor-container-2026\outputs\data_excel\master_vessel_summary.xlsx"
if os.path.exists(file_path):
    try:
        df = pd.read_excel(file_path)
        print(f"File loaded. Columns: {df.columns.tolist()}")
        if "Vessel Name" in df.columns:
            demos = df[df["Vessel Name"].astype(str).str.contains("DEMO", case=False)]
            if not demos.empty:
                print("Found DEMO in Excel:")
                print(demos["Vessel Name"].unique())
            else:
                print("DEMO not found in Excel Vessel Name column.")
        else:
            print("Vessel Name column not found in Excel.")
    except Exception as e:
        print(f"Error reading Excel: {e}")
else:
    print(f"File not found at {file_path}")
