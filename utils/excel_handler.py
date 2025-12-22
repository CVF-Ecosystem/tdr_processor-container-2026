# utils/excel_handler.py
import logging
from pathlib import Path
import pandas as pd
from datetime import time, datetime # Cho isinstance check
import openpyxl # <<< THÊM THƯ VIỆN NÀY
import shutil

try:
    import config
except ImportError:
    print("LỖI: Không tìm thấy config.py trong excel_handler.")
    # Mock config nếu cần
    class ConfigMockExcelHandler:
        DATETIME_FORMAT_OUT = '%d/%m/%Y %H:%M'
        DATE_FORMAT_OUT = '%d/%m/%Y'
        TIME_FORMAT_OUT = '%H:%M'
    config = ConfigMockExcelHandler()

def append_df_to_excel(filename_path_obj: Path, df_to_append: pd.DataFrame, sheet_name_str: str,
                       index=False, datetime_cols_to_format=None, time_cols_to_format=None, **kwargs) -> pd.DataFrame | None:
    """
    Nối dữ liệu vào file Excel một cách an toàn nhất.
    Quy trình: XÓA DỮ LIỆU CŨ -> NỐI DỮ LIỆU MỚI -> GHI ĐÈ.
    """
    logging.info(f"Bắt đầu quy trình ghi an toàn cho file: {filename_path_obj.name}, Sheet: {sheet_name_str}")

    if df_to_append.empty:
        logging.info(f"Không có dữ liệu mới để ghi vào '{sheet_name_str}'. Bỏ qua.")
        if filename_path_obj.exists():
            try:
                return pd.read_excel(filename_path_obj, sheet_name=sheet_name_str, engine='openpyxl')
            except Exception:
                return pd.DataFrame()
        return pd.DataFrame()

    # Bước 1: Đọc dữ liệu cũ (nếu có)
    df_existing = pd.DataFrame()
    if filename_path_obj.exists():
        try:
            df_existing = pd.read_excel(filename_path_obj, sheet_name=sheet_name_str, engine='openpyxl')
            logging.info(f"Đã đọc {len(df_existing)} dòng cũ từ sheet '{sheet_name_str}'.")
        except ValueError:
            logging.info(f"Sheet '{sheet_name_str}' không tồn tại trong file. Sẽ tạo sheet mới.")
        except Exception as e:
            logging.warning(f"Không thể đọc file '{filename_path_obj.name}'. Sẽ tạo file mới. Lỗi: {e}")

    # Bước 2: Xóa tất cả các dòng thuộc về các file đang được xử lý
    filenames_to_update = df_to_append['Filename'].unique()
    if not df_existing.empty and 'Filename' in df_existing.columns:
        before_count = len(df_existing)
        df_cleaned = df_existing[~df_existing['Filename'].isin(filenames_to_update)]
        after_count = len(df_cleaned)
        if before_count > after_count:
            logging.info(f"Đã xóa {before_count - after_count} dòng dữ liệu cũ của các file đang được cập nhật.")
    else:
        df_cleaned = df_existing

    # <<< BƯỚC PHÒNG VỆ QUAN TRỌNG: Xử lý cột trùng lặp trước khi concat >>>
    # Lấy danh sách các cột duy nhất theo đúng thứ tự xuất hiện
    def get_unique_columns(df):
        seen = set()
        unique_cols = []
        for col in df.columns:
            if col not in seen:
                seen.add(col)
                unique_cols.append(col)
        return unique_cols

    # Áp dụng cho cả hai DataFrame
    if not df_cleaned.columns.is_unique:
        logging.warning(f"Phát hiện cột trùng lặp trong dữ liệu cũ của file '{filename_path_obj.name}'. Đang xử lý...")
        df_cleaned = df_cleaned.loc[:, get_unique_columns(df_cleaned)]

    if not df_to_append.columns.is_unique:
        logging.warning(f"Phát hiện cột trùng lặp trong dữ liệu mới cho file '{filename_path_obj.name}'. Đang xử lý...")
        df_to_append = df_to_append.loc[:, get_unique_columns(df_to_append)]
    # <<< KẾT THÚC BƯỚC PHÒNG VỆ >>>

    # Bước 3: Nối dữ liệu mới vào DataFrame đã được làm sạch
    df_final = pd.concat([df_cleaned, df_to_append], ignore_index=True)
    logging.info(f"Sau khi nối, tổng số dòng cuối cùng là {len(df_final)}.")

    # Bước 4: Ghi đè hoàn toàn file với dữ liệu đã được làm sạch
    try:
        temp_file_path = filename_path_obj.with_suffix(f'.{datetime.now().timestamp()}.tmp')
        with pd.ExcelWriter(temp_file_path, engine='openpyxl') as writer:
            df_final.to_excel(writer, sheet_name=sheet_name_str, index=index, **kwargs)
        
        shutil.move(temp_file_path, filename_path_obj)
        
        logging.info(f"Ghi đè thành công file '{filename_path_obj.name}' với {len(df_final)} dòng.")
        return df_final

    except Exception as e:
        logging.error(f"Lỗi nghiêm trọng khi ghi file Excel '{filename_path_obj.name}': {e}", exc_info=True)
        if temp_file_path.exists():
            temp_file_path.unlink()
        return None