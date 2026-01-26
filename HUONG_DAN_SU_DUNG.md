# 📘 Hướng Dẫn Sử Dụng TDR Processor v3.0.0

**Phiên bản:** 3.0.0  
**Ngôn ngữ:** Tiếng Việt  
**Cập nhật:** 26/01/2026  
**Người dùng cuối:** Chưa có kiến thức lập trình

---

## 🆕 Có Gì Mới Trong Phiên Bản 3.0.0?

### ✅ Bảo mật nâng cao
- **Quản lý mật khẩu an toàn**: Không lưu mật khẩu SMTP vào file config
- **Windows Credential Manager**: Lưu trữ credentials bảo mật qua `keyring`
- **UI quản lý credentials**: Test Connection, Save/Clear Credentials trong GUI

### ✅ Kiến trúc module hóa  
- **Core Processor riêng biệt**: Logic xử lý tách khỏi GUI, có thể import từ CLI/scripts
- **Data Schema chuẩn hóa**: Định nghĩa schema cho 5 bảng dữ liệu output
- **Entrypoints rõ ràng**: GUI (main.py), Dashboard (app.py), Core (core_processor.py)

### ✅ Dashboard nâng cao (8 tabs)
- **📈 Tổng quan & Timeline**: KPI cards với delta so sánh mục tiêu
- **🔍 Data Filters**: Lọc theo Operator, Berth, Date Range
- **📊 Data Quality**: Báo cáo chất lượng dữ liệu, completeness score
- **📅 Timeline View**: Gantt chart hoạt động QC theo tàu
- **📥 Export Templates**: Xuất CSV/Excel theo mẫu tùy chọn

---

## 🚀 Bắt Đầu Nhanh (5 phút)

