# app.py
"""
Streamlit Dashboard Entry Point for TDR Processor.

This is a simple dashboard for viewing processed TDR data.
For full dashboard features, use: streamlit run dashboard.py
"""
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="📊 TDR Dashboard", layout="wide")
st.title("🚢 TDR Processor Dashboard")

CSV_FOLDER = Path("outputs/data_csv")
container_csv = CSV_FOLDER / "container_details_long.csv"

if container_csv.exists():
    df_container = pd.read_csv(container_csv)
    st.subheader("🧮 Chi tiết Container")
    st.dataframe(df_container)
else:
    st.warning("⚠️ Không tìm thấy file CSV trong thư mục outputs/data_csv.")

with st.sidebar:
    st.markdown("🔧 **Cập nhật dữ liệu:**")
    if st.button("🔄 Chạy lại xử lý TDR"):
        # Import from core_processor (no GUI dependencies)
        from core_processor import auto_process_input_folder
        with st.spinner("Đang xử lý..."):
            result = auto_process_input_folder()
            if result.get("processed_count", 0) > 0:
                st.success(f"✅ Đã xử lý {result['processed_count']} files")
            else:
                st.info(result.get("message", "Không có file mới"))
        st.rerun()

    st.markdown("📥 **Xuất file:**")
    if container_csv.exists() and st.checkbox("Tải về file CSV"):
        st.download_button(
            label="⬇️ Tải xuống container_details.csv",
            data=open(container_csv, 'rb').read(),
            file_name=container_csv.name,
            mime="text/csv"
        )