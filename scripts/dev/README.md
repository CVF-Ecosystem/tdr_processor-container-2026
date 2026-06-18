# Developer Utility Scripts

This directory contains local utility and developer helper scripts used during the development of the TDR Processor. 

These scripts have been moved out of the repository root to keep it clean and to avoid cluttering static analysis (Ruff, Bandit) gates.

## Scripts Description

- `check_db.py`: Quick helper script to check the SQLite tables and row counts.
- `check_demo_db.py`: Quick helper script to verify demo database data.
- `check_excel_demo.py`: Helper to verify and test Excel file formatting and reading.
- `clean_demo_labels.py`: Database and Excel data cleaning utility to strip the `(DEMO)` suffixes from vessel names.
- `final_data_clean.py`: Utility to perform cleanup steps on Excel, CSV and SQLite databases.
- `reprocess_data.py`: Developer script to trigger reprocessing of raw data files.

## Static Analysis Note

These scripts are not part of the production bundle and are meant for development and testing environments only. Parameterized queries in these scripts use appropriate `# nosec` tags where necessary to keep Bandit scans clean.
