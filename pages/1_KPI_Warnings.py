# pages/1_KPI_Warnings.py
import streamlit as st
import pandas as pd
from dashboard_shared import (
    init_lang, load_all_data, render_language_selector,
    render_sidebar_filters, render_export_sidebar, t, KPI_MOVES_PER_HOUR,
)

st.set_page_config(page_title="KPI Warnings — TDR", layout="wide", page_icon="⚠️")
init_lang()
render_language_selector()

df_vessel_raw, df_qc, df_delay, df_container, df_qc_operator = load_all_data()
df_vessel = render_sidebar_filters(df_vessel_raw)
render_export_sidebar(df_vessel_raw, df_qc, df_qc_operator, df_delay, df_container)

st.header(t("kpi_warning_header", kpi=KPI_MOVES_PER_HOUR))

if 'Grand Total Conts' in df_vessel.columns and 'Net Working (hrs)' in df_vessel.columns:
    df_vessel['Net moves/h'] = (
        df_vessel['Grand Total Conts'] / df_vessel['Net Working (hrs)']
    ).replace([float('inf'), float('-inf')], 0).fillna(0).round(1)

kpi_col = 'Net moves/h'
if kpi_col not in df_vessel.columns:
    st.info("⚠️ KPI analysis requires Net moves/h — missing Grand Total Conts or Net Working (hrs)")
    st.stop()

under = df_vessel[df_vessel[kpi_col] < KPI_MOVES_PER_HOUR].copy()
if under.empty:
    st.success(t("kpi_all_ok", kpi=KPI_MOVES_PER_HOUR))
else:
    st.warning(t("kpi_underperforming_found", count=len(under)))
    cols_show = [
        'Vessel Name', 'Voyage', 'Operator', kpi_col,
        'Gross Working (hrs)', 'Break Time (hrs)', 'Portstay (hrs)', 'Grand Total Conts',
    ]
    display_cols = [c for c in cols_show if c in under.columns]
    col_cfg = {
        col: st.column_config.NumberColumn(format="%.1f")
        for col in display_cols
        if col in ['Net Working (hrs)', 'Portstay (hrs)', 'Gross Working (hrs)', 'Break Time (hrs)', 'Net moves/h']
    }
    st.dataframe(
        under.sort_values(by=kpi_col, ascending=True)[display_cols],
        use_container_width=True,
        column_config=col_cfg,
    )
    st.caption("ℹ️ Sắp xếp theo Net moves/h tăng dần — giá trị thấp nhất ở trên cùng.")
