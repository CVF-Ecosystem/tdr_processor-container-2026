# TDR Processor — Development & Remediation Roadmap (v1.0)

> **Cập nhật lần cuối:** 2026-05-24  
> **Phiên bản hiện tại:** **v3.2.0**  
> **Trạng thái:** Sprint 1–4 ✅ hoàn thành toàn bộ.  
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

<<<<<<< HEAD
### S2-4 · Locales fallback khi key thiếu *(Effort: Thấp | Impact: Vừa)*

**Vấn đề:** Nếu key thiếu trong ngôn ngữ `en` → hiển thị raw key thay vì fallback về `vi`.

**Giải pháp:**
```python
# dashboard_shared.py
def t(key: str, **kwargs) -> str:
    lang = st.session_state.get("lang", "vi")
    text = translations[lang].get(key) or translations["vi"].get(key, key)
    return text.format(**kwargs) if kwargs else text
```

**File cần sửa:** `dashboard_shared.py`

---

## 🟡 Sprint 3 — Architecture (quan trọng dài hạn)

### S3-1 · SQLite thay CSV làm data source *(Effort: Cao | Impact: Cao)*

**Vấn đề:** CSV bị file lock khi đọc/ghi đồng thời, query chậm với dataset lớn, không có schema validation.

**Giải pháp:**
```
outputs/
  tdr_master.db     ← thay thế 5 file CSV
    tables: vessel_summary, qc_productivity, qc_operator_productivity,
            delay_details, container_details_long
```

```python
# dashboard_shared.py
@st.cache_data(ttl=30)
def load_table(table: str) -> pd.DataFrame:
    con = sqlite3.connect("outputs/tdr_master.db")
    return pd.read_sql(f"SELECT * FROM {table}", con)
```

**File cần sửa:** `report_processor.py` (writer), `dashboard_shared.py` (reader)

---

### S3-2 · `pydantic-settings` cho configuration *(Effort: Vừa | Impact: Vừa)*

**Vấn đề:** `config.py` dùng `dataclass` thuần — không validate kiểu, không đọc từ `.env`, không có error message rõ ràng.

**Giải pháp:**
```python
# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    kpi_moves_per_hour: int = 45
    max_message_size_mb: int = 500
    log_level: str = "INFO"
    data_dir: str = "outputs/data_csv"
    
    model_config = SettingsConfigDict(env_file=".env", env_prefix="TDR_")

settings = Settings()
```

**Thêm vào `requirements.txt`:** `pydantic-settings>=2.0`  
**File cần sửa:** `config.py`, `requirements.txt`

---

### S3-3 · Structured logging (JSON) *(Effort: Vừa | Impact: Vừa)*

**Vấn đề:** `tdr_processor.log` là plain text → khó filter, khó tích hợp monitoring.

**Giải pháp:**
```python
from pythonjsonlogger import jsonlogger

handler = logging.FileHandler("tdr_processor.log")
handler.setFormatter(jsonlogger.JsonFormatter(
    '%(asctime)s %(levelname)s %(name)s %(message)s'
))
```

**Thêm vào `requirements.txt`:** `python-json-logger>=2.0`  
**File cần sửa:** `main.py` (logging setup)

---

### S3-4 · Async processing với `asyncio` *(Effort: Cao | Impact: Vừa)*

**Vấn đề:** `ThreadPoolExecutor` + `threading.Lock` phức tạp, cancellation khó, error propagation không rõ ràng.

**Giải pháp:** Chuyển sang `asyncio` + `aiofiles` cho file I/O-bound operations → cleaner cancellation, better error propagation.

**File cần sửa:** `core_processor.py`, `report_processor.py`, `main.py`

---

## 🟢 Sprint 4 — Polish & UX

### S4-1 · KPI Scorecard custom CSS *(Effort: Thấp | Impact: Vừa)*

**Vấn đề:** `st.metric()` thuần — thiếu visual hierarchy, không nổi bật.

**Giải pháp:**
```python
def kpi_card(title: str, value: str, delta: str, color: str = "#FF4B4B"):
    st.markdown(f"""
    <div style="border-left:4px solid {color}; padding:12px 16px;
                border-radius:6px; background:#f8f9fa; margin-bottom:8px;">
        <div style="font-size:12px; color:#666; margin-bottom:4px">{title}</div>
        <div style="font-size:28px; font-weight:700; color:#303030">{value}</div>
        <div style="font-size:12px; color:{color}">{delta}</div>
    </div>""", unsafe_allow_html=True)
```

**File cần sửa:** `dashboard_shared.py`, `dashboard.py`

---

### S4-2 · Excel export có định dạng đẹp *(Effort: Vừa | Impact: Vừa)*

**Vấn đề:** Export Excel hiện tại là raw data, không có header formatting hay conditional formatting.

