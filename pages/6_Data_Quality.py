# pages/6_Data_Quality.py
import streamlit as st
import pandas as pd
from dashboard_shared import (
    init_lang, load_all_data, render_language_selector,
    render_sidebar_filters, render_export_sidebar, t,
)

st.set_page_config(page_title="Data Quality — TDR", layout="wide", page_icon="✅")
init_lang()
render_language_selector()

df_vessel_raw, df_qc, df_delay, df_container, df_qc_operator = load_all_data()
df_vessel = render_sidebar_filters(df_vessel_raw)
render_export_sidebar(df_vessel_raw, df_qc, df_qc_operator, df_delay, df_container)

st.header(t("dq_header"))

tables_to_analyze = [
    ("Vessel Summary", df_vessel_raw),
    ("QC Productivity", df_qc),
    ("QC Operator Productivity", df_qc_operator),
    ("Delay Details", df_delay),
    ("Container Details", df_container),
]

total_records = sum(len(df) for _, df in tables_to_analyze)
total_missing = int(sum(df.isnull().sum().sum() for _, df in tables_to_analyze))
_total_size = sum(df.size for _, df in tables_to_analyze if not df.empty)
overall_completeness = round(100 - (total_missing / _total_size * 100) if _total_size > 0 else 0, 1)

col1, col2, col3 = st.columns(3)
col1.metric(t("dq_completeness_score"), f"{overall_completeness:.1f}%")
col2.metric(t("dq_total_records"), f"{total_records:,}")
col3.metric(t("dq_missing_values"), f"{total_missing:,}")

if overall_completeness >= 90:
    st.success(t("dq_validation_passed"))
else:
    st.warning(t("dq_validation_warning"))

st.markdown("---")
st.subheader(t("dq_column_analysis"))

table_selector = st.selectbox("📊 Table", [name for name, _ in tables_to_analyze])
selected_df = next((df for name, df in tables_to_analyze if name == table_selector), None)

if selected_df is not None and not selected_df.empty:
    total_rows = len(selected_df)
    column_stats = []
    for col in selected_df.columns:
        nc = int(selected_df[col].isnull().sum())
        pct = round((nc / total_rows * 100) if total_rows > 0 else 0, 1)
        column_stats.append({
            "Column": col,
            t("dq_non_null"): total_rows - nc,
            t("dq_null_count"): nc,
            t("dq_missing_percent"): pct,
        })

    col_stats_df = pd.DataFrame(column_stats)

    def highlight_missing(val):
        if isinstance(val, (int, float)):
            if val > 20:
                return 'background-color: #ffcccc'
            elif val > 10:
                return 'background-color: #fff3cd'
        return ''

    st.dataframe(
        col_stats_df.style.map(highlight_missing, subset=[t("dq_missing_percent")]),
        use_container_width=True,
    )

    issues = [
        f"⚠️ {row['Column']}: {row[t('dq_missing_percent')]}% {t('dq_missing_values')}"
        for _, row in col_stats_df.iterrows()
        if row[t("dq_missing_percent")] > 20
    ]
    if issues:
        st.subheader(t("dq_recommendations"))
        for issue in issues:
            st.write(issue)
    else:
        st.info(t("dq_no_issues"))
else:
    st.info("No data available for analysis")
