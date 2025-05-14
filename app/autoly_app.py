"""
autoly_streamlit_ui.py
Streamlit interface for AutoLý – Vietnamese personal background form (Mẫu Sơ yếu lý lịch)
"""
import streamlit as st
from datetime import date
import pandas as pd
from utils import fill_so_yeu_ly_lich
import base64 # For embedding PDF

# 👉 Implement this or adapt to your own PDF‑filling utilities

st.set_page_config(page_title="AutoLý - Form Filler", layout="wide")

st.title("📝 AutoLý – Sơ yếu lý lịch Form Filler")


# ---Initialize session state for PDF bytes ---
# This helps retain the PDF preview if other parts of the app cause a rerun
if 'pdf_bytes_to_display' not in st.session_state:
    st.session_state.pdf_bytes_to_display = None
if 'form_submission_status' not in st.session_state:
    st.session_state.form_submission_status = "" # To store success/error messages

# ========= FORM Column=========
with st.form("syll_form"):
    # I. Thông tin bản thân ---------------------------------------------------
    st.markdown("### I. Thông tin bản thân")

    # 1. Họ & tên + Giới tính
    col_name, col_gender = st.columns([3, 1])
    with col_name:
        full_name = st.text_input("1. Họ và tên (IN HOA)", placeholder="VD: NGUYỄN VĂN A")
    with col_gender:
        gender = st.selectbox("Nam/Nữ", ["", "Nam", "Nữ"], index=0)

    # 2. Họ tên thường dùng
    common_name = st.text_input("2. Họ tên thường dùng", placeholder="VD: Nguyễn Văn A")

    # 3. Ngày sinh
    dob = st.date_input("3. Sinh ngày", value=None, min_value=date(1900, 1, 1),max_value=date.today())

    # 4‑5. Nơi sinh & Nguyên quán
    birth_place = st.text_input("4. Nơi sinh",  placeholder="VD: Hà Nội")
    origin = st.text_input("5. Nguyên quán", placeholder="VD: Hà Nộ (nếu khác)")

    # 6‑7. Hộ khẩu & Chỗ ở hiện nay
    residence = st.text_input("6. Hộ khẩu thường trú", placeholder="VD: Số 1 Phố X, Quận Y, Hà Nội")
    current_address = st.text_input("7. Chỗ ở hiện nay", placeholder="VD: như hộ khẩu / địa chỉ trọ")

    # 8. Điện thoại & Email (cùng hàng)
    col_phone, col_email = st.columns(2)
    with col_phone:
        phone = st.text_input("8a. Số điện thoại", placeholder="VD: 0987654321")
    with col_email:
        email = st.text_input("8b. Email", placeholder="VD: example@gmail.com")

    # 9. Dân tộc & Tôn giáo
    col_eth, col_rel = st.columns(2)
    with col_eth:
        ethnicity = st.text_input("9a. Dân tộc", placeholder="VD: Kinh / Tày / Thái")
    with col_rel:
        religion = st.text_input("9b. Tôn giáo", placeholder="VD: Không / Phật giáo / Thiên chúa giáo")

    # 10. Thành phần gia đình
    family_standing = st.text_input("10. Thành phần gia đình", placeholder="VD: Công nhân / Nông dân / Viên chức")

    # 11. CMND/CCCD – 3 ô trên cùng một hàng
    col_id_num, col_id_date, col_id_place = st.columns([2, 1, 2])
    with col_id_num:
        id_number = st.text_input("11a. Số CMND/CCCD", placeholder="VD: 001234567890")
    with col_id_date:
        id_issue_date = st.date_input("11b. Cấp ngày", value=None, min_value=date(1900, 1, 1) ,max_value=date.today())
    with col_id_place:
        id_issue_place = st.text_input("11c. Nơi cấp", placeholder="VD: Công an Hà Nội")

    # 12. Trình độ chuyên môn (expander)
    with st.expander("12. Trình độ chuyên môn", expanded=False):
        st.markdown("**12.1 Đại học**")
        b_col1, b_col2, b_col3 = st.columns(3)
        with b_col1:
            bachelor_field = st.text_input("Ngành (ĐH)", placeholder="VD: Tin học")
        with b_col2:
            bachelor_major = st.text_input("Chuyên ngành (ĐH)", placeholder="VD: Khoa học dữ liệu")
        with b_col3:
            bachelor_school = st.text_input("Nơi đào tạo (ĐH)", placeholder="VD: ĐH Quốc gia TP.HCM")

        st.markdown("**12.2 Thạc sĩ**")
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            master_field = st.text_input("Ngành (ThS)", placeholder="VD: Công nghệ thông tin / Khoa học máy tính")
        with m_col2:
            master_major = st.text_input("Chuyên ngành (ThS)", placeholder="VD: Trí tuệ nhân tạo / Khoa học máy tính")
        with m_col3:
            master_school = st.text_input("Nơi đào tạo (ThS)", placeholder="VD: ĐH Bách Khoa Hà Nội")

        st.markdown("**12.3 Tiến sĩ**")
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            phd_field = st.text_input("Ngành (TS)", placeholder="VD: Tin học")
        with p_col2:
            phd_major = st.text_input("Chuyên ngành (TS)", placeholder="VD: Trí tuệ nhân tạo")
        with p_col3:
            phd_school = st.text_input("Nơi đào tạo (TS)", placeholder="VD: ĐH Quốc Qia Hà Nội")

    # 13. Ngoại ngữ & Tin học
    col_lang, col_it = st.columns(2)
    with col_lang:
        foreign_language = st.text_input("13a. Trình độ ngoại ngữ", placeholder="VD: IELTS 6.5 / TOEIC 800")
    with col_it:
        it_level = st.text_input("13b. Tin học", placeholder="VD: Thành thạo Word, Excel, PowerPoint")

    # 14. Lý luận chính trị
    politics_level = st.text_input("14. Trình độ lý luận chính trị", placeholder="VD: Chưa học / Sơ cấp")

    # 15‑16. Đoàn & Đảng
    col_doan, col_dang, col_dang_off = st.columns(3)
    with col_doan:
        doan_date = st.date_input("15. Ngày vào Đoàn (VD: 26/3 lớp 10)", value=None, min_value=date(1900, 1, 1), max_value=date.today())
    with col_dang:
        dang_join_date = st.date_input("16a. Ngày vào Đảng (VD: 3/2)", value=None, min_value=date(1900, 1, 1), max_value=date.today())
    with col_dang_off:
        dang_official_date = st.date_input("16b. Ngày chính thức (VD: 3/2)", value=None, min_value=date(1900, 1, 1), max_value=date.today())

    # 17‑18. Cơ quan & Chức vụ
    work_org = st.text_input("17. Cơ quan công tác hiện nay (nếu có)", placeholder="VD: FPT Telecom – Chi nhánh Hà Nội")
    work_position = st.text_input("18. Chức vụ hiện nay (nếu có)", placeholder="VD: Thực tập")

    # 19. Học vị / Danh hiệu
    col_acad_title, col_acad_year = st.columns(2)
    with col_acad_title:
        academic_title = st.text_input("19. Học vị / học hàm / danh hiệu Nhà nước phong tặng", placeholder="VD: Chưa có / Cử nhân / Thạc sĩ")
    with col_acad_year:
        academic_year = st.date_input("Năm nhận", value=None, min_value=date(1900, 1, 1), max_value=date.today())

    # 20‑22. Khen thưởng / Kỷ luật / Sở trường
    awards = st.text_area("20. Khen thưởng", placeholder="VD: Giấy khen học tập tốt")
    discipline = st.text_area("21. Kỷ luật", placeholder="VD: Không / Cảnh cáo / …")
    strengths = st.text_area("22. Sở trường",placeholder="VD: Giao tiếp, Làm việc nhóm, Tin học văn phòng")

    st.markdown("---")

    # II. Quan hệ gia đình
    st.markdown("### II. Quan hệ gia đình")
    family_template = pd.DataFrame({
        "Quan hệ":      pd.Series(dtype="string"),
        "Họ và tên":    pd.Series(dtype="string"),
        "Năm sinh":     pd.Series(dtype="string"),
        "Nghề nghiệp":  pd.Series(dtype="string"),
        "Nơi công tác": pd.Series(dtype="string"),
    })
    family_df = st.data_editor(
        family_template, num_rows="dynamic", key="family_editor", use_container_width=True
    )

    st.markdown("---")

    # III. Quá trình đào tạo
    st.markdown("### III. Quá trình đào tạo, bồi dưỡng")
    edu_template = pd.DataFrame({
        "Từ (tháng/năm)":           pd.Series(dtype="string"),
        "Đến (tháng/năm)":          pd.Series(dtype="string"),
        "Trường / Cơ sở đào tạo":   pd.Series(dtype="string"),
        "Ngành học (viết ngắn)":     pd.Series(dtype="string"),
        "Hình thức (chính quy)":    pd.Series(dtype="string"),
        "Văn bằng / Chứng chỉ":     pd.Series(dtype="string"),
    })
    edu_df = st.data_editor(
        edu_template, num_rows="dynamic", key="edu_editor", use_container_width=True
    )

    st.markdown("---")

    # IV. Quá trình công tác
    st.markdown("### IV. Quá trình công tác")
    work_template = pd.DataFrame({
        "Từ (tháng/năm)":    pd.Series(dtype="string"),
        "Đến (tháng/năm)":   pd.Series(dtype="string"),
        "Đơn vị công tác":   pd.Series(dtype="string"),
        "Chức vụ":          pd.Series(dtype="string"),
    })
    work_df = st.data_editor(
        work_template, num_rows="dynamic", key="work_editor", use_container_width=True
    )
    
    # Submit button -----------------------------------------------------------
    submitted = st.form_submit_button("📄 Tạo PDF")

