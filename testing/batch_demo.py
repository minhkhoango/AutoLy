import streamlit as st
import pandas as pd
from io import StringIO

st.title("AutoLý Batch Demo")

st.write("### 1. Tải về mẫu Excel / CSV")
st.write("[Download template CSV](https://raw.githubusercontent.com/minhkhoango/AutoLy/main/demo/autoly_demo.csv)")

st.write("### 2. Upload file hoặc dán từ Excel")

tab1, tab2 = st.tabs(["Upload file", "Dán từ Excel"])

with tab1:
    file = st.file_uploader("Chọn file CSV/Excel", type=["csv", "xlsx"])
    if file is not None:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        st.write("Xem trước dữ liệu:")
        st.dataframe(df)
        # Here: add validation/generate form logic

with tab2:
    raw = st.text_area("Dán dữ liệu từ Excel (cả header):", height=200)
    if st.button("Xem trước dữ liệu"):
        if raw:
            delimiter = "\t" if "\t" in raw else ","
            try:
                df = pd.read_csv(StringIO(raw), delimiter=delimiter)
                st.write("Xem trước dữ liệu:")
                st.dataframe(df)
            except Exception as e:
                st.error(f"Lỗi đọc dữ liệu: {e}")
            # Here: add validation/generate form logic