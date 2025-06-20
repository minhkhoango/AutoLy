# utils.py
from __future__ import annotations
from nicegui import ui, app
from nicegui.element import Element
from datetime import datetime, date
from typing import Any, NotRequired, TypeAlias, TypedDict, cast
from collections.abc import Callable
from dataclasses import dataclass
import para # Assuming para.py exists and might be used for defaults
from form_data_builder import FORM_TEMPLATE_REGISTRY, FormUseCaseType
from pathlib import Path

# --- Type Aliases ---
ValidationFuncType: TypeAlias = Callable[[Any], tuple[bool, str]]

# --- New Session Key ---
SELECTED_USE_CASE_KEY: str = 'selected_use_case' # <-- Add this new key

# --- ARCHITECTURAL CORE: SINGLE SOURCE OF TRUTH ---
@dataclass(frozen=True)
class FormField:
    """Defines everything about a form field in one place."""
    key: str
    label: str
    ui_type: str = 'text'
    pdf_map: (str | list[str]) | None = None
    options: (list[str] | dict[str, str]) | None = None
    split_date: bool = True
    date_min_max: tuple[(date | None), (date | None)] | None = None
    select_display_key: str | None = None
    select_value_key: str | None = None
    default_value: Any = ''
    pdf_coords: dict[FormUseCaseType, tuple[float, float] | tuple[list[float] | float]] | None = None

class DataframePDFColumn(TypedDict):
    """Defines how to map a single dataframe column """
    key: str # The key from the form's dataframe row (work_task)
    pdf_field_prefix: str # The predfix for the pdf field (work_task_)
    # The magic 
    transformer: NotRequired[Callable[[dict[str, Any]], str]]

# --- APPLICATION SCHEMA DEFINITION ---
# utils.py

# ... (imports and other dataclasses/TypedDicts are unchanged) ...

