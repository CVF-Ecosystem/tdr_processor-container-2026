# pages/3_QC_Operator.py
import streamlit as st
import pandas as pd
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

st.header(f"👨‍🔧 {t('qc_operator_header')}")
st.info(t("qc_operator_info"))

if df_qc_operator.empty:
    st.warning(t("no_data_qc_operator"))
    st.stop()

if 'Net moves/h' not in df_qc_operator.columns and 'Total Conts' in df_qc_operator.columns and 'Net working (hrs)' in df_qc_operator.columns:
    df_qc_operator['Net moves/h'] = (df_qc_operator['Total Conts'] / df_qc_operator['Net working (hrs)']).round(1)


@st.fragment
def render_operator_avg_chart(df_qc_operator):
    st.subheader(t("qc_operator_avg_subheader"))
    if 'Net moves/h' in df_qc_operator.columns:
        avg_op = df_qc_operator.groupby('QC No.')['Net moves/h'].mean().sort_values(ascending=False).reset_index()
        fig = px.bar(
            avg_op, x='QC No.', y='Net moves/h',
            title=t("qc_operator_avg_title"),
            labels={'QC No.': t("qc_axis_label"), 'Net moves/h': t("qc_operator_axis_label")},
            text_auto='.1f',
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        apply_chart_theme(fig)
        st.plotly_chart(fig, use_container_width=True)


@st.fragment
def render_compare_chart(df_qc, df_qc_operator):
    st.subheader(t("qc_compare_subheader"))
    has_qc_data = not df_qc.empty and 'Net moves/h' in df_qc.columns
    if has_qc_data and 'Net moves/h' in df_qc_operator.columns:
        df_c1 = df_qc.groupby('QC No.')['Net moves/h'].mean().reset_index().rename(
            columns={'Net moves/h': t("qc_compare_legend_crane")}
        )
        df_c2 = df_qc_operator.groupby('QC No.')['Net moves/h'].mean().reset_index().rename(
            columns={'Net moves/h': t("qc_compare_legend_operator")}
        )
        df_m = pd.merge(df_c1, df_c2, on='QC No.', how='outer')
        fig_cmp = px.bar(
            df_m, x='QC No.',
            y=[t("qc_compare_legend_crane"), t("qc_compare_legend_operator")],
            barmode='group', title=t("qc_compare_title"),
        )
        apply_chart_theme(fig_cmp)
        st.plotly_chart(fig_cmp, use_container_width=True)
    else:
        st.info(t("no_data_qc_compare"))


@st.fragment
def render_operator_table(df_qc_operator):
    st.subheader(t("qc_details_subheader"))
    render_aggrid_table(df_qc_operator, height=420)


col1, col2 = st.columns(2)
with col1:
    render_operator_avg_chart(df_qc_operator)
with col2:
    render_compare_chart(df_qc, df_qc_operator)

render_operator_table(df_qc_operator)
