# utils/logger_setup.py
"""
Logging configuration for TDR Processor application.

Sets up a file-based logger that writes to a log file specified in the config.
Handles configuration loading from config.py with fallback defaults if import fails.
All log messages include timestamp, level, module name, function name, and message.

Log Format:
    YYYY-MM-DD HH:MM:SS - LEVEL - module - function - message
"""
import logging
from pathlib import Path
from datetime import datetime
try:
    import config # Giả sử config.py ở thư mục gốc của project
except ImportError:
    # Fallback nếu chạy module này riêng lẻ hoặc config.py không ở root
    # Điều này không nên xảy ra khi chạy từ main.py
    print("LỖI: Không tìm thấy config.py khi thiết lập logger.")
    # Định nghĩa các giá trị mặc định nếu config không load được
    LOG_FILENAME_DEFAULT = "tdr_processor_fallback.log"
    LOG_LEVEL_DEFAULT = logging.INFO
    LOG_FORMAT_DEFAULT = '%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'
    LOG_DATE_FORMAT_DEFAULT = '%Y-%m-%d %H:%M:%S'

    class ConfigMock:
        LOG_FILENAME = LOG_FILENAME_DEFAULT
        LOG_LEVEL = "INFO"
        LOG_FORMAT = LOG_FORMAT_DEFAULT
        LOG_DATE_FORMAT = LOG_DATE_FORMAT_DEFAULT
    config = ConfigMock()


def setup_logging():
    """Configure logging: plain-text file + JSON structured file (python-json-logger)."""
    log_file_path = Path(config.LOG_FILENAME)
    json_log_path = log_file_path.with_suffix(".json.log")
    log_level_str = config.LOG_LEVEL.upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Xóa handlers cũ tránh duplicate
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # --- Handler 1: Plain-text (giữ nguyên như cũ) ---
    plain_handler = logging.FileHandler(log_file_path, mode='w', encoding='utf-8')
    plain_handler.setLevel(log_level)
    plain_handler.setFormatter(logging.Formatter(config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT))
    root_logger.addHandler(plain_handler)

    # --- Handler 2: JSON structured log (python-json-logger) ---
    try:
        from pythonjsonlogger import jsonlogger  # type: ignore[import]
        json_handler = logging.FileHandler(json_log_path, mode='w', encoding='utf-8')
        json_handler.setLevel(log_level)
        json_handler.setFormatter(
            jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(module)s %(funcName)s %(message)s')
        )
        root_logger.addHandler(json_handler)
    except ImportError:
        pass  # python-json-logger chưa cài — chỉ dùng plain text

    # Session banner
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.info("=" * 100)
    logging.info(f"🚀 NEW SESSION STARTED: {current_time}")
    logging.info("=" * 100)
    logging.info(f"Logging được thiết lập. Mức log: {log_level_str}. File log: {log_file_path}")
    logging.info(f"Python version: {__import__('sys').version}")
    logging.info(f"Working directory: {Path.cwd()}")
    logging.info("-" * 100)


def log_error_details(error_type: str, error_message: str, context: dict = None):
    """
    Log detailed error information for debugging.
    
    Args:
        error_type: Type of error (e.g., 'FILE_VALIDATION', 'CONFIG_ERROR', 'PROCESSING_ERROR')
        error_message: Detailed error message
        context: Dictionary with additional context (optional)
    
    Example:
        >>> log_error_details('FILE_VALIDATION', 'Path contains invalid characters', 
        ...                   {'file': 'test.xlsx', 'reason': 'parent directory reference'})
    """
    logging.error("=" * 100)
    logging.error(f"❌ ERROR DETECTED: [{error_type}]")
    logging.error(f"Message: {error_message}")
    if context:
        for key, value in context.items():
            logging.error(f"  • {key}: {value}")
    logging.error("=" * 100)


def log_session_end(success: bool, summary: dict = None):
    """
    Log session end with summary.
    
    Args:
        success: Whether session completed successfully
        summary: Dictionary with summary statistics
    """
    status = "✅ SUCCESS" if success else "❌ FAILED"
    logging.info("=" * 100)
    logging.info(f"🏁 SESSION END: {status}")
    if summary:
        for key, value in summary.items():
            logging.info(f"  • {key}: {value}")
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.info(f"Ended at: {end_time}")
    logging.info("=" * 100)