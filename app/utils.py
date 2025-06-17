# utils.py
from __future__ import annotations
from nicegui import ui, app
from nicegui.element import Element
from datetime import datetime, date
from typing import Any, Callable, Dict, List, NotRequired, Optional, Union, Tuple, TypeAlias, TypedDict, cast
from dataclasses import dataclass
import para # Assuming para.py exists and might be used for defaults
from form_data_builder import FORM_TEMPLATE_REGISTRY, FormUseCaseType

# --- Type Aliases ---
ValidationFuncType: TypeAlias = Callable[[Any], Tuple[bool, str]]


# --- New Session Key ---
SELECTED_USE_CASE_KEY: str = 'selected_use_case' # <-- Add this new key

# --- ARCHITECTURAL CORE: SINGLE SOURCE OF TRUTH ---
@dataclass(frozen=True)
class FormField:
    """Defines everything about a form field in one place."""
    key: str
    label: str
    ui_type: str = 'text'
    pdf_map: Optional[Union[str, List[str]]] = None
    options: Optional[Union[List[str], Dict[str, str]]] = None
    split_date: bool = True
    date_min_max: Optional[Tuple[Optional[date], Optional[date]]] = None
    select_display_key: Optional[str] = None
    select_value_key: Optional[str] = None
    default_value: Any = ''

class DataframePDFColumn(TypedDict):
    """Defines how to map a single dataframe column """
    key: str # The key from the form's dataframe row (work_task)
    pdf_field_prefix: str # The predfix for the pdf field (work_task_)
    # The magic 
    transformer: NotRequired[Callable[[Dict[str, Any]], str]]

