# TDR Processor — Development & Remediation Roadmap (v1.0)

> **Cập nhật lần cuối:** 2026-05-24  
> **Phiên bản hiện tại:** **v1.0**  
> **Trạng thái:** Sprint 1 ✅ hoàn thành (Bổ dung Light theme, Stop categories giải thích song ngữ, Cập nhật v1.0).  
> **Kế hoạch tiếp theo:** Sprint 2 & 3 - Sửa lỗi bảo mật (P0), cải thiện kiến trúc và tính năng (P1/P2) dựa trên EA Assessment.

---

## 📋 Tóm tắt Kế hoạch Hành động (Remediation Backlog)

Dưới đây là các hạng mục đã được khảo sát trực tiếp từ mã nguồn thực tế (`dashboard.html`, `dashboard_api.py`) và được phân loại theo mức độ ưu tiên xử lý.

| ID | Hạng mục | Độ ưu tiên | Trạng thái | File cần chỉnh sửa |
|:---|:---|:---:|:---:|:---|
| **S2-1** | Tích hợp **API Token Authentication** cho Flask API (`/api/data` & `/api/meta`) | **🔴 P0 (Critical)** | 📅 Kế hoạch | `dashboard_api.py`, `dashboard.html` |
| **S2-2** | Cấu hình **SQLite WAL Mode** ngăn chặn tranh chấp ghi/đọc (Race Conditions) | **🔴 P0 (Critical)** | 📅 Kế hoạch | `dashboard_api.py` |
| **S2-3** | Tích hợp **Rate Limiting middleware** cho Flask API tránh quá tải | **🔴 P0 (Critical)** | 📅 Kế hoạch | `dashboard_api.py` |
| **S2-4** | Triển khai **Auto-Refresh (Polling 30 giây)** cập nhật dữ liệu tự động | **🟡 P1 (High)** | 📅 Kế hoạch | `dashboard.html` |
| **S2-5** | Bổ sung **Error Boundaries** trong React tránh crash trắng trang khi lỗi biểu đồ | **🟡 P1 (High)** | 📅 Kế hoạch | `dashboard.html` |
| **S2-6** | Hoàn thiện tính năng **Export CSV/Excel** trực tiếp trên giao diện | **🟡 P1 (High)** | 📅 Kế hoạch | `dashboard.html` |
| **S2-7** | Lưu trữ cấu hình **KPI Target** tùy chỉnh vào `localStorage` | **🟡 P1 (High)** | 📅 Kế hoạch | `dashboard.html` |
| **S3-1** | Bổ sung Tab **QC Operator Productivity** (hiện backend đã có nhưng frontend chưa vẽ) | **🟢 P2 (Medium)** | 📅 Kế hoạch | `dashboard.html` |
| **S3-2** | Đồng bộ hóa bộ lọc (Filter State) với **URL Query Parameters** | **🟢 P2 (Medium)** | 📅 Kế hoạch | `dashboard.html` |
| **S3-3** | Khắc phục **Gantt Chart** hiển thị chuẩn khi tàu hoạt động qua nhiều ngày | **🟢 P2 (Medium)** | 📅 Kế hoạch | `dashboard.html` |
| **S3-4** | Tối ưu hóa **Berth Map** hỗ trợ động thay vì giới hạn cứng 4 berths | **🟢 P2 (Medium)** | 📅 Kế hoạch | `dashboard.html` |
| **S3-5** | Tối ưu hóa API Response Caching phía server (30 giây TTL) | **🟢 P2 (Medium)** | 📅 Kế hoạch | `dashboard_api.py` |

---

## 🔴 Sprint 2 — Security & Stability (Ưu tiên Cao nhất)

### S2-1 · API Token Authentication
* **Vấn đề:** Các endpoint dữ liệu nhạy cảm `/api/data` và `/api/meta` đang mở public không cần mật khẩu hay token bảo mật.
* **Giải pháp:** 
  - Yêu cầu token gửi qua header `X-API-Token` hoặc query parameter `?token=...`.
  - Lưu trữ API Token an toàn trong biến môi trường hoặc file config.
  - Cập nhật hàm `fetch` ở `dashboard.html` để tự động đính kèm token.

### S2-2 · SQLite WAL Mode
* **Vấn đề:** Ghi và đọc dữ liệu đồng thời vào SQLite có nguy cơ gây lỗi `database is locked` hoặc hỏng file db.
* **Giải pháp:** Bật chế độ WAL (Write-Ahead Logging) khi khởi tạo kết nối SQLite:
  ```python
  con.execute("PRAGMA journal_mode=WAL;")
  con.execute("PRAGMA synchronous=NORMAL;")
  ```

### S2-3 · API Rate Limiting
* **Vấn đề:** Không có cơ chế chặn brute-force hoặc spam request tải dữ liệu.
* **Giải pháp:** Sử dụng `Flask-Limiter` hoặc cơ chế throttle tự dựng để giới hạn tối đa 60 requests/phút từ cùng một IP.

---

## 🟡 Sprint 3 — Feature Polish & UX (Cải thiện Trải nghiệm)

### S3-1 · Bổ sung Tab Năng suất Vận hành QC (QC Operator)
* **Vấn đề:** Backend đã tổng hợp dữ liệu năng suất tài xế cẩu (`qc_operator_productivity`) nhưng giao diện chưa có tab hiển thị.
* **Giải pháp:**
  - Thêm tab "QC Operator" vào thanh sidebar điều hướng.
  - Vẽ biểu đồ cột so sánh GMPH/NMPH giữa các tài xế cẩu và bảng danh sách chi tiết.

### S3-2 · Auto-Refresh dữ liệu
* **Vấn đề:** Khi có file TDR mới được watcher xử lý, người dùng không biết và phải ấn nút "Refresh" thủ công.
* **Giải pháp:** Sử dụng `setInterval` trong React Hook để tự động gọi `reloadData()` mỗi 30 giây.

### S3-3 · Persist KPI Target & Filter State
* **Vấn đề:** Người dùng nhập target KPI mới hoặc chọn filter, nhưng khi F5 hoặc mở tab mới thì bị mất hết.
* **Giải pháp:**
  - Lưu `customKt` vào `localStorage`.
  - Đồng bộ các bộ lọc (Vessel, Operator, Berth, Date) lên URL thông qua `window.history.pushState` hoặc `URLSearchParams`.

---

## 🟢 Sprint 4 — Code Quality & Refactoring (Dài hạn)

### S4-1 · Tách Monolithic dashboard.html sang React Project tiêu chuẩn
* **Vấn đề:** File `dashboard.html` hiện tại dài gần 1000 dòng, chứa toàn bộ CSS, HTML, Component React, Chart logic, gây khó khăn cho việc quản lý mã nguồn và bảo trì.
* **Giải pháp:** Di chuyển mã nguồn sang cấu trúc Vite + React + TypeScript tiêu chuẩn, build thành bundle tĩnh tối ưu trước khi phân phối.

---

*Tài liệu này được biên soạn và cập nhật trực tiếp dựa trên mã nguồn thực tế của hệ thống TDR Processor v1.0 vào ngày 2026-05-24.*
