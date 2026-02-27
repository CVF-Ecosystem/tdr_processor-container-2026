# dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import json
import logging
# --- Bước 1: Gọi st.set_page_config() ĐẦU TIÊN ---
# Chúng ta sẽ gọi nó với giá trị mặc định, sau đó cập nhật lại tiêu đề nếu cần.
st.set_page_config(page_title="TDR Dashboard", layout="wide", page_icon="🚢")

# --- Bước 2: Cấu hình và tải từ điển ngôn ngữ ---
@st.cache_data
def load_translations(lang_file="locales.json"):
    with open(lang_file, 'r', encoding='utf-8') as f:
        return json.load(f)

translations = load_translations()

# --- Bước 3: Khởi tạo session state và hàm dịch ---
if 'lang' not in st.session_state:
    st.session_state.lang = 'vi'

def t(key, **kwargs):
    text = translations[st.session_state.lang].get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text

# --- Bước 4: Tạo các widget trên sidebar ---
st.sidebar.title("⚙️ Settings")
lang_options = {"Tiếng Việt": "vi", "English": "en"}
# Tìm index của ngôn ngữ hiện tại để đặt giá trị mặc định cho radio
current_lang_key = next((key for key, value in lang_options.items() if value == st.session_state.lang), "Tiếng Việt")
selected_lang_display = st.sidebar.radio(
    "Ngôn ngữ / Language",
    options=lang_options.keys(),
    index=list(lang_options.keys()).index(current_lang_key) # Đặt giá trị mặc định
)
# Cập nhật lại ngôn ngữ trong session state nếu người dùng thay đổi
if st.session_state.lang != lang_options[selected_lang_display]:
    st.session_state.lang = lang_options[selected_lang_display]
    st.rerun() # Chạy lại script để áp dụng ngôn ngữ mới