# --- APPLICATION SCHEMA DEFINITION ---
class AppSchema:
    """
    The single source of truth for the entire application form.
    Defines all fields, their properties, and their mapping to the PDF.
    """
    # Step 1
    FORM_TEMPLATE_SELECTOR = FormField(
        key='form_template_selector', label='Tổ chức bạn đang nộp hồ sơ cho:',
        ui_type='radio', 
        options={use_case.name: template['name'] for use_case, template in FORM_TEMPLATE_REGISTRY.items()},
        default_value=FormUseCaseType.PRIVATE_SECTOR.name
    )

    # Step 2 (Personal Info)
    FULL_NAME = FormField(key='full_name', label='HỌ VÀ TÊN (viết hoa)', pdf_map=['full_name_p1', 'full_name_p2'])
    GENDER = FormField(key='gender', label='Giới tính', ui_type='radio', options=['Nam', 'Nữ'], pdf_map='gender', default_value='Nam')
    DOB = FormField(key='dob', label='Ngày sinh', ui_type='date', pdf_map=['dob_day_p1', 'dob_month_p1', 'dob_year_p1'], 
                    default_value=None, date_min_max=(date(1900, 1, 1), date.today()))
    BIRTH_PLACE = FormField(key='birth_place', label='Nơi sinh', pdf_map='birth_place')

    # Step 3 (Official id)
    ID_PASSPORT_NUM = FormField(key='id_passport_num', label='Số CMND/CCCD', pdf_map='id_number')
    ID_PASSPORT_ISSUE_DATE = FormField(key='id_passport_issue_date', label='Ngày cấp', ui_type='date', pdf_map=['id_issue_day', 'id_issue_month', 'id_issue_year'], 
                                       default_value=None, date_min_max=(date(1900, 1, 1), date.today()))
    ID_PASSPORT_ISSUE_PLACE = FormField(key='id_passport_issue_place', label='Nơi cấp', pdf_map='id_issue_place')

    # Step 4 (contact)
    REGISTERED_ADDRESS = FormField(key='registered_address', label='Địa chỉ hộ khẩu', pdf_map=['registered_address_p1', 'registered_address_p2'], default_value='')
    PHONE = FormField(key='phone', label='Số điện thoại', pdf_map='phone', default_value='')

    # Step 5 (origin_info)
    ETHNICITY = FormField(
        key='ethnicity', label='Dân tộc', ui_type='select',
        options=getattr(para, 'ethnic_groups_vietnam', ['Kinh']),
        pdf_map='ethnicity',
        default_value=getattr(para, 'ethnic_groups_vietnam', ['Không'])[0]
        )
    RELIGION = FormField(
        key='religion', label='Tôn giáo', ui_type='select',
        options=getattr(para, 'religion', ['Không']),
        pdf_map='religion',
        default_value=getattr(para, 'religion', ['Không'])[0]
        ) 
    PLACE_OF_ORIGIN = FormField(key='place_of_origin', label='Nguyên quán (quê của bố)', pdf_map='place_of_origin', default_value='')

    # Step 6 (education)
    FOREIGN_LANGUAGE = FormField(key='foreign_language', label='Ngoại ngữ', pdf_map='foreign_language', default_value='')
    EDUCATION_HIGH_SCHOOL = FormField(key='education_high_school', label='Lộ trình hoàn thành cấp ba', ui_type='select',
                                      options=getattr(para, 'education_high_school', ['12/12']),
                                      pdf_map='education_high_school', 
                                      default_value=getattr(para, 'education_high_school', ['12/12'])[0]
                                      )
    EDUCATION_HIGHEST = FormField(key='education_highest', label='Bằng cấp cao nhất', ui_type='select',
                                  options=getattr(para, 'degrees', ["Không có"]),
                                  pdf_map='education_highest', 
                                  default_value=getattr(para, 'degrees', ["Không có"])[0]
                                  )
    EDUCATION_MAJOR = FormField(key='education_major', label='Chuyên ngành đào tạo', pdf_map='education_major', default_value='')
    EDUCATION_FORMAT = FormField(key='education_format', label='Loại hình đào tạo', ui_type='select',
                                 options=getattr(para, 'education_format', ['Chính quy']),
                                 pdf_map='education_format', 
                                 default_value=getattr(para, 'education_format', ['Chính quy'])[0]
                                 )

    # Step 8 (award)
    AWARD = FormField(key='award', label='Khen thưởng', ui_type='select',
                      options=getattr(para, 'awards_titles', ['Chưa có']),
                      pdf_map='award', 
                      default_value=getattr(para, 'awards_titles', ['Chưa có'])[0]
                      )
    DISCIPLINE = FormField(key='discipline', label='Kỷ luật', pdf_map='discipline', default_value='Không có')

    # Step 9 (basic parents info)
    DAD_NAME = FormField(key='dad_name', label='Họ tên Bố', pdf_map='dad_name', default_value='')
    DAD_AGE = FormField(key='dad_age', label='Tuổi Bố', pdf_map='dad_age', default_value='')
    DAD_JOB = FormField(key='dad_job', label='Nghề nghiệp Bố', pdf_map='dad_job', default_value='')

    MOM_NAME = FormField(key='mom_name', label='Họ tên Mẹ', pdf_map='mom_name', default_value='')
    MOM_AGE = FormField(key='mom_age', label='Tuổi Mẹ', pdf_map='mom_age', default_value='')
    MOM_JOB = FormField(key='mom_job', label='Nghề nghiệp Mẹ', pdf_map='mom_job', default_value='')


    # Step 11 (spouse and kids)
    SPOUSE_NAME = FormField(key='spouse_name', label='Họ tên Vợ/Chồng', pdf_map='spouse_name', default_value='')
    SPOUSE_AGE = FormField(key='spouse_age', label='Tuổi Vợ/Chồng', pdf_map='spouse_age', default_value='')
    SPOUSE_JOB = FormField(key='spouse_job', label='Nghề nghiệp Vợ/Chồng', pdf_map='spouse_job', default_value='')

    CHILD_NAME = FormField(key='child_name', label='Họ tên con', pdf_map='child_name', default_value='')
    CHILD_AGE = FormField(key='child_age', label='Tuổi con', pdf_map='child_age', default_value='')
    CHILD_JOB = FormField(key='child_job', label='Nghề nghiệp con', pdf_map='child_job', default_value='')

    # Step 12 conditional (social standing)
    SOCIAL_STANDING = FormField(key='social_standing', label='Thành phần bản thân hiện nay', ui_type='select',
                                options=getattr(para, 'social_standing', ['Không rõ']),
                                pdf_map='social_standing',
                                default_value=getattr(para, 'social_standing', ['Không rõ'])[0]                
                                )
    FAMILY_STANDING = FormField(key='family_standing', label='Thành phần gia đình sau cải cách ruộng đất', ui_type='select',
                                options=getattr(para, 'family_standing', ['Không rõ']),
                                pdf_map='family_standing',
                                default_value=getattr(para, 'family_standing', ['Không rõ'])[0]
                                )
    
    # --- Step 13: Government Affiliation ---
    YOUTH_DATE = FormField(key='youth_date', label='Ngày kết nạp Đoàn', ui_type='date', 
                           pdf_map=['youth_adm_day', 'youth_adm_month', 'youth_adm_year'], 
                           default_value=None, date_min_max=(date(1900, 1, 1), date.today()),
                            )
    PARTY_DATE = FormField(key='party_date', label='Ngày kết nạp Đảng', ui_type='date', 
                           pdf_map=['party_adm_day', 'party_adm_month', 'party_adm_year'], 
                           default_value=None, date_min_max=(date(1900, 1, 1), date.today()),
                           )
    CURRENT_SALARY = FormField(key='current_salary', label='Mức lương hiện tại', 
                               pdf_map='current_salary', default_value='')

    # --- Step 14: Parent History ---
    DAD_PRE_AUGUST_REVOLUTION = FormField(key='dad_pre_august_revolution', label='Trước CM tháng 8 làm gì? Ở đâu?', default_value='Không rõ')
    DAD_DURING_FRENCH_WAR = FormField(key='dad_during_french_war', label='Trong kháng chiến chống Pháp làm gì? \
                                      Ở đâu?', default_value='Không rõ')
    DAD_FROM_1955_PRESENT = FormField(key='dad_from_1955_present', label='Từ 1955 đến nay làm gì? Ở đâu? \
                                    (Ghi rõ tên cơ quan, xí nghiệp hiện nay đang làm)', ui_type='textarea') # Use textarea

    MOM_PRE_AUGUST_REVOLUTION = FormField(key='mom_pre_august_revolution', label='Trước CM tháng 8 làm gì? Ở đâu?', default_value='Không rõ')
    MOM_DURING_FRENCH_WAR = FormField(key='mom_during_french_war', label='Trong kháng chiến chống Pháp làm gì? \
                                    Ở đâu?', default_value='Không rõ')
    MOM_FROM_1955_PRESENT = FormField(key='mom_from_1955_present', label='Từ 1955 đến nay làm gì? Ở đâu? \
                                    (Ghi rõ tên cơ quan, xí nghiệp hiện nay đang làm)', ui_type='textarea') # Use textarea

    # --- Step 15: Health/Military ---
    HEALTH = FormField(key='health', label='Tình trạng sức khỏe', pdf_map='health')
    HEIGHT = FormField(key='height', label='Chiều cao (cm)', pdf_map='height')
    WEIGHT = FormField(key='weight', label='Cân nặng (kg)', pdf_map='weight')
    JOIN_ARMY_DATE = FormField(key='join_army_date', label='Ngày nhập ngũ', ui_type='date',
                               pdf_map='join_army_date', default_value=None,
                               date_min_max=(date(1900, 1, 1), date.today()), split_date=False)
    LEAVE_ARMY_DATE = FormField(key='leave_army_date', label='Ngày xuất ngũ', ui_type='date',
                                pdf_map='leave_army_date', default_value=None,
                                date_min_max=(date(1900, 1, 1), date.today()), split_date=False)

    # --- Step 16: Emergency Contact ---
    EMERGENCY_CONTACT_DETAILS = FormField(key='emergency_contact', label='Khi cần báo tin cho', 
                                          pdf_map='emergency_contact_details', default_value='')
    
    EMERGENCY_CONTACT_PLACE = FormField(key='emergency_place', label='Địa chỉ báo tin', 
                                        pdf_map='emergency_contact_address')
    SAME_ADDRESS_AS_REGISTERED = FormField(key='same_address_as_registered', label='Nơi báo tin giống địa chỉ hộ khẩu',\
                                           ui_type='checkbox', default_value=False)
    
    # --- DATAFRAME KEYS (for AgGrid-like structures) ---
    # These keys hold list[dict] data
    WORK_DATAFRAME = FormField(key='work_dataframe', label='Lịch sử làm việc')
    SIBLING_DATAFRAME = FormField(key='sibling_dataframe', label='Thông tin anh chị em')
    CHILD_DATAFRAME = FormField(key='child_dataframe', label='Thông tin con cái')


    # --- DATAFRAME-TO-PDF BLUEPRINTS ---
    # This is the new source of truth for mapping the work history dataframe
    WORK_DATAFRAME_PDF_MAPPING: List[DataframePDFColumn] = [
        {
            'key': 'work_from',
            'pdf_field_prefix': 'work_from_to_',
            'transformer': lambda row: f"{row.get('work_from', '')}-{row.get('work_to', '')}"
        },
        {'key': 'work_task', 'pdf_field_prefix': 'work_task_'},
        {'key': 'work_unit', 'pdf_field_prefix': 'work_unit_'},
        {'key': 'work_role', 'pdf_field_prefix': 'work_role_'},
    ]
    SIBLING_DATAFRAME_PDF_MAPPING: List[DataframePDFColumn] = [
        {'key': 'sibling_name',
         'pdf_field_prefix': 'sibling_name_age_job_',
         'transformer': lambda row: (
                f"{row.get('sibling_name', '')} - "
                f"Tuổi: {row.get('sibling_age', '')} - "
                f"Nghề nghiệp: {row.get('sibling_job', '')}"
            )
         },
         {'key': 'sibling_address', 'pdf_field_prefix': 'sibling_address_'},
        #  {'key': 'sibling_political_level', 'pdf_field_prefix': 'sibling_political_level_'},
    ]
    CHILD_DATAFRAME_PDF_MAPPING: List[DataframePDFColumn] = [
        {'key': 'child_name', 'pdf_field_prefix': 'child_name_'},
        {'key': 'child_age', 'pdf_field_prefix': 'child_age_'},
        {'key': 'child_job', 'pdf_field_prefix': 'child_job_'},
    ]

    @classmethod
    def get_all_fields(cls) -> List[FormField]:
        return [
            field for field in cls.__dict__.values()
            if isinstance(field, FormField)
        ]

