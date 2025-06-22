# utils.py
from __future__ import annotations
from nicegui import app
from typing import Any, NotRequired, TypedDict, cast
from collections.abc import Callable
from dataclasses import dataclass
import para # Assuming para.py exists and might be used for defaults
from form_data_builder import FormUseCaseType, FORM_TEMPLATE_REGISTRY

# ===================================================================
# 1. CORE DATA STRUCTURES & TYPE ALIASES
# ===================================================================

class PDFColumn(TypedDict):
    """Defines the layout for a single column in a PDF dataframe."""
    key: str        # The key from the form's dataframe row (e.g., 'work_unit')
    x_offset: float # X-coordinate offset from the dataframe's starting X.
    # Optional transformer for complex fields like combining dates
    transformer: NotRequired[Callable[[dict[str, Any]], str]]

@dataclass(frozen=True)
class FormField:
    """Defines everything about a form field in one place."""
    key: str
    label: str
    ui_type: str = 'text'
    options: list[str] | dict[str, str] | None = None
    split_date: bool = True
    default_value: Any = ''

    # The new, powerful PDF rendering metadata
    pdf_coords: dict[FormUseCaseType, tuple[float, float] | tuple[list[float], float]] | None = None
    pdf_columns: list[PDFColumn] | None = None

class DataframePDFColumn(TypedDict):
    """Defines how to map a single dataframe column """
    key: str # The key from the form's dataframe row (work_task)
    pdf_field_prefix: str # The predfix for the pdf field (work_task_)
    # The magic 
    transformer: NotRequired[Callable[[dict[str, Any]], str]]

# ===================================================================
# 2. THE APPLICATION SCHEMA (Single Source of Truth)
# ===================================================================

class AppSchema:
    """
    Defines all fields used in the application. Each field is an instance
    of the FormField dataclass, containing all its necessary metadata.
    """
    # NOTE: Coordinates are (X, Y) from the bottom-left of the page.
    # Page 1 Fields
    FULL_NAME = FormField(key='full_name', label='HỌ VÀ TÊN (viết hoa)',
                          pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (214.52, 179.88)})
    GENDER = FormField(key='gender', label='Giới tính', ui_type='radio', options=['Nam', 'Nữ'], default_value='Nam',
                       pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (436.02, 179.88)})
    DOB = FormField(key='dob', label='Ngày sinh', ui_type='date', default_value=None,
                    pdf_coords={FormUseCaseType.PRIVATE_SECTOR: ([152.52, 202.02, 242.02], 201.5)})
    BIRTH_PLACE = FormField(key='birth_place', label='Nơi sinh', ui_type='select', options=getattr(para, 'vn_province', ['Hà Nội', 'TP. Hồ Chí Minh', 'Thanh Hóa']), 
                            pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (332.06, 201.5)})
    REGISTERED_ADDRESS = FormField(key='registered_address', label='Địa chỉ hộ khẩu',
                                   default_value='Hà Nội', pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (259.06, 244.83)})
    PHONE = FormField(key='phone', label='Số điện thoại',
                      pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (209.06, 287.46)})
    ETHNICITY = FormField(key='ethnicity', label='Dân tộc', ui_type='select', options=getattr(para, 'ethnic_groups_vietnam', ['Kinh']), default_value='Kinh',
                          pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (150.06, 309.56)})
    RELIGION = FormField(key='religion', label='Tôn giáo', ui_type='select', options=getattr(para, 'religion', ['Không']), default_value='Không',
                         pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (312.06, 309.56)})
    EDUCATION_HIGH_SCHOOL = FormField(key='education_high_school', label='Lộ trình hoàn thành cấp ba', ui_type='select', options=getattr(para, 'education_high_school', ['12/12']), default_value='12/12',
                                      pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (202.56, 352.56)})
    AWARD = FormField(key='award', label='Khen thưởng', ui_type='select', options=getattr(para, 'awards_titles', ['Không có']), default_value='Không có',
                      pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (222.06, 417.06)})
    DISCIPLINE = FormField(key='discipline', label='Kỷ luật', default_value='Không có',
                           pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (377.06, 417.06)})

    # Page 2 Fields (Dataframes)
    # The coordinate is for the STARTING position of the first row.
    # The rendering function will calculate the position of subsequent rows.
    TRAINING_DATAFRAME = FormField(
        key='training_dataframe', label='Quá trình đào tạo', ui_type='dataframe',
        pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (62, 234)},
        pdf_columns=[
            PDFColumn(key='training_from', x_offset=0.0,
                      transformer=lambda row: f"{row.get( 'training_from','')} - {row.get('training_to','')}"),
            PDFColumn(key='training_unit', x_offset=72.5),
            PDFColumn(key='training_field', x_offset=208),
            PDFColumn(key='training_format', x_offset=315.8),
            PDFColumn(key='training_certificate', x_offset=402),
        ]
    )
    WORK_DATAFRAME = FormField(
        key='work_dataframe', label='Lịch sử làm việc',ui_type='dataframe',
        pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (62, 414)},
        pdf_columns=[
            PDFColumn(key='work_from', x_offset=0,
                      transformer=lambda row: f"{row.get('work_from','')} - {row.get('work_to','')}"),
            PDFColumn(key='work_unit', x_offset=76.5),
            PDFColumn(key='work_role', x_offset=353),
        ]
    )

    # --- Fields that are in the UI but NOT rendered on this specific PDF ---
    # They have no `pdf_coords` or `pdf_columns`.
    FORM_TEMPLATE_SELECTOR = FormField(key='form_template_selector', label='Tổ chức bạn đang nộp hồ sơ cho:', ui_type='radio',
        options={use_case.name: template['name'] for use_case, template in FORM_TEMPLATE_REGISTRY.items()},
        # Set a valid default value. We'll default to the first one in the registry.
        default_value=next(iter(FORM_TEMPLATE_REGISTRY.keys())).name
    )
    
    ### FIELD NOT USED IN THE PRIVATE-TEMPLATE - ONLY FOCUS ON TEMPLATE-PRIVATE FOR THE MVP ###
    ID_PASSPORT_NUM = FormField(key='id_passport_num', label='Số CMND/CCCD') # Example, assuming not on private cv
    ID_PASSPORT_ISSUE_DATE = FormField(key='id_passport_issue_date', label='Ngày cấp', ui_type='date', default_value=None)
    ID_PASSPORT_ISSUE_PLACE = FormField(key='id_passport_issue_place', label='Nơi cấp')
    PLACE_OF_ORIGIN = FormField(key='place_of_origin', label='Nguyên quán (quê của bố)')
    YOUTH_DATE = FormField(key='youth_date', label='Ngày kết nạp Đoàn', ui_type='date', default_value=None)
    PARTY_DATE = FormField(key='party_date', label='Ngày kết nạp Đảng', ui_type='date', default_value=None)
    DAD_NAME = FormField(key='dad_name', label='Họ tên Bố')
    DAD_AGE = FormField(key='dad_dob_year', label='Năm sinh Bố')
    DAD_JOB = FormField(key='dad_job', label='Nghề nghiệp Bố')
    MOM_NAME = FormField(key='mom_name', label='Họ tên Mẹ')
    MOM_AGE = FormField(key='mom_dob_year', label='Năm sinh Mẹ')
    MOM_JOB = FormField(key='mom_job', label='Nghề nghiệp Mẹ')
    EMERGENCY_CONTACT_DETAILS = FormField(key='emergency_contact', label='Khi cần báo tin cho')
    EMERGENCY_CONTACT_PLACE = FormField(key='emergency_place', label='Địa chỉ báo tin')
    SAME_ADDRESS_AS_REGISTERED = FormField(key='same_address_as_registered', label='Nơi báo tin giống địa chỉ hộ khẩu', ui_type='checkbox')
    SIBLING_DATAFRAME = FormField(key='sibling_dataframe', label='Thông tin anh chị em')
    CHILD_DATAFRAME = FormField(key='child_dataframe', label='Thông tin con cái')
    ### FIELD NOT USED, MAYBE NEEDED LATER ### 

    @classmethod
    def get_all_fields(cls) -> list[FormField]:
        return [
            field_instance for field_instance in cls.__dict__.values()
            if isinstance(field_instance, FormField)
        ]