**Giải pháp (dùng `openpyxl` styling):**
- Header row: bold + màu nền `#4472C4`, chữ trắng
- Conditional formatting: đỏ nếu `Net moves/h < 45`  
- Auto column width
- Freeze top row (`freeze_panes = "A2"`)

**File cần sửa:** `dashboard_shared.py` (hàm `render_export_sidebar`)

---

### S4-3 · System tray icon cho GUI Desktop *(Effort: Vừa | Impact: Thấp)*

**Vấn đề:** Minimize/đóng cửa sổ → kill toàn bộ app kể cả watcher đang chạy ngầm.

**Giải pháp:**
```python
import pystray
from PIL import Image

def on_quit(icon, item): icon.stop(); app.destroy()
icon = pystray.Icon("TDR", Image.open("icon.ico"),
    menu=pystray.Menu(pystray.MenuItem("Open", lambda: app.deiconify()),
                      pystray.MenuItem("Quit", on_quit)))
```

**Thêm vào `requirements.txt`:** `pystray>=0.19`, `Pillow>=10.0`  
**File cần sửa:** `main.py`, `requirements.txt`

---

### S4-4 · Dark mode toggle trong Dashboard *(Effort: Thấp | Impact: Thấp)*

**Giải pháp:**
```python
dark = st.sidebar.toggle("🌙 Dark mode", key="dark_mode")
if dark:
    st.markdown("<style>:root { --bg: #1e1e1e; }</style>", unsafe_allow_html=True)
```

**File cần sửa:** `dashboard_shared.py`

---

### S4-5 · Tối ưu hóa Biểu đồ (Plotly Styling) *(Effort: Vừa | Impact: Cao)*

**Vấn đề:** Biểu đồ Plotly mặc định thường có màu sắc ngẫu nhiên, viền khung rối mắt và tooltip hiển thị kiểu dữ liệu thô.

**Giải pháp:** Thống nhất một `layout template` đồ thị cho toàn app (giấu grid lines, font chữ chuẩn, chuẩn hóa bảng màu, format số).

**File cần sửa:** `dashboard_shared.py` (tạo hàm wrap trả về figure đã style)

---

### S4-6 · Nâng cấp Bảng dữ liệu tương tác (AgGrid) *(Effort: Vừa | Impact: Cao)*

**Vấn đề:** Bảng dữ liệu mặc định của Streamlit hơi đơn điệu khi cần lọc (filter) hoặc ghim cột (pin column) với lượng dữ liệu lớn.

**Giải pháp:** Dùng thư viện `streamlit-aggrid` tạo cảm giác giống Excel/Enterprise App: kéo thả cột, ghim cột, lọc trực tiếp trên header.

**Thêm vào `requirements.txt`:** `streamlit-aggrid>=1.0.0`  
**File cần sửa:** Các file chứa bảng trong `pages/*.py`

---

### S4-7 · Skeleton Loading & Trạng thái chờ *(Effort: Thấp | Impact: Vừa)*

**Vấn đề:** Khi query dữ liệu lớn, web bị "đứng" hoặc hiện `st.spinner` xoay tròn khá đơn điệu.

**Giải pháp:** Sử dụng `st.status()` để hiển thị các bước đang xử lý chi tiết, thêm placeholder text tránh giật cục UI.

**File cần sửa:** Các `pages/*.py` có fetch data nặng

---

### S4-8 · Branding & Xóa rác giao diện (Clean UI) *(Effort: Thấp | Impact: Vừa)*

**Vấn đề:** Dấu ấn Streamlit mặc định (menu góc phải, nút Deploy, footer) làm giảm độ chuyên nghiệp.

**Giải pháp:** Dùng CSS để ẩn UI Streamlit mặc định, chèn Logo Công ty vào sidebar/header.

**File cần sửa:** `dashboard_shared.py` / `.streamlit/config.toml`

---

### S4-9 · Hiện đại hóa Desktop UI (CustomTkinter) *(Effort: Vừa | Impact: Cao)*

**Vấn đề:** Giao diện `tkinter` mặc định trông khá lỗi thời.

**Giải pháp:** Áp dụng `customtkinter` hoặc theme `sv-ttk` (Sun Valley Theme) để mang lại giao diện bo góc, dark/light mode chuẩn Windows 11.

**Thêm vào `requirements.txt`:** `customtkinter` hoặc `sv-ttk`  
**File cần sửa:** `main.py`

---

### S4-10 · Vùng kéo-thả File (Drag & Drop Zone) *(Effort: Vừa | Impact: Cao)*

**Vấn đề:** Người dùng phải bấm click để chọn file khá chậm.

**Giải pháp:** Hỗ trợ kéo thả file/folder TDR trực tiếp vào màn hình Desktop app.

