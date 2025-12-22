# utils/watcher.py
"""
File system watcher for monitoring directory changes.

Provides RobustFileHandler and Watcher classes for monitoring directories
and detecting file creation/modification events. Uses watchdog library with
threading for non-blocking operation.

Features:
- Monitors file creation and modification events
- Filters for Excel files (.xlsx, .xls)
- Prevents duplicate events within short time windows
- Runs in background daemon thread
"""
import logging
import time
from pathlib import Path
from queue import Queue
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Optional

class RobustFileHandler(FileSystemEventHandler):
    """
    Robust file system event handler with deduplication.
    
    Extends FileSystemEventHandler to listen to both file creation and
    modification events. Prevents duplicate processing by tracking recent
    events and ignoring files processed within 2-second windows.
    
    Only queues Excel files (.xlsx, .xls).
    """
    def __init__(self, queue: Queue) -> None:
        """
        Initialize file system event handler.
        
        Args:
            queue: Queue object where detected file paths are placed
        """
        self.queue: Queue = queue
        # Sử dụng set để tránh đưa cùng một file vào queue nhiều lần trong một khoảng thời gian ngắn
        self.recently_processed: set = set()
        self.last_event_time: dict = {}

    def _queue_file(self, filepath: Path) -> None:
        """
        Internal method to check and queue file for processing.
        
        Filters for Excel files only and prevents duplicate processing
        by checking if file was processed within the last 2 seconds.
        
        Args:
            filepath: Path to file to potentially queue
        
        Returns:
            None
        """
        # Chỉ xử lý file Excel
        if filepath.suffix.lower() not in ['.xlsx', '.xls']:
            return

        current_time = time.time()
        # Nếu file này đã được xử lý gần đây (trong vòng 2 giây), bỏ qua
        if filepath in self.last_event_time and current_time - self.last_event_time[filepath] < 2.0:
            return
        
        logging.info(f"[Watcher] Phát hiện sự kiện cho file: {filepath.name}")
        self.queue.put(filepath)
        self.last_event_time[filepath] = current_time

    def on_created(self, event) -> None:
        """
        Handle file creation events.
        
        Called by watchdog when a file is created in the monitored directory.
        Ignores directory events, only processes files.
        
        Args:
            event: FileSystemEventHandler event from watchdog
        """
        if not event.is_directory:
            self._queue_file(Path(event.src_path))

    def on_modified(self, event) -> None:
        """
        Handle file modification events.
        
        Called by watchdog when a file is modified in the monitored directory.
        Ignores directory events, only processes files.
        
        Args:
            event: FileSystemEventHandler event from watchdog
        """
        if not event.is_directory:
            self._queue_file(Path(event.src_path))

class Watcher:
    """
    Directory watcher that manages file monitoring in a separate thread.
    
    Monitors a directory for Excel file changes (creation/modification) and
    queues detected files for processing. Runs in background daemon thread
    using the watchdog library.
    """
    def __init__(self, path_to_watch, queue: Optional[Queue] = None) -> None:
        """
        Initialize directory watcher.
        
        Args:
            path_to_watch: Directory path to monitor (str or Path)
            queue: Optional Queue for detected files. Creates new Queue if not provided.
        """
        self.path: Path = path_to_watch if isinstance(path_to_watch, Path) else Path(path_to_watch)
        self.queue: Queue = queue if queue else Queue()
        # <<< THAY ĐỔI: Sử dụng handler mới
        self.event_handler: RobustFileHandler = RobustFileHandler(self.queue)
        self.observer: Observer = Observer()
        self.thread: Optional[Thread] = None
        self.is_running: bool = False

    def start(self) -> None:
        """
        Start the directory watcher thread.
        
        Creates and starts a daemon thread to monitor the directory.
        If watcher is already running, logs a warning and returns without
        creating a duplicate thread.
        
        Returns:
            None
        
        Example:
            >>> watcher.start()
            # Now monitoring the directory
        """
        if self.thread and self.thread.is_alive():
            logging.warning("[Watcher] Tiến trình theo dõi đã chạy.")
            return

        self.is_running = True
        self.observer = Observer()
        self.observer.schedule(self.event_handler, str(self.path), recursive=False)
        
        self.thread = Thread(target=self.observer.start, daemon=True)
        self.thread.start()
        logging.info(f"[Watcher] Bắt đầu theo dõi thư mục: {self.path}")

    def stop(self) -> None:
        """
        Stop the directory watcher thread.
        
        Stops the observer and waits for the thread to join. Sets is_running
        flag to False. Safe to call even if watcher is not currently running.
        
        Returns:
            None
        
        Example:
            >>> watcher.stop()
            # Directory monitoring has stopped
        """
        self.is_running = False
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            logging.info("[Watcher] Đã dừng theo dõi thư mục.")