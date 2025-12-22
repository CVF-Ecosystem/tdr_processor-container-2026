# tests/test_excel_utils.py
import pytest
from datetime import date, datetime, time, timedelta
import pandas as pd # Cần cho pd.NA nếu dùng trong các hàm được test

# Để import các module từ thư mục cha (tdr_processor) khi chạy pytest từ thư mục gốc
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Hoặc nếu bạn cấu hình PYTHONPATH, hoặc dùng pytest-pythonpath

from utils.excel_utils import (
    col_letter_to_index,
    timedelta_to_hours,
    classify_error_code,
    # find_label_row_col, # Test hàm này cần mock openpyxl.Worksheet hoặc file Excel mẫu
    excel_to_time,
    parse_excel_datetime,
    parse_time_duration
)
# Mock config cho các hàm trong excel_utils nếu chúng dựa vào global config
# Tốt nhất là các hàm tiện ích không nên phụ thuộc vào global config, mà nhận qua tham số
# Hoặc chúng ta phải đảm bảo rằng khi chạy test, config của project được load đúng cách.
# Giả sử các hàm trong excel_utils đã được điều chỉnh để không phụ thuộc config toàn cục
# hoặc chúng ta sẽ mock config nếu cần thiết cho từng test.

# --- Mock config cho classify_error_code ---
# Đây là cách để mock nếu hàm đó đọc trực tiếp từ module config
# và chúng ta không muốn sửa hàm đó để nhận config làm tham số ngay.
class MockExcelUtilsConfig:
    DELAY_ERROR_UNKNOWN_TYPE = "Unknown Test Type"
    DELAY_ERROR_CODE_CLASSIFICATION = {
        "Terminal Convenience": list('abc'), # Giả sử config test khác production
        "Non-Terminal Convenience": list('xyz')
    }
    DELAY_ERROR_FORCE_MAJEURE_KEYWORDS = ["bão", "thiên tai"]

# --- Tests for col_letter_to_index ---
def test_col_letter_to_index_single_char():
    assert col_letter_to_index('A') == 1
    assert col_letter_to_index('Z') == 26

def test_col_letter_to_index_multi_char():
    assert col_letter_to_index('AA') == 27
    assert col_letter_to_index('AZ') == 52
    assert col_letter_to_index('BA') == 53

def test_col_letter_to_index_lowercase():
    assert col_letter_to_index('a') == 1
    assert col_letter_to_index('az') == 52

def test_col_letter_to_index_invalid_input():
    assert col_letter_to_index('') is None
    assert col_letter_to_index(None) is None
    assert col_letter_to_index('123') is None # Đã sửa hàm để trả về None
    assert col_letter_to_index('A1') is None  # Đã sửa hàm để trả về None

@pytest.mark.parametrize("input_val, ref_date, is_date_only, expected", [
    ("25/12/2023 14:30", None, False, datetime(2023, 12, 25, 14, 30)),
    ("25/12/2023", None, True, date(2023, 12, 25)),
    ("12/25/2023 10:00 AM", None, False, datetime(2023, 12, 25, 10, 0)),
    ("12/25/2023 02:30 PM", None, False, datetime(2023, 12, 25, 14, 30)),
    (datetime(2023, 5, 10, 8, 0), None, False, datetime(2023, 5, 10, 8, 0)),
    (datetime(2023, 5, 10, 8, 0), None, True, date(2023, 5, 10)),
    (date(2023, 7, 7), None, False, date(2023, 7, 7)),
    (date(2023, 7, 7), None, True, date(2023, 7, 7)),
    ("15:45", date(2023, 1, 1), False, datetime(2023, 1, 1, 15, 45)),
    ("08:00", date(2023, 10, 20), False, datetime(2023, 10, 20, 8, 0)),
    # DÒNG CẦN SỬA ĐÂY:
    (0.75, date(2023, 1, 1), False, datetime(2023, 1, 1, 18, 0, 0)), # Thêm giây = 0 cho đầy đủ
    (45321.5, None, False, datetime(2024, 1, 30, 12, 0, 0)),
    (45321, None, True, date(2024, 1, 30)),
    ("Invalid String", None, False, None),
    (None, None, False, None),
    ("10/07", date(2023,1,1), True, date(2023, 7, 10)),
    ("07/25", date(2023,1,1), True, date(2023, 7, 25)),
    ("Jul 10", date(2023,1,1), True, date(2023, 7, 10)),
    ("10-Jul-2023", None, True, date(2023, 7, 10)),
    ("July 10, 2023", None, True, date(2023, 7, 10)),
])
def test_parse_excel_datetime_various_inputs(input_val, ref_date, is_date_only, expected):
    assert parse_excel_datetime(input_val, date_val_for_time=ref_date, is_just_date=is_date_only) == expected
# --- Tests for timedelta_to_hours ---
def test_timedelta_to_hours_positive():
    assert timedelta_to_hours(timedelta(hours=1)) == 1.0
    assert timedelta_to_hours(timedelta(hours=2, minutes=30)) == 2.5
    assert timedelta_to_hours(timedelta(minutes=15)) == 0.25
    assert timedelta_to_hours(timedelta(seconds=36)) == 0.01 # 36/3600

def test_timedelta_to_hours_zero():
    assert timedelta_to_hours(timedelta(0)) == 0.0