# --- APPLICATION SCHEMA DEFINITION ---
class AppSchema:
    """
    The single source of truth for the entire application form.
    Defines all fields, their properties, and their mapping to the PDF.
    """
    # NOTE: Coordinates are (X, Y) from the bottom-left of the page.
    # Page 1 Fields
    FULL_NAME = FormField(key='full_name', label='HỌ VÀ TÊN (viết hoa)', 
                          pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (160.0, 725.0)})
    GENDER = FormField(key='gender', label='Giới tính', ui_type='radio', options=['Nam', 'Nữ'], default_value='Nam',
                       pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (490.0, 725.0)})
    DOB = FormField(key='dob', label='Ngày sinh', ui_type='date', default_value=None,
                    pdf_coords={FormUseCaseType.PRIVATE_SECTOR: ([130.0, 180.0, 235.0], 705.0)})
    BIRTH_PLACE = FormField(key='birth_place', label='Nơi sinh', 
                            pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (410.0, 705.0)})
    ID_PASSPORT_NUM = FormField(key='id_passport_num', label='Số CMND/CCCD',
                                pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (150.0, 605.0)})
    ID_PASSPORT_ISSUE_DATE = FormField(key='id_passport_issue_date', label='Ngày cấp', ui_type='date', default_value=None,
                                       pdf_coords={FormUseCaseType.PRIVATE_SECTOR: ([325.0, 355.0, 390.0], 605.0)})
    ID_PASSPORT_ISSUE_PLACE = FormField(key='id_passport_issue_place', label='Nơi cấp',
                                        pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (480.0, 605.0)})
    REGISTERED_ADDRESS = FormField(key='registered_address', label='Địa chỉ hộ khẩu', default_value='',
                                   pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (230.0, 665.0)})
    PHONE = FormField(key='phone', label='Số điện thoại', default_value='',
                      pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (160.0, 645.0)})
    ETHNICITY = FormField(key='ethnicity', label='Dân tộc', ui_type='select', options=getattr(para, 'ethnic_groups_vietnam', ['Kinh']), default_value='Kinh',
                          pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (130.0, 625.0)})
    RELIGION = FormField(key='religion', label='Tôn giáo', ui_type='select', options=getattr(para, 'religion', ['Không']), default_value='Không',
                         pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (380.0, 625.0)})
    PLACE_OF_ORIGIN = FormField(key='place_of_origin', label='Nguyên quán (quê của bố)', default_value='',
                                pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (160.0, 685.0)})
    EDUCATION_HIGH_SCHOOL = FormField(key='education_high_school', label='Lộ trình hoàn thành cấp ba', ui_type='select', options=getattr(para, 'education_high_school', ['12/12']), default_value='12/12',
                                      pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (180.0, 585.0)})
    YOUTH_DATE = FormField(key='youth_date', label='Ngày kết nạp Đoàn', ui_type='date', default_value=None,
                           pdf_coords={FormUseCaseType.PRIVATE_SECTOR: ([225.0, 255.0, 285.0], 565.0)})
    PARTY_DATE = FormField(key='party_date', label='Ngày kết nạp Đảng', ui_type='date', default_value=None,
                           pdf_coords={FormUseCaseType.PRIVATE_SECTOR: ([225.0, 255.0, 285.0], 545.0)})
    AWARD = FormField(key='award', label='Khen thưởng', ui_type='select', options=getattr(para, 'awards_titles', ['Chưa có']), default_value='Chưa có',
                      pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (180.0, 525.0)})
    DISCIPLINE = FormField(key='discipline', label='Kỷ luật', default_value='Không có',
                           # This field shares a line with Award, so it would be drawn over it.
                           # The logic should be to combine these into one string before drawing.
                           # For now, we map it to the same spot.
                           pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (350.0, 525.0)})
    DAD_NAME = FormField(key='dad_name', label='Họ tên Bố', default_value='',
                         pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (160.0, 460.0)})
    DAD_AGE = FormField(key='dad_dob_year', label='Năm sinh Bố', default_value='',
                        pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (490.0, 460.0)})
    DAD_JOB = FormField(key='dad_job', label='Nghề nghiệp Bố', default_value='',
                        # Note: This PDF has separate lines for job, company, address.
                        # Your schema combines them. This coordinate is for the "Nghề nghiệp" line.
                        pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (200.0, 440.0)})
    MOM_NAME = FormField(key='mom_name', label='Họ tên Mẹ', default_value='',
                         pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (160.0, 380.0)})
    MOM_AGE = FormField(key='mom_dob_year', label='Năm sinh Mẹ', default_value='',
                        pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (490.0, 380.0)})
    MOM_JOB = FormField(key='mom_job', label='Nghề nghiệp Mẹ', default_value='',
                        pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (200.0, 360.0)})

    # Page 2 Fields (Dataframes)
    # The coordinate is for the STARTING position of the first row.
    # The rendering function will calculate the position of subsequent rows.
    TRAINING_DATAFRAME = FormField(
        key='training_dataframe', label='Quá trình đào tạo',
        pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (60.0, 680.0)} # Starting coordinate on Page 2
    )
    WORK_DATAFRAME = FormField(
        key='work_dataframe', label='Lịch sử làm việc',
        pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (60.0, 500.0)} # Starting coordinate on Page 2
    )
    
    # --- Fields NOT MAPPED on this PDF template ---
    # These fields from your schema do not have a clear, corresponding place
    # on the provided TEMPLATE-PRIVATE.pdf and are left without coordinates.
    FORM_TEMPLATE_SELECTOR = FormField(key='form_template_selector', label='Tổ chức bạn đang nộp hồ sơ cho:', ui_type='radio')
    FOREIGN_LANGUAGE = FormField(key='foreign_language', label='Ngoại ngữ', default_value='')
    EDUCATION_HIGHEST = FormField(key='education_highest', label='Bằng cấp cao nhất', ui_type='select')
    EDUCATION_MAJOR = FormField(key='education_major', label='Chuyên ngành đào tạo', default_value='')
    EDUCATION_FORMAT = FormField(key='education_format', label='Loại hình đào tạo', ui_type='select')
    SPOUSE_NAME = FormField(key='spouse_name', label='Họ tên Vợ/Chồng', default_value='')
    SPOUSE_AGE = FormField(key='spouse_age', label='Tuổi Vợ/Chồng', default_value='')
    SPOUSE_JOB = FormField(key='spouse_job', label='Nghề nghiệp Vợ/Chồng', default_value='')
    SOCIAL_STANDING = FormField(key='social_standing', label='Thành phần bản thân hiện nay', ui_type='select')
    FAMILY_STANDING = FormField(key='family_standing', label='Thành phần gia đình sau cải cách ruộng đất', ui_type='select')
    CURRENT_SALARY = FormField(key='current_salary', label='Mức lương hiện tại', default_value='')
    DAD_PRE_AUGUST_REVOLUTION = FormField(key='dad_pre_august_revolution', label='Trước CM tháng 8 làm gì? Ở đâu?')
    DAD_DURING_FRENCH_WAR = FormField(key='dad_during_french_war', label='Trong kháng chiến chống Pháp làm gì? Ở đâu?')
    DAD_FROM_1955_PRESENT = FormField(key='dad_from_1955_present', label='Từ 1955 đến nay làm gì? Ở đâu?', ui_type='textarea')
    MOM_PRE_AUGUST_REVOLUTION = FormField(key='mom_pre_august_revolution', label='Trước CM tháng 8 làm gì? Ở đâu?')
    MOM_DURING_FRENCH_WAR = FormField(key='mom_during_french_war', label='Trong kháng chiến chống Pháp làm gì? Ở đâu?')
    MOM_FROM_1955_PRESENT = FormField(key='mom_from_1955_present', label='Từ 1955 đến nay làm gì? Ở đâu?', ui_type='textarea')
    HEALTH = FormField(key='health', label='Tình trạng sức khỏe')
    HEIGHT = FormField(key='height', label='Chiều cao (cm)')
    WEIGHT = FormField(key='weight', label='Cân nặng (kg)')
    JOIN_ARMY_DATE = FormField(key='join_army_date', label='Ngày nhập ngũ', ui_type='date', default_value=None)
    LEAVE_ARMY_DATE = FormField(key='leave_army_date', label='Ngày xuất ngũ', ui_type='date', default_value=None)
    EMERGENCY_CONTACT_DETAILS = FormField(key='emergency_contact', label='Khi cần báo tin cho', default_value='')
    EMERGENCY_CONTACT_PLACE = FormField(key='emergency_place', label='Địa chỉ báo tin')
    SAME_ADDRESS_AS_REGISTERED = FormField(key='same_address_as_registered', label='Nơi báo tin giống địa chỉ hộ khẩu', ui_type='checkbox')
    SIBLING_DATAFRAME = FormField(key='sibling_dataframe', label='Thông tin anh chị em') # Layout is too complex for simple row rendering
    CHILD_DATAFRAME = FormField(key='child_dataframe', label='Thông tin con cái') # No section for this on the PDF

    @classmethod
    def get_all_fields(cls) -> list[FormField]:
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

