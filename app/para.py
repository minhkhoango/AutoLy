from typing import List, Dict

degrees: List[str] = [
    "Không có",
    "Trung học cơ sở",
    "Trung học phổ thông",
    "Trung cấp",
    "Cao đẳng",
    "Đại học (Cử nhân)",
    "Kỹ sư",
    "Dược sĩ đại học",
    "Bác sĩ đa khoa",
    "Thạc sĩ",
    "Tiến sĩ",
    "Tiến sĩ khoa học",
    "Phó giáo sư",
    "Giáo sư",
    "Văn bằng 2"
]

ethnic_groups_vietnam: List[str] = [
    "Kinh",
    "Tày",
    "Thái",
    "Mường",
    "H'Mông",
    "Khmer",
    "Nùng",
    "Hoa",
    "Dao",
    "Gia Rai",
    "Ê Đê",
    "Ba Na",
    "Sán Chay",
    "Cơ Ho",
    "Sán Dìu",
    "Chăm",
    "Hrê",
    "Raglai",
    "Mnông",
    "Xơ Đăng",
    "X'Tiêng",
    "Bru-Vân Kiều",
    "Thổ",
    "Khơ Mú",
    "Cơ Tu",
    "Giáy",
    "Gié Triêng",
    "Tà Ôi",
    "Mạ",
    "Co",
    "Chơ Ro",
    "Xinh Mun",
    "Hà Nhì",
    "Chu Ru",
    "Lào",
    "La Chí",
    "La Ha",
    "Phù Lá",
    "La Hủ",
    "Lự",
    "Lô Lô",
    "Chứt",
    "Mảng",
    "Pà Thẻn",
    "Cờ Lao",
    "Bố Y",
    "Cống",
    "Ngái",
    "Si La",
    "Pu Péo",
    "Brâu",
    "Rơ Măm",
    "Ơ Đu",
    "Người nước ngoài (Foreign)",
    "Không rõ (Unknown)"
]

religion_options: List[str] = [
    "Không",                   # No religion
    "Phật giáo",               # Buddhism
    "Công giáo",               # Catholicism (Roman Catholic)
    "Tin Lành",                # Protestantism/Evangelical
    "Hòa Hảo",                 # Hoa Hao Buddhism
    "Cao Đài",                 # Caodaism
    "Hồi giáo",                # Islam
    "Bửu Sơn Kỳ Hương",        # Buu Son Ky Huong
    "Tịnh độ cư sĩ",            # Pure Land Buddhist Home Practice
    "Phật giáo Tứ Ân Hiếu Nghĩa", # Four Debts of Gratitude Buddhism
    "Phật giáo Nam tông",      # Theravada Buddhism
    "Phật giáo Bắc tông",      # Mahayana Buddhism
    "Minh Sư Đạo",             # Minh Su Religion
    "Minh Lý Đạo",             # Minh Ly Religion
    "Baháʼí",                  # Baháʼí Faith
    "Ấn Độ giáo",              # Hinduism
    "Do Thái giáo",            # Judaism
    "Chăm Bà-la-môn",          # Cham Balamon (Brahmanism)
    "Chăm Islam",              # Cham Islam
    "Khác (Other – Ghi rõ)"    # Other – Please specify
]

politics_options: List[str] = [
    "Chưa học",
    "Sơ cấp",
    "Trung cấp",
    "Cao cấp",
    "Cử nhân"
]

work_position_options: List[str] = [
    "Thực tập",            # Intern
    "Nhân viên",           # Staff/Employee
    "Tổ trưởng",           # Team Leader
    "Phó phòng",           # Deputy Manager
    "Trưởng phòng",        # Manager
    "Trợ lý",              # Assistant
    "Thư ký",              # Secretary
    "Giám sát",            # Supervisor
    "Trưởng nhóm",         # Group Leader
    "Phó giám đốc",        # Deputy Director
    "Giám đốc",            # Director
    "Chủ tịch",            # Chairman
    "Phó chủ tịch",        # Vice Chairman
    "Tổng giám đốc",       # General Director/CEO
    "Phó tổng giám đốc",   # Deputy CEO
    "Cố vấn",              # Advisor
    "Giáo viên",           # Teacher
    "Kỹ sư",               # Engineer
    "Khác (Other – Ghi rõ)"
]

