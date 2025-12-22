# app.py
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
        # Gọi lại hàm xử lý chính nếu cần
        from main import auto_process_input_folder
        auto_process_input_folder()
        st.experimental_rerun()

    st.markdown("📥 **Xuất file:**")
    if st.checkbox("Tải về file CSV"):
        st.download_button(
            label="⬇️ Tải xuống container_details.csv",
            data=open(container_csv, 'rb').read(),
            file_name=container_csv.name,
            mime="text/csv"
        )