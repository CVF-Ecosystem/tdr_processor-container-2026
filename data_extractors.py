# data_extractors.py
import logging
from pathlib import Path
from datetime import datetime, date, timedelta # <<< THÊM timedelta VÀO ĐÂY
import pandas as pd # <<< THÊM DÒNG NÀY


try:
    import config
    from utils.excel_utils import (
        col_letter_to_index, timedelta_to_hours, classify_error_code,
        find_label_row_col, excel_to_time, parse_excel_datetime, parse_time_duration,
        get_column_letter # Đảm bảo get_column_letter được import nếu dùng trong logging của extract
    )
    from utils.input_validator import validate_file_path
except ImportError as e:
    print(f"LỖI IMPORT trong data_extractors.py: {e}")
    # Fallback tối thiểu nếu chạy riêng (không khuyến khích)
    class MockConfig:
        # Thêm các thuộc tính config tối thiểu mà các hàm extract cần nếu muốn test riêng
        MAX_SEARCH_ROWS_VESSEL_INFO = 35
        VESSEL_INFO_LABELS = {} # Cần định nghĩa đầy đủ nếu test
        # ... và các config khác
    config = MockConfig()
    # Cần mock các hàm từ excel_utils nếu không import được
    def find_label_row_col(*args, **kwargs): return None, None
    def parse_excel_datetime(*args, **kwargs): return None
    # ... (mock các hàm khác)


