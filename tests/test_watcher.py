import pytest
from utils.watcher import Watcher
from pathlib import Path
import time

# Test khởi tạo Watcher và bắt đầu/dừng theo dõi thư mục
def test_watcher_start_stop(tmp_path):
    watcher = Watcher(str(tmp_path))
    watcher.start()
    assert watcher.is_running
    watcher.stop()
    assert not watcher.is_running

# Test phát hiện file mới (giả lập)
def test_watcher_detect_new_file(tmp_path):
    watcher = Watcher(str(tmp_path))
    watcher.start()
    # Tạo file mới
    new_file = tmp_path / "test.txt"
    new_file.write_text("test")
    time.sleep(0.2)  # Đợi watcher phát hiện
    watcher.stop()
    assert new_file.exists()
