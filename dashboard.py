# dashboard.py — Home: Tổng quan & Theo thời gian
import streamlit as st
import pandas as pd
import plotly.express as px
from dashboard_shared import (
    init_lang, load_all_data, render_language_selector,
    render_sidebar_filters, render_export_sidebar, t, KPI_MOVES_PER_HOUR,
)

st.set_page_config(page_title="TDR Dashboard", layout="wide", page_icon="🚢")

init_lang()
render_language_selector()

df_vessel_raw, df_qc, df_delay, df_container, df_qc_operator = load_all_data()
df_vessel = render_sidebar_filters(df_vessel_raw)
render_export_sidebar(df_vessel_raw, df_qc, df_qc_operator, df_delay, df_container)

st.title(f'🚢 {t("main_title")}')
st.markdown("---")

if df_vessel.empty:
    st.warning(t("data_not_found_warning"))
    st.stop()

# --- KPI Metrics ---
st.header(t("overview_header"))

if 'Grand Total Conts' in df_vessel.columns and 'Net Working (hrs)' in df_vessel.columns:
    df_vessel['Net moves/h'] = (
        df_vessel['Grand Total Conts'] / df_vessel['Net Working (hrs)']
    ).replace([float('inf'), float('-inf')], 0).fillna(0).round(1)

total_vessels = len(df_vessel)
avg_portstay = df_vessel['Portstay (hrs)'].mean() if 'Portstay (hrs)' in df_vessel.columns else 0.0
avg_net_working = df_vessel['Net Working (hrs)'].mean() if 'Net Working (hrs)' in df_vessel.columns else 0.0
total_teus = df_vessel['Grand Total TEUs'].sum() if 'Grand Total TEUs' in df_vessel.columns else 0
avg_net_moves = df_vessel['Net moves/h'].mean() if 'Net moves/h' in df_vessel.columns else 0.0
total_delay_hrs = df_delay['Duration (hrs)'].sum() if not df_delay.empty and 'Duration (hrs)' in df_delay.columns else 0.0
avg_delay_per_vessel = total_delay_hrs / total_vessels if total_vessels > 0 else 0.0
moves_delta = avg_net_moves - KPI_MOVES_PER_HOUR

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric(t("metric_total_vessels"), f"{total_vessels:,}")
col2.metric(t("metric_total_teus"), f"{total_teus:,.0f}")
col3.metric(t("metric_avg_portstay"), f"{avg_portstay:.1f}")
col4.metric(t("metric_avg_net_working"), f"{avg_net_working:.1f}")
col5.metric(
    t("metric_avg_net_moves"), f"{avg_net_moves:.1f}",
    delta=f"{moves_delta:+.1f} {t('kpi_vs_target')}",
    delta_color="normal" if moves_delta >= 0 else "inverse",
)
col6.metric(t("kpi_avg_delay"), f"{avg_delay_per_vessel:.1f}")
st.caption(f"🎯 {t('kpi_target')}: {KPI_MOVES_PER_HOUR} moves/h")
st.markdown("---")

# --- Operator Performance ---
if 'Net moves/h' in df_vessel.columns and 'Operator' in df_vessel.columns:
    st.subheader(t("operator_performance_subheader"))
    avg_by_op = df_vessel.groupby('Operator')['Net moves/h'].mean().sort_values(ascending=False).reset_index()
    fig = px.bar(
        avg_by_op, x='Operator', y='Net moves/h',
        title=t("operator_performance_title"),
        labels={'Operator': t("operator_axis_label"), 'Net moves/h': t("moves_per_hour_axis_label")},
        text_auto='.1f',
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Time Analysis ---
if 'Report Date' in df_vessel.columns and 'Net moves/h' in df_vessel.columns:
    st.markdown("---")
    st.header(t("time_analysis_header"))
    try:
        df_vessel['Report Date'] = pd.to_datetime(df_vessel['Report Date'], errors='coerce')
        df_vessel['Month'] = df_vessel['Report Date'].dt.to_period('M').astype(str)
        df_vessel['Quarter'] = df_vessel['Report Date'].dt.to_period('Q').astype(str)

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.subheader(t('monthly_performance_subheader'))
            monthly = df_vessel.groupby('Month')['Net moves/h'].mean().reset_index()
            if not monthly.empty:
                fig_m = px.line(
                    monthly, x='Month', y='Net moves/h', markers=True,
                    title=t('monthly_performance_title'),
                    labels={'Month': t('month_axis_label'), 'Net moves/h': t('moves_per_hour_axis_label')},
                    text=monthly['Net moves/h'].apply(lambda x: f'{x:.1f}'),
                )
                fig_m.update_traces(textposition="top center")
                st.plotly_chart(fig_m, use_container_width=True)

        with col_t2:
            st.subheader(t('quarterly_performance_subheader'))
            quarterly = df_vessel.groupby('Quarter')['Net moves/h'].mean().reset_index()
            if not quarterly.empty:
                fig_q = px.bar(
                    quarterly, x='Quarter', y='Net moves/h', text_auto='.1f',
                    title=t('quarterly_performance_title'),
                    labels={'Quarter': t('quarter_axis_label'), 'Net moves/h': t('moves_per_hour_axis_label')},
                )
                fig_q.update_traces(marker_color='#636EFA')
                st.plotly_chart(fig_q, use_container_width=True)
    except Exception as e:
        st.info(f"⚠️ Time-based analysis error: {e}")