from pathlib import Path
from report_processor import ReportProcessor


def reprocess():
    input_dir = Path("data_input")

    # Get all excel files in data_input
    files = list(input_dir.glob("*.xlsx")) + list(input_dir.glob("*.xls"))
    if not files:
        print("No files found in data_input")
        return

    print(f"Reprocessing {len(files)} files...")
    processor = ReportProcessor(Path.cwd())
    result = processor.process_tdr_files(
        files,
        update_status_callback=lambda x: print(f"Status: {x}"),
        update_progress_callback=lambda cur, tot: print(f"Progress: {cur}/{tot}"),
        overwrite=True,  # Set overwrite to True to refresh all data
    )
    print("Reprocessing complete!")
    print(result)


if __name__ == "__main__":
    reprocess()
