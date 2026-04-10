# pages/5_Container_Details.py
import streamlit as st
from dashboard_shared import (
    init_lang, load_all_data, render_language_selector,
    render_sidebar_filters, render_export_sidebar,
    render_aggrid_table, t,
)

init_lang()
render_language_selector()

df_vessel_raw, df_qc, df_delay, df_container, df_qc_operator = load_all_data()

df_vessel = render_sidebar_filters(df_vessel_raw)
render_export_sidebar(df_vessel_raw, df_qc, df_qc_operator, df_delay, df_container)

st.header(t("container_header"))

if df_container.empty:
    st.warning("Không có dữ liệu Container.")
    st.stop()

total_rows = len(df_container)
st.caption(f"📦 {total_rows:,} rows | {len(df_container.columns)} columns")


@st.fragment
def render_container_table(df_container):
    # AgGrid hỗ trợ phân trang, lọc, ghim cột trực tiếp trên header
    render_aggrid_table(df_container, height=550, page_size=100, fit_columns=False)


render_container_table(df_container)