# --- CENTRALIZED CONSTANTS ---
DATE_FORMAT_STORAGE: str = '%Y-%m-%d'
DATE_FORMAT_DISPLAY: str = '%d/%m/%Y'

# Keys for app.storage.user
STEP_KEY: str = 'step'
FORM_DATA_KEY: str = 'form_data'
NEEDS_CLEARANCE_KEY: str = 'needs_clearance'
FORM_ATTEMPTED_SUBMISSION_KEY: str = 'form_attempted_submission'
CURRENT_STEP_ERRORS_KEY: str = 'current_step_errors'

PDF_TEMPLATE_PATH: str = "assets/TEMPLATE-Arial.pdf" # Ensure this path is correct
PDF_FILENAME: str = "SoYeuLyLich_DaDien.pdf"

# --- DECOMPOSED UI CREATION HELPERS ---
def get_form_data() -> Dict[str, Any]:
    """Safely retrieves the form_data dictionary from user storage."""
    user_storage = cast(Dict[str, Any], app.storage.user)
    if not isinstance(user_storage.get(FORM_DATA_KEY), dict):
        user_storage[FORM_DATA_KEY] = {}
    return cast(Dict[str, Any], user_storage[FORM_DATA_KEY])

def _create_text_input(field: FormField, current_value: Any) -> Element:
    return ui.input(
        label=field.label,
        value=str(current_value),
        on_change=lambda e, k=field.key: get_form_data().update({k: e.value})
    ).classes('full-width').props(f"outlined dense ")

