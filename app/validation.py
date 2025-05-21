import re
from datetime import date
import pandas as pd

# Regex patterns
FULL_NAME_PATTERN = r'^[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴĐÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸ ]+$'
PHONE_PATTERN = r'^0\d{9}$'
EMAIL_PATTERN = r'^[^@]+@[^@]+\.[^@]+$'
ID_NUMBER_PATTERN = r'^(?:\d{9}|\d{12})$'
DATE_MM_YYYY_PATTERN = r'^(0?[1-9]|1[0-2])/\d{4}$'

# Validation functions
def validate_full_name(name_str: str) -> tuple[bool, str]:
    if not name_str or len(name_str) < 2:
        return False, 'Vui lòng điền đầy đủ tên'
    if not re.match(FULL_NAME_PATTERN, name_str):
        return False, 'Vui lòng điền lại tên viết hoa'
    return True, ''

def validate_gender(gender_str: str) -> tuple[bool, str]:
    if not gender_str:
        return False, 'Vui lòng chọn giới tính'
    return True, ''

def validate_dob(dob_date: date) -> tuple[bool, str]:
    if not dob_date:
        return False, 'Vui lòng điền ngày tháng năm sinh'
    return True, ''

def validate_phone(phone_str: str) -> tuple[bool, str]:
    if not phone_str:
        return False, 'Vui lòng điền số điện thoại'
    if not re.match(PHONE_PATTERN, phone_str):
        return False, 'Số điện thoại phải có 10 chữ số, bắt đầu bằng 0 (VD: 0987654321)'
    return True, ''

def validate_email(email_str: str) -> tuple[bool, str]:
    if not email_str:
        return False, 'Vui lòng điền email'
    if not re.match(EMAIL_PATTERN, email_str):
        return False, 'Email không hợp lệ (VD: example@gmail.com)'
    return True, ''

def validate_ethnicity(ethnicity_str: str) -> tuple[bool, str]:
    if not ethnicity_str: # Assuming ethnic_groups_vietnam[0] is ''
        return False, 'Vui lòng chọn dân tộc'
    return True, ''

def validate_religion(religion_str: str) -> tuple[bool, str]:
    if not religion_str: # Assuming religion_options[0] is ''
        return False, 'Vui lòng chọn tôn giáo'
    return True, ''

def validate_family_standing(family_standing_str: str) -> tuple[bool, str]:
    if not family_standing_str:
        return False, 'Vui lòng điền thành phần gia đình'
    return True, ''

def validate_id_number(id_number_str: str) -> tuple[bool, str]:
    if not id_number_str:
        return False, 'Vui lòng điền CMND/CCCD'
    if not re.match(ID_NUMBER_PATTERN, id_number_str):
        return False, 'CMND/CCCD không hợp lệ, vui lòng thử lại'
    return True, ''

def validate_id_issue_date(id_date: date) -> tuple[bool, str]:
    if not id_date:
        return False, 'Vui lòng điền ngày cấp CMND/CCCD'
    return True, ''

def validate_id_issue_place(id_place_str: str) -> tuple[bool, str]:
    if not id_place_str:
        return False, 'Vui lòng điền nơi cấp CMND/CCCD'
    return True, ''

def validate_politics_level(politics_level_str: str) -> tuple[bool, str]:
    if not politics_level_str: # Assuming politics_options[0] is ''
        return False, 'Vui lòng chọn trình độ lý luận chính trị'
    return True, ''

def validate_work_position_if_org(
        work_position_str: str, work_org_str: str) -> tuple[bool, str]:
    if work_org_str and not work_position_str:
        return False, 'Vui lòng chọn vị trí hiện nay nếu điền cơ quan công tác'
    return True, ''

def validate_academic_year_if_title(
        academic_year_str: str, academic_title_str: str) -> tuple[bool, str]:
    if academic_title_str and not academic_year_str:
        return False, 'Vui lòng chọn năm nhận'
    return True, ''

def validate_family_df(df: pd.DataFrame, form_attempted: bool
                              ) -> tuple[bool, list[str]]:
    family_valid = True
    error_messages = []
    if len(df) == 0:
        if form_attempted:
            error_messages.append('Vui lòng điền Quan hệ gia đình')
        return False, error_messages
    
    for idx, row in df.iterrows():
        if pd.isna(row['Quan hệ']) or str(row['Quan hệ']).strip() == '':
            if form_attempted:
                error_messages.append(
                    f'Hàng {idx+1} (Gia Đình): Quan hệ không được để trống')
            family_valid = False
        if pd.isna(row['Họ và tên']) or str(row['Họ và tên']).strip() == '':
            if form_attempted:
                error_messages.append(f'Hàng {idx+1} (Gia đình): Họ và tên không được để trống')
            family_valid = False
        if not pd.isna(row['Năm sinh']) and str(row['Năm sinh']).strip() != '':
            try:
                birth_year = int(row['Năm sinh'])
                current_year = date.today().year
                if birth_year < 1900 or birth_year > current_year:
                    error_messages.append(f'Hàng {idx+1} (Gia đình): Năm sinh phải từ 1900 đến {current_year}')
                    family_valid = False
            except ValueError:
                error_messages.append(f'Hàng {idx+1} (Gia đình): Năm sinh phải là số')
                family_valid = False
    return family_valid, error_messages
    