# ===================================================================
# 3. CENTRALIZED CONSTANTS & SESSION MANAGEMENT
# ===================================================================

# --- Session Storage Keys ---
STEP_KEY: str = 'step'
FORM_DATA_KEY: str = 'form_data'
SELECTED_USE_CASE_KEY: str = 'selected_use_case'
FORM_ATTEMPTED_SUBMISSION_KEY: str = 'form_attempted_submission'
CURRENT_STEP_ERRORS_KEY: str = 'current_step_errors'

# --- Date Formats ---
DATE_FORMAT_STORAGE: str = '%Y-%m-%d'

# ===================================================================
# 4. UI & DATA HELPER FUNCTIONS
# ===================================================================

# --- DECOMPOSED UI CREATION HELPERS ---
def get_form_data() -> dict[str, Any]:
    """Safely retrieves the form_data dictionary from user storage."""
    user_storage = cast(dict[str, Any], app.storage.user)
    if not isinstance(user_storage.get(FORM_DATA_KEY), dict):
        user_storage[FORM_DATA_KEY] = {}
    return cast(dict[str, Any], user_storage[FORM_DATA_KEY])

# --- Helper to initialize form_data structure ---
def initialize_form_data() -> None:
    """Populates form_data with default values from the AppSchema."""
    form_data = get_form_data()
    if form_data: # Don't re-initialize if data already exists
        return
    
    for field in AppSchema.get_all_fields():
        if field.key not in form_data:
            form_data[field.key] = field.default_value
    
    form_data[AppSchema.TRAINING_DATAFRAME.key] = []
    form_data[AppSchema.WORK_DATAFRAME.key] = []
    form_data[AppSchema.CHILD_DATAFRAME.key] = []
    
    