def _create_select_input(field: FormField, current_value: Any) -> Element:
    select_el = ui.select(
        options=field.options or [],
        label=field.label,
        value=current_value,
        on_change=lambda e, k=field.key: get_form_data().update({k: e.value})
    ).classes('full-width').props(f"outlined dense")

    if field.options and isinstance(field.options, list) and len(field.options) > 0 and isinstance(field.options[0], dict):
        if field.select_display_key:
            select_el.props(f"option-label='{field.select_display_key}'")
        if field.select_value_key:
            select_el.props(f"option-value='{field.select_value_key}'")
    return select_el

def _create_radio_input(field: FormField, current_value: Any) -> Element:
    """Creates a standard ui.radio element."""
    # --- DEBUGGING ---
    print(f"Creating radio for key: '{field.key}' with value: {current_value} (type: {type(current_value)}) and options: {field.options}")
    # --- END DEBUGGING ---
    #  
    with ui.column().classes('q-gutter-y-xs'):
        ui.label(field.label).classes('text-caption')
        radio_el = ui.radio(
            options=field.options or [],
            value=str(current_value) if current_value is not None else None,
            on_change=lambda e, k=field.key: get_form_data().update({k: e.value})
        ).props("inline")
    return radio_el

def _create_date_input(field: FormField, current_value: Any) -> Element:
    """
    Creates a robust, 3-field date input (Day, Month, Year) for unambiguous entry.
    This is the most reliable method, avoiding all popup/CSS issues.
    """
    form_data = get_form_data()
    
    # --- State Setup ---
    day_val, month_val, year_val = '', '', ''
    storage_value: str | None = form_data.get(field.key)
    
    # Pre-fill D/M/Y fields if a valid date is already in storage.
    if storage_value:
        try:
            dt_object = datetime.strptime(storage_value, DATE_FORMAT_STORAGE)
            day_val = dt_object.strftime('%d')
            month_val = dt_object.strftime('%m')
            year_val = dt_object.strftime('%Y')
        except (ValueError, TypeError):
            # If storage has bad data, ensure it's cleared.
            form_data[field.key] = None

    # --- UI Component Creation ---
    
    # We create a container row for the three input fields.
    with ui.row().classes('w-full no-wrap items-center').props('align=bottom') as container:
        ui.label(field.label).classes('text-caption col-shrink q-pr-md')
        
        # We need references to each input to read their values.
        day_input = ui.input(placeholder='DD', value=day_val).props('outlined dense style="width: 60px;" max_length=2')
        month_input = ui.input(placeholder='MM', value=month_val).props('outlined dense style="width: 60px;" max_length=2')
        year_input = ui.input(placeholder='YYYY', value=year_val).props('outlined dense style="width: 90px;" max_length=4')


    # --- Synchronization Logic ---
    def sync_date_parts() -> None:
        """Reads the three fields, validates them, and updates the canonical storage value."""
        d: str = day_input.value
        m: str = month_input.value
        y: str = year_input.value
        
        # Only proceed if all fields are filled.
        if d and m and y and d.isdigit() and m.isdigit() and y.isdigit():
            try:
                # Pad day and month for safety
                d_str, m_str = f"{int(d):02d}", f"{int(m):02d}"
                # Validate the date is a real calendar date (e.g., no Feb 30).
                dt_object = datetime.strptime(f'{y}-{m_str}-{d_str}', '%Y-%m-%d')
                        
                # If everything is valid, update the single source of truth.
                form_data[field.key] = dt_object.strftime(DATE_FORMAT_STORAGE)

            except ValueError:
                # The date is invalid (e.g., 30/02/2025). Clear the storage.
                # The required() validator will catch this on submission.
                form_data[field.key] = None
        else:
            # If any field is empty or non-numeric, the date is incomplete.
            form_data[field.key] = None

    # --- Connect Logic to Events ---
    # We sync the data whenever the user changes any of the three fields.
    day_input.on('change', sync_date_parts)
    month_input.on('change', sync_date_parts)
    year_input.on('change', sync_date_parts)

    # Return the main row container.
    return container

