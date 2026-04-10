# pages/7_Timeline.py
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
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

st.header(t("timeline_header"))

if df_qc.empty or 'Start Time' not in df_qc.columns or 'End Time' not in df_qc.columns:
    st.info(t("timeline_no_data"))
    st.stop()

vessels = df_qc['Vessel Name'].unique().tolist() if 'Vessel Name' in df_qc.columns else []
if not vessels:
    st.info("No vessel data available")
    st.stop()

selected_vessel = st.selectbox(t("timeline_vessel_select"), vessels)


@st.fragment
def render_timeline_chart(df_qc, selected_vessel):
    df_tl = df_qc[df_qc['Vessel Name'] == selected_vessel].copy()

    if df_tl.empty:
        st.warning(t("timeline_no_data"))
        return

    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    def parse_time(time_str):
        try:
            if pd.isna(time_str):
                return None
            parts = str(time_str).split(':')
            if len(parts) >= 2:
                return base_date.replace(hour=int(parts[0]), minute=int(parts[1]))
            return None
        except Exception:
            return None

    df_tl['Start DateTime'] = df_tl['Start Time'].apply(parse_time)
    df_tl['End DateTime'] = df_tl['End Time'].apply(parse_time)
    df_tl = df_tl.dropna(subset=['Start DateTime', 'End DateTime'])

    if df_tl.empty:
        st.warning(t("timeline_no_data"))
        return

    hover_cols = ['Total Conts', 'Net working (hrs)'] if 'Total Conts' in df_tl.columns else None
    fig_tl = px.timeline(
        df_tl,
        x_start='Start DateTime', x_end='End DateTime',
        y='QC No.', color='QC No.',
        title=f"{t('timeline_gantt_title')} - {selected_vessel}",
        hover_data=hover_cols,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    apply_chart_theme(fig_tl)
    fig_tl.update_layout(
        xaxis_title=f"{t('timeline_operation_start')} / {t('timeline_operation_end')}",
        yaxis_title="QC",
        showlegend=True,
        height=420,
        xaxis=dict(tickformat='%H:%M'),
    )
    st.plotly_chart(fig_tl, use_container_width=True)

    st.subheader("📋 QC Summary")
    summary_cols = ['QC No.', 'Start Time', 'End Time', 'Total Conts', 'Net working (hrs)', 'Net moves/h']
    avail_cols = [c for c in summary_cols if c in df_tl.columns]
    df_sum = df_tl[avail_cols].copy()
    for tc in ['Start Time', 'End Time']:
        if tc in df_sum.columns:
            df_sum[tc] = df_sum[tc].apply(lambda x: x[:5] if isinstance(x, str) and len(x) >= 5 else x)

    render_aggrid_table(df_sum, height=280)


render_timeline_chart(df_qc, selected_vessel)
