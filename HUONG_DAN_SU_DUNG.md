# 📘 Hướng Dẫn Sử Dụng TDR Processor v3.0.0

**Phiên bản:** 3.0.0  
**Ngôn ngữ:** Tiếng Việt  
**Người dùng cuối:** Chưa có kiến thức lập trình

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
cd C:\Users\YourName\Desktop\tdr_processor v 2.1
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
  - vessel_summary.csv
  - qc_productivity.csv
  - delay_details.csv
  - container_summary.csv
```

### 2️⃣ Dashboard Web
**Làm gì:** Xem biểu đồ, thống kê dữ liệu  
**Cách dùng:**
1. Nhấn nút **"📈 Open Web Dashboard"**
2. Trình duyệt mở ra tự động
3. Xem các biểu đồ, KPI, phân tích

### 3️⃣ Power BI Report
**Làm gì:** Tạo báo cáo Power BI từ dữ liệu  
**Cách dùng:**
1. Nhấn nút **"📊 Open Power BI Report"**
2. Power BI sẽ mở ra
3. Kết nối đến thư mục `data_csv/`
4. Xem báo cáo hình ảnh

---

## 📁 Cấu Trúc Thư Mục

```
tdr_processor/
├── 📂 data_input/          ← Bạn đặt file TDR ở đây
├── 📂 outputs/
│   ├── 📂 data_csv/        ← File CSV (dùng cho Power BI)
│   └── 📂 data_excel/      ← File Excel
├── 📂 templates/           ← Mẫu Power BI
├── main.py                 ← Chương trình chính
├── HUONG_DAN_SU_DUNG.md   ← File này
└── requirements.txt        ← Danh sách thư viện
```

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

### Gửi Báo Cáo qua Email (Nâng Cao)

Nếu muốn ứng dụng tự động gửi báo cáo qua email:

**Bước 1: Tạo file `.env`**
```
Tạo file tên `.env` (không có tên, chỉ có phần mở rộng)
Nằm cùng thư mục với main.py

Nội dung:
TDR_SMTP_SERVER=smtp.gmail.com
TDR_SMTP_PORT=587
TDR_SMTP_USER=your_email@gmail.com
TDR_SMTP_PASSWORD=your_app_password
```

**Bước 2: Lấy App Password (Gmail)**
1. Vào [myaccount.google.com](https://myaccount.google.com)
2. Bảo mật → Mật khẩu ứng dụng
3. Copy mật khẩu vào file `.env`

**Bước 3: Chạy lại**
```
python main.py
```

Ứng dụng sẽ tự động gửi email khi xử lý xong.

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
- `C:\Users\YourName\Desktop\tdr_processor v 2.1\outputs\`

**macOS/Linux:**
- Mở Terminal
- `cd ~/Desktop/tdr_processor\ v\ 2.1/outputs/`

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
   - [QUICK_START.md](QUICK_START.md) - Setup chi tiết
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

**Bước tiếp theo:**
1. Chạy ứng dụng: `python main.py`
2. Chọn file TDR
3. Xem kết quả trong `outputs/`
4. Dùng Power BI để hiển thị

**Chúc bạn sử dụng vui vẻ!** 🚀

---

**Phiên bản:** v3.0.0  
**Cập nhật:** 22/12/2025  
**Ngôn ngữ:** Tiếng Việt  
**Trạng thái:** Production Ready ✅

Để tìm hiểu thêm, xem [QUICK_START.md](QUICK_START.md) hoặc [ARCHITECTURE.md](ARCHITECTURE.md).
