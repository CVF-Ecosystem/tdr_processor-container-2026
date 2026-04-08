# pages/4_Delay_Analysis.py
import streamlit as st
import plotly.express as px
from dashboard_shared import (
    init_lang, load_all_data, render_language_selector,
    render_sidebar_filters, render_export_sidebar, t,
)

st.set_page_config(page_title="Delay Analysis — TDR", layout="wide", page_icon="⏱️")
init_lang()
render_language_selector()

df_vessel_raw, df_qc, df_delay, df_container, df_qc_operator = load_all_data()
df_vessel = render_sidebar_filters(df_vessel_raw)
render_export_sidebar(df_vessel_raw, df_qc, df_qc_operator, df_delay, df_container)

st.header(t("delay_header"))

if df_delay.empty:
    st.warning("Không có dữ liệu Delay.")
    st.stop()

st.subheader(t("delay_by_type_subheader"))
delay_by_qc = (
    df_delay.groupby('QC No.')['Duration (hrs)'].sum()
    .sort_values(ascending=False)
    .reset_index()
)
fig_pie = px.pie(
    delay_by_qc, names='QC No.', values='Duration (hrs)',
    title=t("delay_by_type_title"),
)
st.plotly_chart(fig_pie, use_container_width=True)

st.subheader(t("delay_details_subheader"))
st.dataframe(df_delay.head(1000), use_container_width=True)
if len(df_delay) > 1000:
    st.caption(f"⚠️ Hiển thị 1,000 / {len(df_delay):,} rows. Export để xem toàn bộ.")