awards_titles_options: List[str] = [                           
    "Chưa có",                    # None / Not yet
    "Cử nhân",                    # Bachelor
    "Kỹ sư",                      # Engineer
    "Bác sĩ",                     # Doctor (Medical)
    "Thạc sĩ",                    # Master
    "Tiến sĩ",                    # PhD/Doctorate
    "Tiến sĩ khoa học",           # Doctor of Science
    "Phó giáo sư",                # Associate Professor
    "Giáo sư",                    # Professor

    # State Honors
    "Nhà giáo ưu tú",             # Distinguished Teacher
    "Nhà giáo nhân dân",          # People's Teacher
    "Nghệ sĩ ưu tú",              # Distinguished Artist
    "Nghệ sĩ nhân dân",           # People's Artist
    "Thầy thuốc ưu tú",           # Distinguished Physician
    "Thầy thuốc nhân dân",        # People's Physician
    "Nhà khoa học ưu tú",         # Distinguished Scientist
    "Nhà khoa học nhân dân",      # People's Scientist
    "Anh hùng Lao động",          # Labor Hero
    "Anh hùng Lực lượng vũ trang",# Armed Forces Hero
    "Chiến sĩ thi đua toàn quốc", # National Emulation Fighter

    # Party/Government Honors
    "Huân chương Lao động",       # Labor Order
    "Huân chương Độc lập",        # Independence Order
    "Huân chương Quân công",      # Military Merit Order
    "Huân chương Chiến công",     # Feat of Arms Order
    "Huân chương Kháng chiến",    # Resistance Order
    "Huân chương Hữu nghị",       # Friendship Order
    "Huân chương Hồ Chí Minh",    # Ho Chi Minh Order

    # Others (Academic, Professional)
    "Giải thưởng Hồ Chí Minh",    # Ho Chi Minh Prize
    "Giải thưởng Nhà nước",       # State Prize
    "Bằng khen của Thủ tướng",    # Prime Minister's Certificate of Merit
    "Bằng khen của Chủ tịch nước",# President's Certificate of Merit
    "Bằng khen của Bộ trưởng",    # Minister's Certificate of Merit
    "Giải thưởng Khoa học & Công nghệ", # Science & Technology Prize
    "Giải thưởng Sáng tạo Khoa học Kỹ thuật", # Science & Technology Innovation Prize
    "Giải thưởng quốc tế",        # International Award

    "Khác (Other – Ghi rõ)"
]

expected_columns: List[str] = [
    # sanity check
    'Họ và tên (Khai sinh, IN HOA)', # Full name (Birth name, ALL CAPS)
    'Ngày sinh (dd/mm/yyyy)',
    'Giới tính (Nam/Nữ)',           # Gender (from first page of old SYLL, usually present)
    'Nơi sinh (Như trong giấy khai sinh)', # Place of birth (As in birth certificate)
    'Nguyên quán (Như trong giấy khai sinh)', # Place of origin
    'Nơi đăng ký thường trú hiện nay (Chi tiết)', # Current permanent residence
    'Dân tộc',
    'Tôn giáo',
    'Số CMND/CCCD hoặc Hộ chiếu',    # ID number (Passport also an option for some contexts)
    # The following are for basic family context often considered essential
    'Bố - Họ và tên',
    'Bố - Tuổi (Hoặc năm sinh yyyy)',
    'Mẹ - Họ và tên',
    'Mẹ - Tuổi (Hoặc năm sinh yyyy)',
]

# --- COLUMN_MAPPING for the new detailed Sơ Yếu Lý Lịch ---
# Keys: Exact user-facing headers from your Excel/CSV template
# Values: Internal keys for your Python processing logic