# --- Bước 5: Tải dữ liệu ---
@st.cache_data
def load_data(file_path):
    if file_path.exists():
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            st.error(f"Error reading file {file_path.name}: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

# Tải dữ liệu
DATA_DIR = Path("outputs/data_csv")
df_vessel_raw = load_data(DATA_DIR / "vessel_summary.csv")
df_qc = load_data(DATA_DIR / "qc_productivity.csv")
df_delay = load_data(DATA_DIR / "delay_details.csv")
df_container = load_data(DATA_DIR / "container_details_long.csv")
df_qc_operator = load_data(DATA_DIR / "qc_operator_productivity.csv")

# --- Bước 6: Sidebar Filters ---
st.sidebar.markdown("---")
st.sidebar.subheader(t("filter_header"))

# Initialize filter state
if 'filters_applied' not in st.session_state:
    st.session_state.filters_applied = False

df_vessel = df_vessel_raw.copy()

# Xử lý dữ liệu thời gian
if 'Report Date' in df_vessel.columns:
    df_vessel['Report Date'] = pd.to_datetime(df_vessel['Report Date'], errors='coerce')
    df_vessel['YearMonth'] = df_vessel['Report Date'].dt.to_period('M').astype(str)
    df_vessel['Quarter'] = df_vessel['Report Date'].dt.to_period('Q').astype(str)

# Filter: Operator
if 'Operator' in df_vessel.columns:
    operators = [t("filter_all")] + sorted(df_vessel['Operator'].dropna().unique().tolist())
    selected_operator = st.sidebar.selectbox(t("filter_operator"), operators)
else:
    selected_operator = t("filter_all")

# Filter: Berth  
if 'Berth' in df_vessel.columns:
    berths = [t("filter_all")] + sorted(df_vessel['Berth'].dropna().unique().tolist())
    selected_berth = st.sidebar.selectbox(t("filter_berth"), berths)
else:
    selected_berth = t("filter_all")

# Filter: Date Range
if 'Report Date' in df_vessel.columns and df_vessel['Report Date'].notna().any():
    min_date = df_vessel['Report Date'].min().date()
    max_date = df_vessel['Report Date'].max().date()
    date_range = st.sidebar.date_input(
        t("filter_date_range"),
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
else:
    date_range = None

# Apply filters
if selected_operator != t("filter_all"):
    df_vessel = df_vessel[df_vessel['Operator'] == selected_operator]
if selected_berth != t("filter_all"):
    df_vessel = df_vessel[df_vessel['Berth'] == selected_berth]
if date_range and len(date_range) == 2:
    start_date, end_date = date_range
    # Convert date to datetime for proper comparison with datetime64[ns]
    start_datetime = pd.Timestamp(start_date)
    end_datetime = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    df_vessel = df_vessel[
        (df_vessel['Report Date'] >= start_datetime) & 
        (df_vessel['Report Date'] <= end_datetime)
    ]

# Show filter status
filtered_count = len(df_vessel)
total_count = len(df_vessel_raw)
if filtered_count < total_count:
    st.sidebar.info(f"📊 {t('filtered_vessels')}: {filtered_count}/{total_count}")

# Reset filters button
if st.sidebar.button(t("filter_reset")):
    st.session_state.filters_applied = False
    st.rerun()

# --- Bước 7: Giao diện chính ---

# Giao diện chính
st.title(f'🚢 {t("main_title")}')
st.markdown("---")

if df_vessel.empty:
    st.warning(t("data_not_found_warning"))
    st.stop()

# Định nghĩa KPI
KPI_MOVES_PER_HOUR = 45

# Tạo các tab
tabs = st.tabs([
    t("tab_overview"), 
    t("tab_kpi_warning"), 
    t("tab_qc_productivity"), 
    t("tab_qc_operator_productivity"),
    t("tab_delay_analysis"), 
    t("tab_container_details"),
    t("tab_data_quality"),
    t("tab_timeline")
])


# --- Tab 0: Tổng quan & Theo thời gian ---
with tabs[0]:
    st.header(t("overview_header"))
    
    # Calculate metrics
    total_vessels = len(df_vessel)
    avg_portstay = df_vessel['Portstay (hrs)'].mean() if 'Portstay (hrs)' in df_vessel.columns else 0.0
    avg_net_working = df_vessel['Net Working (hrs)'].mean() if 'Net Working (hrs)' in df_vessel.columns else 0.0
    total_teus = df_vessel['Grand Total TEUs'].sum() if 'Grand Total TEUs' in df_vessel.columns else 0
    
    # Calculate Net moves/h = Total Conts / Net Working hrs (actual productivity when working)
    if 'Grand Total Conts' in df_vessel.columns and 'Net Working (hrs)' in df_vessel.columns:
        df_vessel['Net moves/h'] = (df_vessel['Grand Total Conts'] / df_vessel['Net Working (hrs)']).replace([float('inf'), float('-inf')], 0).fillna(0).round(1)
        avg_net_moves = df_vessel['Net moves/h'].mean()
    else:
        avg_net_moves = 0.0
    
    # Calculate total delay from delay dataframe
    total_delay_hrs = df_delay['Duration (hrs)'].sum() if not df_delay.empty and 'Duration (hrs)' in df_delay.columns else 0.0
    avg_delay_per_vessel = total_delay_hrs / total_vessels if total_vessels > 0 else 0.0
    
    # KPI Cards with delta comparison
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    # Delta calculation (vs KPI target)
    moves_delta = avg_net_moves - KPI_MOVES_PER_HOUR
    moves_delta_str = f"{moves_delta:+.1f} {t('kpi_vs_target')}"
    
    col1.metric(t("metric_total_vessels"), f"{total_vessels:,}")
    col2.metric(t("metric_total_teus"), f"{total_teus:,.0f}")
    col3.metric(t("metric_avg_portstay"), f"{avg_portstay:.1f}")
    col4.metric(t("metric_avg_net_working"), f"{avg_net_working:.1f}")
    col5.metric(
        t("metric_avg_net_moves"), 
        f"{avg_net_moves:.1f}",
        delta=moves_delta_str,
        delta_color="normal" if moves_delta >= 0 else "inverse"
    )
    col6.metric(t("kpi_avg_delay"), f"{avg_delay_per_vessel:.1f}")
    
    # KPI Target info
    st.caption(f"🎯 {t('kpi_target')}: {KPI_MOVES_PER_HOUR} moves/h")
    st.markdown("---")

    if not df_vessel.empty:
        st.subheader(t("operator_performance_subheader"))
        # Use Net moves/h for operator analysis (actual productivity when working)
        if 'Net moves/h' in df_vessel.columns:
            avg_by_operator = df_vessel.groupby('Operator')['Net moves/h'].mean().sort_values(ascending=False).reset_index()
            fig = px.bar(avg_by_operator, x='Operator', y='Net moves/h',
                         title=t("operator_performance_title"),
                         labels={'Operator': t("operator_axis_label"), 'Net moves/h': t("moves_per_hour_axis_label")},
                         text_auto='.1f')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("⚠️ Net moves/h not available - missing Grand Total Conts or Net Working (hrs)")

    if 'Report Date' in df_vessel.columns and 'Net moves/h' in df_vessel.columns:
        st.markdown("---")
        st.header(t("time_analysis_header"))
        
        # Calculate time-based analysis using Net moves/h (actual productivity)
        try:
            df_vessel['Report Date'] = pd.to_datetime(df_vessel['Report Date'], errors='coerce')
            df_vessel['Month'] = df_vessel['Report Date'].dt.to_period('M').astype(str)
            df_vessel['Quarter'] = df_vessel['Report Date'].dt.to_period('Q').astype(str)
            
            time_col1, time_col2 = st.columns(2)
            
            # Monthly chart - simple like image 3
            with time_col1:
                st.subheader(t('monthly_performance_subheader'))
                monthly_performance = df_vessel.groupby('Month')['Net moves/h'].mean().reset_index()
                if not monthly_performance.empty:
                    fig_monthly = px.line(monthly_performance, x='Month', y='Net moves/h',
                                          title=t('monthly_performance_title'), markers=True,
                                          labels={'Month': t('month_axis_label'), 'Net moves/h': t('moves_per_hour_axis_label')},
                                          text=monthly_performance['Net moves/h'].apply(lambda x: f'{x:.1f}'))
                    fig_monthly.update_traces(textposition="top center")
                    st.plotly_chart(fig_monthly, use_container_width=True)
            
            # Quarterly chart - simple like image 3
            with time_col2:
                st.subheader(t('quarterly_performance_subheader'))
                quarterly_performance = df_vessel.groupby('Quarter')['Net moves/h'].mean().reset_index()
                if not quarterly_performance.empty:
                    fig_quarterly = px.bar(quarterly_performance, x='Quarter', y='Net moves/h',
                                           title=t('quarterly_performance_title'),
                                           labels={'Quarter': t('quarter_axis_label'), 'Net moves/h': t('moves_per_hour_axis_label')},
                                           text_auto='.1f')
                    fig_quarterly.update_traces(marker_color='#636EFA')
                    st.plotly_chart(fig_quarterly, use_container_width=True)
                    
        except Exception as e:
            st.info(f"⚠️ Time-based analysis error: {e}")

# --- Tab 1: Cảnh báo KPI ---
with tabs[1]:
    st.header(t("kpi_warning_header", kpi=KPI_MOVES_PER_HOUR))
    # KPI metric should be Net moves/h (actual productivity when working)
    kpi_metric_col = 'Net moves/h' if 'Net moves/h' in df_vessel.columns else None
    
    if kpi_metric_col and kpi_metric_col in df_vessel.columns:
        underperforming_vessels = df_vessel[df_vessel[kpi_metric_col] < KPI_MOVES_PER_HOUR].copy()
        if underperforming_vessels.empty:
            st.success(t("kpi_all_ok", kpi=KPI_MOVES_PER_HOUR))
        else:
            st.warning(t("kpi_underperforming_found", count=len(underperforming_vessels)))
            columns_to_show = ['Vessel Name', 'Voyage', 'Operator', kpi_metric_col, 'Gross Working (hrs)', 'Break Time (hrs)', 'Portstay (hrs)', 'Grand Total Conts']
            display_cols = [col for col in columns_to_show if col in underperforming_vessels.columns]
            underperforming_vessels_sorted = underperforming_vessels.sort_values(by=kpi_metric_col, ascending=True)
            
            # Build format dict dynamically for available columns
            format_dict = {}
            for col in display_cols:
                if col in ['Net Working (hrs)', 'Portstay (hrs)', 'Gross Working (hrs)', 'Break Time (hrs)', 'Net moves/h']:
                    format_dict[col] = '{:.1f}'
            
            st.dataframe(
                underperforming_vessels_sorted[display_cols].style.format(format_dict).highlight_min(
                    subset=[kpi_metric_col], color='lightcoral'
                ),
                use_container_width=True
            )
    else:
        st.info("⚠️ KPI analysis requires performance metrics (Net Working hrs or Portstay hrs) not currently available")

# --- Tab 2: Năng suất khai thác (QC) ---
with tabs[2]:
    st.header(t("qc_header"))
    if not df_qc.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(t("qc_avg_subheader"))
            # Calculate moves/h if not in CSV (Total Conts / Net working hrs)
            if 'Net moves/h' not in df_qc.columns and 'Total Conts' in df_qc.columns and 'Net working (hrs)' in df_qc.columns:
                df_qc['Net moves/h'] = (df_qc['Total Conts'] / df_qc['Net working (hrs)']).round(1)
            
            if 'Net moves/h' in df_qc.columns:
                avg_by_qc = df_qc.groupby('QC No.')['Net moves/h'].mean().sort_values(ascending=False).reset_index()
                fig_qc = px.bar(avg_by_qc, x='QC No.', y='Net moves/h',
                                title=t("qc_avg_title"),
                                labels={'QC No.': t("qc_axis_label"), 'Net moves/h': t("moves_per_hour_axis_label")},
                                text_auto='.1f')
                st.plotly_chart(fig_qc, use_container_width=True)
            else:
                st.info("⚠️ Cannot calculate Net moves/h - missing required columns")
        with col2:
            st.subheader(t("qc_details_subheader"))
            # Format display for QC details
            df_qc_display = df_qc.copy()
            # Format time columns to HH:MM
            for time_col in ['Start Time', 'End Time']:
                if time_col in df_qc_display.columns:
                    df_qc_display[time_col] = df_qc_display[time_col].apply(
                        lambda x: x[:5] if isinstance(x, str) and len(x) >= 5 else x
                    )
            # Format numeric columns
            format_dict_qc = {}
            for col in df_qc_display.columns:
                if col in ['Net working (hrs)', 'Gross working (hrs)', 'Delay times (hrs)', 'Net moves/h']:
                    format_dict_qc[col] = '{:.1f}'
            st.dataframe(df_qc_display.style.format(format_dict_qc, na_rep=''), use_container_width=True)

# --- Tab 3: Năng suất vận hành (QC) ---
with tabs[3]:
    st.header(f"👨‍🔧 {t('qc_operator_header')}")
    st.info(t("qc_operator_info"))
    if not df_qc_operator.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(t("qc_operator_avg_subheader"))
            # Calculate moves/h for operator data
            if 'Net moves/h' not in df_qc_operator.columns and 'Total Conts' in df_qc_operator.columns and 'Net working (hrs)' in df_qc_operator.columns:
                df_qc_operator['Net moves/h'] = (df_qc_operator['Total Conts'] / df_qc_operator['Net working (hrs)']).round(1)
            
            if 'Net moves/h' in df_qc_operator.columns:
                avg_by_qc_operator = df_qc_operator.groupby('QC No.')['Net moves/h'].mean().sort_values(ascending=False).reset_index()
                fig_qc_operator = px.bar(avg_by_qc_operator, x='QC No.', y='Net moves/h',
                                title=t("qc_operator_avg_title"),
                                labels={'QC No.': t("qc_axis_label"), 'Net moves/h': t("qc_operator_axis_label")},
                                text_auto='.1f',
                                color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_qc_operator, use_container_width=True)
            else:
                st.info("⚠️ Cannot calculate Net moves/h for operator data")
        with col2:
            st.subheader(t("qc_compare_subheader"))
            if not df_qc.empty and 'Net moves/h' in df_qc.columns and 'Net moves/h' in df_qc_operator.columns:
                df_compare1 = df_qc.groupby('QC No.')['Net moves/h'].mean().reset_index().rename(columns={'Net moves/h': t("qc_compare_legend_crane")})
                df_compare2 = df_qc_operator.groupby('QC No.')['Net moves/h'].mean().reset_index().rename(columns={'Net moves/h': t("qc_compare_legend_operator")})
                df_merged = pd.merge(df_compare1, df_compare2, on='QC No.', how='outer')
                
                fig_compare = px.bar(df_merged, x='QC No.', y=[t("qc_compare_legend_crane"), t("qc_compare_legend_operator")], barmode='group',
                                     title=t("qc_compare_title"))
                st.plotly_chart(fig_compare, use_container_width=True)
            else:
                st.info("Không có dữ liệu 'Năng suất khai thác' để so sánh.")

        st.subheader(t("qc_details_subheader"))
        st.dataframe(df_qc_operator)
    else:
        st.warning("Không tìm thấy dữ liệu 'qc_operator_productivity.csv'.")
# --- Tab 4: Phân tích Delay ---
with tabs[4]:
    st.header(t("delay_header"))
    if not df_delay.empty:
        st.subheader(t("delay_by_type_subheader"))
        # Group by QC No. since Error Type column not available
        delay_by_qc = df_delay.groupby('QC No.')['Duration (hrs)'].sum().sort_values(ascending=False).reset_index()
        fig_delay_pie = px.pie(delay_by_qc, names='QC No.', values='Duration (hrs)',
                               title=t("delay_by_type_title"))
        st.plotly_chart(fig_delay_pie, use_container_width=True)
        st.subheader(t("delay_details_subheader"))
        st.dataframe(df_delay)

# --- Tab 5: Chi tiết Container ---
with tabs[5]:
    st.header(t("container_header"))
    if not df_container.empty:
        st.dataframe(df_container)

# --- Tab 6: Data Quality ---
with tabs[6]:
    st.header(t("dq_header"))
    
    # Data quality analysis function
    def analyze_data_quality(df: pd.DataFrame, table_name: str) -> dict:
        """Analyze data quality for a dataframe."""
        if df.empty:
            return {"empty": True}
        
        total_rows = len(df)
        total_cells = df.size
        null_cells = df.isnull().sum().sum()
        completeness = ((total_cells - null_cells) / total_cells * 100) if total_cells > 0 else 0
        
        # Column-level analysis
        column_stats = []
        for col in df.columns:
            null_count = df[col].isnull().sum()
            non_null = total_rows - null_count
            pct_missing = (null_count / total_rows * 100) if total_rows > 0 else 0
            column_stats.append({
                "Column": col,
                t("dq_non_null"): non_null,
                t("dq_null_count"): null_count,
                t("dq_missing_percent"): round(pct_missing, 1)
            })
        
        # Identify issues
        issues = []
        for stat in column_stats:
            if stat[t("dq_missing_percent")] > 20:
                issues.append(f"⚠️ {stat['Column']}: {stat[t('dq_missing_percent')]}% {t('dq_missing_values')}")
        
        return {
            "empty": False,
            "table_name": table_name,
            "total_rows": total_rows,
            "completeness": round(completeness, 1),
            "column_stats": column_stats,
            "issues": issues
        }
    
    # Analyze all tables
    tables_to_analyze = [
        ("Vessel Summary", df_vessel_raw),
        ("QC Productivity", df_qc),
        ("QC Operator Productivity", df_qc_operator),
        ("Delay Details", df_delay),
        ("Container Details", df_container)
    ]
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_records = sum(len(df) for _, df in tables_to_analyze)
    total_missing = sum(df.isnull().sum().sum() for _, df in tables_to_analyze)
    overall_completeness = 100 - (total_missing / sum(df.size for _, df in tables_to_analyze if not df.empty) * 100) if total_records > 0 else 0
    total_issues = 0
    
    with col1:
        st.metric(t("dq_completeness_score"), f"{overall_completeness:.1f}%")
    with col2:
        st.metric(t("dq_total_records"), f"{total_records:,}")
    with col3:
        st.metric(t("dq_missing_values"), f"{total_missing:,}")
    
    # Validation status
    if overall_completeness >= 90:
        st.success(t("dq_validation_passed"))
    else:
        st.warning(t("dq_validation_warning"))
    
    st.markdown("---")
    
    # Detailed analysis per table
    st.subheader(t("dq_column_analysis"))
    
    table_selector = st.selectbox(
        "📊 Table",
        [name for name, _ in tables_to_analyze]
    )
    
    # Find selected table
    selected_df = None
    for name, df in tables_to_analyze:
        if name == table_selector:
            selected_df = df
            break
    
    if selected_df is not None and not selected_df.empty:
        quality_result = analyze_data_quality(selected_df, table_selector)
        
        # Column stats table
        col_stats_df = pd.DataFrame(quality_result["column_stats"])
        
        # Color coding for missing percentage
        def highlight_missing(val):
            if isinstance(val, (int, float)):
                if val > 20:
                    return 'background-color: #ffcccc'
                elif val > 10:
                    return 'background-color: #fff3cd'
            return ''
        
        styled_df = col_stats_df.style.map(
            highlight_missing, 
            subset=[t("dq_missing_percent")]
        )
        st.dataframe(styled_df, use_container_width=True)
        
        # Issues and recommendations
        if quality_result["issues"]:
            st.subheader(t("dq_recommendations"))
            for issue in quality_result["issues"]:
                st.write(issue)
        else:
            st.info(t("dq_no_issues"))
    else:
        st.info("No data available for analysis")

# --- Tab 7: Timeline ---
with tabs[7]:
    st.header(t("timeline_header"))
    
    if not df_qc.empty and 'Start Time' in df_qc.columns and 'End Time' in df_qc.columns:
        # Vessel selector
        vessels = df_qc['Vessel Name'].unique().tolist() if 'Vessel Name' in df_qc.columns else []
        
        if vessels:
            selected_vessel = st.selectbox(t("timeline_vessel_select"), vessels)
            
            # Filter data for selected vessel
            df_timeline = df_qc[df_qc['Vessel Name'] == selected_vessel].copy()
            
            if not df_timeline.empty:
                # Prepare data for Gantt chart - parse time only (HH:MM:SS format)
                # Use today's date as base for timeline visualization
                from datetime import datetime, timedelta
                base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                
                def parse_time_to_datetime(time_str, base=base_date):
                    """Convert HH:MM:SS to datetime for timeline display"""
                    try:
                        if pd.isna(time_str):
                            return None
                        parts = str(time_str).split(':')
                        if len(parts) >= 2:
                            hour = int(parts[0])
                            minute = int(parts[1])
                            return base.replace(hour=hour, minute=minute)
                        return None
                    except:
                        return None
                
                df_timeline['Start DateTime'] = df_timeline['Start Time'].apply(parse_time_to_datetime)
                df_timeline['End DateTime'] = df_timeline['End Time'].apply(parse_time_to_datetime)
                
                # Remove rows with invalid times
                df_timeline = df_timeline.dropna(subset=['Start DateTime', 'End DateTime'])
                
                if not df_timeline.empty:
                    # Create Gantt-style timeline
                    fig_timeline = px.timeline(
                        df_timeline,
                        x_start='Start DateTime',
                        x_end='End DateTime',
                        y='QC No.',
                        color='QC No.',
                        title=f"{t('timeline_gantt_title')} - {selected_vessel}",
                        hover_data=['Total Conts', 'Net working (hrs)'] if 'Total Conts' in df_timeline.columns else None
                    )
                    
                    fig_timeline.update_layout(
                        xaxis_title=t("timeline_operation_start") + " / " + t("timeline_operation_end"),
                        yaxis_title="QC",
                        showlegend=True,
                        height=400,
                        xaxis=dict(tickformat='%H:%M')  # Format x-axis to show HH:MM
                    )
                    
                    st.plotly_chart(fig_timeline, use_container_width=True)
                    
                    # Summary table - format times to HH:MM
                    st.subheader("📋 QC Summary")
                    summary_cols = ['QC No.', 'Start Time', 'End Time', 'Total Conts', 'Net working (hrs)', 'Net moves/h']
                    available_cols = [c for c in summary_cols if c in df_timeline.columns]
                    df_summary = df_timeline[available_cols].copy()
                    # Format time to HH:MM
                    for time_col in ['Start Time', 'End Time']:
                        if time_col in df_summary.columns:
                            df_summary[time_col] = df_summary[time_col].apply(
                                lambda x: x[:5] if isinstance(x, str) and len(x) >= 5 else x
                            )
                    # Format numeric columns
                    format_dict_summary = {}
                    for col in df_summary.columns:
                        if col in ['Net working (hrs)', 'Net moves/h']:
                            format_dict_summary[col] = '{:.1f}'
                    st.dataframe(df_summary.style.format(format_dict_summary, na_rep=''), use_container_width=True)
                else:
                    st.warning(t("timeline_no_data"))
            else:
                st.warning(t("timeline_no_data"))
        else:
            st.info("No vessel data available")
    else:
        st.info(t("timeline_no_data"))

# --- Sidebar: Export Section ---
st.sidebar.markdown("---")
st.sidebar.subheader(t("export_header"))

export_format = st.sidebar.selectbox(
    t("export_format"),
    ["CSV", "Excel"]
)

export_template = st.sidebar.selectbox(
    t("export_template"),
    [t("export_all_tables"), t("export_summary_only")]
)

if st.sidebar.button(t("export_btn")):
    import io
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if export_format == "CSV":
        # Create ZIP with all CSVs
        import zipfile
        
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            if export_template == t("export_all_tables"):
                tables = [
                    ("vessel_summary.csv", df_vessel_raw),
                    ("qc_productivity.csv", df_qc),
                    ("qc_operator_productivity.csv", df_qc_operator),
                    ("delay_details.csv", df_delay),
                    ("container_details.csv", df_container)
                ]
            else:
                tables = [("vessel_summary.csv", df_vessel_raw)]
            
            for filename, df in tables:
                if not df.empty:
                    csv_data = df.to_csv(index=False)
                    zf.writestr(filename, csv_data)
        
        buffer.seek(0)
        st.sidebar.download_button(
            label=f"📥 Download ZIP",
            data=buffer,
            file_name=f"tdr_export_{timestamp}.zip",
            mime="application/zip"
        )
    else:
        # Excel export
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            if export_template == t("export_all_tables"):
                tables = [
                    ("Vessel Summary", df_vessel_raw),
                    ("QC Productivity", df_qc),
                    ("QC Operator", df_qc_operator),
                    ("Delay Details", df_delay),
                    ("Container Details", df_container)
                ]
            else:
                tables = [("Vessel Summary", df_vessel_raw)]
            
            for sheet_name, df in tables:
                if not df.empty:
                    df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        
        buffer.seek(0)
        st.sidebar.download_button(
            label=f"📥 Download Excel",
            data=buffer,
            file_name=f"tdr_export_{timestamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )