# Hướng Dẫn Sử Dụng TDR Processor

**Phiên bản ứng dụng:** v3.1.0  
**Cập nhật:** 18/06/2026  
**Đối tượng:** Người dùng cuối vận hành xử lý file TDR

---

## 1. Mục Đích Ứng Dụng

TDR Processor dùng để đọc file Excel TDR, trích xuất dữ liệu tàu/cẩu/container/delay, rồi xuất dữ liệu chuẩn để xem trên Dashboard Web, Excel, CSV hoặc Power BI.

Ứng dụng hiện có 3 phần chính:

| Thành phần | Dùng để làm gì |
|---|---|
| GUI desktop | Chọn file TDR, xử lý dữ liệu, theo dõi log, cấu hình email |
| Web Dashboard | Xem KPI, năng suất, delay, timeline, chi tiết container |
| Output data | CSV, Excel và SQLite database trong thư mục `outputs/` |

---

## 2. Chạy Nhanh Cho Người Dùng Cuối

### Cách khuyến nghị: dùng file exe

1. Mở thư mục chứa `TDR_Processor.exe`.
2. Double-click `TDR_Processor.exe`.
3. Nhấn **Select files** để chọn file TDR Excel.
4. Nhấn **Process** để xử lý.
5. Xem kết quả trong thư mục `outputs/`.

Ứng dụng sẽ tự tạo các thư mục cần thiết nếu chưa có:

```text
data_input/
backup/
outputs/
templates/
```

### Chạy từ mã nguồn cho kỹ thuật/dev

```powershell
python -m pip install -r requirements.txt
python main.py
```

---

## 3. Quy Trình Xử Lý File TDR

### Bước 1: Chuẩn bị file

File đầu vào nên là Excel:

```text
.xlsx
.xls
```

Có thể chọn file từ bất kỳ thư mục nào qua nút **Select files**. Nếu dùng chế độ theo dõi tự động, đặt file vào `data_input/`.

### Bước 2: Xử lý

Trong GUI:

1. Chọn file.
2. Kiểm tra danh sách file đã chọn.
3. Nhấn **Process**.
4. Theo dõi trạng thái và log trên màn hình.

Sau khi xử lý xong, file gốc được backup theo cấu hình ứng dụng, dữ liệu tổng hợp được ghi vào `outputs/`.

### Bước 3: Kiểm tra kết quả

Các kết quả chính nằm trong:

```text
outputs/data_csv/
outputs/data_excel/
outputs/tdr_master.db
outputs/skipped_files_log.xlsx
```

`skipped_files_log.xlsx` chỉ xuất hiện khi có file bị bỏ qua hoặc không đọc được.

---

## 4. File Output Quan Trọng

### CSV

```text
outputs/data_csv/vessel_summary.csv
outputs/data_csv/qc_productivity.csv
outputs/data_csv/qc_operator_productivity.csv
outputs/data_csv/delay_details.csv
outputs/data_csv/container_details_long.csv
outputs/data_csv/container_details_wide.csv
```

### Excel

```text
outputs/data_excel/vessel_master.xlsx
outputs/data_excel/qc_productivity_master.xlsx
outputs/data_excel/qc_operator_productivity_master.xlsx
outputs/data_excel/delay_master.xlsx
outputs/data_excel/container_master_long.xlsx
outputs/data_excel/container_master_wide.xlsx
```

### SQLite

```text
outputs/tdr_master.db
```

Dashboard sẽ ưu tiên đọc SQLite. Nếu database chưa có hoặc không đọc được, dashboard tự fallback sang CSV trong `outputs/data_csv/`.

---

## 5. Web Dashboard

### Mở dashboard từ GUI

Nhấn nút **Web Dashboard** trong ứng dụng. Ứng dụng sẽ:

1. Khởi chạy dashboard local tại `http://localhost:8503`.
2. Chỉ cho phép truy cập local trên máy đang chạy app.
3. Mở trình duyệt để người dùng xem dashboard.

Người dùng cuối không cần nhập token khi mở dashboard từ GUI hoặc từ file exe.

### Chạy dashboard thủ công cho kỹ thuật/dev

Nếu chạy trực tiếp bằng Python, cần cấu hình token:

```powershell
$env:TDR_API_TOKEN="your-local-token"
python dashboard_api.py
```

Mở:

```text
http://localhost:8503/?token=your-local-token
```

Chỉ dùng trong môi trường dev:

```powershell
$env:TDR_AUTH_DISABLED="true"
python dashboard_api.py
```