class DataExtractor:
    def __init__(self, worksheet, filepath_obj: Path):
        """
        Initialize DataExtractor with worksheet and file path.
        
        Args:
            worksheet: openpyxl Worksheet object
            filepath_obj: Path object pointing to Excel file
            
        Raises:
            ValueError: If file path validation fails (path traversal attempt, invalid path)
        
        Security:
            - Validates file path to prevent path traversal attacks
            - Ensures file exists and is accessible
            - Logs only filename, not full path in some contexts
        """
        # SECURITY: Validate file path to prevent traversal attacks
        is_valid, error = validate_file_path(str(filepath_obj))
        if not is_valid:
            logging.error(f"File path validation failed: {error}")
            raise ValueError(f"Invalid file path: {error}")
        
        # Additional check: ensure file exists
        if not filepath_obj.exists():
            logging.error(f"File does not exist: {filepath_obj}")
            raise ValueError(f"File does not exist: {filepath_obj}")
        
        self.worksheet = worksheet
        self.filepath_obj = filepath_obj # Lưu lại để có thể dùng filename trong các phương thức
        self.filename_str = filepath_obj.name # Để tiện logging

        # Các thông tin chung có thể được trích xuất một lần và lưu vào self
        # để các phương thức khác sử dụng nếu cần, ví dụ:
        self.vessel_name = None
        self.voyage_no = None
        self.reference_date_for_events = None # Sẽ được xác định trong extract_vessel_info

    def extract_vessel_info(self):
        """Extract vessel summary information from the worksheet."""
        info = {"Filename": self.filename_str}
        logging.info(f"--- Extracting Vessel Info: {info['Filename']} ---")
        
        raw_vals = {}
        for key, label_str in config.VESSEL_INFO_LABELS.items():
            label_col_letter = config.VESSEL_INFO_LABEL_COL_LETTERS.get(key)
            value_col_letter = config.VESSEL_INFO_VALUE_COL_LETTERS.get(key)
            if not label_col_letter or not value_col_letter:
                logging.warning(f"Vessel Info: Missing column config for key '{key}' in config.py")
                raw_vals[key] = None
                continue
            
            r, _ = find_label_row_col(self.worksheet, label_str, specific_col_letter=label_col_letter,
                                      max_search_rows=config.MAX_SEARCH_ROWS_VESSEL_INFO, partial_match=True)
            val_idx = col_letter_to_index(value_col_letter)
            raw_vals[key] = self.worksheet.cell(row=r, column=val_idx).value if r and val_idx else None
            if "str" not in key: 
                 info[key] = str(raw_vals[key]).strip() if raw_vals[key] is not None else None

        init_ref_date = parse_excel_datetime(raw_vals.get("Report Date_str"), is_just_date=True, context="ReportDateStr")
        info["Report Date"] = init_ref_date

        atd_dt = parse_excel_datetime(raw_vals.get("ATD_str"), init_ref_date, False, "ATDStr")
        info["ATD"] = atd_dt
        # Tìm ngày bắt đầu hoạt động sớm nhất
        comm_dis = info.get("Commenced Discharge")
        comm_load = info.get("Commenced Loading")
        
        first_op_datetime = None
        if isinstance(comm_dis, datetime) and isinstance(comm_load, datetime):
            first_op_datetime = min(comm_dis, comm_load)
        elif isinstance(comm_dis, datetime):
            first_op_datetime = comm_dis
        elif isinstance(comm_load, datetime):
            first_op_datetime = comm_load

        # Gán ngày tham chiếu
        if first_op_datetime:
            self.reference_date_for_events = first_op_datetime.date()
        elif info.get("ATB") and isinstance(info.get("ATB"), datetime):
            self.reference_date_for_events = info.get("ATB").date()
        else:
            self.reference_date_for_events = date.today()
            logging.warning(f"Không tìm thấy ngày bắt đầu hoạt động, sử dụng ngày hôm nay làm tham chiếu.")        
        self.reference_date_for_events = (atd_dt.date() if isinstance(atd_dt, datetime) else
                                    (atd_dt if isinstance(atd_dt, date) else init_ref_date))
        if self.reference_date_for_events is None: 
            self.reference_date_for_events = date.today()
            logging.warning(f"Vessel Info: ATD and Report Date are missing. Using today's date ({self.reference_date_for_events}) as reference for other events.")

        dt_keys_in_config = ["ETB", "ATB", "ETD", "Gangway Secured", "Commenced Discharge",
                             "Completed Discharge", "Commenced Loading", "Completed Loading", "Lashing Finished"]
        for key_prefix in dt_keys_in_config:
            raw_val_key = key_prefix + "_str" 
            info[key_prefix] = parse_excel_datetime(raw_vals.get(raw_val_key), self.reference_date_for_events, False, key_prefix + "Str")

        r_gt, _ = find_label_row_col(self.worksheet, config.LABEL_GRAND_TOTAL_IN_CONTAINER_SUMMARY,
                                     specific_col_letter='B', 
                                     max_search_rows=self.worksheet.max_row, partial_match=True)
        if r_gt:
            gt_conts_col_idx = col_letter_to_index(config.CONTAINER_SUMMARY_ROW_TOTAL_CONTS_COL_LETTER)
            gt_teus_col_idx = col_letter_to_index(config.CONTAINER_SUMMARY_ROW_TEUS_COL_LETTER)
            info["Grand Total Conts"] = int(self.worksheet.cell(r_gt, gt_conts_col_idx).value or 0) if gt_conts_col_idx else 0
            info["Grand Total TEUs"] = int(self.worksheet.cell(r_gt, gt_teus_col_idx).value or 0) if gt_teus_col_idx else 0
        else:
            info["Grand Total Conts"], info["Grand Total TEUs"] = 0,0
            logging.warning(f"Vessel Info: Could not find '{config.LABEL_GRAND_TOTAL_IN_CONTAINER_SUMMARY}' to get vessel Grand Total Conts/TEUs.")

        atb, atd = info.get("ATB"), info.get("ATD")
        cd, completed_discharge = info.get("Commenced Discharge"), info.get("Completed Discharge")
        cl, completed_loading = info.get("Commenced Loading"), info.get("Completed Loading")

        info["Portstay (hrs)"] = timedelta_to_hours(atd - atb) if all(isinstance(x, datetime) for x in [atd, atb]) and atd > atb else 0.0
        info["Discharge Duration (hrs)"] = timedelta_to_hours(completed_discharge - cd) if all(isinstance(x, datetime) for x in [completed_discharge, cd]) and completed_discharge > cd else 0.0
        info["Load Duration (hrs)"] = timedelta_to_hours(completed_loading - cl) if all(isinstance(x, datetime) for x in [completed_loading, cl]) and completed_loading > cl else 0.0
        
        first_op = min(filter(None, [cd, cl]), default=None, key=lambda x: x if isinstance(x, datetime) else datetime.max)
        last_op = max(filter(None, [completed_discharge, completed_loading]), default=None, key=lambda x: x if isinstance(x, datetime) else datetime.min)
        info["Gross Working (hrs)"] = timedelta_to_hours(last_op - first_op) if all(isinstance(x, datetime) for x in [last_op, first_op]) and last_op > first_op else 0.0
        # <<< THAY THẾ HOÀN TOÀN KHỐI CODE LẤY BREAK TIME DƯỚI ĐÂY
        info["Break Dis (hrs)"], info["Break Load (hrs)"] = 0.0, 0.0
        # 1. Tìm vị trí của bảng "Break Time"
        r_break_time_header, _ = find_label_row_col(self.worksheet, config.LABEL_BREAK_TIME_SUMMARY_VESSEL,
                                                    specific_col_letter='B', 
                                                    max_search_rows=self.worksheet.max_row, partial_match=True)
        
        if r_break_time_header:
        # 2. Từ vị trí đó, tìm dòng "Total stop" trong phạm vi 5 dòng tiếp theo
            #    chỉ tìm trong cột B để đảm bảo đúng
            r_total_stop, _ = find_label_row_col(self.worksheet, "Total stop",
                                                 start_row=r_break_time_header + 1,
                                                 max_search_rows=5, # Giới hạn vùng tìm kiếm
                                                 specific_col_letter='B',
                                                 partial_match=True)
            
            if r_total_stop:
                logging.info(f"Tìm thấy dòng 'Total stop' cho Break Time ở hàng {r_total_stop}.")
            # 3. Lấy dữ liệu từ các cột đã định nghĩa trong config tại dòng "Total stop"
                dis_break_col_idx = col_letter_to_index(config.BREAK_TIME_DISCHARGE_COL_LETTER)
                load_break_col_idx = col_letter_to_index(config.BREAK_TIME_LOADING_COL_LETTER)

                if dis_break_col_idx:
                    raw_dis_break = self.worksheet.cell(r_total_stop, dis_break_col_idx).value
                    info["Break Dis (hrs)"] = parse_time_duration(raw_dis_break)
                
                if load_break_col_idx:
                    raw_load_break = self.worksheet.cell(r_total_stop, load_break_col_idx).value
                    info["Break Load (hrs)"] = parse_time_duration(raw_load_break)
            else:
                logging.warning(f"Không tìm thấy dòng 'Total stop' trong bảng Break Time. Break time có thể không chính xác.")
        else:
            logging.warning(f"Không tìm thấy bảng '{config.LABEL_BREAK_TIME_SUMMARY_VESSEL}'. Break time sẽ là 0.")
        # <<< KẾT THÚC KHỐI CODE THAY THẾ
        # 4. Tính toán các giá trị khác dựa trên thông tin đã trích xuất
        info["Break Time (hrs)"] = round(info.get("Break Dis (hrs)", 0.0) + info.get("Break Load (hrs)", 0.0), 2) 
        info["Net Working (hrs)"] = info["Gross Working (hrs)"] 
        info["Idle (hrs)"] = max(0, info["Portstay (hrs)"] - info["Gross Working (hrs)"])

        for kpi in ["Vessel Moves/Net Hour", "Vessel Moves/Gross Hour", "Vessel Moves/Portstay Hour"]:
            info[kpi] = 0.0
            
        # Lưu lại vessel_name và voyage_no để các hàm extract khác có thể dùng
        self.vessel_name = info.get("Vessel Name")
        self.voyage_no = info.get("Voyage")
            
        logging.info(f"--- Vessel Info Extracted & Calculated for {info['Filename']} ---\n{info}\n")
        return info

    @staticmethod
    def _parse_moves_hour_value(val) -> float:
        """Parse moves/hour value from various input types."""
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            try:
                return float(val.replace(",", "."))
            except ValueError:
                return 0.0
        return 0.0

    def _get_cell_value(self, row: int, column_map: dict, key: str, parse_func=None, default_value=None):
        """Get and optionally parse a cell value from the worksheet using column_map."""
        if key not in column_map or column_map[key] is None:
            return default_value
        raw = self.worksheet.cell(row=row, column=column_map[key]).value
        if raw is None or (isinstance(raw, str) and raw.strip() == ''):
            return default_value
        if parse_func:
            parsed = parse_func(raw)
            return parsed if parsed is not None else default_value
        try:
            return raw if not pd.isna(raw) else default_value
        except (TypeError, ValueError):
            return raw

    def extract_qc_productivity(self):
        """Extract QC crane productivity data from the worksheet."""
        qc_data_list = []
        logging.info(f"--- Extracting QC Productivity: {self.filename_str}, Vessel: {self.vessel_name} ---")

        if not self.vessel_name or not self.voyage_no:
            logging.error(f"QC Productivity: Vessel Name or Voyage No. not extracted prior to QC extraction for {self.filename_str}. Skipping.")
            return []

        r_qc_h, _ = find_label_row_col(self.worksheet, config.LABEL_CRANES_PRODUCTIVITY,
                                       max_search_rows=config.MAX_SEARCH_ROWS_QC_HEADER)
        if not r_qc_h:
            logging.warning(f"'{config.LABEL_CRANES_PRODUCTIVITY}' not found in {self.filename_str}. Skipping QC productivity.")
            return qc_data_list

        hdr_r1 = r_qc_h + config.QC_HEADER_ROW_1_OFFSET
        hdr_r2 = r_qc_h + config.QC_HEADER_ROW_2_OFFSET
        header_values_row_1 = [str(self.worksheet.cell(hdr_r1, c).value or "").lower().strip() for c in range(1, self.worksheet.max_column + 1)]
        header_values_row_2 = [str(self.worksheet.cell(hdr_r2, c).value or "").lower().strip() for c in range(1, self.worksheet.max_column + 1)]

        column_map = {}
        for key, variants in config.QC_PRODUCTIVITY_HEADER_VARIANTS.items():
            found_in_h1 = False
            for name_v in variants:
                try:
                    column_map[key] = header_values_row_1.index(name_v) + 1
                    logging.info(f"QC_HDR_MAP: Found '{key}' (as '{name_v}') in header row 1, col {column_map[key]} for {self.filename_str}")
                    found_in_h1 = True
                    break
                except ValueError:
                    pass
            if not found_in_h1 and key in ["dis_conts", "load_conts", "shifting_conts"]:
                for name_v in variants:
                    try:
                        column_map[key] = header_values_row_2.index(name_v) + 1
                        logging.info(f"QC_HDR_MAP: Found '{key}' (as '{name_v}') in header row 2, col {column_map[key]} for {self.filename_str}")
                        break
                    except ValueError:
                        pass
            if key not in column_map:
                logging.warning(f"QC_HDR_MAP: NOT Found '{key}' for {self.filename_str}")

        if "qc_no" not in column_map:
            logging.error(f"'QC No.' column (key 'qc_no') not found in QC Productivity header for {self.filename_str}. Skipping QC data.")
            return qc_data_list

        if any(h for h in header_values_row_2 if h):
            data_start_row = hdr_r2 + 1
        else:
            data_start_row = hdr_r1 + config.QC_DATA_START_ROW_OFFSET_FROM_H1

        curr_r = data_start_row
        while curr_r <= self.worksheet.max_row:
            qc_no_val = self.worksheet.cell(curr_r, column_map["qc_no"]).value
            s_val_cell = self.worksheet.cell(curr_r, column_map.get("start_time")) if "start_time" in column_map else None
            e_val_cell = self.worksheet.cell(curr_r, column_map.get("end_time")) if "end_time" in column_map else None
            start_value = s_val_cell.value if s_val_cell else None
            end_value = e_val_cell.value if e_val_cell else None
            qc_no_str = str(qc_no_val).strip().upper() if qc_no_val else ""

            if not qc_no_str or "total" in qc_no_str.lower() or (pd.isna(start_value) and pd.isna(end_value)):
                logging.info(f"QC Productivity: Stopping read at row {curr_r} due to empty/total QC No. or missing Start/End Time.")
                break

            is_valid_qc_identifier = any(identifier in qc_no_str for identifier in config.QC_IDENTIFIERS_IN_DATA)
            if not is_valid_qc_identifier:
                logging.debug(f"QC Productivity: Row {curr_r} QC No. '{qc_no_str}' does not match identifiers. Skipping.")
                curr_r += 1
                continue

            qc_no_to_store = str(qc_no_val).strip()

            # Use _get_cell_value helper (defined outside loop - no redefinition per iteration)
            s_time = self._get_cell_value(curr_r, column_map, "start_time", excel_to_time)
            e_time = self._get_cell_value(curr_r, column_map, "end_time", excel_to_time)

            # Prefer reported gross working hours; fall back to calculated from start/end times
            gross_w_rep = self._get_cell_value(curr_r, column_map, "gross_working_reported", parse_time_duration, 0.0)
            gross_w_calc = 0.0
            if s_time and e_time and self.reference_date_for_events:
                start_dt = datetime.combine(self.reference_date_for_events, s_time)
                end_dt = datetime.combine(self.reference_date_for_events, e_time)
                while end_dt < start_dt:
                    end_dt += timedelta(days=1)
                gross_w_calc = timedelta_to_hours(end_dt - start_dt)

            gross_w = round(gross_w_rep if gross_w_rep > 0 else gross_w_calc, 2)

            delay_t_reported = self._get_cell_value(curr_r, column_map, "delay_times_reported", parse_time_duration, 0.0)
            net_w_reported = self._get_cell_value(curr_r, column_map, "net_working_reported", parse_time_duration, 0.0)
            dis_c = int(self._get_cell_value(curr_r, column_map, "dis_conts", None, 0) or 0)
            load_c = int(self._get_cell_value(curr_r, column_map, "load_conts", None, 0) or 0)
            shift_c = int(self._get_cell_value(curr_r, column_map, "shifting_conts", None, 0) or 0)
            total_c_rep = int(self._get_cell_value(curr_r, column_map, "total_conts_qc_reported", None, 0) or 0)
            total_c_calc = dis_c + load_c + shift_c
            total_c = total_c_calc if total_c_calc > 0 else total_c_rep

            gross_moves_h_rep = self._get_cell_value(curr_r, column_map, "gross_moves_h_reported", self._parse_moves_hour_value, 0.0)
            net_moves_h_rep = self._get_cell_value(curr_r, column_map, "net_moves_h_reported", self._parse_moves_hour_value, 0.0)
            gross_moves_calc = round(total_c / gross_w, 1) if gross_w > 0 and total_c > 0 else gross_moves_h_rep

            qc_data_list.append({
                "Filename": self.filename_str,
                "Vessel Name": self.vessel_name,
                "Voyage": self.voyage_no,
                "QC No.": qc_no_to_store,
                "Start Time": s_time,
                "End Time": e_time,
                "Gross working (hrs)": gross_w,
                "Delay times (hrs)": delay_t_reported,
                "Net working (hrs)": net_w_reported,
                "Discharge Conts": dis_c,
                "Load Conts": load_c,
                "Shifting Conts": shift_c,
                "Total Conts": total_c,
                "Gross moves/h": gross_moves_calc,
                "Net moves/h": net_moves_h_rep,  # Matches QC_COLS_OUTPUT_ORDER in config
            })
            curr_r += 1
            if curr_r > self.worksheet.max_row + 5:
                logging.error(f"QC Productivity: Exceeded max row search limit for {self.filename_str}. Breaking loop.")
                break

        logging.info(f"--- QC Productivity Extracted for {self.filename_str}. Count: {len(qc_data_list)} ---")
        return qc_data_list


    def extract_delay_details(self, ref_date_for_delay_calc: date):
        """Extract delay/stop event details from the delay times record table."""
        delay_list = []
        logging.info(f"--- Extracting Delay Details: {self.filename_str} ---")
        if not self.vessel_name or not self.voyage_no:
            logging.error(f"Delay Details: Vessel Name or Voyage No. not extracted prior to Delay extraction for {self.filename_str}. Skipping.")
            return []

        r_delay_start, _ = find_label_row_col(self.worksheet, config.LABEL_DELAY_TIMES_RECORD, max_search_rows=config.MAX_SEARCH_ROWS_DELAY_HEADER, partial_match=True)
        if not r_delay_start:
            r_delay_start_alt, _ = find_label_row_col(self.worksheet, config.LABEL_QC_NO_IN_DELAY_HEADER, search_cols=(col_letter_to_index('B'), col_letter_to_index('B')), max_search_rows=config.MAX_SEARCH_ROWS_DELAY_HEADER, partial_match=False)
            if r_delay_start_alt:
                r_delay_start = r_delay_start_alt - config.DELAY_QC_HEADER_ROW_OFFSET
                logging.info(f"Delay Details: Found header via '{config.LABEL_QC_NO_IN_DELAY_HEADER}' at row {r_delay_start_alt}, adjusted to {r_delay_start}.")
            else:
                logging.warning(f"Delay header ('{config.LABEL_DELAY_TIMES_RECORD}' or '{config.LABEL_QC_NO_IN_DELAY_HEADER}') not found in {self.filename_str}. Skipping delay details.")
                return delay_list
        qc_header_row = r_delay_start + config.DELAY_QC_HEADER_ROW_OFFSET
        qc_configs_from_file = []
        for qc_block_cfg in config.DELAY_QC_COLUMN_BLOCKS:
            qc_name_col_idx = col_letter_to_index(qc_block_cfg["name_col_letter"])
            if not qc_name_col_idx: continue
            qc_name_val = self.worksheet.cell(qc_header_row, qc_name_col_idx).value
            qc_name_str = str(qc_name_val).strip().upper() if qc_name_val else ""
            if qc_name_str and any(identifier in qc_name_str for identifier in config.DELAY_QC_IDENTIFIERS_IN_HEADER):
                qc_configs_from_file.append({
                    "name": str(qc_name_val).strip(), 
                    "from_idx": col_letter_to_index(qc_block_cfg["from_col_letter"]),
                    "to_idx": col_letter_to_index(qc_block_cfg["to_col_letter"]),
                    "hrs_idx": col_letter_to_index(qc_block_cfg["hours_col_letter"]),
                    "err_idx": col_letter_to_index(qc_block_cfg["error_remark_col_letter"])
                })
        if not qc_configs_from_file:
            logging.warning(f"No valid QC names found in delay header (row {qc_header_row}) for {self.filename_str}. Skipping delay details.")
            return delay_list
        logging.info(f"Delay QC Configs from file: {[qc['name'] for qc in qc_configs_from_file]}")
        last_processed_row_for_stops = qc_header_row + 1
        for stop_cat_key, stop_cat_config in config.DELAY_STOP_CATEGORIES.items():
            stop_label_text = stop_cat_config["label"]
            rows_to_check_for_stop = stop_cat_config["rows_to_check"]
            sub_header_texts_for_stop = stop_cat_config.get("sub_header_texts", [])
            r_stop_label, _ = find_label_row_col(self.worksheet, stop_label_text, specific_col_letter='B', start_row=last_processed_row_for_stops, max_search_rows=config.MAX_SEARCH_ROWS_DELAY_STOP_LABEL, partial_match=True)
            if not r_stop_label:
                logging.info(f"Delay Details: Label '{stop_label_text}' not found in {self.filename_str} from row {last_processed_row_for_stops}.")
                continue
            logging.info(f"Delay Details: Processing '{stop_label_text}' found at row {r_stop_label}")
            data_start_for_this_stop = r_stop_label
            first_qc_from_col_idx = qc_configs_from_file[0]["from_idx"] if qc_configs_from_file else None
            if first_qc_from_col_idx:
                cell_val_at_from_col_for_label_row = str(self.worksheet.cell(r_stop_label, first_qc_from_col_idx).value or "").lower().strip()
                if any(sub_hdr_txt in cell_val_at_from_col_for_label_row for sub_hdr_txt in sub_header_texts_for_stop):
                    data_start_for_this_stop = r_stop_label + 1
                    logging.info(f"Delay Details: Row {r_stop_label} for '{stop_label_text}' is a sub-header. Data starts at {data_start_for_this_stop}.")
            for i in range(rows_to_check_for_stop):
                current_data_row = data_start_for_this_stop + i
                if current_data_row > self.worksheet.max_row: break 
                label_in_col_b = str(self.worksheet.cell(current_data_row, col_letter_to_index('B')).value or "").lower().strip()
                if config.LABEL_TOTAL_STOP_IN_DELAY_TABLE in label_in_col_b:
                    logging.info(f"Delay Details: Found '{config.LABEL_TOTAL_STOP_IN_DELAY_TABLE}' for '{stop_label_text}' at row {current_data_row}. Stopping this category.")
                    last_processed_row_for_stops = current_data_row + 1
                    break
                is_empty_across_all_qcs_this_row = True
                if i > 0: 
                    is_empty_across_all_qcs_this_row = all(
                        (not self.worksheet.cell(current_data_row, qc_cfg["from_idx"]).value and
                         not self.worksheet.cell(current_data_row, qc_cfg["to_idx"]).value and
                         not self.worksheet.cell(current_data_row, qc_cfg["hrs_idx"]).value)
                        for qc_cfg in qc_configs_from_file
                    )
                if i > 0 and not label_in_col_b and is_empty_across_all_qcs_this_row:
                    logging.info(f"Delay Details: Row {current_data_row} for '{stop_label_text}' appears empty. Stopping this category.")
                    last_processed_row_for_stops = current_data_row 
                    break
                for qc_c in qc_configs_from_file:
                    qc_name_d = qc_c["name"]
                    from_raw = self.worksheet.cell(current_data_row, qc_c["from_idx"]).value if qc_c["from_idx"] else None
                    to_raw = self.worksheet.cell(current_data_row, qc_c["to_idx"]).value if qc_c["to_idx"] else None
                    hrs_raw = self.worksheet.cell(current_data_row, qc_c["hrs_idx"]).value if qc_c["hrs_idx"] else None
                    err_rem_raw = self.worksheet.cell(current_data_row, qc_c["err_idx"]).value if qc_c["err_idx"] else None
                    err_rem_s = str(err_rem_raw or "").strip()
                    hrs_s = str(hrs_raw or "").strip()
                    if (from_raw is None or (isinstance(from_raw, str) and not from_raw.strip())) and \
                       (to_raw is None or (isinstance(to_raw, str) and not to_raw.strip())) and \
                       (hrs_raw is None or (isinstance(hrs_raw, str) and not hrs_s)): 
                        continue
                    dur_from_file = parse_time_duration(hrs_raw) 
                    from_p = parse_excel_datetime(from_raw, ref_date_for_delay_calc, False, f"DFrom_{qc_name_d}_{stop_cat_key}")
                    to_p = parse_excel_datetime(to_raw, ref_date_for_delay_calc, False, f"DTo_{qc_name_d}_{stop_cat_key}")
                    dur_calc, from_f, to_f = 0.0, from_p, to_p
                    if isinstance(from_p, datetime) and isinstance(to_p, datetime):
                        tmp_f, tmp_t = from_p, to_p
                        if tmp_t < tmp_f: tmp_t += timedelta(days=1)
                        if tmp_t > tmp_f: dur_calc = timedelta_to_hours(tmp_t - tmp_f)
                        from_f, to_f = tmp_f, tmp_t 
                    elif from_p or to_p: 
                        logging.warning(f"Delay Details: Incomplete From/To datetime for QC='{qc_name_d}',Stop='{stop_label_text}',R={current_data_row}. From='{from_p}', To='{to_p}'. Cannot calculate duration.")
                    dur_use = dur_from_file if dur_from_file > 0 else dur_calc
                    if dur_from_file > 0 and dur_calc > 0 and abs(dur_from_file - dur_calc) > config.DELAY_DURATION_MISMATCH_THRESHOLD:
                        logging.warning(f"DUR_MISMATCH: QC='{qc_name_d}',Stop='{stop_label_text}',R={current_data_row}. FileHrs={dur_from_file:.2f}, CalcHrs={dur_calc:.2f}. Using FileHrs.")
                        dur_use = dur_from_file 
                    if dur_use > 0:
                        err_c, err_t = classify_error_code(err_rem_s)
                        delay_list.append({
                            "Filename": self.filename_str, "Vessel Name": self.vessel_name, "Voyage": self.voyage_no,
                            "QC No.": qc_name_d, "Stop Category": stop_label_text,
                            "From Time": from_f, "To Time": to_f, "Duration (hrs)": dur_use,
                            "Error Code": err_c, "Error Type": err_t, "Remark": err_rem_s
                        })
                        logging.info(f"DELAY_REC: QC='{qc_name_d}',Stop='{stop_label_text}',R={current_data_row},From='{from_f}',To='{to_f}',Dur={dur_use:.2f},Err='{err_c}',Type='{err_t}'")
                if i == rows_to_check_for_stop -1 or config.LABEL_TOTAL_STOP_IN_DELAY_TABLE in label_in_col_b:
                     last_processed_row_for_stops = current_data_row + 1
        logging.info(f"--- Delay Details Extracted for {self.filename_str}. Count: {len(delay_list)} ---")
        return delay_list

    # <<< THÊM HÀM MỚI DƯỚI ĐÂY >>>
    def extract_qc_actual_delays(self) -> dict[str, float]:
        """
        Trích xuất tổng thời gian delay thực tế của từng QC từ bảng '* Delay times record:'.
        Hàm này chỉ tính tổng từ các dòng 'Total stop'.
        Trả về một dictionary: {'QC_NAME': total_delay_hours, ...}
        """
        qc_delays = {}
        logging.info(f"--- Extracting QC Actual Delays: {self.filename_str} ---")

        # 1. Tìm header của bảng delay
        r_delay_start, _ = find_label_row_col(self.worksheet, config.LABEL_DELAY_TIMES_RECORD, max_search_rows=config.MAX_SEARCH_ROWS_DELAY_HEADER, partial_match=True)
        if not r_delay_start:
            logging.warning(f"Không tìm thấy bảng '{config.LABEL_DELAY_TIMES_RECORD}'. Không thể tính delay thực tế của QC.")
            return qc_delays

        qc_header_row = r_delay_start + config.DELAY_QC_HEADER_ROW_OFFSET
        
        # 2. Xác định các QC và cột 'Hours' tương ứng của chúng
        qc_configs = []
        for qc_block_cfg in config.DELAY_QC_COLUMN_BLOCKS:
            qc_name_col_idx = col_letter_to_index(qc_block_cfg["name_col_letter"])
            if not qc_name_col_idx: continue
            
            qc_name_val = self.worksheet.cell(qc_header_row, qc_name_col_idx).value
            qc_name_str = str(qc_name_val).strip().upper() if qc_name_val else ""

            if qc_name_str and any(identifier in qc_name_str for identifier in config.DELAY_QC_IDENTIFIERS_IN_HEADER):
                qc_configs.append({
                    "name": str(qc_name_val).strip(),
                    "hrs_idx": col_letter_to_index(qc_block_cfg["hours_col_letter"])
                })
        
        if not qc_configs:
            logging.warning(f"Không tìm thấy tên QC hợp lệ trong header của bảng delay. Không thể tính delay thực tế.")
            return qc_delays

        # Khởi tạo tổng delay cho mỗi QC
        for qc in qc_configs:
            qc_delays[qc['name']] = 0.0

        # 3. Duyệt qua các dòng để tìm 'Total stop' và cộng dồn thời gian
        # Bắt đầu tìm từ sau dòng header của bảng delay
        current_row = qc_header_row + 1
        while current_row <= self.worksheet.max_row:
            # Tìm 'Total stop' trong cột B
            cell_b_val = str(self.worksheet.cell(current_row, 2).value or "").lower().strip()
            if "total stop" in cell_b_val:
                # Nếu tìm thấy, cộng dồn giá trị từ cột 'Hours' của mỗi QC
                for qc_cfg in qc_configs:
                    if qc_cfg['hrs_idx']:
                        raw_hours = self.worksheet.cell(current_row, qc_cfg['hrs_idx']).value
                        delay_hours = parse_time_duration(raw_hours)
                        qc_delays[qc_cfg['name']] += delay_hours
                logging.info(f"Đã tìm và cộng dồn 'Total stop' tại dòng {current_row}. Delays hiện tại: {qc_delays}")
            
            # Dừng nếu gặp bảng "Break Time" để tránh đọc nhầm
            if "break time" in cell_b_val:
                break
            
            current_row += 1
            # Giới hạn tìm kiếm để tránh vòng lặp vô tận
            if current_row > r_delay_start + 50: 
                break
        
        logging.info(f"--- QC Actual Delays Extracted: {qc_delays} ---")
        return qc_delays
    def extract_container_details(self):
        """Extract container discharge/load summary details from the worksheet."""
        container_details_list = []
        logging.info(f"--- Extracting Container Details: {self.filename_str} ---")
        if not self.vessel_name or not self.voyage_no:
            logging.error(f"Container Details: Vessel Name or Voyage No. not extracted prior to Container extraction for {self.filename_str}. Skipping.")
            return []

        r_summary_start, _ = find_label_row_col(self.worksheet, config.LABEL_DISCHARGE_LOAD_SUMMARY, max_search_rows=config.MAX_SEARCH_ROWS_CONTAINER_HEADER, partial_match=True)
        if not r_summary_start:
            logging.warning(f"Không tìm thấy bảng '{config.LABEL_DISCHARGE_LOAD_SUMMARY}' trong file {self.filename_str}. Bỏ qua Container Details.")
            return container_details_list
        header_cat_row = r_summary_start + config.CONTAINER_SUMMARY_CAT_ROW_OFFSET
        header_size_row = r_summary_start + config.CONTAINER_SUMMARY_SIZE_ROW_OFFSET
        data_start_row = r_summary_start + config.CONTAINER_SUMMARY_DATA_START_ROW_OFFSET
        col_configs_from_file = [] 
        for start_col_letter, end_col_letter, default_cat_name_in_config in config.CONTAINER_CATEGORY_COL_RANGES_DEF:
            start_col_idx = col_letter_to_index(start_col_letter)
            end_col_idx = col_letter_to_index(end_col_letter)
            if not start_col_idx or not end_col_idx:
                logging.warning(f"Container Details: Invalid column letters '{start_col_letter}' or '{end_col_letter}' in CONTAINER_CATEGORY_COL_RANGES_DEF. Skipping this range.")
                continue
            category_name_from_header = str(self.worksheet.cell(row=header_cat_row, column=start_col_idx).value or "").strip()
            actual_category_name = category_name_from_header if category_name_from_header else default_cat_name_in_config
            if not actual_category_name: 
                actual_category_name = config.CONTAINER_DEFAULT_CATEGORY_NAMES_BY_START_COL.get(start_col_letter, "Unknown Category")
                logging.warning(f"Container Details: Category name at {get_column_letter(start_col_idx)}{header_cat_row} is empty. Using '{actual_category_name}'.")
            size_offset_in_config = 0 
            for c_idx in range(start_col_idx, end_col_idx + 1):
                if size_offset_in_config < len(config.CONTAINER_SIZES_IN_ORDER):
                    expected_size_from_config = config.CONTAINER_SIZES_IN_ORDER[size_offset_in_config]
                    actual_size_in_header = str(self.worksheet.cell(row=header_size_row, column=c_idx).value or "").replace("'", "").strip()
                    final_size_to_use = expected_size_from_config 
                    if actual_size_in_header and actual_size_in_header in config.CONTAINER_SIZES_IN_ORDER:
                        final_size_to_use = actual_size_in_header
                        if actual_size_in_header != expected_size_from_config:
                            logging.debug(f"Container Details: Size from header '{actual_size_in_header}' at {get_column_letter(c_idx)}{header_size_row} for category '{actual_category_name}' differs from expected config order '{expected_size_from_config}'. Using header size.")
                    elif actual_size_in_header: 
                        logging.warning(f"Container Details: Non-standard size '{actual_size_in_header}' found in header at {get_column_letter(c_idx)}{header_size_row} for category '{actual_category_name}'. Attempting to use it.")
                        final_size_to_use = actual_size_in_header 
                    col_configs_from_file.append({"col_idx": c_idx, "category": actual_category_name, "size": final_size_to_use})
                    size_offset_in_config += 1
                else: 
                    logging.debug(f"Container Details: Exceeded expected sizes for category '{actual_category_name}' at column {get_column_letter(c_idx)}. Max sizes in config: {len(config.CONTAINER_SIZES_IN_ORDER)}.")
                    actual_size_in_header_extra = str(self.worksheet.cell(row=header_size_row, column=c_idx).value or "").replace("'", "").strip()
                    if actual_size_in_header_extra:
                         col_configs_from_file.append({"col_idx": c_idx, "category": actual_category_name, "size": actual_size_in_header_extra})
                         logging.info(f"Container Details: Added extra column config for {actual_category_name} size {actual_size_in_header_extra} at {get_column_letter(c_idx)}")
        logging.debug(f"CONTAINER_DETAILS: Column Configs from file: {col_configs_from_file}")
        if not col_configs_from_file:
            logging.error(f"Không thể xác định cấu hình cột cho bảng Container Summary trong file {self.filename_str}. Bỏ qua.")
            return container_details_list
        col_total_conts_idx = col_letter_to_index(config.CONTAINER_SUMMARY_ROW_TOTAL_CONTS_COL_LETTER)
        col_teus_idx = col_letter_to_index(config.CONTAINER_SUMMARY_ROW_TEUS_COL_LETTER)
        current_main_operation = None 
        for r_idx in range(data_start_row, data_start_row + config.MAX_ROWS_TO_READ_CONTAINER_DATA):
            if r_idx > self.worksheet.max_row: break
            label_col_b_val = str(self.worksheet.cell(row=r_idx, column=col_letter_to_index('B')).value or "").strip()
            label_lower = label_col_b_val.lower()
            operation_type_for_row = None
            port_for_row = config.PORT_ALL 
            if label_col_b_val:
                if label_lower == config.OP_DISCHARGE.lower(): current_main_operation = config.OP_DISCHARGE; operation_type_for_row = config.OP_DISCHARGE; port_for_row = config.PORT_ALL
                elif label_lower == config.OP_LOADING.lower(): current_main_operation = config.OP_LOADING; operation_type_for_row = config.OP_LOADING; port_for_row = config.PORT_ALL 
                elif label_lower == config.OP_SHIFTING_DIS.lower(): current_main_operation = config.OP_SHIFTING_DIS; operation_type_for_row = config.OP_SHIFTING_DIS; port_for_row = config.PORT_ALL
                elif label_lower == config.OP_SHIFTING_LOAD.lower(): current_main_operation = config.OP_SHIFTING_LOAD; operation_type_for_row = config.OP_SHIFTING_LOAD; port_for_row = config.PORT_ALL
                elif label_lower == config.OP_TOTAL_DIS.lower(): operation_type_for_row = config.OP_TOTAL_DIS; port_for_row = config.PORT_ALL
                elif label_lower == config.OP_TOTAL_LOAD.lower(): operation_type_for_row = config.OP_TOTAL_LOAD; port_for_row = config.PORT_ALL
                elif label_lower == config.LABEL_GRAND_TOTAL_IN_CONTAINER_SUMMARY.lower(): operation_type_for_row = config.OP_GRAND_TOTAL; port_for_row = config.PORT_ALL
                elif current_main_operation: operation_type_for_row = current_main_operation; port_for_row = label_col_b_val 
                else: 
                    is_data_present_in_row = any(self.worksheet.cell(row=r_idx, column=cfg["col_idx"]).value for cfg in col_configs_from_file)
                    if not is_data_present_in_row and r_idx > data_start_row: logging.debug(f"CONTAINER_DETAILS: Dòng {r_idx} có nhãn '{label_col_b_val}' nhưng không có số liệu container. Dừng đọc cho nhãn này.")
                    else:
                        logging.warning(f"CONTAINER_DETAILS: Bỏ qua dòng {r_idx}, nhãn không xác định rõ ràng: '{label_col_b_val}' nhưng có thể có dữ liệu.")
                        if not current_main_operation: continue
            elif current_main_operation:
                operation_type_for_row = current_main_operation
                is_data_present_in_row = any(self.worksheet.cell(row=r_idx, column=cfg["col_idx"]).value for cfg in col_configs_from_file)
                if not is_data_present_in_row:
                    logging.debug(f"CONTAINER_DETAILS: Dòng {r_idx} cột B trống và không có số liệu container. Bỏ qua.")
                    if container_details_list and container_details_list[-1]["OperationType"] == config.OP_GRAND_TOTAL: logging.info("CONTAINER_DETAILS: Dòng trống sau Grand Total. Dừng."); break
                    continue
                else: 
                    port_for_row = "Yard" 
                    if config.OP_SHIFTING_DIS not in current_main_operation and config.OP_SHIFTING_LOAD not in current_main_operation: port_for_row = "Unknown Detail" 
                    logging.debug(f"CONTAINER_DETAILS: Dòng {r_idx} cột B trống nhưng có dữ liệu. Gán Port='{port_for_row}' dưới Operation='{current_main_operation}'.")
            else: logging.debug(f"CONTAINER_DETAILS: Dòng {r_idx} cột B trống và không có operation chính hiện tại. Dừng đọc."); break 
            if not operation_type_for_row: logging.debug(f"CONTAINER_DETAILS: Không xác định được OperationType cho dòng {r_idx}. Bỏ qua."); continue
            row_total_conts_from_file = 0
            row_teus_from_file = 0
            if col_total_conts_idx:
                val_conts = self.worksheet.cell(row=r_idx, column=col_total_conts_idx).value
                try: row_total_conts_from_file = int(val_conts) if pd.notna(val_conts) else 0
                except ValueError: logging.warning(f"CONTAINER_DETAILS: Invalid RowTotalConts value '{val_conts}' at cell {get_column_letter(col_total_conts_idx)}{r_idx}. Treating as 0.")
            if col_teus_idx:
                val_teus = self.worksheet.cell(row=r_idx, column=col_teus_idx).value
                try: row_teus_from_file = int(val_teus) if pd.notna(val_teus) else 0
                except ValueError: logging.warning(f"CONTAINER_DETAILS: Invalid RowTEUs value '{val_teus}' at cell {get_column_letter(col_teus_idx)}{r_idx}. Treating as 0.")
            for col_cfg_item in col_configs_from_file:
                quantity_val = self.worksheet.cell(row=r_idx, column=col_cfg_item["col_idx"]).value
                quantity = 0
                if pd.notna(quantity_val) and str(quantity_val).strip() != '':
                    try: quantity = int(quantity_val)
                    except ValueError:
                        logging.warning(f"CONTAINER_DETAILS: Invalid quantity value '{quantity_val}' at cell {get_column_letter(col_cfg_item['col_idx'])}{r_idx} for {col_cfg_item['category']} {col_cfg_item['size']}. Treating as 0.")
                        quantity = 0
                if quantity > 0: 
                    container_details_list.append({
                        "Filename": self.filename_str, "Vessel Name": self.vessel_name, "Voyage": self.voyage_no,
                        "OperationType": operation_type_for_row, "Port": port_for_row,
                        "ContainerCategory": col_cfg_item["category"], "ContainerSize": col_cfg_item["size"],       
                        "Quantity": quantity, "RowTotalConts_from_TDR": row_total_conts_from_file, "RowTEUs_from_TDR": row_teus_from_file
                    })
            if label_lower == config.LABEL_GRAND_TOTAL_IN_CONTAINER_SUMMARY.lower():
                logging.info(f"CONTAINER_DETAILS: Đã đọc dòng '{config.LABEL_GRAND_TOTAL_IN_CONTAINER_SUMMARY}'. Dừng đọc bảng container.")
                break
        logging.info(f"--- Hoàn thành trích xuất Container Details cho file: {self.filename_str}. Số dòng dữ liệu chi tiết (long format): {len(container_details_list)} ---")
        return container_details_list