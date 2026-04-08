# pages/5_Container_Details.py
import streamlit as st
from dashboard_shared import (
    init_lang, load_all_data, render_language_selector,
    render_sidebar_filters, render_export_sidebar, t,
)

st.set_page_config(page_title="Container Details — TDR", layout="wide", page_icon="📦")
init_lang()
render_language_selector()

df_vessel_raw, df_qc, df_delay, df_container, df_qc_operator = load_all_data()
df_vessel = render_sidebar_filters(df_vessel_raw)
render_export_sidebar(df_vessel_raw, df_qc, df_qc_operator, df_delay, df_container)

st.header(t("container_header"))

if df_container.empty:
    st.warning("Không có dữ liệu Container.")
    st.stop()

PAGE_SIZE = 500
total_rows = len(df_container)
total_pages = max(1, (total_rows + PAGE_SIZE - 1) // PAGE_SIZE)

col_info, col_page = st.columns([3, 1])
with col_info:
    st.caption(f"📦 {total_rows:,} rows | {len(df_container.columns)} columns | {PAGE_SIZE} rows/page")
with col_page:
    page_num = st.number_input("Trang", min_value=1, max_value=total_pages, value=1, step=1)

start_idx = (page_num - 1) * PAGE_SIZE
end_idx = min(start_idx + PAGE_SIZE, total_rows)
st.dataframe(df_container.iloc[start_idx:end_idx], use_container_width=True)
st.caption(f"Hiển thị {start_idx+1:,}–{end_idx:,} / {total_rows:,} rows (trang {page_num}/{total_pages})")
