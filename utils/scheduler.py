"""
Task scheduler using the schedule library with threading support.

Provides TaskScheduler class for scheduling and running tasks at specific times.
Uses daemon threading to run scheduled jobs without blocking the main application.
"""
import schedule
import time
import threading
import logging
from typing import Callable, Optional

class TaskScheduler:
    def __init__(self, job_func: Optional[Callable[[], None]] = None) -> None:
        """
        Initialize the task scheduler.
        
        Args:
            job_func: Optional callable to execute on schedule. Can be set later
                     via set_schedule() method.
        
        Attributes:
            running (bool): Flag indicating if scheduler thread is active
            thread (Optional[threading.Thread]): Scheduler background thread
            scheduled_time (Optional[str]): Time of day for scheduled execution
        """
        self.job_func: Optional[Callable[[], None]] = job_func
        self.running: bool = False  # <<< THÊM CỜ TRẠNG THÁI
        self.thread: Optional[threading.Thread] = None
        self.scheduled_time: Optional[str] = None

    def set_schedule(self, time_str: str) -> None:
        """
        Set daily schedule for job execution.
        
        Clears existing schedules and sets a new one to run at the specified time
        every day. The job function must be set before or during initialization.
        
        Args:
            time_str: Execution time in "HH:MM" format (24-hour) (e.g., "14:30")
        
        Raises:
            ValueError: If time_str format is invalid
        
        Example:
            >>> scheduler = TaskScheduler(job_func=my_task)
            >>> scheduler.set_schedule("09:00")  # Run at 9 AM daily
        """
        self.scheduled_time = time_str
        if self.job_func:
            schedule.clear()
            schedule.every().day.at(time_str).do(self.job_func)
        logging.info(f"[Scheduler] Đã đặt lịch chạy vào lúc {time_str} hàng ngày.")

    def clear_schedule(self) -> None:
        """
        Clear all scheduled jobs.
        
        Removes all pending scheduled tasks and resets the scheduled_time attribute.
        Can be called multiple times safely.
        
        Returns:
            None
        
        Example:
            >>> scheduler.clear_schedule()
            # All jobs removed
        """
        schedule.clear()
        self.scheduled_time = None
        logging.info("[Scheduler] Đã xóa tất cả các lịch chạy.")

    def _run_pending(self) -> None:
        """
        Background thread main loop for checking and executing scheduled jobs.
        
        Runs continuously while self.running is True. Checks for pending jobs
        every 1 second and executes them. Designed to run in a daemon thread.
        
        Returns:
            None (thread loop)
        
        Note:
            This is a private method - do not call directly. Started by start().
        """
        logging.info("[Scheduler] Thread của scheduler đã bắt đầu.")
        while self.running:  # <<< DÙNG CỜ ĐỂ KIỂM SOÁT VÒNG LẶP
            schedule.run_pending()
            time.sleep(1) # Ngủ 1 giây để giảm tải CPU
        logging.info("[Scheduler] Thread của scheduler đã dừng.")

    def start(self) -> None:
        """
        Start the scheduler background thread.
        
        Creates and starts a daemon thread to run scheduled jobs. If scheduler
        is already running, logs a message and returns without creating a new thread.
        
        Returns:
            None
        
        Note:
            Thread is created as daemon=True, so it will not prevent program exit.
        
        Example:
            >>> scheduler.start()
            # Scheduler thread now active
        """
        if not self.is_running(): # <<< KIỂM TRA TRƯỚC KHI CHẠY
            self.running = True
            self.thread = threading.Thread(target=self._run_pending, daemon=True)
            self.thread.start()
        else:
            logging.info("[Scheduler] Scheduler đã đang chạy, không cần khởi động lại.")

    def stop(self) -> None:
        """
        Stop the scheduler background thread.
        
        Sets the running flag to False, which causes the scheduler thread loop
        to exit. The daemon thread will terminate automatically without needing join().
        Safe to call even if scheduler is not currently running.
        
        Returns:
            None
        
        Example:
            >>> scheduler.stop()
            # Scheduler thread will exit after current iteration
        """
        if self.is_running():
            self.running = False # <<< ĐẶT CỜ ĐỂ DỪNG VÒNG LẶP
            # Không cần join() ở đây vì thread là daemon, nó sẽ tự thoát
            # khi chương trình chính kết thúc.
        else:
            logging.info("[Scheduler] Scheduler đã dừng, không cần dừng lại.")

    # <<< THÊM HÀM MỚI NÀY >>>
    def is_running(self) -> bool:
        """
        Check if scheduler background thread is currently active.
        
        Returns True only if the running flag is set AND the thread object exists
        AND the thread is alive. This prevents false positives if thread object
        exists but has terminated.
        
        Returns:
            bool: True if scheduler is actively running, False otherwise
        
        Example:
            >>> if scheduler.is_running():
            ...     print("Scheduler is active")
        """
        return self.running and self.thread is not None and self.thread.is_alive()