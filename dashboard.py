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

# --- Bước 5: Tải dữ liệu và hiển thị phần còn lại của trang ---
# (Toàn bộ phần code còn lại từ đây trở đi giữ nguyên như cũ)

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
df_vessel = load_data(DATA_DIR / "vessel_summary.csv")
df_qc = load_data(DATA_DIR / "qc_productivity.csv")
df_delay = load_data(DATA_DIR / "delay_details.csv")
df_container = load_data(DATA_DIR / "container_details_long.csv")
df_qc_operator = load_data(DATA_DIR / "qc_operator_productivity.csv")

# Xử lý dữ liệu thời gian
if 'Report Date' in df_vessel.columns:
    df_vessel['Report Date'] = pd.to_datetime(df_vessel['Report Date'], errors='coerce')
    df_vessel['YearMonth'] = df_vessel['Report Date'].dt.to_period('M').astype(str)
    df_vessel['Quarter'] = df_vessel['Report Date'].dt.to_period('Q').astype(str)
else:
    st.sidebar.warning(t("report_date_not_found_warning"))

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
    t("tab_container_details")
])


# --- Tab 0: Tổng quan & Theo thời gian ---
with tabs[0]:
    st.header(t("overview_header"))
    col1, col2, col3, col4, col5 = st.columns(5)
    total_vessels = len(df_vessel)
    avg_portstay = df_vessel['Portstay (hrs)'].mean() if 'Portstay (hrs)' in df_vessel.columns else 0.0
    avg_net_working = df_vessel['Net Working (hrs)'].mean() if 'Net Working (hrs)' in df_vessel.columns else 0.0
    avg_net_moves = df_vessel['Vessel Moves/Portstay Hour'].mean() if 'Vessel Moves/Portstay Hour' in df_vessel.columns else 0.0
    total_teus = df_vessel['Grand Total TEUs'].sum() if 'Grand Total TEUs' in df_vessel.columns else 0
    
    col1.metric(t("metric_total_vessels"), f"{total_vessels:,}")
    col2.metric(t("metric_total_teus"), f"{total_teus:,.0f}")
    col3.metric(t("metric_avg_portstay"), f"{avg_portstay:.1f}")
    col4.metric(t("metric_avg_net_working"), f"{avg_net_working:.1f}")
    col5.metric(t("metric_avg_net_moves"), f"{avg_net_moves:.1f}")
    st.markdown("---")

    if not df_vessel.empty:
        st.subheader(t("operator_performance_subheader"))
        # Use available column for operator analysis
        metric_col = 'Net Working (hrs)' if 'Net Working (hrs)' in df_vessel.columns else ('Portstay (hrs)' if 'Portstay (hrs)' in df_vessel.columns else None)
        
        if metric_col:
            avg_by_operator = df_vessel.groupby('Operator')[metric_col].mean().sort_values(ascending=False).reset_index()
            fig = px.bar(avg_by_operator, x='Operator', y=metric_col,
                         title=t("operator_performance_title"),
                         labels={'Operator': t("operator_axis_label"), metric_col: t("moves_per_hour_axis_label")},
                         text_auto='.1f')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("⚠️ Performance metrics (Net Working hrs, Portstay hrs) not available in current dataset")

    if 'Report Date' in df_vessel.columns and 'Portstay (hrs)' in df_vessel.columns:
        st.markdown("---")
        st.header(t("time_analysis_header"))
        
        # Calculate simple time-based analysis using available data
        try:
            df_vessel['Report Date'] = pd.to_datetime(df_vessel['Report Date'], errors='coerce')
            df_vessel['Month'] = df_vessel['Report Date'].dt.to_period('M').astype(str)
            
            monthly_portstay = df_vessel.groupby('Month')['Portstay (hrs)'].mean().reset_index()
            if not monthly_portstay.empty:
                fig_monthly = px.line(monthly_portstay, x='Month', y='Portstay (hrs)',
                                      title=t("monthly_performance_title"), markers=True,
                                      labels={'Month': 'Month', 'Portstay (hrs)': t("moves_per_hour_axis_label")})
                st.plotly_chart(fig_monthly, use_container_width=True)
            else:
                st.info("No monthly data available")
        except Exception as e:
            st.info("⚠️ Time-based analysis requires Report Date column and performance metrics")

# --- Tab 1: Cảnh báo KPI ---
with tabs[1]:
    st.header(t("kpi_warning_header", kpi=KPI_MOVES_PER_HOUR))
    kpi_metric_col = 'Net Working (hrs)' if 'Net Working (hrs)' in df_vessel.columns else ('Portstay (hrs)' if 'Portstay (hrs)' in df_vessel.columns else None)
    
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
                if col in ['Net Working (hrs)', 'Portstay (hrs)', 'Gross Working (hrs)', 'Break Time (hrs)']:
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
            st.dataframe(df_qc)

# --- Tab 3: Năng suất vận hành (QC) ---
with tabs[3]:
    st.header("👨‍🔧 qc_operator")
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