# Max rows
TRAINING_HISTORY_MAX_ROWS: int = 5
WORK_HISTORY_MAX_ROWS: int = 4
SIBLING_MAX_ROWS: int = 3
CHILD_MAX_ROWS: int = 5

PDF_TEMPLATE_PATH: str | Path = "assets/TEMPLATE-PRIVATE.pdf" # Ensure this path is correct
PDF_FILENAME: str | Path = "SoYeuLyLich_DaDien.pdf"

# --- DECOMPOSED UI CREATION HELPERS ---
def get_form_data() -> dict[str, Any]:
    """Safely retrieves the form_data dictionary from user storage."""
    user_storage = cast(dict[str, Any], app.storage.user)
    if not isinstance(user_storage.get(FORM_DATA_KEY), dict):
        user_storage[FORM_DATA_KEY] = {}
    return cast(dict[str, Any], user_storage[FORM_DATA_KEY])

def _create_text_input(field: FormField, current_value: Any, error_msg: str | None) -> Element:
    return ui.input(
        label=field.label,
        value=str(current_value),
        on_change=lambda e, k=field.key: get_form_data().update({k: e.value})
    ).classes('full-width').props(f"outlined dense")

def _create_select_input(field: FormField, current_value: Any, error_msg: str | None) -> Element:
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

def _create_radio_input(field: FormField, current_value: Any, error_msg: str | None) -> Element:
    """Creates a standard ui.radio element."""
    with ui.column().classes('q-gutter-y-xs'):
        ui.label(field.label).classes('text-caption')
        radio_el = ui.radio(
            options=field.options or [],
            value=str(current_value) if current_value is not None else None,
            on_change=lambda e, k=field.key: get_form_data().update({k: e.value})
        ).props(f"outlined dense")

    return radio_el

def _create_date_input(field: FormField, current_value: Any, error_msg: str | None) -> Element:
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

def _create_textarea_input(field: FormField, current_value: Any, error_msg: str | None) -> Element:
    return ui.textarea(
        label=field.label,
        value=str(current_value),
        on_change=lambda e, k=field.key: get_form_data().update({k: e.value})
    ).classes('full-width').props(f"outlined dense")


def _create_checkbox_input(field: FormField, current_value: Any, error_msg: str | None) -> Element:
    """Creates a checkbox input that properly displays validation errors."""

    with ui.column().classes('q-gutter-y-xs'):
        checkbox = ui.checkbox(
            text=field.label,
            value=bool(current_value),
            on_change=lambda e, k=field.key: get_form_data().update({k: e.value})
        ).props(f"outlined dense")

    return checkbox