def validate_edu_df(df: pd.DataFrame, form_attempted: bool
                                 ) -> tuple[bool, list[str]]:
    edu_valid = True
    error_messages = []
    date_pattern = re.compile(DATE_MM_YYYY_PATTERN)

    if len(df) == 0:
        if form_attempted:
            error_messages.append('Vui lòng điền Quá trình đào tạo, bồi dưỡng')
        return False, error_messages
    
    for idx, row in df.iterrows():
        from_date_str = str(row.get('Từ (tháng/năm)', ''))
        to_date_str = str(row.get('Đến (tháng/năm)', ''))
        school_str = str(row.get('Trường / Cơ sở đào tạo', ''))
        degree_str = str(row.get('Văn bằng / Chứng chỉ', ''))

        if pd.isna(from_date_str) or from_date_str.strip() == '':
            if form_attempted:
                error_messages.append(f'Đào tạo {idx+1}: Thời gian bắt đầu không được để trống')
            edu_valid = False
        elif not date_pattern.match(from_date_str):
            error_messages.append(f'Đào tạo {idx+1}: Thời gian bắt đầu phải theo định dạng MM/YYYY (VD: 09/2015)')
            edu_valid = False
        
        if pd.isna(to_date_str) or to_date_str.strip() == '':
            if form_attempted:
                error_messages.append(f'Đào tạo {idx+1}: Thời gian kết thúc không được để trống')
            edu_valid = False
        elif not date_pattern.match(to_date_str):
            error_messages.append(f'Đào tạo {idx+1}: Thời gian kết thúc phải theo định dạng MM/YYYY (VD: 06/2019)')
            edu_valid = False

        if not pd.isna(from_date_str) and not pd.isna(to_date_str) and \
        date_pattern.match(from_date_str) and date_pattern.match(to_date_str):
            start_parts = from_date_str.split('/')
            end_parts = to_date_str.split('/')
            start_date_val = int(start_parts[1])*12 + int(start_parts[0])
            end_date_val = int(end_parts[1])*12 + int(end_parts[0])
            if start_date_val > end_date_val:
                error_messages.append(f'Công tác {idx+1}: Thời gian bắt đầu phải trước thời gian kết thúc')
                edu_valid = False
        
        if pd.isna(school_str) or school_str.strip() == '':
            if form_attempted:
                error_messages.append(f'Đào tạo {idx+1}: Trường/Cơ sở đào tạo không được để trống')
            edu_valid = False

        if pd.isna(degree_str) or degree_str.strip() == '':
            if form_attempted:
                error_messages.append(f'Đào tạo {idx+1}: Văn bằng/Chứng chỉ không được để trống')
            edu_valid = False
    return edu_valid, error_messages

def validate_work_df(df: pd.DataFrame, form_attempted: bool
                            ) -> tuple[bool, list[str]]:
    work_valid = True
    error_messages = []
    date_pattern = re.compile(DATE_MM_YYYY_PATTERN)

    # Work history is optional, so if df is empty, it's valid.
    if df.empty:
        return True, []

    for idx, row in df.iterrows():
        from_date_str = str(row.get('Từ (tháng/năm)', ''))
        to_date_str = str(row.get('Đến (tháng/năm)', ''))
        org_str = str(row.get('Đơn vị công tác', ''))
        position_str = str(row.get('Chức vụ', ''))

        # All fields are mandatory if a row is added
        if pd.isna(from_date_str) or from_date_str.strip() == '':
            if form_attempted or any(not pd.isna(c) and str(c).strip()!='' for c in [to_date_str, org_str, position_str]): # if any other field in row is filled
                error_messages.append(f'Công tác {idx+1}: Thời gian bắt đầu không được để trống nếu có thông tin khác trong hàng')
                work_valid = False
        elif not date_pattern.match(from_date_str):
            error_messages.append(f'Công tác {idx+1}: Thời gian bắt đầu phải theo định dạng MM/YYYY (VD: 09/2015)')
            work_valid = False

        if not pd.isna(to_date_str) and to_date_str.strip() != '' and \
           to_date_str.lower() not in ['hiện tại', 'nay'] and \
           not date_pattern.match(to_date_str):
            error_messages.append(f"Công tác {idx+1}: Thời gian kết thúc phải để trống, ghi 'Hiện tại', 'Nay', hoặc theo định dạng MM/YYYY")
            work_valid = False
        
        if not (pd.isna(to_date_str) or to_date_str.strip() == '' or to_date_str.lower() in ['hiện tại', 'nay']) and \
           not pd.isna(from_date_str) and date_pattern.match(from_date_str) and date_pattern.match(to_date_str):
            start_parts = from_date_str.split('/')
            end_parts = to_date_str.split('/')
            start_date_val = int(start_parts[1]) * 12 + int(start_parts[0])
            end_date_val = int(end_parts[1]) * 12 + int(end_parts[0])
            if start_date_val > end_date_val:
                error_messages.append(f'Công tác {idx+1}: Thời gian bắt đầu phải trước thời gian kết thúc')
                work_valid = False
        
        if pd.isna(org_str) or org_str.strip() == '':
            if form_attempted or any(not pd.isna(c) and str(c).strip()!='' for c in [from_date_str, to_date_str, position_str]):
                error_messages.append(f'Công tác {idx+1}: Đơn vị công tác không được để trống nếu có thông tin khác trong hàng')
                work_valid = False
        
        if pd.isna(position_str) or position_str.strip() == '':
            if form_attempted or any(not pd.isna(c) and str(c).strip()!='' for c in [from_date_str, to_date_str, org_str]):
                error_messages.append(f'Công tác {idx+1}: Chức vụ không được để trống nếu có thông tin khác trong hàng')
                work_valid = False
                
    return work_valid, error_messages