**Thêm vào `requirements.txt`:** `tkinterdnd2`  
**File cần sửa:** `main.py`

---

### S4-11 · Thông báo hệ thống (Windows Toast) *(Effort: Thấp | Impact: Vừa)*

**Vấn đề:** Người dùng không biết khi nào xử lý file ngầm xong nếu đang mở tab khác.

**Giải pháp:** Bắn popup notification hệ thống khi hoàn thành tác vụ dài.

**Thêm vào `requirements.txt`:** `win11toast` hoặc `plyer`  
**File cần sửa:** `main.py`

---

## 📊 Ma trận ưu tiên

| ID | Đề xuất | Effort | Impact | Sprint |
|----|---------|:------:|:------:|:------:|
| S2-1 | `st.navigation()` API | 🟢 Thấp | 🔴 Cao | 2 |
| S2-2 | `@st.fragment` sidebar | 🟢 Thấp | 🔴 Cao | 2 |
| S2-3 | Progress bar thực | 🟡 Vừa | 🟡 Vừa | 2 |
| S2-4 | Locales fallback | 🟢 Thấp | 🟡 Vừa | 2 |
| S3-1 | SQLite data source | 🔴 Cao | 🔴 Cao | 3 |
| S3-2 | `pydantic-settings` | 🟡 Vừa | 🟡 Vừa | 3 |
| S3-3 | Structured logging | 🟡 Vừa | 🟡 Vừa | 3 |
| S3-4 | Async processing | 🔴 Cao | 🟡 Vừa | 3 |
| S4-1 | KPI Card custom CSS | 🟢 Thấp | 🟡 Vừa | 4 |
| S4-2 | Excel export đẹp | 🟡 Vừa | 🟡 Vừa | 4 |
| S4-3 | System tray icon | 🟡 Vừa | 🟢 Thấp | 4 |
| S4-4 | Dark mode toggle | 🟢 Thấp | 🟢 Thấp | 4 |
| S4-5 | Tối ưu hóa Biểu đồ | 🟡 Vừa | 🔴 Cao | 4 |
| S4-6 | Nâng cấp Bảng dữ liệu | 🟡 Vừa | 🔴 Cao | 4 |
| S4-7 | Skeleton Loading | 🟢 Thấp | 🟡 Vừa | 4 |
| S4-8 | Branding & Clean UI | 🟢 Thấp | 🟡 Vừa | 4 |
| S4-9 | Hiện đại hóa Desktop UI | 🟡 Vừa | 🔴 Cao | 4 |
| S4-10 | Vùng kéo-thả File | 🟡 Vừa | 🔴 Cao | 4 |
| S4-11 | Thông báo hệ thống | 🟢 Thấp | 🟡 Vừa | 4 |

---

## 📋 Checklist triển khai theo sprint

```
Sprint 2 (Quick wins):
  [x] S2-1: st.navigation() → dashboard.py
  [x] S2-2: @st.fragment → pages/*.py
  [x] S2-3: Progress bar → report_processor.py + main.py  (đã có sẵn từ Sprint 1)
  [x] S2-4: Locales fallback → dashboard_shared.py

Sprint 3 (Architecture):
  [x] S3-1: SQLite migration → report_processor.py + dashboard_shared.py
  [x] S3-2: pydantic-settings → config.py + requirements.txt
  [x] S3-3: JSON logging → logger_setup.py + requirements.txt
  [ ] S3-4: Async processing → core_processor.py (optional — bỏ qua)

Sprint 4 (Polish):
  [x] S4-1: KPI card CSS → dashboard_shared.py + dashboard.py
  [x] S4-2: Excel formatting → dashboard_shared.py (_create_styled_excel)
  [x] S4-3: System tray → main.py + requirements.txt (pystray + Pillow)
  [x] S4-4: Dark mode → dashboard_shared.py (inject_global_css)
  [x] S4-5: Tối ưu đồ thị Plotly → dashboard_shared.py (apply_chart_theme)
  [x] S4-6: AgGrid Interactive Tables → pages/*.py (render_aggrid_table)
  [x] S4-7: Loading states (st.status) → pages/*.py + dashboard.py
  [x] S4-8: Custom Branding & Streamlit cleanup → dashboard_shared.py (inject_global_css)
  [x] S4-9: Desktop UI hiện đại → ttkbootstrap đã đáp ứng (litera theme)
  [x] S4-10: Drag & Drop files → main.py + requirements.txt (tkinterdnd2)
  [x] S4-11: Windows Toast Notifications → main.py + requirements.txt (plyer)
```

---

*Tài liệu này được biên soạn và cập nhật trực tiếp dựa trên mã nguồn thực tế của hệ thống TDR Processor v3.2.0 vào ngày 2026-05-24.*