### Bước 1: Chuẩn Bị
1. Tải ứng dụng từ file `TDR_Processor.exe` (nếu có bản build sẵn)
2. Hoặc cài đặt Python 3.11+ từ [python.org](https://www.python.org)

### Bước 2: Chạy Ứng Dụng

**Cách 1: Double-click exe (Dễ nhất)**
```
Double-click vào TDR_Processor.exe
→ Giao diện sẽ mở ra
```

**Cách 2: Chạy từ Command Prompt**
```cmd
cd C:\Users\YourName\Desktop\tdr_processor
python main.py
```

### Bước 3: Sử Dụng
1. Nhấn nút **"📁 Select files"**
2. Chọn file Excel TDR (.xlsx)
3. Chọn **"Process"** (hoặc tự động xử lý)
4. Xem kết quả trong thư mục `outputs/`

---

## 📋 Các Tính Năng Chính

### 1️⃣ Xử Lý File TDR
**Làm gì:** Đọc file TDR Excel, trích xuất dữ liệu quan trọng  
**Kết quả:** File CSV và Excel trong `outputs/`

```
Input: TDR_Ship_2025.xlsx
         ↓
Xử lý: Trích xuất Vessel, QC, Container, Delay
         ↓
Output: 
  - vessel_summary.csv       ← Thông tin tàu, năng suất
  - qc_productivity.csv      ← Năng suất QC (khai thác)
  - qc_operator_productivity.csv ← Năng suất QC (vận hành)
  - delay_details.csv        ← Chi tiết delay
  - container_details_long.csv ← Chi tiết container
```

### 2️⃣ Dashboard Web (8 Tabs)
**Làm gì:** Xem biểu đồ, thống kê, phân tích dữ liệu  
**Cách dùng:**
1. Nhấn nút **"📈 Open Web Dashboard"**
2. Trình duyệt mở ra tự động (http://localhost:8501)
3. Xem các tab phân tích

**8 Tabs trong Dashboard:**
| Tab | Nội dung |
|-----|----------|
| 📈 Tổng quan | KPI cards, biểu đồ theo tháng/quý |
| ⚠️ Cảnh báo KPI | Danh sách tàu không đạt 45 moves/h |
| ⚙️ Năng suất khai thác | Phân tích QC productivity |
| 👨‍🔧 Năng suất vận hành | QC operator productivity (loại delay không do operator) |
| ⏳ Phân tích Delay | Thống kê delay theo QC, loại |
| 📦 Chi tiết Container | Bảng dữ liệu container |
| 🔍 Chất lượng dữ liệu | Completeness score, missing values |
| 📅 Timeline | Gantt chart hoạt động QC |

### 3️⃣ Data Filters (Sidebar)
**Làm gì:** Lọc dữ liệu theo nhiều tiêu chí
**Cách dùng:**
1. Mở Dashboard
2. Ở sidebar bên trái, chọn:
   - **Operator**: Lọc theo hãng tàu
   - **Berth**: Lọc theo cầu tàu
   - **Date Range**: Lọc theo khoảng thời gian
3. Dữ liệu cập nhật tự động
4. Nhấn "Reset Filters" để xóa bộ lọc

### 4️⃣ Export Data (Mới)
**Làm gì:** Xuất dữ liệu ra CSV hoặc Excel
**Cách dùng:**
1. Ở sidebar Dashboard, cuộn xuống phần "Export"
2. Chọn định dạng: **CSV** hoặc **Excel**
3. Chọn mẫu:
   - **All Tables**: Xuất tất cả 5 bảng
   - **Summary Only**: Chỉ vessel_summary
4. Nhấn **"Download"**

### 5️⃣ Quản Lý Email Credentials (Mới - Bảo mật)
**Làm gì:** Lưu trữ thông tin SMTP an toàn (không lưu vào file)
**Cách dùng:**
1. Mở GUI (python main.py)
2. Vào tab Settings/Email
3. Nhập SMTP Server, Port, User, Password
4. Nhấn **"Test Connection"** để kiểm tra
5. Nhấn **"Save Credentials"** để lưu an toàn
6. Credentials được lưu vào Windows Credential Manager

### 6️⃣ Power BI Report
**Làm gì:** Tạo báo cáo Power BI từ dữ liệu  
**Cách dùng:**
1. Nhấn nút **"📊 Open Power BI Report"**
2. Power BI sẽ mở ra
3. Kết nối đến thư mục `outputs/data_csv/`
4. Xem báo cáo hình ảnh

---

## 📁 Cấu Trúc Thư Mục

```
tdr_processor/
├── 📂 data_input/          ← Bạn đặt file TDR ở đây
├── 📂 outputs/
│   ├── 📂 data_csv/        ← File CSV (dùng cho Power BI, Dashboard)
│   │   ├── vessel_summary.csv
│   │   ├── qc_productivity.csv
│   │   ├── qc_operator_productivity.csv
│   │   ├── delay_details.csv
│   │   └── container_details_long.csv
│   └── 📂 data_excel/      ← File Excel
├── 📂 templates/           ← Mẫu Power BI
├── 📂 utils/               ← Các module tiện ích
│   ├── credential_manager.py  ← Quản lý credentials bảo mật (MỚI)
│   └── ...
├── main.py                 ← GUI chính (Tkinter)
├── dashboard.py            ← Web Dashboard (Streamlit)
├── app.py                  ← Streamlit entrypoint
├── core_processor.py       ← Logic xử lý thuần (MỚI - có thể dùng từ CLI)
├── data_schema.py          ← Schema định nghĩa (MỚI)
├── HUONG_DAN_SU_DUNG.md   ← File này
└── requirements.txt        ← Danh sách thư viện
```

---

## 📊 5 Bảng Dữ Liệu Output (Schema v3.0.0)

| Bảng | Mô tả | Primary Key |
|------|-------|-------------|
| `vessel_summary` | Thông tin tàu, thời gian cảng, năng suất tổng | Filename |
| `qc_productivity` | Năng suất khai thác từng QC | Filename + QC No. |
| `qc_operator_productivity` | Năng suất vận hành (loại delay không do operator) | Filename + QC No. |
| `delay_details` | Chi tiết từng sự kiện delay | Filename + QC No. + From Time |
| `container_details_long` | Chi tiết container (long format) | Filename + QC + Operation + Size + Category |

**Công thức KPI quan trọng:**
- `Net moves/h = Grand Total Conts / Net Working (hrs)` - Năng suất thực khi làm việc
- `Gross moves/h = Grand Total Conts / Gross Working (hrs)` - Năng suất tổng (bao gồm delay)
- `KPI Target = 45 moves/h`

---

## 🎯 Các Bước Sử Dụng Chi Tiết

### Bước 1: Chuẩn Bị File Input

1. **Copy file TDR vào thư mục `data_input/`**
   ```
   data_input/
   ├── TDR_Ship_20250101.xlsx
   ├── TDR_Ship_20250102.xlsx
   └── ...
   ```

2. **File phải có định dạng Excel (.xlsx)**
   - ✅ Đúng: `TDR_20250122.xlsx`
   - ❌ Sai: `TDR_20250122.xls` (quá cũ)
   - ❌ Sai: `TDR_20250122.csv` (không phải Excel)

### Bước 2: Chạy Ứng Dụng

**Cách 1: GUI (Dễ nhất)**
```
1. Chạy: python main.py
2. Giao diện sẽ mở
3. Nhấn "Select files"
4. Chọn file TDR từ data_input/
5. Nhấn "Process"
```

**Cách 2: Tự động (Nếu file ở data_input/)**
```
1. Chạy: python main.py
2. Ứng dụng tự động phát hiện file mới
3. Tự động xử lý
4. Hoàn tất (không cần bấm gì)
```

### Bước 3: Xem Kết Quả

**File CSV (Dùng cho Power BI):**
```
outputs/data_csv/
├── vessel_summary.csv          ← Thông tin tàu
├── qc_productivity.csv         ← Năng suất QC
├── delay_details.csv           ← Chi tiết delay
└── container_summary.csv       ← Tóm tắt container
```

**File Excel (Dùng trực tiếp):**
```
outputs/data_excel/
├── TDR_Report.xlsx
└── TDR_Dashboard.xlsx
```

### Bước 4: Xem Báo Cáo

**Tùy chọn 1: Power BI**
- Nhấn nút "📊 Open Power BI Report"
- Kết nối file CSV từ `data_csv/`
- Xem biểu đồ

**Tùy chọn 2: Web Dashboard**
- Nhấn nút "📈 Open Web Dashboard"
- Xem biểu đồ trực tiếp (Streamlit)
- Không cần Power BI

**Tùy chọn 3: Excel**
- Mở file từ `outputs/data_excel/`
- Xem pivot table, biểu đồ

---

## ⚙️ Cấu Hình (Tùy Chọn)

### Gửi Báo Cáo qua Email (Nâng Cao - Bảo Mật Mới)

**Cách 1: Qua GUI (Khuyến nghị - Bảo mật nhất)**

1. Mở ứng dụng: `python main.py`
2. Vào phần **Email Settings**
3. Nhập thông tin:
   - SMTP Server: `smtp.gmail.com`
   - SMTP Port: `587`
   - Email: `your_email@gmail.com`
   - Password: App Password (xem bước lấy App Password bên dưới)
4. Nhấn **"Test Connection"** để kiểm tra
5. Nhấn **"Save Credentials"** để lưu an toàn
6. ✅ Credentials được lưu vào Windows Credential Manager (không phải file!)

**Cách 2: Qua Environment Variables**

```cmd
# Windows (Command Prompt)
set TDR_SMTP_USER=your_email@gmail.com
set TDR_SMTP_PASS=your_app_password
python main.py

# PowerShell
$env:TDR_SMTP_USER="your_email@gmail.com"
$env:TDR_SMTP_PASS="your_app_password"
python main.py
```

**Lấy App Password (Gmail):**
1. Vào [myaccount.google.com](https://myaccount.google.com)
2. Bảo mật → Xác minh 2 bước (bật nếu chưa)
3. Mật khẩu ứng dụng → Tạo mới
4. Copy mật khẩu 16 ký tự

**⚠️ Lưu ý bảo mật:**
- ❌ Không lưu mật khẩu vào file `app_settings.json`
- ❌ Không commit file `.env` lên Git
- ✅ Dùng Windows Credential Manager (qua GUI)
- ✅ Hoặc dùng Environment Variables

---

## ❓ Câu Hỏi Thường Gặp

### Q1: Tôi không có Python, phải làm sao?

**Cách 1: Dùng file exe sẵn**
```
Double-click vào TDR_Processor.exe (nếu có)
```

**Cách 2: Cài đặt Python**
1. Vào [python.org](https://www.python.org)
2. Tải Python 3.11+ (Windows Installer)
3. Cài đặt (✓ Add Python to PATH)
4. Chạy `python main.py`

### Q2: File Excel bị lỗi, không chạy được?

**Kiểm tra:**
1. File có phải `.xlsx` không? (Không phải `.xls`)
2. File có bị mở ở chương trình khác không?
3. File có dữ liệu không? (Không trống)

**Giải pháp:**
```
1. Đóng Excel
2. Xóa file khỏi data_input/
3. Copy lại file
4. Chạy lại ứng dụng
```

### Q3: Kết quả đâu? Chúng nằm ở đâu?

**Tìm ở đây:**
```
outputs/
├── data_csv/        ← File CSV (Power BI)
└── data_excel/      ← File Excel
```

**Windows:**
- Mở File Explorer
- `C:\Users\YourName\Desktop\tdr_processor\outputs\`

**macOS/Linux:**
- Mở Terminal
- `cd ~/Desktop/tdr_processor/outputs/`

### Q4: Dashboard web không mở được?

**Nguyên nhân:** Port 8501 bị chiếm

**Giải pháp:**
```
1. Đóng ứng dụng (Ctrl+C)
2. Đợi 10 giây
3. Chạy lại: python main.py
```

### Q5: Muốn xử lý nhiều file cùng lúc?

**Cách 1: Drag & drop**
1. Chọn nhiều file Excel
2. Kéo vào thư mục `data_input/`
3. Chạy ứng dụng
4. Tất cả sẽ được xử lý

**Cách 2: Tự động**
1. Copy tất cả file vào `data_input/`
2. Chạy ứng dụng
3. Nó sẽ xử lý tất cả tự động

### Q6: Muốn xóa dữ liệu cũ?

```
1. Mở thư mục outputs/
2. Xóa các file CSV, Excel cũ
3. Chạy lại để tạo mới
```

### Q7: Báo cáo bao lâu?

**Thời gian xử lý:**
- File 10 MB: ~5-10 giây
- File 50 MB: ~20-30 giây
- File 100+ MB: ~1-2 phút

---

## 🔐 Bảo Mật & Lưu Ý

### ⚠️ Lưu Ý Quan Trọng

1. **Không shared password ở file config**
   - File `.env` chứa mật khẩu
   - Đừng share file này cho ai

2. **File TDR chứa dữ liệu nhạy cảm**
   - Xóa file cũ sau khi xử lý
   - Không để nơi công cộng

3. **Backup dữ liệu quan trọng**
   - Copy file từ `outputs/` ra nơi an toàn
   - Trước khi xóa dữ liệu cũ

### ✅ Thực Hành Tốt

```
1. Xử lý file hàng ngày/tuần
2. Backup kết quả ra ngoài
3. Xóa file TDR gốc sau xử lý
4. Giữ thư mục sạch sẽ
```

---

## 📊 Kết Quả Dự Kiến

### Input: File TDR Original

```
TDR_20250122.xlsx
├── Sheet 1: VESSEL SUMMARY
│   └── Thông tin tàu, thời gian cảng
├── Sheet 2: CONTAINER DETAILS
│   └── Chi tiết container, hàng hóa
├── Sheet 3: QC PRODUCTIVITY
│   └── Năng suất QC, toàn bộ
└── Sheet 4: DELAY ANALYSIS
    └── Chi tiết delay, nguyên nhân
```

### Output: Dữ liệu Xử Lý

```
outputs/data_csv/
├── vessel_summary.csv
│   └── Tàu, ngày vào, ngày ra, thời gian cảng
├── qc_productivity.csv
│   └── QC code, năng suất, số moves
├── delay_details.csv
│   └── Loại delay, thời gian, chi tiết
└── container_summary.csv
    └── Container, hàng, trạng thái

outputs/data_excel/
├── TDR_Report.xlsx (Multi-sheet)
└── TDR_Dashboard.xlsx (Pivot tables)
```

### Dashboard Power BI

```
Trang 1: Tổng Quan
├── Biểu đồ: Số container xử lý
├── KPI: Năng suất trung bình
└── Timeline: Dòng chảy theo ngày

Trang 2: Năng Suất QC
├── Top 10 QC tốt nhất
├── Biểu đồ: Năng suất theo giờ
└── So sánh: QC vs mục tiêu

Trang 3: Phân Tích Delay
├── Loại delay (pie chart)
├── Top nguyên nhân delay
└── Timeline: Delay theo thời gian

Trang 4: Chi Tiết Container
├── Bảng: Danh sách container
└── Filter: Theo tàu, QC, loại delay
```

---

## 📞 Hỗ Trợ & Liên Hệ

### Gặp Lỗi?

1. **Kiểm tra log**
   ```
   Xem file: tdr_processor.log
   Chứa chi tiết lỗi gì xảy ra
   ```

2. **Đọc thêm:**
   - [SECURITY.md](SECURITY.md) - Bảo mật
   - [README.md](Readme.md) - Tổng quan

3. **Liên hệ hỗ trợ:**
   - Xem file log để cung cấp chi tiết lỗi
   - Mô tả file input (tên, kích thước)
   - Bước nào bị lỗi?

---

## 🎓 Ví Dụ Sử Dụng

### Ví Dụ 1: Xử Lý File TDR Hôm Nay

```
1. Sáng: Nhận file TDR từ hệ thống
   TDR_20250122_morning.xlsx

2. Copy vào thư mục:
   data_input/

3. Chạy ứng dụng:
   python main.py

4. Chờ 30-60 giây

5. Xem kết quả:
   outputs/data_csv/ → Dùng cho Power BI
   outputs/data_excel/ → Dùng trực tiếp

6. Gửi cho từng bộ phận:
   - QC: qc_productivity.csv
   - Delay: delay_details.csv
   - Container: container_summary.csv
```

### Ví Dụ 2: Xử Lý Hàng Loạt (Tuần)

```
1. Copy tất cả file TDR tuần vào data_input/:
   TDR_20250115.xlsx
   TDR_20250116.xlsx
   TDR_20250117.xlsx
   ...
   TDR_20250122.xlsx

2. Chạy 1 lần:
   python main.py

3. Ứng dụng sẽ xử lý tất cả tự động

4. Kết quả sẽ tính toán chung cho cả tuần:
   - qc_productivity.csv (tuần)
   - delay_details.csv (tuần)
   - vessel_summary.csv (tuần)

5. Import vào Power BI một lần duy nhất
```

### Ví Dụ 3: Tự Động Gửi Email

```
1. Cấu hình email (xem phần "Cấu Hình")

2. Chạy:
   python main.py

3. Sau khi xử lý xong, ứng dụng tự gửi email:
   To: your_email@gmail.com
   Subject: TDR Processing Complete
   Files: Attached

4. Nhận email ngay lập tức
```

---

## 📈 Tối Ưu Hóa Sử Dụng

### Mẹo 1: Xử Lý Nhanh

```
✅ Tốt:
- File <50 MB
- Xử lý 1-2 file cùng lúc
- Đủ RAM (4GB+)

❌ Chậm:
- File >100 MB
- Xử lý 10 file cùng lúc
- RAM đầy, máy chậy
```

### Mẹo 2: Tiết Kiệm Dung Lượng

```
Sau xử lý 1 tuần:
- CSV: ~5-10 MB
- Excel: ~2-5 MB
- Total: ~10-15 MB

Mẹo: Xóa file TDR gốc sau 1 tháng
(Giữ lại kết quả CSV, Excel)
```

### Mẹo 3: Sử Dụng Dashboard

```
Thay vì mở Excel từng lần
→ Dùng Power BI hoặc Web Dashboard
→ Xem trực tiếp, tương tác

Lợi ích:
- Nhanh hơn
- Đẹp hơn
- Thao tác dễ hơn
```

---

## 🎉 Kết Luận

**TDR Processor v3.0.0** giúp bạn:
- ✅ Xử lý file TDR tự động
- ✅ Tạo báo cáo chuyên nghiệp
- ✅ Phân tích dữ liệu nhanh
- ✅ Tiết kiệm thời gian 80%
- ✅ Dashboard 8 tabs với filters, export, quality report
- ✅ Bảo mật credentials qua Windows Credential Manager
- ✅ Architecture module hóa cho mở rộng

**Bước tiếp theo:**
1. Chạy ứng dụng: `python main.py`
2. Chọn file TDR
3. Xem kết quả trong `outputs/`
4. Mở Dashboard để phân tích

**Chúc bạn sử dụng vui vẻ!** 🚀

---

## 🔧 Dành cho Developer (Nâng cao)

### Import Core Processor từ Scripts

```python
# CLI script hoặc scheduled task
from core_processor import (
    get_valid_tdr_files,
    process_tdr_files,
    auto_process_input_folder,
    get_processing_summary
)
from pathlib import Path

# Xử lý tự động
result = auto_process_input_folder()
print(result['message'])

# Hoặc xử lý thủ công
files = get_valid_tdr_files(Path("data_input"))
result = process_tdr_files(files, overwrite=True)

# Xem summary
summary = get_processing_summary()
print(f"Vessels: {summary['vessel_count']}")
```

### Data Schema API

```python
from data_schema import (
    SCHEMAS,
    validate_dataframe,
    normalize_qc_name,
    calculate_moves_per_hour,
    get_schema_info
)

# Xem schema info
info = get_schema_info()
print(info['version'])  # "3.0.0"

# Validate dataframe
result = validate_dataframe(df, SCHEMAS['vessel_summary'])
if not result['valid']:
    print(result['missing_columns'])
```

---

**Phiên bản:** v3.0.0  
**Cập nhật:** 26/01/2026  
**Ngôn ngữ:** Tiếng Việt  
**Trạng thái:** Production Ready ✅
**Tests:** 139/139 passed

Để tìm hiểu thêm, xem [ARCHITECTURE.md](ARCHITECTURE.md).
