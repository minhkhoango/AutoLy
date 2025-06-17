from typing import List

degrees: List[str] = [
    "Không có",
    "Trung học cơ sở",
    "Trung học phổ thông",
    "Trung cấp",
    "Cao đẳng",
    "Đại học",
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

education_format: List[str] = [
    "Chính quy",
    "Tại chức",
    "Từ xa",
    "Liên thông"
]

education_high_school: List[str] = [
    '12/12',
    '11/12',
    '10/12',
    '9/12',
    '8/12',
    '7/12',
    '6/12',
    '5/12',
    '4/12',
    '3/12',
    '2/12',
    '1/12',
    '0/12',
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

religion: List[str] = [
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

social_standing: List[str] = [
    "Công chức",          # state civil servant
    "Viên chức",          # public-service employee
    "Công nhân",          # industrial/blue-collar worker
    "Nông dân",           # farmer
    "Bộ đội",             # army personnel
    "Công an",            # police/公安
    "Nhân viên",          # salaried staff / office worker
    "Chủ doanh nghiệp",   # business owner
    "Tiểu thương",        # small retailer / trader
    "Thợ thủ công",       # artisan / craft worker
    "Học sinh",           # pupil
    "Sinh viên",          # student
    "Lao động tự do",     # freelance / gig worker
    "Chưa có việc làm",   # currently unemployed
]

family_standing: List[str] = [
    "Nông dân",        # generic farmer (covers đa số rural households)
    "Trung nông",      # middle-income farmer
    "Bần nông",        # poor peasant
    "Cố nông",         # landless peasant
    "Phú nông",        # rich farmer
    "Địa chủ",         # (historic) landlord
    "Công nhân",       # worker family
    "Công chức",       # civil-servant family
    "Viên chức",       # public-service family
    "Dân nghèo",       # low-income labourer family
    "Tiểu thương",     # small-trade family
    "Tiểu chủ",        # small proprietor
    "Tiểu tư sản",     # petty bourgeois
    "Tư sản",          # capitalist / entrepreneur family
]

politics: List[str] = [
    "Chưa học",
    "Sơ cấp",
    "Trung cấp",
    "Cao cấp",
    "Cử nhân"
]

work_position: List[str] = [
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

awards_titles: List[str] = [                           
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
