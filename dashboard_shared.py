# dashboard_shared.py
"""Shared utilities for TDR multi-page Streamlit dashboard."""
import io
import json
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path("outputs/data_csv")
KPI_MOVES_PER_HOUR = 45


@st.cache_data
def load_translations(lang_file: str = "locales.json") -> dict:
    with open(lang_file, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=30)
def load_csv(path_str: str) -> pd.DataFrame:
    """Load CSV with 30-second TTL — auto-refreshes when new data is processed."""
    path = Path(path_str)
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"Error reading {path.name}: {e}")
        return pd.DataFrame()


def t(key: str, **kwargs) -> str:
    """Return translated string for current language."""
    translations = load_translations()
    lang = st.session_state.get("lang", "vi")
    text = translations[lang].get(key, key)
    return text.format(**kwargs) if kwargs else text


def init_lang() -> None:
    """Initialize language session state (call at top of every page)."""
    if "lang" not in st.session_state:
        st.session_state.lang = "vi"


def load_all_data():
    """Return (df_vessel_raw, df_qc, df_delay, df_container, df_qc_operator)."""
    return (
        load_csv(str(DATA_DIR / "vessel_summary.csv")),
        load_csv(str(DATA_DIR / "qc_productivity.csv")),
        load_csv(str(DATA_DIR / "delay_details.csv")),
        load_csv(str(DATA_DIR / "container_details_long.csv")),
        load_csv(str(DATA_DIR / "qc_operator_productivity.csv")),
    )


def render_language_selector() -> None:
    """Render language radio in sidebar; rerun on change."""
    st.sidebar.title("⚙️ Settings")
    lang_options = {"Tiếng Việt": "vi", "English": "en"}
    current_key = next(
        (k for k, v in lang_options.items() if v == st.session_state.get("lang", "vi")),
        "Tiếng Việt",
    )
    selected = st.sidebar.radio(
        "Ngôn ngữ / Language",
        options=list(lang_options.keys()),
        index=list(lang_options.keys()).index(current_key),
        key="lang_radio",
    )
    if st.session_state.lang != lang_options[selected]:
        st.session_state.lang = lang_options[selected]
        st.rerun()


def render_sidebar_filters(df_vessel_raw: pd.DataFrame) -> pd.DataFrame:
    """Render filter widgets and return filtered vessel DataFrame."""
    st.sidebar.markdown("---")
    st.sidebar.subheader(t("filter_header"))

    df = df_vessel_raw.copy()
    if "Report Date" in df.columns:
        df["Report Date"] = pd.to_datetime(df["Report Date"], errors="coerce")
        df["YearMonth"] = df["Report Date"].dt.to_period("M").astype(str)
        df["Quarter"] = df["Report Date"].dt.to_period("Q").astype(str)

    sel_op = t("filter_all")
    if "Operator" in df.columns:
        ops = [t("filter_all")] + sorted(df["Operator"].dropna().unique().tolist())
        sel_op = st.sidebar.selectbox(t("filter_operator"), ops, key="sb_operator")

    sel_berth = t("filter_all")
    if "Berth" in df.columns:
        berths = [t("filter_all")] + sorted(df["Berth"].dropna().unique().tolist())
        sel_berth = st.sidebar.selectbox(t("filter_berth"), berths, key="sb_berth")

    date_range = None
    if "Report Date" in df.columns and df["Report Date"].notna().any():
        min_d = df["Report Date"].min().date()
        max_d = df["Report Date"].max().date()
        date_range = st.sidebar.date_input(
            t("filter_date_range"),
            value=(min_d, max_d),
            min_value=min_d,
            max_value=max_d,
            key="sb_date_range",
        )

    if sel_op != t("filter_all"):
        df = df[df["Operator"] == sel_op]
    if sel_berth != t("filter_all"):
        df = df[df["Berth"] == sel_berth]
    if date_range and len(date_range) == 2:
        s = pd.Timestamp(date_range[0])
        e = pd.Timestamp(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df = df[(df["Report Date"] >= s) & (df["Report Date"] <= e)]

    if len(df) < len(df_vessel_raw):
        st.sidebar.info(f"📊 {t('filtered_vessels')}: {len(df)}/{len(df_vessel_raw)}")

    if st.sidebar.button(t("filter_reset"), key="btn_reset"):
        for key in ("sb_operator", "sb_berth", "sb_date_range"):
            st.session_state.pop(key, None)
        st.rerun()

    return df


def render_export_sidebar(df_vessel_raw, df_qc, df_qc_operator, df_delay, df_container) -> None:
    """Render export section at bottom of sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.subheader(t("export_header"))

    export_fmt = st.sidebar.selectbox(t("export_format"), ["CSV", "Excel"], key="sb_exp_fmt")
    export_tpl = st.sidebar.selectbox(
        t("export_template"),
        [t("export_all_tables"), t("export_summary_only")],
        key="sb_exp_tpl",
    )

    if st.sidebar.button(t("export_btn"), key="btn_export"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        if export_tpl == t("export_all_tables"):
            tables = [
                ("vessel_summary", df_vessel_raw),
                ("qc_productivity", df_qc),
                ("qc_operator_productivity", df_qc_operator),
                ("delay_details", df_delay),
                ("container_details", df_container),
            ]
        else:
            tables = [("vessel_summary", df_vessel_raw)]

        if export_fmt == "CSV":
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for name, df in tables:
                    if not df.empty:
                        zf.writestr(f"{name}.csv", df.to_csv(index=False))
            buf.seek(0)
            st.sidebar.download_button(
                "📥 Download ZIP", buf,
                file_name=f"tdr_export_{ts}.zip", mime="application/zip",
            )
        else:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                for name, df in tables:
                    if not df.empty:
                        df.to_excel(writer, sheet_name=name[:31], index=False)
            buf.seek(0)
            st.sidebar.download_button(
                "📥 Download Excel", buf,
                file_name=f"tdr_export_{ts}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
