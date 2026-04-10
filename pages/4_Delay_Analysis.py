# pages/4_Delay_Analysis.py
import streamlit as st
import plotly.express as px
from dashboard_shared import (
    init_lang, load_all_data, render_language_selector,
    render_sidebar_filters, render_export_sidebar,
    render_aggrid_table, apply_chart_theme, t,
)

init_lang()
render_language_selector()

with st.status("Đang tải dữ liệu...", expanded=False):
    df_vessel_raw, df_qc, df_delay, df_container, df_qc_operator = load_all_data()

df_vessel = render_sidebar_filters(df_vessel_raw)
render_export_sidebar(df_vessel_raw, df_qc, df_qc_operator, df_delay, df_container)

st.header(t("delay_header"))

if df_delay.empty:
    st.warning("Không có dữ liệu Delay.")
    st.stop()


@st.fragment
def render_delay_chart(df_delay):
    st.subheader(t("delay_by_type_subheader"))
    delay_by_qc = (
        df_delay.groupby('QC No.')['Duration (hrs)'].sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    fig_pie = px.pie(
        delay_by_qc, names='QC No.', values='Duration (hrs)',
        title=t("delay_by_type_title"),
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    apply_chart_theme(fig_pie)
    st.plotly_chart(fig_pie, use_container_width=True)


@st.fragment
def render_delay_table(df_delay):
    st.subheader(t("delay_details_subheader"))
    render_aggrid_table(df_delay, height=450, page_size=50)
    if len(df_delay) > 1000:
        st.caption(f"⚠️ {len(df_delay):,} rows — dùng filter trên header để thu hẹp. Export để xem toàn bộ.")


render_delay_chart(df_delay)
render_delay_table(df_delay)