def create_field(field_definition: FormField) -> Element:
    """
    Creates a UI element based on a FormField definition.
    This is a dispatcher, delegating to specialized _create_* functions.
    It NO LONGER returns a validator entry.
    """
    user_storage = cast(dict[str, Any], app.storage.user)
    form_data = get_form_data()
    current_value = form_data.get(field_definition.key)

    # Get the error state for this specific field
    form_attempted: bool = user_storage.get(FORM_ATTEMPTED_SUBMISSION_KEY, False)
    current_errors: dict[str, str] = user_storage.get(CURRENT_STEP_ERRORS_KEY, {})
    error_message: str | None = current_errors.get(field_definition.key) if form_attempted else None

    creator_map: dict[str, Callable[[FormField, Any, str | None], Element]] = {
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
    
    element = creator(field_definition, current_value, error_message)
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
    form_data[AppSchema.TRAINING_DATAFRAME.key] = []
    form_data[AppSchema.WORK_DATAFRAME.key] = []
    form_data[AppSchema.SIBLING_DATAFRAME.key] = []
    form_data[AppSchema.CHILD_DATAFRAME.key] = []

# --- PDF Data Mapping Utility ---
def _split_date_for_pdf(date_str: str | None) -> tuple[str, str, str]:
    """Helper to parse a date string (YYYY-MM-DD) and split into d, m, y for PDF."""
    if not date_str:
        return '', '', ''
    try:
        dt_obj = datetime.strptime(date_str, DATE_FORMAT_STORAGE)
        return dt_obj.strftime('%d'), dt_obj.strftime('%m'), dt_obj.strftime('%Y')
    except (ValueError, TypeError):
        return '', '', ''

def _map_dataframe_to_pdf(
    pdf_data: dict[str, Any],
    dataframe: list[dict[str, str]],
    column_map: list[DataframePDFColumn],
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

def generate_pdf_data_mapping() -> dict[str, str]:
    """
    Transforms app data into a PDF-ready dictionary by dynamically
    iterating through the AppSchema. No more hardcoding.
    """
    form_data = get_form_data()
    pdf_data: dict[str, str] = {}

    # 1. Map all simple fields defined in AppSchema
    for field in AppSchema.get_all_fields():
        if not field.pdf_map or field.key not in form_data:
            continue
        
        value = form_data.get(field.key, '')

        if field.ui_type == 'date' and isinstance(field.pdf_map, list) and field.split_date==True:
            day, month, year = _split_date_for_pdf(cast(str | None, value))
            pdf_data[field.pdf_map[0]] = day
            pdf_data[field.pdf_map[1]] = month
            pdf_data[field.pdf_map[2]] = year

        elif isinstance(field.pdf_map, list):
            for pdf_key in field.pdf_map:
                pdf_data[pdf_key] = value
        else: # pdf_map is a string
            pdf_data[field.pdf_map] = value

    # 2. Map the dataframes (training, work, siblings, children)
    _map_dataframe_to_pdf(
        pdf_data=pdf_data,
        dataframe=cast(list[dict[str, str]], form_data.get(AppSchema.TRAINING_DATAFRAME.key, [])),
        column_map=AppSchema.TRAINING_DATAFRAME_PDF_MAPPING,
        max_entries=TRAINING_HISTORY_MAX_ROWS
    )

    _map_dataframe_to_pdf(
        pdf_data=pdf_data,
        dataframe=cast(list[dict[str, str]], form_data.get(AppSchema.WORK_DATAFRAME.key, [])),
        column_map=AppSchema.WORK_DATAFRAME_PDF_MAPPING,
        max_entries=WORK_HISTORY_MAX_ROWS
    )

    _map_dataframe_to_pdf(
        pdf_data=pdf_data,
        dataframe=cast(list[dict[str, str]], form_data.get(AppSchema.SIBLING_DATAFRAME.key, [])),
        column_map=AppSchema.SIBLING_DATAFRAME_PDF_MAPPING,
        max_entries=SIBLING_MAX_ROWS
    )

    _map_dataframe_to_pdf(
        pdf_data=pdf_data,
        dataframe=cast(list[dict[str, str]], form_data.get(AppSchema.CHILD_DATAFRAME.key, [])),
        column_map=AppSchema.CHILD_DATAFRAME_PDF_MAPPING,
        max_entries=CHILD_MAX_ROWS
    )

    return pdf_data