def test_timedelta_to_hours_invalid_input():
    assert timedelta_to_hours(None) == 0.0 # Theo thiết kế hiện tại
    assert timedelta_to_hours(123) == 0.0   # Theo thiết kế hiện tại

# --- Tests for parse_excel_datetime ---
@pytest.mark.parametrize("input_val, ref_date, is_date_only, expected", [
    ("25/12/2023 14:30", None, False, datetime(2023, 12, 25, 14, 30)),
    ("25/12/2023", None, True, date(2023, 12, 25)),
    ("12/25/2023 10:00 AM", None, False, datetime(2023, 12, 25, 10, 0)), # Giả sử hàm hỗ trợ AM/PM
    (datetime(2023, 5, 10, 8, 0), None, False, datetime(2023, 5, 10, 8, 0)),
    (datetime(2023, 5, 10, 8, 0), None, True, date(2023, 5, 10)),
    (date(2023, 7, 7), None, False, date(2023, 7, 7)), # Nếu input là date, is_date_only=False vẫn trả date
    (date(2023, 7, 7), None, True, date(2023, 7, 7)),
    ("15:45", date(2023, 1, 1), False, datetime(2023, 1, 1, 15, 45)),
    ("08:00", date(2023, 10, 20), False, datetime(2023, 10, 20, 8, 0)),
    (0.75, date(2023, 1, 1), False, datetime(2023, 1, 1, 18, 0)), # 0.75 của một ngày là 6 PM
    (45321.5, None, False, datetime(2024, 1, 30, 12, 0, 0)), # Excel serial date
    (45321, None, True, date(2024, 1, 30)),
    ("Invalid String", None, False, None),
    (None, None, False, None),
    ("10/07", date(2023,1,1), True, date(2023,10,7)), # dd/mm với ref year
    ("Jul 10", date(2023,1,1), True, date(2023,7,10)), # Giả sử hàm hỗ trợ "Mon Day"
])
def test_parse_excel_datetime_various_inputs(input_val, ref_date, is_date_only, expected):
    assert parse_excel_datetime(input_val, date_val_for_time=ref_date, is_just_date=is_date_only) == expected

# --- Tests for classify_error_code ---
# Để test hàm này một cách độc lập, tốt nhất là nó không nên đọc config toàn cục
# mà nhận config làm tham số. Nếu không, chúng ta cần mock config.
# Giả sử chúng ta đã inject MockExcelUtilsConfig vào excel_utils.config cho test này
def test_classify_error_code_logic(monkeypatch):
    # Tạm thời monkeypatch config trong module excel_utils cho test này
    monkeypatch.setattr("utils.excel_utils.config", MockExcelUtilsConfig())

    assert classify_error_code("a - Hư hỏng thiết bị")[1] == "Terminal Convenience"
    assert classify_error_code("a")[1] == "Terminal Convenience"
    assert classify_error_code("x - Tàu chờ hoa tiêu")[1] == "Non-Terminal Convenience"
    assert classify_error_code("y")[1] == "Non-Terminal Convenience"
    assert classify_error_code("Thời tiết bão mạnh")[1] == "Other/Force Majeure"
    assert classify_error_code("kẹt xe ngoài cảng")[1] == MockExcelUtilsConfig.DELAY_ERROR_UNKNOWN_TYPE # Không có trong keywords
    assert classify_error_code("p - Lý do khác")[1] == MockExcelUtilsConfig.DELAY_ERROR_UNKNOWN_TYPE # 'p' không trong config
    assert classify_error_code(None)[1] == MockExcelUtilsConfig.DELAY_ERROR_UNKNOWN_TYPE
    assert classify_error_code("")[1] == MockExcelUtilsConfig.DELAY_ERROR_UNKNOWN_TYPE

# --- Tests for parse_time_duration ---
@pytest.mark.parametrize("input_val, expected_hours", [
    (timedelta(hours=1, minutes=45), 1.75),
    (time(2, 15, 0), 2.25),
    (datetime(2023,1,1, 3, 30, 0), 3.50), # Nếu truyền datetime, nó sẽ lấy phần time
    ("01:10", 1.17), # 1 + 10/60
    ("0:30:00", 0.5),
    (0.5, 12.0), # Nếu là 0.5 (nửa ngày theo Excel) -> 12 giờ
    (1.0/24.0 * 2.0, 2.0), # 2 giờ biểu diễn dạng Excel fraction
    (2.75, 2.75), # Nếu là số float > 1, coi là số giờ trực tiếp
    ("Invalid", 0.0),
    (None, 0.0)
])
def test_parse_time_duration_various(input_val, expected_hours):
    assert parse_time_duration(input_val) == expected_hours

# Test cho find_label_row_col sẽ phức tạp hơn vì cần mock Worksheet.
# Chúng ta có thể tạo file Excel mẫu và dùng openpyxl để load nó trong test.
# Ví dụ (cần file test_labels.xlsx):
# def test_find_label_row_col_found():
#     from openpyxl import load_workbook
#     # Tạo file test_labels.xlsx với "Target Label" ở C5
#     # wb = load_workbook("tests/test_data/test_labels.xlsx")
#     # ws = wb.active
#     # assert find_label_row_col(ws, "Target Label") == (5, 3)
    pass