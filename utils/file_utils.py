# utils/file_utils.py
"""
File and directory utilities for TDR Processor.

Provides functions for:
- Checking if files are locked or in use by other processes
- Managing project directory structures
- Creating file backups with timestamps
- Removing files and directories safely

All functions are Windows and Unix compatible.
"""
import os
import logging
from pathlib import Path
import shutil # <<< THÊM THƯ VIỆN NÀY
from datetime import datetime # <<< THÊM THƯ VIỆN NÀY
from typing import List, Optional


def is_file_locked(filepath) -> bool:
    """
    Check if a file is locked or in use by another process.
    
    Attempts to detect if a file is currently open by another application (e.g., Excel).
    Works by attempting to rename the file to itself; if this fails with PermissionError,
    the file is considered locked. Accepts both str and Path objects.
    
    Args:
        filepath: Path to file as str or Path object
    
    Returns:
        True if file is locked/inaccessible, False if file is accessible or doesn't exist
    
    Note:
        This method is particularly reliable on Windows for detecting Excel file locks.
        On Unix systems, this will mostly only catch permission issues.
    
    Example:
        >>> is_file_locked("data/excel_file.xlsx")
        False  # File is available
    """
    # Chuyển đổi thành Path nếu là string
    if isinstance(filepath, str):
        filepath = Path(filepath)
    
    if not filepath.exists():
        return False # File không tồn tại thì không bị khóa
    try:
        # Cố gắng đổi tên file thành chính nó.
        # Nếu file đang được mở bởi ứng dụng khác (như Excel), thao tác này sẽ gây ra PermissionError.
        os.rename(filepath, filepath)
        return False
    except PermissionError:
        logging.warning(f"KIỂM TRA FILE: File '{filepath.name}' đang bị khóa hoặc không có quyền truy cập.")
        return True
    except Exception as e:
        logging.error(f"KIỂM TRA FILE: Lỗi không xác định khi kiểm tra file '{filepath.name}': {e}")
        return True # Coi như bị khóa để an toàn

def setup_project_directories(base_path: Path, dir_list: List[str]) -> bool:
    """
    Create project directory structure if it doesn't exist.
    
    Verifies and creates all necessary project directories in a single operation.
    Uses mkdir with parents=True and exist_ok=True for safe creation.
    
    Args:
        base_path: Base directory path as Path object
        dir_list: List of directory names to create relative to base_path
    
    Returns:
        True if all directories exist or were successfully created, False on error
    
    Example:
        >>> base = Path.cwd()
        >>> dirs = ['data_input', 'data_csv', 'outputs']
        >>> setup_project_directories(base, dirs)
        True
    """
    logging.info("Kiểm tra và tạo cấu trúc thư mục dự án...")
    try:
        for dir_name in dir_list:
            dir_path = base_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
        logging.info("Cấu trúc thư mục đã sẵn sàng.")
        return True
    except Exception as e:
        logging.error(f"Không thể tạo thư mục dự án: {e}", exc_info=True)
        return False
# <<< THÊM HÀM MỚI DƯỚI ĐÂY >>>
def backup_file(file_path: Path) -> None:
    """
    Create timestamped backup of file in backup directory.
    
    Creates a backup directory structure with subdirectory named backup_DDMM_HHMM
    and copies the file there. If file doesn't exist, operation is skipped silently.
    
    Args:
        file_path: Path to file to backup (Path object)
    
    Returns:
        None
    
    Side Effects:
        Creates backup directory structure if needed
        Logs backup location on success
        Logs errors on failure
    
    Example:
        >>> backup_file(Path("data_input/vessel_details.xlsx"))
        # Creates: backup/backup_0912_1430/vessel_details.xlsx
    """
    if not file_path.exists():
        return # Không có gì để backup

    try:
        # Tạo thư mục backup chính nếu chưa có
        backup_root = Path("backup")
        backup_root.mkdir(exist_ok=True)

        # Tạo thư mục con với timestamp cho lần backup này
        timestamp = datetime.now().strftime("%d%m_%H%M")
        backup_dir = backup_root / f"backup_{timestamp}"
        backup_dir.mkdir(exist_ok=True)

        # Sao chép file vào thư mục backup
        shutil.copy(file_path, backup_dir)
        logging.info(f"BACKUP: Đã sao lưu '{file_path.name}' vào '{backup_dir}'")
    except Exception as e:
        logging.error(f"BACKUP: Lỗi khi sao lưu file '{file_path.name}': {e}", exc_info=True)