# ========= END FORM =========

if submitted:
    form_data = {
        "full_name": full_name, "gender": gender, "common_name": common_name, "dob": dob,
        "birth_place": birth_place, "origin": origin, "residence": residence,
        "current_address": current_address if current_address else residence, # Default current_address to residence if empty
        "phone": phone, "email": email, "ethnicity": ethnicity, "religion": religion,
        "family_standing": family_standing, "id_number": id_number,
        "id_issue_date": id_issue_date, "id_issue_place": id_issue_place,
        "bachelor": {"field": bachelor_field, "major": bachelor_major, "school": bachelor_school},
        "master": {"field": master_field, "major": master_major, "school": master_school},
        "phd": {"field": phd_field, "major": phd_major, "school": phd_school},
        "foreign_language": foreign_language, "it_level": it_level, "politics_level": politics_level,
        "doan_date": doan_date, "dang_join_date": dang_join_date, "dang_official_date": dang_official_date,
        "work_org": work_org, "work_position": work_position,
        "academic_title": academic_title, "academic_year": academic_year,
        "awards": awards, "discipline": discipline, "strengths": strengths,
        "family_df": family_df, "edu_df": edu_df, "work_df": work_df
    }

    # Call the utility function to get PDF bytes
    pdf_bytes_result = fill_so_yeu_ly_lich(form_data)

    if pdf_bytes_result:
        st.session_state.pdf_bytes_to_display = pdf_bytes_result
        # For conditional message in PDF column
        st.session_state.form_submission_status = "success"
    else:
        st.session_state.pdf_bytes_to_display = None
        st.session_state.form_submission_status = "error"
        st.error("Không thể tạo file PDF. Vui lòng kiểm tra lại thông tin hoặc file mẫu/font trên server.")

