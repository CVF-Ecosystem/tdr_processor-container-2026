# core_processor.py
"""
Core processing module for TDR Processor - NO GUI dependencies.

This module provides pure processing logic that can be safely imported by:
- GUI application (main.py / Tkinter)
- Dashboard (app.py, dashboard.py / Streamlit)
- CLI scripts
- Scheduled tasks
- REST API (api.py)

NO Tkinter, NO GUI side effects. Pure data processing only.

v3.1 additions:
- Parallel file processing with ThreadPoolExecutor
- Integration with SQLite database layer
- Plugin system support
"""
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any, Tuple
from datetime import datetime
import shutil
import re

# Core imports - no GUI
import config
from report_processor import ReportProcessor
from utils.file_utils import setup_project_directories
from utils.input_validator import validate_excel_file

# Default max workers for parallel processing
# Use CPU count but cap at 4 to avoid overwhelming Excel file I/O
_DEFAULT_MAX_WORKERS = min(4, (os.cpu_count() or 1))


def normalize_filename(filename: str) -> str:
    """
    Normalize filename by removing extra spaces and standardizing format.
    
    This helps detect duplicate files that have slightly different names
    but represent the same voyage (e.g., "2534S-N" vs "2534S - N").
    
    Args:
        filename: Original filename
        
    Returns:
        Normalized filename for comparison
    """
    # Remove file extension
    name_without_ext = Path(filename).stem
    
    # Convert to uppercase for case-insensitive comparison
    normalized = name_without_ext.upper()
    
    # Remove all extra spaces around common separators
    # Pattern: spaces before/after hyphens, dots, underscores
    normalized = re.sub(r'\s*-\s*', '-', normalized)
    normalized = re.sub(r'\s*\.\s*', '.', normalized)
    normalized = re.sub(r'\s*_\s*', '_', normalized)
    
    # Collapse multiple spaces to single space
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remove leading/trailing spaces
    normalized = normalized.strip()
    
    return normalized


def detect_and_move_duplicates(
    input_dir: Path,
    duplicates_folder_name: str = "duplicates"
) -> Tuple[List[Path], List[Path]]:
    """
    Detect duplicate TDR files and move them to a separate folder.
    
    Duplicate detection is based on normalized filename comparison.
    Files that have the same normalized name (after removing extra spaces
    and standardizing separators) are considered duplicates.
    
    The file with the larger size is kept, small one is moved to duplicates folder.
    
    Args:
        input_dir: Path to input directory containing TDR files
        duplicates_folder_name: Name of subfolder for duplicates
        
    Returns:
        Tuple of (valid_files, duplicate_files):
            - valid_files: List of unique files to process
            - duplicate_files: List of files moved to duplicates folder
    """
    if not input_dir.exists():
        logging.warning(f"Input directory does not exist: {input_dir}")
        return [], []
    
    # Create duplicates folder
    duplicates_dir = input_dir / duplicates_folder_name
    duplicates_dir.mkdir(exist_ok=True)
    
    # Get all Excel files
    excel_files = list(input_dir.glob("*.xlsx")) + list(input_dir.glob("*.xls"))
    # Filter out temp files
    excel_files = [f for f in excel_files if not f.name.startswith("~$")]
    
    # Group files by normalized name
    normalized_groups: Dict[str, List[Path]] = {}
    for file_path in excel_files:
        normalized_name = normalize_filename(file_path.name)
        if normalized_name not in normalized_groups:
            normalized_groups[normalized_name] = []
        normalized_groups[normalized_name].append(file_path)
    
    valid_files = []
    duplicate_files = []
    
    for normalized_name, files in normalized_groups.items():
        if len(files) == 1:
            # No duplicate, keep the file
            valid_files.append(files[0])
        else:
            # Multiple files with same normalized name - keep the larger one
            # Sort by file size (descending) - keep the largest
            sorted_files = sorted(files, key=lambda f: f.stat().st_size, reverse=True)
            
            # Keep the first (largest) file
            valid_files.append(sorted_files[0])
            logging.info(f"Keeping: {sorted_files[0].name} (largest file)")
            
            # Move the rest to duplicates folder
            for dup_file in sorted_files[1:]:
                dest_path = duplicates_dir / dup_file.name
                
                # Handle if file already exists in duplicates folder
                if dest_path.exists():
                    base = dest_path.stem
                    ext = dest_path.suffix
                    counter = 1
                    while dest_path.exists():
                        dest_path = duplicates_dir / f"{base}_{counter}{ext}"
                        counter += 1
                
                try:
                    shutil.move(str(dup_file), str(dest_path))
                    duplicate_files.append(dest_path)
                    logging.warning(f"Moved duplicate file: {dup_file.name} -> {duplicates_folder_name}/")
                except Exception as e:
                    logging.error(f"Failed to move duplicate {dup_file.name}: {e}")
    
    if duplicate_files:
        logging.info(f"Detected and moved {len(duplicate_files)} duplicate file(s) to '{duplicates_folder_name}' folder")
    
    return valid_files, duplicate_files


