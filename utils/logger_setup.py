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
    """
    Configure logging for the entire TDR Processor application.
    
    Sets up file-based logging with the following features:
    - Reads configuration from config.py (LOG_FILENAME, LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT)
    - Removes old handlers to prevent duplicate log entries
    - Creates log file in UTF-8 encoding
    - Overwrites log file on each run (filemode='w')
    - Logs setup confirmation with configured log level and file path
    
    Log Levels Supported:
        DEBUG, INFO, WARNING, ERROR, CRITICAL (case-insensitive)
    
    Returns:
        None (configures logging module globally)
    
    Example:
        >>> setup_logging()
        # Logs: "Logging được thiết lập. Mức log: INFO. File log: tdr_processor.log"
    
    Note:
        This function should be called once at application startup.
        Calling it multiple times is safe due to handler cleanup.
    """
    log_file_path = Path(config.LOG_FILENAME)
    log_level_from_config_str = config.LOG_LEVEL.upper()
    log_level = getattr(logging, log_level_from_config_str, logging.INFO)

    # Xóa các handlers cũ để tránh log bị nhân đôi khi gọi lại hàm này
    # (Hữu ích nếu bạn có các kịch bản phức tạp hơn)
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        filename=log_file_path,
        level=log_level,
        format=config.LOG_FORMAT,
        datefmt=config.LOG_DATE_FORMAT,
        filemode='w',       # <<< THAY ĐỔI: 'w' để ghi đè (tạo mới) mỗi lần chạy
        encoding='utf-8'    # <<< THÊM MỚI: Chỉ định mã hóa UTF-8
    )
    logging.info(f"Logging được thiết lập. Mức log: {log_level_from_config_str}. File log: {log_file_path}")