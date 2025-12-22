import pytest
from utils.scheduler import TaskScheduler
import time

# Test khởi tạo và đặt lịch

def test_scheduler_set_and_clear_schedule():
    scheduler = TaskScheduler()
    scheduler.set_schedule("08:00")
    assert scheduler.scheduled_time == "08:00"
    scheduler.clear_schedule()
    assert scheduler.scheduled_time is None

# Test chạy thread scheduler (mock run)
def test_scheduler_thread_start_stop():
    scheduler = TaskScheduler()
    scheduler.set_schedule("08:00")
    scheduler.start()
    assert scheduler.is_running()
    scheduler.stop()
    assert not scheduler.is_running()