def get_duplicate_report(input_dir: Path, duplicates_folder_name: str = "duplicates") -> Dict[str, Any]:
    """
    Get report of duplicate files without moving them.
    
    Useful for previewing duplicates before actually moving.
    
    Args:
        input_dir: Path to input directory
        duplicates_folder_name: Name of duplicates folder
        
    Returns:
        Dict with duplicate analysis results
    """
    if not input_dir.exists():
        return {"error": "Input directory does not exist"}
    
    excel_files = list(input_dir.glob("*.xlsx")) + list(input_dir.glob("*.xls"))
    excel_files = [f for f in excel_files if not f.name.startswith("~$")]
    
    # Group by normalized name
    normalized_groups: Dict[str, List[Path]] = {}
    for file_path in excel_files:
        normalized_name = normalize_filename(file_path.name)
        if normalized_name not in normalized_groups:
            normalized_groups[normalized_name] = []
        normalized_groups[normalized_name].append(file_path)
    
    # Find duplicates
    duplicates = {}
    for normalized_name, files in normalized_groups.items():
        if len(files) > 1:
            duplicates[normalized_name] = [
                {
                    "name": f.name,
                    "size": f.stat().st_size,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                }
                for f in files
            ]
    
    # Check existing duplicates folder
    duplicates_dir = input_dir / duplicates_folder_name
    existing_duplicates = []
    if duplicates_dir.exists():
        existing_duplicates = [f.name for f in duplicates_dir.glob("*.xlsx")]
    
    return {
        "total_files": len(excel_files),
        "unique_files": len(normalized_groups),
        "duplicate_groups": len(duplicates),
        "duplicates": duplicates,
        "existing_in_duplicates_folder": existing_duplicates
    }


def get_valid_tdr_files(input_dir: Path) -> List[Path]:
    """
    Get list of valid TDR Excel files from input directory.
    
    Args:
        input_dir: Path to input directory
        
    Returns:
        List of valid Excel file paths
    """
    if not input_dir.exists():
        logging.warning(f"Input directory does not exist: {input_dir}")
        return []
    
    excel_files = list(input_dir.glob("*.xlsx")) + list(input_dir.glob("*.xls"))
    
    # Filter out temp files and validate
    valid_files = []
    for f in excel_files:
        if f.name.startswith("~$"):
            continue
        is_valid, error_msg = validate_excel_file(str(f))
        if is_valid:
            valid_files.append(f)
        else:
            logging.warning(f"Skipping invalid file: {f.name} - {error_msg}")
    
    return valid_files


