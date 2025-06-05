import re
from datetime import date
from typing import Tuple, List, Optional, Pattern


# Regex patterns
FULL_NAME_PATTERN: Pattern[str] = re.compile(r'^[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴĐÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸ ]+$')
PHONE_PATTERN: Pattern[str] = re.compile(r'^0\d{9}$')
EMAIL_PATTERN: Pattern[str] = re.compile(r'^[^@]+@[^@]+\.[^@]+$')
ID_NUMBER_PATTERN: Pattern[str] = re.compile(r'^(?:\d{9}|\d{12})$')
DATE_MM_YYYY_PATTERN: Pattern[str] = re.compile(r'^(0?[1-9]|1[0-2])/\d{4}$')

class Vl:
    @staticmethod
    def validate_full_name(name_str: Optional[str]) -> Tuple[bool, str]:
        if not name_str or len(name_str.strip()) < 2:
            return False, 'Vui lòng điền đầy đủ tên'
        if not re.match(FULL_NAME_PATTERN, name_str):
            return False, 'Vui lòng điền lại tên viết hoa'
        return True, ''

    @staticmethod
    def validate_gender(gender_str: Optional[str]) -> Tuple[bool, str]:
        if not gender_str:
            return False, 'Vui lòng chọn giới tính'
        return True, ''

    @staticmethod
    def validate_dob(dob_date: Optional[date]) -> Tuple[bool, str]:
        if not dob_date:
            return False, 'Vui lòng điền ngày tháng năm sinh'
        return True, ''
    
    @staticmethod
    def validate_id_number(id_number_str: Optional[str]) -> Tuple[bool, str]:
        if not id_number_str or not id_number_str.strip():
            return False, 'Vui lòng điền CMND/CCCD'
        if not ID_NUMBER_PATTERN.match(id_number_str):
            return False, 'CMND/CCCD không hợp lệ, vui lòng thử lại'
        return True, ''
    
    @staticmethod
    def validate_id_issue_date(issue_date: Optional[date]) -> Tuple[bool, str]:
        """
        Validates the ID issue date.
        Assumes create_field's date_min_max handles future dates and very old dates.
        """
        if issue_date is None:
            return False, 'Vui lòng điền ngày cấp CMND/CCCD.'

        # Because create_field for this input uses date_min_max ending at date.today(),
        # we are guaranteed that issue_date is not in the future if it's not None.
        # Any further specific logic (e.g., must be after DOB, though that's complex) could be added here.
        # For now, simply ensuring a date is provided is the main check,
        # relying on the input component's restrictions for range.
        
        return True, ''
    
    @staticmethod
    def validate_id_issue_place(id_place_str: Optional[str]) -> Tuple[bool, str]: # id_place_str can be None
        if not id_place_str or not id_place_str.strip():
            return False, 'Vui lòng điền nơi cấp CMND/CCCD'
        return True, ''
    
    @staticmethod
    def validate_address(address: Optional[str]) -> Tuple[bool, str]:
        # In testing.py, this is used for 'registered_address' and 'current_address'
        # which are text inputs. The label is 'Địa chỉ hộ khẩu'/'Địa chỉ chỗ ở hiện nay'
        # Assuming it means "required address field".
        if not address:
            return False, 'Vui lòng điền địa chỉ'
        return True, ''
    
    @staticmethod
    def validate_phone(phone_str: Optional[str]) -> Tuple[bool, str]:
        if not phone_str:
            return False, 'Vui lòng điền số điện thoại'
        if not PHONE_PATTERN.match(phone_str.strip()):
            # Assuming phone number must be 10 digits starting with 0
            return False, 'Số điện thoại phải có 10 chữ số, bắt đầu bằng 0 (VD: 0987654321)'
        return True, ''
    
    @staticmethod
    def validate_emergency_contact(emergency_contact_combined: Optional[str]) -> Tuple[bool, str]: # Can be None
        if not emergency_contact_combined or not emergency_contact_combined.strip():
            return False, 'Vui lòng điền thông tin người cần báo tin'
        parts: List[str] = emergency_contact_combined.split(',')
        if len(parts) < 2:
            return False, 'Vui lòng điền đầy đủ người cần báo tin và quan hệ với họ (Họ tên, Quan hệ)'
        
        name: str = parts[0].strip()
        relationship: str = parts[1].strip()

        if not name:
            return False, 'Vui lòng điền họ tên người cần báo tin'
        if not relationship:
            return False, 'Vui lòng điền quan hệ với người cần báo tin'
        return True, ''
    
    @staticmethod
    def validate_emergency_contact_address(address: Optional[str]) -> Tuple[bool, str]: # address can be None
        if not address or not address.strip():
            return False, 'Vui lòng điền địa chỉ báo tin'
        return True, ''
    
    @staticmethod
    def validate_email(email_str: Optional[str]) -> Tuple[bool, str]: # email_str can be None
        if not email_str or not email_str.strip():
            return False, 'Vui lòng điền email'
        if not EMAIL_PATTERN.match(email_str.strip()):
            return False, 'Email không hợp lệ (VD: example@gmail.com)'
        return True, ''
    
    @staticmethod
    def validate_ethnicity(ethnicity_str: Optional[str]) -> Tuple[bool, str]: 
        if not ethnicity_str: # Assuming ethnic_groups_vietnam[0] is ''
            return False, 'Vui lòng chọn dân tộc'
        return True, ''
    
    @staticmethod
    def validate_religion(religion_str: Optional[str]) -> Tuple[bool, str]:
        if not religion_str: # Assuming religion_options[0] is ''
            return False, 'Vui lòng chọn tôn giáo'
        return True, ''
    
    @staticmethod
    def validate_family_standing(family_standing_str: Optional[str]) -> Tuple[bool, str]: # Can be None
        if not family_standing_str or not family_standing_str.strip():
            return False, 'Vui lòng điền thành phần bản thân hiện nay'
        return True, ''
    
    
    @staticmethod
    def validate_politics_level(politics_level_str: Optional[str]) -> Tuple[bool, str]: # Can be None
        if not politics_level_str: # Assuming politics_options[0] is ''
            return False, 'Vui lòng chọn trình độ lý luận chính trị'
        return True, ''
    
    @staticmethod
    def validate_work_position_if_org(
        work_position_str: Optional[str], work_org_str: Optional[str]) -> Tuple[bool, str]: # Args can be None
        work_org_filled: bool = bool(work_org_str and work_org_str.strip())
        work_position_filled: bool = bool(work_position_str and work_position_str.strip())

        if work_org_filled and not work_position_filled:
            return False, 'Vui lòng chọn vị trí hiện nay nếu điền cơ quan công tác'
        return True, ''
    
    @staticmethod
    def validate_academic_year_if_title(
            # academic_year_str is expected to be a year string, e.g., "2023"
            academic_year_str: Optional[str], 
            academic_title_str: Optional[str]
            ) -> Tuple[bool, str]:
        
        title_filled: bool = bool(academic_title_str and academic_title_str.strip())
        year_filled: bool = bool(academic_year_str and academic_year_str.strip())
        if not title_filled and not year_filled:
            return False, 'Vui lòng điền học hàm, học vị hoặc năm nhận'
        
        if year_filled and academic_year_str is not None:
            try:
                year_val: int = int(academic_year_str.strip())
                current_year: int = date.today().year
                if not (1900 <= year_val <= current_year):
                    return False, f'Năm nhận phải từ 1900 đến {current_year}'
            except ValueError:
                return False, 'Năm nhận không hợp lệ'
        return True, ''
    
    @staticmethod
    def validate_choice_made(value_selected: Optional[str]) -> Tuple[bool, str]:
        """
        Validates that a choice has been made (value is not None or empty/whitespace).
        Suitable for mandatory select/radio fields where all options are valid data points.
        """
        if value_selected and value_selected.strip():
            return True, ""
        return False, "Vui lòng thực hiện lựa chọn cho mục này."

    @staticmethod
    def validate_text_input_required(text_value: Optional[str]) -> Tuple[bool, str]:
        """Validates that a text input is not empty or just whitespace."""
        if text_value and text_value.strip():
            return True, ""
        return False, "Vui lòng không để trống trường này."

    @staticmethod
    def validate_date_required(date_value: Optional[date]) -> Tuple[bool, str]:
        """Validates that a date has been selected."""
        if date_value: # Assuming create_field's arg func for date returns date object or None
            return True, ""
        return False, "Vui lòng chọn ngày."
