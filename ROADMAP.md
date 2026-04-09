# TDR Processor — Development Roadmap

> Cập nhật lần cuối: 2026-04-09  
> Phiên bản hiện tại: **3.0.0**  
> Trạng thái: Sprint 1 ✅ hoàn thành

---

## ✅ Đã hoàn thành (Sprint 1)

| Hạng mục | Mô tả | Kết quả |
|----------|-------|---------|
| Multi-page dashboard | Tách `dashboard.py` (681 dòng) thành 8 page độc lập | ✅ `pages/1–7_*.py` |
| `dashboard_shared.py` | Shared: translations, `load_csv(ttl=30s)`, sidebar, export | ✅ |
| `st.column_config` | Thay `.style.format()` → Arrow serialization | ✅ KPI Warnings, Timeline |
| Port conflict fix | Kill process cũ trên port 8501 trước khi launch | ✅ `main.py` |
| `.streamlit/config.toml` | `maxMessageSize=500MB`, theme, fastReruns | ✅ |
| PyInstaller spec | Thêm `dashboard.py`, `pages/`, `.streamlit/`, `locales.json` vào `datas` | ✅ |
| Unit tests | 42 tests cho `VesselTransformer`, `QCTransformer`, `DelayTransformer`, `ContainerTransformer` | ✅ 42/42 pass |
| CI/CD pipeline | GitHub Actions: lint, test, security scan, Docker build | ✅ `.github/workflows/ci.yml` |

---

## 🔴 Sprint 2 — High Impact (ưu tiên cao)

### S2-1 · `st.navigation()` API *(Effort: Thấp | Impact: Cao)*

**Vấn đề:** Quy ước `pages/` tự sinh tên xấu (`1 Kpi Warnings`), không kiểm soát được icon và thứ tự.

**Giải pháp:**
```python
# dashboard.py
pg = st.navigation([
    st.Page("dashboard.py",               title="🏠 Tổng quan",       icon="🏠"),
    st.Page("pages/1_KPI_Warnings.py",    title="⚠️ Cảnh báo KPI",    icon="⚠️"),
    st.Page("pages/2_QC_Productivity.py", title="🏗️ Năng suất QC",    icon="🏗️"),
    st.Page("pages/3_QC_Operator.py",     title="👷 Vận hành QC",      icon="👷"),
    st.Page("pages/4_Delay_Analysis.py",  title="⏱️ Phân tích Delay",  icon="⏱️"),
    st.Page("pages/5_Container_Details.py", title="📦 Container",      icon="📦"),
    st.Page("pages/6_Data_Quality.py",    title="✅ Chất lượng dữ liệu", icon="✅"),
    st.Page("pages/7_Timeline.py",        title="📅 Timeline",         icon="📅"),
])
pg.run()
```

**File cần sửa:** `dashboard.py`

---

### S2-2 · `@st.fragment` cho filter sidebar *(Effort: Thấp | Impact: Cao)*

**Vấn đề:** Thay đổi filter → rerun toàn bộ page kể cả các chart không liên quan.

**Giải pháp:** Wrap phần chart/table trong `@st.fragment` → chỉ rerun component đó:
```python
@st.fragment
def render_charts(df_vessel):
    fig = px.bar(df_vessel, ...)
    st.plotly_chart(fig, use_container_width=True)

@st.fragment
def render_kpi_table(df_vessel):
    st.dataframe(df_vessel, ...)
```

**File cần sửa:** Tất cả `pages/*.py`

---

### S2-3 · Progress bar thực trong GUI Desktop *(Effort: Vừa | Impact: Cao)*

**Vấn đề:** `Progressbar` dùng `indeterminate` mode — không phản ánh tiến độ thực tế.

**Giải pháp:**
- `ReportProcessor` emit callback `on_progress(processed, total)`
- `main.py` nhận callback → update `progressbar['value'] = processed`
- Mode `determinate`, `maximum = total_files`

**File cần sửa:** `report_processor.py`, `main.py`

---

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

---

## 📋 Checklist triển khai theo sprint

```
Sprint 2 (Quick wins):
  [ ] S2-1: st.navigation() → dashboard.py
  [ ] S2-2: @st.fragment → pages/*.py
  [ ] S2-3: Progress bar → report_processor.py + main.py
  [ ] S2-4: Locales fallback → dashboard_shared.py

Sprint 3 (Architecture):
  [ ] S3-1: SQLite migration → report_processor.py + dashboard_shared.py
  [ ] S3-2: pydantic-settings → config.py + requirements.txt
  [ ] S3-3: JSON logging → main.py + requirements.txt
  [ ] S3-4: Async processing → core_processor.py (optional)

Sprint 4 (Polish):
  [ ] S4-1: KPI card CSS → dashboard_shared.py + dashboard.py
  [ ] S4-2: Excel formatting → dashboard_shared.py
  [ ] S4-3: System tray → main.py + requirements.txt
  [ ] S4-4: Dark mode → dashboard_shared.py
```

---

*Roadmap này được tạo dựa trên phân tích codebase TDR Processor v3.0.0 ngày 2026-04-09.*