def process_tdr_files(
    files: List[Path],
    output_dir: Optional[Path] = None,
    overwrite: bool = False,
    update_status_callback: Optional[Callable[[str], None]] = None,
    update_progress_callback: Optional[Callable[[int, int], None]] = None
) -> Dict[str, Any]:
    """
    Process TDR files and generate reports.
    
    This is the main processing function that can be called from anywhere.
    
    Args:
        files: List of TDR Excel files to process
        output_dir: Output directory (default: outputs/)
        overwrite: Whether to overwrite existing output files
        update_status_callback: Optional callback for status updates
        update_progress_callback: Optional callback for progress updates (current, total)
        
    Returns:
        Dict with processing results:
            - message: Summary message
            - processed_count: Number of files processed
            - skipped_count: Number of files skipped
            - errors: List of error messages (if any)
    """
    if output_dir is None:
        output_dir = Path("outputs")
    
    # Ensure output directories exist
    setup_project_directories(Path.cwd(), ["outputs", "outputs/data_csv", "outputs/data_excel"])
    
    if not files:
        return {
            "message": "No files to process",
            "processed_count": 0,
            "skipped_count": 0,
            "errors": []
        }
    
    try:
        processor = ReportProcessor(output_dir=output_dir)
        result = processor.process_tdr_files(
            files,
            update_status_callback=update_status_callback,
            update_progress_callback=update_progress_callback,
            overwrite=overwrite
        )
        return result
    except Exception as e:
        logging.error(f"Processing error: {e}", exc_info=True)
        return {
            "message": f"Processing failed: {str(e)}",
            "processed_count": 0,
            "skipped_count": len(files),
            "errors": [str(e)]
        }


def auto_process_input_folder(
    input_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    overwrite: bool = False,
    check_duplicates: bool = True,
    duplicates_folder_name: str = "duplicates"
) -> Dict[str, Any]:
    """
    Automatically process all TDR files in input folder.
    
    Convenience function for automated/scheduled processing.
    
    Args:
        input_dir: Input directory (default: data_input/)
        output_dir: Output directory (default: outputs/)
        overwrite: Whether to overwrite existing files
        check_duplicates: Whether to detect and move duplicates before processing
        duplicates_folder_name: Name of folder to move duplicates to
        
    Returns:
        Dict with processing results including duplicate info
    """
    if input_dir is None:
        input_dir = Path("data_input")
    if output_dir is None:
        output_dir = Path("outputs")
    
    logging.info(f"[AutoProcess] Starting auto-processing from {input_dir}")
    
    # Step 1: Detect and move duplicates if enabled
    duplicate_files = []
    if check_duplicates:
        valid_files, duplicate_files = detect_and_move_duplicates(input_dir, duplicates_folder_name)
        if duplicate_files:
            logging.warning(f"[AutoProcess] Moved {len(duplicate_files)} duplicate file(s) to '{duplicates_folder_name}' folder")
    else:
        valid_files = get_valid_tdr_files(input_dir)
    
    # Step 2: Validate remaining files
    validated_files = []
    for f in valid_files:
        is_valid, error_msg = validate_excel_file(str(f))
        if is_valid:
            validated_files.append(f)
        else:
            logging.warning(f"Skipping invalid file: {f.name} - {error_msg}")
    
    if not validated_files:
        logging.info("[AutoProcess] No valid TDR files found in input folder")
        return {
            "message": "No valid TDR files found",
            "processed_count": 0,
            "skipped_count": 0,
            "duplicate_count": len(duplicate_files),
            "duplicate_files": [f.name for f in duplicate_files],
            "errors": []
        }
    
    logging.info(f"[AutoProcess] Found {len(validated_files)} valid files to process")
    
    # Step 3: Process files
    result = process_tdr_files(
        files=validated_files,
        output_dir=output_dir,
        overwrite=overwrite
    )
    
    # Add duplicate info to result
    result["duplicate_count"] = len(duplicate_files)
    result["duplicate_files"] = [f.name for f in duplicate_files]
    
    logging.info(f"[AutoProcess] Completed: {result.get('message', 'Done')}")
    return result