column_mapping: Dict[str, str] = {
    # --- Thông tin cá nhân (Personal Information) ---
    'Họ và tên (Khai sinh, IN HOA)': 'full_name',
    'Giới tính (Nam/Nữ)': 'gender', # Assuming this field is added/expected
    'Ngày sinh (dd/mm/yyyy)': 'dob', # Your code parses to date object
    'Nơi sinh (Như trong giấy khai sinh)': 'birth_place',
    'Nguyên quán (Như trong giấy khai sinh)': 'origin',
    'Nơi đăng ký thường trú hiện nay (Chi tiết)': 'residence',
    'Dân tộc': 'ethnicity',
    'Tôn giáo': 'religion',
    'Số CMND/CCCD hoặc Hộ chiếu': 'id_passport_num', # More general
    'Ngày cấp CMND/CCCD/Hộ chiếu (dd/mm/yyyy)': 'id_passport_issue_date', # Parses to date
    'Nơi cấp CMND/CCCD/Hộ chiếu (Tên cơ quan)': 'id_passport_issue_place',

    'Số điện thoại liên hệ (Di động)': 'phone', # From simpler SYLL version
    'Khi cần báo tin cho ai (Tên, quan hệ)': 'emergency_contact_name_relation', # From simpler SYLL version
    'Địa chỉ báo tin (Chi tiết)': 'emergency_contact_address_detail', # From simpler SYLL version

    # --- Thành phần gia đình & bản thân (Social/Family Background) ---
    # 'Thành phần gia đình sau CCRĐ/CCTN (Nếu có)': 'family_class_post_land_reform', # CCRĐ: Cải cách ruộng đất, CCTN: Cải tạo công thương nghiệp
    'Thành phần bản thân hiện nay': 'applicant_social_class_current',

    # --- Trình độ (Qualifications) ---
    'Trình độ văn hoá (Lớp mấy/12)': 'general_education_level', # e.g., 12/12
    # 'Ngoại ngữ - Tên & Trình độ (VD: Tiếng Anh B2)': 'foreign_language_level_detail', # Combined name and level
    'Trình độ chuyên môn cao nhất (Tên bằng cấp)': 'highest_qualification_degree_name',
    'Loại hình đào tạo (Chính quy, Tại chức,...)': 'training_mode',
    'Chuyên ngành đào tạo (Tên chuyên ngành)': 'specific_major_name',

    # --- Đảng & Đoàn (Party & Youth Union) ---
    # 'Ngày kết nạp Đảng CSVN (dd/mm/yyyy)': 'party_admission_date', # Parses to date
    # 'Nơi kết nạp Đảng CSVN': 'party_admission_place',
    # 'Ngày vào Đoàn TNCSHCM (dd/mm/yyyy)': 'youth_union_admission_date', # Parses to date
    # 'Nơi vào Đoàn TNCSHCM': 'youth_union_admission_place',

    'Nghề nghiệp hoặc trình độ chuyên môn (Tóm tắt)': 'occupation_or_profession_summary', # This seems different from highest_qualification_degree_name
    # 'Cấp bậc hiện tại (Nếu có)': 'current_rank_grade',
    # 'Lương chính hiện nay (Nếu có)': 'current_main_salary',

    # --- Quân ngũ (Military Service - Nếu có) ---
    # 'Ngày nhập ngũ (dd/mm/yyyy)': 'military_enlistment_date', # Parses to date
    # 'Ngày xuất ngũ (dd/mm/yyyy)': 'military_discharge_date', # Parses to date
    # 'Lý do xuất ngũ': 'military_discharge_reason',

    # --- HOÀN CẢNH GIA ĐÌNH (FAMILY BACKGROUND - PARENTS) ---
    # Bố (Father)
    'Bố - Họ và tên': 'father_full_name',
    'Bố - Tuổi (Hoặc năm sinh yyyy)': 'father_birth_year', # Your code will need to handle age vs year
    'Bố - Nghề nghiệp (Hiện tại hoặc trước khi mất/về hưu)': 'father_occupation_status',
    'Bố - Từ 1955 đến nay: Hoạt động & Nơi ở (Nêu rõ cơ quan/DN hiện tại nếu có)': 'father_post_1955_activity_location_current_org',

    # Mẹ (Mother)
    'Mẹ - Họ và tên': 'mother_full_name',
    'Mẹ - Tuổi (Hoặc năm sinh yyyy)': 'mother_birth_year',
    'Mẹ - Nghề nghiệp (Hiện tại hoặc trước khi mất/về hưu)': 'mother_occupation_status',
    'Mẹ - Từ 1955 đến nay: Hoạt động & Nơi ở (Nêu rõ cơ quan/DN hiện tại nếu có)': 'mother_post_1955_activity_location_current_org',

    # --- ANH CHỊ EM RUỘT (SIBLINGS) - Max N entries, e.g., N=5 ---
    # You'll repeat this block in your Excel for Sibling_1, Sibling_2, ... Sibling_N
    # Example for Sibling 1:
    'AnhChịEmRuột_1_HọTên': 'temp_sibling_1_full_name',
    'AnhChịEmRuột_1_TuổiHoặcNămSinh': 'temp_sibling_1_birth_year',
    'AnhChịEmRuột_1_ChỗỞHiệnNay': 'temp_sibling_1_current_residence',
    'AnhChịEmRuột_1_NghềNghiệp': 'temp_sibling_1_occupation',
    # 'AnhChịEmRuột_1_TrìnhĐộChínhTrị': 'temp_sibling_1_political_level',

    # --- VỢ HOẶC CHỒNG (SPOUSE - Nếu có) ---
    'VợChồng_HọTên': 'spouse_full_name',
    'VợChồng_TuổiHoặcNămSinh': 'spouse_birth_year',
    'VợChồng_NghềNghiệp': 'spouse_occupation',
    'VợChồng_NơiLàmViệcHiệnNay': 'spouse_current_workplace',
    'VợChồng_ChỗỞHiệnNay': 'spouse_current_residence',

    # --- CÁC CON (CHILDREN - Nếu có) - Max M entries, e.g., M=5 ---
    # Example for Child 1:
    'Con_1_HọTên': 'temp_child_1_full_name',
    'Con_1_TuổiHoặcNămSinh': 'temp_child_1_birth_year',
    'Con_1_NghềNghiệpHoặcTrườngHọc': 'temp_child_1_occupation_or_school',
    # ... Repeat for Child_2, Child_3, etc. up to your chosen max ...

    # --- QUÁ TRÌNH HOẠT ĐỘNG CỦA BẢN THÂN (APPLICANT'S ACTIVITY/WORK/EDUCATION HISTORY) - Max P entries ---
    # This table covers both work and potentially further education periods.
    # Example for Activity 1:
    'HoatDong_1_TuThangNam (mm/yyyy)': 'temp_activity_1_from_date', # Parse to date parts
    'HoatDong_1_DenThangNam (mm/yyyy Hiện tại)': 'temp_activity_1_to_date_or_current', # Parse carefully
    'HoatDong_1_NoiDungCongTacHocTap': 'temp_activity_1_task_study_description', # "Làm công tác gì?"
    'HoatDong_1_NoiCongTacHocTap': 'temp_activity_1_place', # "Ở đâu?"
    'HoatDong_1_ChucVu': 'temp_activity_1_position', # "Giữ chức vụ gì?"
    # ... Repeat for HoatDong_2, HoatDong_3, etc. up to your chosen max ...

    # --- KHEN THƯỞNG VÀ KỶ LUẬT (AWARDS AND DISCIPLINE) ---
    'Khen thưởng (Nội dung, cấp quyết định)': 'awards_detail_authority',
    'Kỷ luật (Nội dung, cấp quyết định, hình thức)': 'discipline_detail_authority_form',
}