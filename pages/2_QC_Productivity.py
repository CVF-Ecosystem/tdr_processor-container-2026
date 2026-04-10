# pages/2_QC_Productivity.py
import streamlit as st
import plotly.express as px
from dashboard_shared import (
    init_lang, load_all_data, render_language_selector,
    render_sidebar_filters, render_export_sidebar,
    render_aggrid_table, apply_chart_theme, t,
)

init_lang()
render_language_selector()

df_vessel_raw, df_qc, df_delay, df_container, df_qc_operator = load_all_data()

df_vessel = render_sidebar_filters(df_vessel_raw)
render_export_sidebar(df_vessel_raw, df_qc, df_qc_operator, df_delay, df_container)

st.header(t("qc_header"))

if df_qc.empty:
    st.warning(t("no_data_qc"))
    st.stop()

if 'Net moves/h' not in df_qc.columns and 'Total Conts' in df_qc.columns and 'Net working (hrs)' in df_qc.columns:
    df_qc['Net moves/h'] = (df_qc['Total Conts'] / df_qc['Net working (hrs)']).round(1)


@st.fragment
def render_qc_chart(df_qc):
    st.subheader(t("qc_avg_subheader"))
    if 'Net moves/h' in df_qc.columns:
        avg_by_qc = df_qc.groupby('QC No.')['Net moves/h'].mean().sort_values(ascending=False).reset_index()
        fig = px.bar(
            avg_by_qc, x='QC No.', y='Net moves/h',
            title=t("qc_avg_title"),
            labels={'QC No.': t("qc_axis_label"), 'Net moves/h': t("moves_per_hour_axis_label")},
            text_auto='.1f', color_discrete_sequence=["#2563EB"],
        )
        apply_chart_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("⚠️ Cannot calculate Net moves/h — missing required columns")


render_qc_chart(df_qc)