# --- PDF Viewer Section (now below the form) ---
if st.session_state.form_submission_status: # Only show this section if form has been submitted at least once
    st.markdown("---") # Add a separator
    st.header("Bản xem trước PDF")
    
    if st.session_state.form_submission_status == "success" and st.session_state.pdf_bytes_to_display:
        try:
            base64_pdf = base64.b64encode(st.session_state.pdf_bytes_to_display).decode('utf-8')
            pdf_display_html = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="700px" type="application/pdf" style="border: 1px solid #ddd; border-radius: 8px;"></iframe>'
            st.markdown(pdf_display_html, unsafe_allow_html=True)
            
            st.success("PDF đã được tạo thành công!")
            st.download_button(
                label="📥 Tải xuống PDF",
                data=st.session_state.pdf_bytes_to_display,
                file_name="SoYeuLyLich_DaDien.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Lỗi hiển thị PDF: {e}")
            st.write("Không thể hiển thị bản xem trước PDF.")
            st.session_state.form_submission_status = "error_display"
            
    elif st.session_state.form_submission_status == "error":
        # The error message is already shown above after form submission.
        # You could add a small note here if needed, or leave it blank.
        st.info("Do có lỗi trong quá trình tạo PDF, bản xem trước không có sẵn.")
    # No need for an 'else' here to show "Điền thông tin..." as it's always visible above.