def _create_textarea_input(field: FormField, current_value: Any) -> Element:
    return ui.textarea(
        label=field.label,
        value=str(current_value),
        on_change=lambda e, k=field.key: get_form_data().update({k: e.value})
    ).classes('full-width').props(f"outlined dense")

def _create_checkbox_input(field: FormField, current_value: Any) -> Element:
    """Creates a checkbox input that properly displays validation errors."""

    with ui.column().classes('q-gutter-y-xs'):
        checkbox = ui.checkbox(
            text=field.label,
            value=bool(current_value),
            on_change=lambda e, k=field.key: get_form_data().update({k: e.value})
        )
    return checkbox

def create_field(field_definition: FormField) -> Element:
    """
    Creates a UI element based on a FormField definition.
    This is a dispatcher, delegating to specialized _create_* functions.
    It NO LONGER returns a validator entry.
    """
    form_data = get_form_data()
    current_value = form_data.get(field_definition.key)

    creator_map: Dict[str, Callable[[FormField, Any], Element]] = {
        'text': _create_text_input,
        'select': _create_select_input,
        'radio': _create_radio_input,
        'date': _create_date_input,
        'textarea': _create_textarea_input,
        'checkbox': _create_checkbox_input,
    }

    creator = creator_map.get(field_definition.ui_type)
    if not creator:
        raise ValueError(f"Unsupported UI type: {field_definition.ui_type}")
    
    element = creator(field_definition, current_value)
    return element

