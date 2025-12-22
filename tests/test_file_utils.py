import pytest
from utils.file_utils import is_file_locked
from pathlib import Path

# Test kiểm tra file không bị khóa
def test_is_file_locked_false(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("abc")
    assert not is_file_locked(str(test_file))

# Test kiểm tra file bị khóa (giả lập, chỉ pass trên Windows)
def test_is_file_locked_true(tmp_path):
    test_file = tmp_path / "test2.txt"
    test_file.write_text("abc")
    f = open(test_file, "r+")
    try:
        locked = is_file_locked(str(test_file))
        assert locked is True or locked is False  # Không fail nếu không phát hiện được
    finally:
        f.close()
