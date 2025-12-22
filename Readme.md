# 🚢 TDR Processor

![alt text](https://img.shields.io/badge/Python-3.10+-blue.svg)
![alt text](image.png)

Ứng dụng tự động xử lý, tổng hợp và trực quan hóa dữ liệu từ các file Báo cáo Khai thác Tàu (Terminal Departure Report - TDR).

(Gợi ý: Thay thế link trên bằng ảnh chụp màn hình thực tế của ứng dụng để tăng tính trực quan)
✨ Tính năng nổi bật (Features)

    Tổng hợp tự động: Tự động đọc và tổng hợp dữ liệu từ nhiều file TDR (định dạng .xlsx, .xls).

    Phân tích KPI: Tính toán các chỉ số hiệu suất quan trọng như Portstay, Gross/Net Working Time, Moves/Hour.

    Thống kê Delay: Phân loại và thống kê chi tiết thời gian dừng hoạt động (Delay) theo nhiều cấp độ.

    Giao diện thân thiện: Giao diện đồ họa (GUI) được thiết kế đơn giản, dễ sử dụng cho mọi người.

    Hỗ trợ đa ngôn ngữ: Chuyển đổi linh hoạt giữa Tiếng Việt và Tiếng Anh.

    Tích hợp Dashboard: Dữ liệu đầu ra được chuẩn hóa, sẵn sàng để import vào Power BI hoặc Streamlit để xây dựng dashboard trực quan.

🔁 Quy trình làm việc (Workflow)

Ứng dụng hoạt động theo một luồng xử lý dữ liệu rõ ràng từ đầu vào đến đầu ra:

    Thu thập dữ liệu (Data Collection): Người dùng cung cấp các file TDR gốc thông qua giao diện.

    Xử lý tự động (Automated Processing): Ứng dụng Python sẽ đọc, trích xuất, làm sạch và tổng hợp dữ liệu từ các file đã chọn.

    Xuất dữ liệu (Data Export): Các kết quả phân tích và dữ liệu tổng hợp được lưu vào các file "master" (định dạng Excel hoặc CSV) trong thư mục outputs.

    Trực quan hóa (Visualization): Các file master này có cấu trúc chuẩn, sẵn sàng để kết nối với Power BI hoặc các công cụ khác để xây dựng báo cáo và dashboard.

    Chia sẻ (Sharing): Dashboard sau khi được thiết kế có thể xuất bản lên Power BI Service để chia sẻ trong nội bộ.

🚀 Cài đặt (Dành cho Lập trình viên)
Yêu cầu (Prerequisites)

    Python 3.10 trở lên

    Git

Các bước cài đặt

1. Clone dự án về máy:
git clone [https://your-repository-url.git](https://your-repository-url.git)
cd tdr_processor

2.(Khuyến khích) Tạo và kích hoạt môi trường ảo:
Tạo môi trường ảo
python -m venv venv

Kích hoạt trên Windows
.\venv\Scripts\activate

Kích hoạt trên macOS/Linux
source venv/bin/activate
3. Cài đặt các thư viện cần thiết:
pip install -r requirements.txt
🏃‍♂️ Sử dụng (Usage)
1.Chạy từ mã nguồn (Dành cho Lập trình viên)

Sau khi hoàn tất cài đặt, chạy ứng dụng bằng lệnh:
python main.py
2. Hướng dẫn cho Người dùng cuối

    Chạy file TDR_Processor.exe (xem mục Đóng gói và Phân phối bên dưới).

    Trên giao diện ứng dụng, nhấn nút "Chọn Files TDR & Xử lý".

    Một cửa sổ sẽ hiện ra, cho phép bạn chọn một hoặc nhiều file TDR (.xlsx, .xls).

    Sau khi chọn file, một cửa sổ khác sẽ hiện ra yêu cầu bạn chọn thư mục để lưu kết quả.

    Theo dõi quá trình xử lý trên giao diện.

    Khi có thông báo hoàn tất, nhấn nút "Mở Thư Mục Kết Quả" để xem các file master đã được tạo.

📦 Đóng gói và Phân phối (Deployment)

Để tạo file .exe cho người dùng cuối không cần cài đặt Python.
Các bước đóng gói
1.Cài đặt PyInstaller:
pip install pyinstaller
2. Chạy lệnh đóng gói:
Mở Terminal hoặc Command Prompt trong thư mục gốc của dự án và chạy lệnh sau. Lệnh này sẽ gom tất cả thành một file .exe duy nhất và ẩn cửa sổ dòng lệnh màu đen.
pyinstaller --onefile --windowed --name "TDR_Processor" main.py
        Lưu ý: Nếu bạn có các file tài nguyên (như config.py, icon, ảnh...), hãy sử dụng file .spec để đảm bảo chúng được đính kèm.

3.Tìm sản phẩm cuối cùng:
    Sau khi chạy xong, PyInstaller sẽ tạo thư mục dist. File TDR_Processor.exe sẽ nằm trong đó.

4.Chuẩn bị để phân phối:

        Quan trọng: Trước khi chạy file .exe, hãy tạo thủ công các thư mục mà ứng dụng cần để hoạt động, ngay trong thư mục dist, bên cạnh file .exe:

            data_input

            data_excel

            data_csv

            backup

            outputs

        Bây giờ, bạn có thể chạy TDR_Processor.exe để kiểm tra.

🔒 Bảo mật (Security)

TDR Processor v3.0 implements comprehensive security hardening:

- ✅ **Credential Protection**: Credentials loaded from environment variables, never hardcoded
- ✅ **Input Validation**: All user inputs validated to prevent injection attacks
- ✅ **Path Traversal Prevention**: File path validation prevents directory traversal attacks
- ✅ **File Type Validation**: Only Excel files (.xlsx, .xls) are processed
- ✅ **Secure Logging**: Sensitive information never logged

**Setting Up Email Credentials Securely:**

```bash
# Windows (Command Prompt)
set TDR_SMTP_USER=your-email@gmail.com
set TDR_SMTP_PASS=your-app-password
python main.py

# Linux/macOS
export TDR_SMTP_USER="your-email@gmail.com"
export TDR_SMTP_PASS="your-app-password"
python main.py
```

**For Gmail:**
1. Enable 2-factor authentication at https://myaccount.google.com/security
2. Create an App Password at https://myaccount.google.com/apppasswords
3. Use the 16-character password in TDR_SMTP_PASS

**Never:**
- ❌ Hardcode passwords in configuration files
- ❌ Commit .env files with credentials to version control
- ❌ Share credentials in emails or chat
- ❌ Use your actual email password (use app-specific password instead)

**For full security documentation, see [SECURITY.md](SECURITY.md)**

    Chia sẻ:
    Nén toàn bộ thư mục dist (đã bao gồm file .exe và các thư mục con bạn vừa tạo) thành một file .zip và gửi cho người dùng. Họ chỉ cần giải nén và chạy file .exe.

📁 Cấu trúc thư mục (Project Structure)
tdr_processor/
├── main.py               # Điểm khởi chạy ứng dụng GUI
├── config.py             # File cấu hình chính (thông số, đường dẫn, tên cột...)
├── data_extractors.py    # Class chứa logic trích xuất dữ liệu thô từ TDR
├── report_processor.py   # Class điều phối toàn bộ quy trình xử lý
├── requirements.txt      # Danh sách các thư viện Python cần thiết
├── tdr_processor.log     # File log tự động tạo để ghi lại quá trình hoạt động
│
├── utils/                  # Các module tiện ích
│   ├── __init__.py
│   ├── excel_handler.py    # Các hàm đọc/ghi file Excel tổng hợp (master files)
│   ├── excel_utils.py      # Các hàm tiện ích chung cho việc xử lý Excel
│   └── logger_setup.py     # Module cấu hình logging cho ứng dụng
│
└── tests/                  # Thư mục chứa các bài kiểm thử (unit tests)
    └── test_excel_utils.py # Ví dụ một file test
    Tác giả: Tien - Tan Thuan Port © 2025