# --- Helper to initialize form_data structure ---
def initialize_form_data() -> None:
    """Populates form_data with default values from the AppSchema."""
    form_data = get_form_data()
    if form_data: # Don't re-initialize if data already exists
        return
    
    for field in AppSchema.get_all_fields():
        form_data[field.key] = field.default_value
    
    # Initialize dataframe keys to empty lists
    form_data[AppSchema.WORK_DATAFRAME.key] = []
    form_data[AppSchema.SIBLING_DATAFRAME.key] = []
    form_data[AppSchema.CHILD_DATAFRAME.key] = []

# --- PDF Data Mapping Utility ---
def _split_date_for_pdf(date_str: Optional[str]) -> Tuple[str, str, str]:
    """Helper to parse a date string (YYYY-MM-DD) and split into d, m, y for PDF."""
    if not date_str:
        return '', '', ''
    try:
        dt_obj = datetime.strptime(date_str, DATE_FORMAT_STORAGE)
        return dt_obj.strftime('%d'), dt_obj.strftime('%m'), dt_obj.strftime('%Y')
    except (ValueError, TypeError):
        return '', '', ''

def _map_dataframe_to_pdf(
    pdf_data: Dict[str, Any],
    dataframe: List[Dict[str, str]],
    column_map: List[DataframePDFColumn],
    max_entries: int
) -> None:
    """Generic helper to map a list of dicts to indexed PDF fields."""
    for i in range(max_entries):
        pdf_index = i+1
        if i < len(dataframe):
            row_data = dataframe[i]
            for column_rule in column_map:
                pdf_field_name = f"{column_rule['pdf_field_prefix']}{[pdf_index]}"

                if 'transformer' in column_rule:
                    transformer_func = column_rule['transformer']
                    pdf_data[pdf_field_name] = transformer_func(row_data)
                else:
                    pdf_data[pdf_field_name] = row_data.get(column_rule['key'], '')
        else:
            # For rows that don't exist
            for column_rule in column_map:
                pdf_field_name = f"{column_rule['pdf_field_prefix']}{pdf_index}"
                pdf_data[pdf_field_name] = ''

def generate_pdf_data_mapping() -> Dict[str, Any]:
    """
    Transforms app data into a PDF-ready dictionary by dynamically
    iterating through the AppSchema. No more hardcoding.
    """
    form_data = get_form_data()
    pdf_data: Dict[str, Any] = {}

    # 1. Map all simple fields defined in AppSchema
    for field in AppSchema.get_all_fields():
        if not field.pdf_map or field.key not in form_data:
            continue
        
        value = form_data.get(field.key)

        if field.ui_type == 'date' and isinstance(field.pdf_map, list) and field.split_date==True:
            day, month, year = _split_date_for_pdf(cast(Optional[str], value))
            pdf_data[field.pdf_map[0]] = day
            pdf_data[field.pdf_map[1]] = month
            pdf_data[field.pdf_map[2]] = year

        elif isinstance(field.pdf_map, list):
            for pdf_key in field.pdf_map:
                pdf_data[pdf_key] = value
        else: # pdf_map is a string
            pdf_data[field.pdf_map] = value

    # 2. Map the dataframes (work, siblings, children)
    _map_dataframe_to_pdf(
        pdf_data=pdf_data,
        dataframe=cast(List[Dict[str, str]], form_data.get(AppSchema.WORK_DATAFRAME.key, [])),
        column_map=AppSchema.WORK_DATAFRAME_PDF_MAPPING,
        max_entries=5
    )
    
    _map_dataframe_to_pdf(
        pdf_data=pdf_data,
        dataframe=cast(List[Dict[str, str]], form_data.get(AppSchema.SIBLING_DATAFRAME.key, [])),
        column_map=AppSchema.SIBLING_DATAFRAME_PDF_MAPPING,
        max_entries=5
    )
    
    _map_dataframe_to_pdf(
        pdf_data=pdf_data,
        dataframe=cast(List[Dict[str, str]], form_data.get(AppSchema.CHILD_DATAFRAME.key, [])),
        column_map=AppSchema.CHILD_DATAFRAME_PDF_MAPPING,
        max_entries=5
    )

    return pdf_data