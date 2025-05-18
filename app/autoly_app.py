"""
autoly_streamlit_ui.py
Streamlit interface for AutoLý – Vietnamese personal background form (Mẫu Sơ yếu lý lịch)
"""
import streamlit as st
from datetime import date
import pandas as pd
from utils import fill_so_yeu_ly_lich
from custom_selectbox import *
import base64 # For embedding PDF
import re

# 👉 Implement this or adapt to your own PDF‑filling utilities

st.set_page_config(page_title="AutoLý - Form Filler", layout="wide")

st.title("📝 AutoLý – Sơ yếu lý lịch Form Filler")


# ---Initialize session state for PDF bytes ---
# This helps retain the PDF preview if other parts of the app cause a rerun
if 'pdf_bytes_to_display' not in st.session_state:
    st.session_state.pdf_bytes_to_display = None
if 'form_submission_status' not in st.session_state:
    st.session_state.form_submission_status = "" # To store success/error messages
if 'form_attempted_submission' not in st.session_state:
    st.session_state.form_attempted_submission = False # after first submission, this flag will be True

# ========= FORM Column=========
with st.form("syll_form"):
    # I. Thông tin bản thân ---------------------------------------------------
    st.markdown("### I. Thông tin bản thân")

    validation_flags = []


    # 1. Họ & tên + Giới tính
    col_name, col_gender = st.columns([3, 1])

    with col_name:
        full_name = st.text_input("1. Họ và tên (IN HOA)", placeholder="VD: NGUYỄN VĂN A")
        full_name_is_valid = True
        
        if len(full_name) < 2:
            if st.session_state.form_attempted_submission:
                st.error(" ⚠️ Vui lòng điền đầy đủ tên")
            full_name_is_valid = False
        elif not re.match(r"^[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴĐÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸ ]+$", full_name):
            st.error(" ⚠️ Vui lòng điền lại tên viết hoa")
            full_name_is_valid = False
        validation_flags.append(full_name_is_valid)
    with col_gender:
        gender = st.selectbox("Nam/Nữ", ["", "Nam", "Nữ"], index=0)
        gender_is_valid = True

        if gender == "":
            if st.session_state.form_attempted_submission:
                st.error(" ⚠️ Vui lòng chọn giới tính")
            gender_is_valid = False
        validation_flags.append(gender_is_valid)


    # 2. Họ tên thường dùng
    common_name = st.text_input("2. Họ tên thường dùng **(tùy chọn)**", placeholder="VD: Nguyễn Văn A")


    # 3. Ngày sinh
    dob = st.date_input("3. Sinh ngày", value=None, min_value=date(1900, 1, 1),max_value=date.today())
    dob_is_valid = True

    if not dob:
        if st.session_state.form_attempted_submission:
            st.error(" ⚠️ Vui lòng điền ngày tháng năm sinh")
        dob_is_valid = False
    validation_flags.append(dob_is_valid)


    # 4‑5. Nơi sinh & Nguyên quán
    birth_place = st.text_input("4. Nơi sinh",  placeholder="VD: Hà Nội")
    origin = st.text_input("5. Nguyên quán", placeholder="VD: Hà Nội (nếu khác)")


    # 6‑7. Hộ khẩu & Chỗ ở hiện nay
    residence = st.text_input("6. Hộ khẩu thường trú", placeholder="VD: Số 1 Phố X, Quận Y, Hà Nội")
    current_address = st.text_input("7. Chỗ ở hiện nay", placeholder="VD: như hộ khẩu / địa chỉ trọ")


    # 8. Điện thoại & Email (cùng hàng) Mandatory
    col_phone, col_email = st.columns(2)

    with col_phone:
        phone = st.text_input("8a. Số điện thoại", placeholder="VD: 0987654321")
        phone_is_valid = True

        if not phone:
            if st.session_state.form_attempted_submission:
                st.error(" ⚠️ Vui lòng điền số điện thoại")
            phone_is_valid = False
        elif not re.match(r"^0\d{9}$", phone):
            st.error(" ⚠️ Số điện thoại phải có 10 chữ số, bắt đầu bằng 0 (VD: 0987654321)")
            phone_is_valid = False
        # else: phone is filled and valid, phone_is_valid remains True
        validation_flags.append(phone_is_valid)

    with col_email:
        email = st.text_input("8b. Email", placeholder="VD: example@gmail.com")
        email_is_valid = True

        if not email:
            if st.session_state.form_attempted_submission:
                st.error(" ⚠️ Vui lòng điền email")
            email_is_valid = False
        elif not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            st.error(" ⚠️ Email không hợp lệ (VD: example@gmail.com)")
            email_is_valid = False
        # else: email is filled and valid, email_is_valid remains True
        validation_flags.append(email_is_valid)


    # 9. Dân tộc & Tôn giáo
    col_eth, col_rel = st.columns(2)
    with col_eth:
        ethnicity = st.selectbox("9a. Dân tộc", ethnic_groups_vietnam)
        ethnicity_is_valid = True
        if ethnicity == "":
            if st.session_state.form_attempted_submission:
                st.error(" ⚠️ Vui lòng chọn dân tộc")
            ethnicity_is_valid = False
    with col_rel:
        religion = st.selectbox("9b. Tôn giáo", religion_options)
        religion_is_valid = True
        other_religion = ""
        if religion == "":
            if st.session_state.form_attempted_submission:
                st.error(" ⚠️ Vui lòng chọn tôn giáo")
            religion_is_valid = False
        elif religion == "Khác (Other – Ghi rõ)":
            other_religion = st.text_input("Vui lòng ghi rõ tôn giáo của bạn")

    # 10. Thành phần gia đình
    family_standing = st.text_input("10. Thành phần gia đình", placeholder="VD: Công nhân / Nông dân / Viên chức")
    family_standing_is_valid = True
    if not family_standing:
        if st.session_state.form_attempted_submission:
            st.error(" ⚠️ Vui lòng điền thành phần gia đình")
        family_standing_is_valid = False
    validation_flags.append(family_standing_is_valid)


    # 11. CMND/CCCD – 3 ô trên cùng một hàng
    col_id_num, col_id_date, col_id_place = st.columns([2, 1, 2])
    with col_id_num:
        id_number = st.text_input("11a. Số CMND/CCCD", placeholder="VD: 001234567890")
        id_number_is_valid = True
        if not id_number:
            if st.session_state.form_attempted_submission:
                st.error(" ⚠️ Vui lòng điền CMND/CCCD")
            id_number_is_valid = False
        elif not re.match(r"^(?:\d{9}|\d{12})$", id_number):
            st.error(" ⚠️ CMND/CCCD không hợp lệ, vui lòng thử lại")
            id_number_is_valid = False
        validation_flags.append(id_number_is_valid)

    with col_id_date:
        id_issue_date = st.date_input("11b. Cấp ngày", value=None, min_value=date(1900, 1, 1) ,max_value=date.today())
        id_issue_date_is_valid = True
        if not id_issue_date:
            if st.session_state.form_attempted_submission:
                st.error(" ⚠️ Vui lòng điền ngày cấp CMND/CCCD")
            id_issue_date_is_valid = False
        validation_flags.append(id_issue_date_is_valid)
            
    with col_id_place:
        id_issue_place = st.text_input("11c. Nơi cấp", placeholder="VD: Công an Hà Nội")
        id_issue_place_is_valid = True
        if not id_issue_place:
            if st.session_state.form_attempted_submission:
                st.error(" ⚠️ Vui lòng điền nơi cấp CMND/CCCD")
            id_issue_place_is_valid = False
        validation_flags.append(id_issue_place_is_valid)
       

    # 12. Trình độ chuyên môn (expander)
    with st.expander("12. Trình độ chuyên môn", expanded=False):
        st.markdown("**12.1 Đại học (tùy chọn)** ")
        b_col1, b_col2, b_col3 = st.columns(3)
        with b_col1:
            bachelor_field = st.text_input("Ngành (ĐH)", placeholder="VD: Tin học")
        with b_col2:
            bachelor_major = st.text_input("Chuyên ngành (ĐH)", placeholder="VD: Khoa học dữ liệu")
        with b_col3:
            bachelor_school = st.text_input("Nơi đào tạo (ĐH)", placeholder="VD: ĐH Quốc gia TP.HCM")

        if bachelor_field and not (bachelor_major and bachelor_school): 
            st.warning("Vui lòng bổ sung chuyên ngành và nơi đào tạo cho bằng cử nhân nếu ghi ngành")

        st.markdown("**12.2 Thạc sĩ (tùy chọn)**")
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            master_field = st.text_input("Ngành (ThS)", placeholder="VD: Công nghệ thông tin / Khoa học máy tính")
        with m_col2:
            master_major = st.text_input("Chuyên ngành (ThS)", placeholder="VD: Trí tuệ nhân tạo / Khoa học máy tính")
        with m_col3:
            master_school = st.text_input("Nơi đào tạo (ThS)", placeholder="VD: ĐH Bách Khoa Hà Nội")

        if master_field and not (master_major and master_school): 
            st.warning("Vui lòng bổ sung chuyên ngành và nơi đào tạo cho bằng thạc sĩ nếu ghi ngành")    

        st.markdown("**12.3 Tiến sĩ (tùy chọn)**")
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            phd_field = st.text_input("Ngành (TS)", placeholder="VD: Tin học")
        with p_col2:
            phd_major = st.text_input("Chuyên ngành (TS)", placeholder="VD: Trí tuệ nhân tạo")
        with p_col3:
            phd_school = st.text_input("Nơi đào tạo (TS)", placeholder="VD: ĐH Quốc Qia Hà Nội")

        if phd_field and not (phd_major and phd_school): 
            st.warning("Vui lòng bổ sung chuyên ngành và nơi đào tạo cho bằng tiến sĩ nếu ghi ngành")


    # 13. Ngoại ngữ & Tin học
    col_lang, col_it = st.columns(2)
    with col_lang:
        foreign_language = st.text_input("13a. Trình độ ngoại ngữ **(tùy chọn)**", 
                                         placeholder="VD: English (IELTS 6.5) / Japanese (N3)")
    with col_it:
        it_level = st.text_input("13b. Tin học **(tùy chọn)**", placeholder="VD: Thành thạo Word, Excel, PowerPoint")


    # 14. Lý luận chính trị
    politics_level = st.selectbox("14. Trình độ lý luận chính trị", politics_options)
    politics_level_is_valid = True
    if politics_level == "":
        if st.session_state.form_attempted_submission:
            st.error(" ⚠️ Vui lòng chọn trình độ lý luận chính trị")
        politics_level_is_valid = False
    validation_flags.append(politics_level_is_valid)


    # 15‑16. Đoàn & Đảng
    col_doan, col_dang, col_dang_off = st.columns(3)
    with col_doan:
        doan_date = st.date_input("15. Ngày vào Đoàn **(tùy chọn)** (VD: 26/3 lớp 10)", 
                                  value=None, min_value=date(1900, 1, 1), max_value=date.today())
    with col_dang:
        dang_join_date = st.date_input("16a. Ngày vào Đảng **(tùy chọn)** (VD: 3/2/2020)", 
                                       value=None, min_value=date(1900, 1, 1), max_value=date.today())
    with col_dang_off:
        dang_official_date = st.date_input("16b. Ngày chính thức **(tùy chọn)** (VD: 3/2/2021)", 
                                           value=None, min_value=date(1900, 1, 1), max_value=date.today())


    # 17‑18. Cơ quan & Chức vụ
    work_org = st.text_input("17. Cơ quan công tác hiện nay **(tùy chọn)**", 
                             placeholder="VD: FPT Telecom – Chi nhánh Hà Nội")
    work_position = st.selectbox("18. Chức vụ hiện nay **(tùy chọn)**", work_position_options)
    if work_org:
        work_position_is_valid = True
        other_work_position = ""
        if work_position == "":
            st.error(" ⚠️ Vui lòng chọn vị trí hiện nay nếu điền cơ quan công tác")
            work_position_is_valid = False
        elif work_position == "Khác (Other – Ghi rõ)":
            other_work_position = st.text_input("Vui lòng ghi rõ chức vụ")
        validation_flags.append(work_position_is_valid)

    # 19. Học vị / Danh hiệu
    col_acad_title, col_acad_year = st.columns(2)
    with col_acad_title:
        academic_title = st.selectbox("19. Học vị / học hàm / danh hiệu Nhà nước phong tặng **(tùy chọn)**", 
                                       awards_titles_options)
        other_academic_title = ""

        if academic_title == "Khác (Other – Ghi rõ)":
            other_academic_title = st.text_input("Vui lòng ghi rõ học vị / học hàm / danh hiệu khác")

    with col_acad_year:
        years = [""] + list(range(date.today().year, 1899, -1))
        academic_year = st.selectbox('Năm nhận', years)

        if academic_title:
            academic_year_is_valid = True
            if academic_year == "":

                st.error(" ⚠️ Vui lòng chọn năm nhận")
                academic_year_is_valid = False
            validation_flags.append(academic_year_is_valid)
            


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

    # Validate family relationships data
    family_valid = True
    if st.session_state.form_attempted_submission and len(family_df) > 0:
        # Check for empty required fields in family data
        for idx, row in family_df.iterrows():
            if pd.isna(row["Quan hệ"]) or row["Quan hệ"].strip() == "":
                st.error(f" ⚠️ Hàng {idx+1}: Quan hệ không được để trống")
                family_valid = False
            
            if pd.isna(row["Họ và tên"]) or row["Họ và tên"].strip() == "":
                st.error(f" ⚠️ Hàng {idx+1}: Họ và tên không được để trống")
                family_valid = False
            
            # Validate year of birth - must be numeric and reasonable
            if not pd.isna(row["Năm sinh"]) and row["Năm sinh"].strip() != "":
                try:
                    birth_year = int(row["Năm sinh"])
                    current_year = date.today().year
                    if birth_year < 1900 or birth_year > current_year:
                        st.error(f" ⚠️ Hàng {idx+1}: Năm sinh phải từ 1900 đến {current_year}")
                        family_valid = False
                except ValueError:
                    st.error(f" ⚠️ Hàng {idx+1}: Năm sinh phải là số")
                    family_valid = False

    validation_flags.append(family_valid)

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

    # Validate education data
    edu_valid = True
    date_pattern = re.compile(r'^(0?[1-9]|1[0-2])/\d{4}$')  # MM/YYYY format

    if st.session_state.form_attempted_submission and len(edu_df) > 0:
        for idx, row in edu_df.iterrows():
            # Check date format and range
            if pd.isna(row["Từ (tháng/năm)"]) or row["Từ (tháng/năm)"].strip() == "":
                st.error(f" ⚠️ Đào tạo {idx+1}: Thời gian bắt đầu không được để trống")
                edu_valid = False
            elif not date_pattern.match(row["Từ (tháng/năm)"]):
                st.error(f" ⚠️ Đào tạo {idx+1}: Thời gian bắt đầu phải theo định dạng MM/YYYY (VD: 09/2015)")
                edu_valid = False
            
            if pd.isna(row["Đến (tháng/năm)"]) or row["Đến (tháng/năm)"].strip() == "":
                st.error(f" ⚠️ Đào tạo {idx+1}: Thời gian kết thúc không được để trống")
                edu_valid = False
            elif not date_pattern.match(row["Đến (tháng/năm)"]):
                st.error(f" ⚠️ Đào tạo {idx+1}: Thời gian kết thúc phải theo định dạng MM/YYYY (VD: 06/2019)")
                edu_valid = False
            
            # Validate start date is before end date
            if not pd.isna(row["Từ (tháng/năm)"]) and not pd.isna(row["Đến (tháng/năm)"]) and \
            date_pattern.match(row["Từ (tháng/năm)"]) and date_pattern.match(row["Đến (tháng/năm)"]):
                start_parts = row["Từ (tháng/năm)"].split('/')
                end_parts = row["Đến (tháng/năm)"].split('/')
                
                start_date = int(start_parts[1]) * 12 + int(start_parts[0])
                end_date = int(end_parts[1]) * 12 + int(end_parts[0])
                
                if start_date > end_date:
                    st.error(f" ⚠️ Đào tạo {idx+1}: Thời gian bắt đầu phải trước thời gian kết thúc")
                    edu_valid = False
            
            # Check school/institution name
            if pd.isna(row["Trường / Cơ sở đào tạo"]) or row["Trường / Cơ sở đào tạo"].strip() == "":
                st.error(f" ⚠️ Đào tạo {idx+1}: Trường/Cơ sở đào tạo không được để trống")
                edu_valid = False
            
            # Check degree/certificate
            if pd.isna(row["Văn bằng / Chứng chỉ"]) or row["Văn bằng / Chứng chỉ"].strip() == "":
                st.error(f" ⚠️ Đào tạo {idx+1}: Văn bằng/Chứng chỉ không được để trống")
                edu_valid = False

    validation_flags.append(edu_valid)

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

    # Validate work history data
    work_valid = True
    if st.session_state.form_attempted_submission and len(work_df) > 0:
        for idx, row in work_df.iterrows():
            # Check date format and range
            if pd.isna(row["Từ (tháng/năm)"]) or row["Từ (tháng/năm)"].strip() == "":
                st.error(f" ⚠️ Công tác {idx+1}: Thời gian bắt đầu không được để trống")
                work_valid = False
            elif not date_pattern.match(row["Từ (tháng/năm)"]):
                st.error(f" ⚠️ Công tác {idx+1}: Thời gian bắt đầu phải theo định dạng MM/YYYY (VD: 09/2015)")
                work_valid = False
            
            # End date can be empty if it's current job
            if not pd.isna(row["Đến (tháng/năm)"]) and row["Đến (tháng/năm)"].strip() != "" and \
            not date_pattern.match(row["Đến (tháng/năm)"]):
                if row["Đến (tháng/năm)"].lower() != "hiện tại" and row["Đến (tháng/năm)"].lower() != "nay":
                    st.error(f" ⚠️ Công tác {idx+1}: Thời gian kết thúc phải để trống, ghi 'Hiện tại', hoặc theo định dạng MM/YYYY")
                    work_valid = False
            
            # Validate start date is before end date
            if not pd.isna(row["Từ (tháng/năm)"]) and not pd.isna(row["Đến (tháng/năm)"]) and \
            date_pattern.match(row["Từ (tháng/năm)"]) and date_pattern.match(row["Đến (tháng/năm)"]):
                start_parts = row["Từ (tháng/năm)"].split('/')
                end_parts = row["Đến (tháng/năm)"].split('/')
                
                start_date = int(start_parts[1]) * 12 + int(start_parts[0])
                end_date = int(end_parts[1]) * 12 + int(end_parts[0])
                
                if start_date > end_date:
                    st.error(f" ⚠️ Công tác {idx+1}: Thời gian bắt đầu phải trước thời gian kết thúc")
                    work_valid = False
            
            # Check organization
            if pd.isna(row["Đơn vị công tác"]) or row["Đơn vị công tác"].strip() == "":
                st.error(f" ⚠️ Công tác {idx+1}: Đơn vị công tác không được để trống")
                work_valid = False
            
            # Check position
            if pd.isna(row["Chức vụ"]) or row["Chức vụ"].strip() == "":
                st.error(f" ⚠️ Công tác {idx+1}: Chức vụ không được để trống")
                work_valid = False

    validation_flags.append(work_valid)

    # Submit button -----------------------------------------------------------
    def mark_submitted():
        st.session_state.form_attempted_submission = True

    submitted = st.form_submit_button("📄 Tạo PDF", on_click=mark_submitted)

# ========= END FORM =========

if submitted:

    # Crucially, set this to True now.
    # On the *next* rerun (which happens immediately as part of this submission process),
    # the form rendering logic above will use this updated state to show mandatory field errors.
    st.session_state.form_attempted_submission = True
    
    # Due to Streamlit's rerun, the validation_flags will contain the validation results for the submitted data.
    all_form_fields_are_valid = all(validation_flags)

    if all_form_fields_are_valid:
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

    else:
        st.error("Vui lòng sửa các lỗi được đánh dấu trong form trước khi tạo PDF.")
        st.session_state.form_submission_status = "validation_error"
        st.session_state.pdf_bytes_to_display = None



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