Không bật `TDR_AUTH_DISABLED=true` trên máy dùng chung hoặc môi trường có truy cập mạng.

---

## 6. Các Nhóm Dữ Liệu Trên Dashboard

| Nhóm | Nội dung |
|---|---|
| Tổng quan KPI | Số tàu, moves, năng suất, KPI target |
| Cảnh báo KPI | Tàu/cẩu không đạt ngưỡng KPI |
| Năng suất QC | Phân tích năng suất khai thác từng QC |
| Năng suất vận hành | Năng suất sau khi loại delay không do operator |
| Delay | Tổng hợp delay theo loại, QC, tàu |
| Container | Chi tiết container long/wide format |
| Timeline | Diễn biến làm hàng theo thời gian |
| Data quality | Kiểm tra độ đầy đủ và bất thường dữ liệu |

KPI mặc định:

```text
45 moves/hour
```

---

## 7. Email Và Credential

Ứng dụng hỗ trợ lưu SMTP credential qua Windows Credential Manager bằng `keyring`.

Trong GUI:

1. Mở **Settings**.
2. Nhập SMTP server, port, email/user và password.
3. Nhấn **Test Connection** để kiểm tra.
4. Nhấn **Save Credentials** để lưu.

Password không được lưu trực tiếp vào file `.env` hoặc file cấu hình thường.

---

## 8. Power BI

Nếu cần xem báo cáo Power BI:

1. Mở file `tdr_dashboard.pbix` hoặc dùng nút mở Power BI trong GUI nếu có sẵn Power BI Desktop.
2. Trỏ nguồn dữ liệu về thư mục:

```text
outputs/data_csv/
```

Nếu Power BI báo thiếu dữ liệu, hãy chạy xử lý TDR trước để tạo lại CSV.

---

## 9. Cấu Trúc Thư Mục Thực Tế

```text
tdr_processor/
├── TDR_Processor.exe              # Bản đóng gói cho người dùng cuối nếu đã build
├── data_input/                    # File TDR đầu vào khi dùng chế độ theo dõi
├── backup/                        # File đã xử lý/backup
├── outputs/
│   ├── data_csv/                  # CSV cho dashboard/Power BI
│   ├── data_excel/                # Excel tổng hợp
│   ├── tdr_master.db              # SQLite database
│   └── skipped_files_log.xlsx     # Log file bị bỏ qua nếu có
├── templates/                     # Template bổ sung nếu dùng
├── assets/                        # Asset dashboard
├── main.py                        # GUI desktop
├── dashboard_api.py               # Dashboard Flask
├── api.py                         # REST API FastAPI cho tích hợp
└── TDR_Processor.spec             # Cấu hình build exe
```

---

## 10. Lỗi Thường Gặp

| Hiện tượng | Cách xử lý |
|---|---|
| Không mở được file Excel | Đóng Excel nếu file đang mở, kiểm tra file đúng `.xlsx`/`.xls` |
| Dashboard không có dữ liệu | Chạy xử lý TDR trước, kiểm tra `outputs/data_csv/` hoặc `outputs/tdr_master.db` |
| Dashboard hỏi token | Đóng dashboard/server cũ, mở lại từ GUI hoặc file exe. Token chỉ cần khi kỹ thuật chạy thủ công `dashboard_api.py` |
| Power BI không cập nhật | Refresh dữ liệu và kiểm tra đường dẫn `outputs/data_csv/` |
| File bị bỏ qua | Mở `outputs/skipped_files_log.xlsx` để xem lý do |
| ATB/ATD hoặc mốc vận hành sai năm | Ứng dụng sẽ bỏ qua toàn bộ file, hiện cảnh báo và ghi rõ cột/giá trị sai trong `outputs/skipped_files_log.xlsx` |
| Không gửi được email | Kiểm tra SMTP/port/mạng, dùng **Test Connection** trong Settings |

---

## 11. Ghi Chú Kỹ Thuật

Trạng thái kiểm thử gần nhất trước khi đóng gói:

```text
pytest tests/ -q
251 passed
```

Các kiểm tra chất lượng đã dùng:

```powershell
python -m ruff check .
python -m compileall -q .
python -m bandit -r . -x tests,build,dist,node_modules,__pycache__,.git
pytest tests/ -q
```

Build exe:

```powershell
python -m PyInstaller TDR_Processor.spec --clean --noconfirm
```

File exe sau khi build:

```text
dist/TDR_Processor.exe
```