def get_processing_summary(output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Get summary of processed data.
    
    Args:
        output_dir: Output directory to check
        
    Returns:
        Dict with summary statistics
    """
    if output_dir is None:
        output_dir = Path("outputs")
    
    csv_dir = output_dir / "data_csv"
    excel_dir = output_dir / "data_excel"
    
    summary = {
        "csv_files": [],
        "excel_files": [],
        "last_modified": None
    }
    
    if csv_dir.exists():
        summary["csv_files"] = [f.name for f in csv_dir.glob("*.csv")]
        
        # Get most recent modification time
        csv_files = list(csv_dir.glob("*.csv"))
        if csv_files:
            latest = max(csv_files, key=lambda f: f.stat().st_mtime)
            summary["last_modified"] = datetime.fromtimestamp(latest.stat().st_mtime).isoformat()

    if excel_dir.exists():
        summary["excel_files"] = [f.name for f in excel_dir.glob("*.xlsx")]

    return summary


def process_tdr_files_parallel(
    files: List[Path],
    output_dir: Optional[Path] = None,
    overwrite: bool = False,
    max_workers: int = _DEFAULT_MAX_WORKERS,
    update_status_callback: Optional[Callable[[str], None]] = None,
    update_progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Dict[str, Any]:
    """
    Process TDR files in parallel using ThreadPoolExecutor.

    For large batches (10+ files), parallel processing can significantly
    reduce total processing time by utilizing multiple CPU cores.

    Note: Uses threads (not processes) because openpyxl is not picklable.
    Thread-based parallelism still helps with I/O-bound Excel reading.

    Args:
        files: List of TDR Excel files to process
        output_dir: Output directory (default: outputs/)
        overwrite: Whether to overwrite existing output files
        max_workers: Maximum number of parallel workers (default: min(4, cpu_count))
        update_status_callback: Optional callback for status updates
        update_progress_callback: Optional callback for progress updates

    Returns:
        Dict with processing results (same format as process_tdr_files)
    """
    if not files:
        return {
            "message": "No files to process",
            "processed_count": 0,
            "skipped_count": 0,
            "errors": []
        }

    # For small batches, use sequential processing (less overhead)
    if len(files) <= 3 or max_workers <= 1:
        logging.info(f"[ParallelProcess] Small batch ({len(files)} files), using sequential processing")
        return process_tdr_files(
            files=files,
            output_dir=output_dir,
            overwrite=overwrite,
            update_status_callback=update_status_callback,
            update_progress_callback=update_progress_callback,
        )

    if output_dir is None:
        output_dir = Path("outputs")

    setup_project_directories(Path.cwd(), ["outputs", "outputs/data_csv", "outputs/data_excel"])

    logging.info(f"[ParallelProcess] Starting parallel processing of {len(files)} files with {max_workers} workers")

    total_files = len(files)
    processed_count = 0
    skipped_count = 0
    errors = []
    completed = 0

    if update_progress_callback:
        update_progress_callback(0, total_files)

    # Split files into chunks for each worker
    # Each worker gets its own ReportProcessor instance to avoid shared state
    chunk_size = max(1, total_files // max_workers)
    chunks = [files[i:i + chunk_size] for i in range(0, total_files, chunk_size)]

    def process_chunk(chunk: List[Path]) -> Dict[str, Any]:
        """Process a chunk of files with a dedicated ReportProcessor."""
        processor = ReportProcessor(output_dir=output_dir)
        return processor.process_tdr_files(
            chunk,
            overwrite=overwrite
        )

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_chunk = {
            executor.submit(process_chunk, chunk): chunk
            for chunk in chunks
        }

        for future in as_completed(future_to_chunk):
            chunk = future_to_chunk[future]
            try:
                result = future.result()
                processed_count += result.get("processed_count", 0)
                skipped_count += result.get("skipped_count", 0)
                if result.get("errors"):
                    errors.extend(result["errors"])
            except Exception as e:
                logging.error(f"[ParallelProcess] Chunk processing failed: {e}", exc_info=True)
                skipped_count += len(chunk)
                errors.append(str(e))

            completed += len(chunk)
            if update_progress_callback:
                update_progress_callback(min(completed, total_files), total_files)
            if update_status_callback:
                update_status_callback(f"Processed {completed}/{total_files} files...")

    message = f"Parallel processing complete: {processed_count} processed, {skipped_count} skipped"
    logging.info(f"[ParallelProcess] {message}")

    return {
        "message": message,
        "processed_count": processed_count,
        "skipped_count": skipped_count,
        "errors": errors,
    }
