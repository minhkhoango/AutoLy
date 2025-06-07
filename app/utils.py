# utils.py
from nicegui import ui, app # ui, app not directly used here, but often kept for consistency
from nicegui.element import Element # Not used here, consider removing if not needed by other utils
from nicegui.events import ValueChangeEventArguments # Not used here
from datetime import datetime, date
from typing import Any, Callable, Dict, List, Optional, Union, Tuple, TypeAlias, cast
import para # Assuming para.py exists and might be used for defaults

# --- Type Aliases ---
ValidationFuncType: TypeAlias = Callable[[Any], Tuple[bool, str]]
ValidationArgsFuncType: TypeAlias = Callable[[Dict[str, Any], str], Any]
ValidatorEntryType: TypeAlias = Tuple[str, ValidationFuncType, ValidationArgsFuncType, str]

# --- CENTRALIZED CONSTANTS ---
DATE_FORMAT_NICEGUI: str = '%Y-%m-%d'
DATE_FORMAT_DISPLAY: str = '%d/%m/%Y'

# Keys for app.storage.user
STEP_KEY: str = 'step'
FORM_DATA_KEY: str = 'form_data'
NEED_CLEARANCE_KEY: str = 'need_clearance'
FORM_ATTEMPTED_SUBMISSION_KEY: str = 'form_attempted_submission'
CURRENT_STEP_ERRORS_KEY: str = 'current_step_errors'

# --- Form Data Keys (used within FORM_DATA_KEY dict) ---
# Step 0
STEP0_ANS_KEY: str = 'step0_ans'

# Step 1 (Personal Info)
FULL_NAME_KEY: str = 'full_name'
GENDER_KEY: str = 'gender'
DOB_KEY: str = 'dob' 
ID_PASSPORT_NUM_KEY: str = 'id_passport_num'
ID_PASSPORT_ISSUE_DATE_KEY: str = 'id_passport_issue_date'
ID_PASSPORT_ISSUE_PLACE_KEY: str = 'id_passport_issue_place'
## MENTOR NOTE: Added new app-side keys for health info, which will be needed for the PDF.
HEALTH_KEY: str = 'health'
HEIGHT_KEY: str = 'height'
WEIGHT_KEY: str = 'weight'

# Step 2 (Contact & Address)
REGISTERED_ADDRESS_KEY: str = 'registered_address'
PHONE_KEY: str = 'phone'
EMERGENCY_CONTACT_COMBINED_KEY: str = 'emergency_contact_combined'
EMERGENCY_PLACE_KEY: str = 'emergency_place'
SAME_ADDRESS1_KEY: str = 'same_address1' 

# Step 3 (Education & Work)
EDUCATION_HIGHEST_KEY: str = 'highest_education'
EDUCATION_MAJOR_KEY: str = 'specialized_area'
WORK_DF_KEY: str = 'work_df' 

# Keys for individual entries within the WORK_DF_KEY list
WORK_FROM_DATE_KEY: str = "Từ (tháng/năm)"
WORK_TO_DATE_KEY: str = "Đến (tháng/năm)"
WORK_TASK_KEY: str = "Nhiệm vụ công tác" 
WORK_UNIT_KEY: str = "Đơn vị công tác"
WORK_ROLE_KEY: str = "Chức vụ"

# Step 4 (Clearance & Family Info)
PARTY_MEMBERSHIP_KEY: str = 'party_membership'
PARTY_DATE_KEY: str = 'party_date'
YOUTH_MEMBERSHIP_KEY: str = 'youth_membership'
YOUTH_DATE_KEY: str = 'youth_date'
ETHNICITY_KEY: str = 'ethnicity' 
RELIGION_KEY: str = 'religion'   

## MENTOR NOTE: Added specific keys for family members. This is more robust than a generic 'family_involvement'.
# You will need to build UI elements in your steps to capture this data.
DAD_NAME_KEY: str = 'dad_name'
DAD_AGE_KEY: str = 'dad_age'
DAD_JOB_KEY: str = 'dad_job'
MOM_NAME_KEY: str = 'mom_name'
MOM_AGE_KEY: str = 'mom_age'
MOM_JOB_KEY: str = 'mom_job'
SIBLINGS_KEY: str = 'siblings_list' # List of dicts: {'name_age': '...', 'job': '...'}
SPOUSE_NAME_KEY: str = 'spouse_name'
SPOUSE_AGE_KEY: str = 'spouse_age'
SPOUSE_JOB_KEY: str = 'spouse_job'
CHILDREN_KEY: str = 'children_list' # List of dicts: {'name': '...', 'age': '...'}

# --- PDF Field Name Constants (for data_for_pdf keys) ---
## MENTOR NOTE: Using your new, cleaner key structure without the '_pdf' suffix and with P1/P2 for duplicates.
PDF_FULL_NAME_P1_KEY: str = 'full_name_p1' 
PDF_FULL_NAME_P2_KEY: str = 'full_name_p2' 
PDF_GENDER_KEY: str = 'gender'

PDF_DOB_DAY_P1_KEY:str = 'dob_day_p1'
PDF_DOB_MONTH_P1_KEY: str = 'dob_month_p1'
PDF_DOB_YEAR_P1_KEY:str = 'dob_year_p1'
PDF_DOB_DAY_P2_KEY:str = 'dob_day_p2'
PDF_DOB_MONTH_P2_KEY: str = 'dob_month_p2'
PDF_DOB_YEAR_P2_KEY:str = 'dob_year_p2'

PDF_REGISTERED_ADDRESS_P1_KEY: str = 'registered_address_p1'
PDF_REGISTERED_ADDRESS_P2_KEY: str = 'registered_address_p2'

PDF_ID_NUM_KEY: str = 'id_number'
PDF_ID_ISSUE_DAY_KEY: str = 'id_issue_day'
PDF_ID_ISSUE_MONTH_KEY: str = 'id_issue_month'
PDF_ID_ISSUE_YEAR_KEY: str = 'id_issue_year'
PDF_ID_ISSUE_PLACE_KEY: str = 'id_issue_place'

PDF_PHONE_MOBILE_KEY: str = 'phone_mobile'
PDF_EMERGENCY_CONTACT_DETAILS_KEY: str = 'emergency_contact_details'
PDF_EMERGENCY_CONTACT_ADDRESS_KEY: str = 'emergency_contact_address'

PDF_ETHNICITY_KEY: str = 'ethnicity'
PDF_RELIGION_KEY: str = 'religion'

PDF_HIGHEST_EDUCATION_KEY: str = 'highest_education'
PDF_SPECIALIZED_AREA_KEY: str = 'specialized_area'

PDF_YOUTH_ADM_DAY_KEY: str = 'youth_adm_day'
PDF_YOUTH_ADM_MONTH_KEY: str = 'youth_adm_month'
PDF_YOUTH_ADM_YEAR_KEY: str = 'youth_adm_year'
PDF_PARTY_ADM_DAY_KEY: str = 'party_adm_day'
PDF_PARTY_ADM_MONTH_KEY: str = 'party_adm_month'
PDF_PARTY_ADM_YEAR_KEY: str = 'party_adm_year'

PDF_HEALTH_KEY: str = 'health'
PDF_HEIGHT_KEY: str = 'height'
PDF_WEIGHT_KEY: str = 'weight'

PDF_DAD_NAME_KEY: str = 'dad_name'
PDF_DAD_AGE_KEY: str = 'dad_age'
PDF_DAD_JOB_KEY: str = 'dad_job'

PDF_MOM_NAME_KEY: str = 'mom_name'
PDF_MOM_AGE_KEY: str = 'mom_age'
PDF_MOM_JOB_KEY: str = 'mom_job'

PDF_SIBLING_INFO_KEY: str = 'sibling_info_' # Note the trailing underscore for looping

PDF_SPOUSE_NAME_KEY: str = 'spouse_name'
PDF_SPOUSE_AGE_KEY: str = 'spouse_age'
PDF_SPOUSE_JOB_KEY: str = 'spouse_job'

PDF_CHILD_NAME_KEY: str = 'child_name_' # Note the trailing underscore
PDF_CHILD_AGE_KEY: str = 'child_age_' # Note the trailing underscore
PDF_CHILD_JOB_KEY: str = 'child_job_' # Note the trailing underscore

PDF_WORK_FROM_TO_KEY: str = 'work_from_to_'
PDF_WORK_TASK_KEY: str = 'work_task_'
PDF_WORK_UNIT_KEY: str = 'work_unit_'
PDF_WORK_ROLE_KEY: str = 'work_role_'

# Default options if not found in para.py
ETHNIC_OPTIONS_DEFAULT_FOR_INIT: List[str] = ["Kinh", "Tày", "Thái", "Mường", "Khác"]
RELIGION_OPTIONS_DEFAULT_FOR_INIT: List[str] = ["Không", "Phật giáo", "Công giáo", "Khác"]

PDF_TEMPLATE_PATH: str = "assets/Mau-so-yeu-ly-lich-TEMPLATE.pdf" # Ensure this path is correct
PDF_FILENAME: str = "SoYeuLyLich_DaDien.pdf"

# --- Global Helper Function: create_field ---
def create_field(
    label_text: str,
    storage_key: str,
    validation_func: ValidationFuncType,
    input_type: str = 'text',
    options: Optional[Union[List[Any], Dict[Any, Any]]] = None,
    date_min_max: Optional[Tuple[Optional[date], Optional[date]]] = None,
    select_display_key: Optional[str] = None,
    select_value_key: Optional[str] = None,
    error_message_for_field: Optional[str] = None,
    form_attempted: bool = False,
) -> Tuple[Optional[Element], ValidatorEntryType]:
    user_storage = cast(Dict[str, Any], app.storage.user)
    if FORM_DATA_KEY not in user_storage or not isinstance(user_storage.get(FORM_DATA_KEY), dict):
        user_storage[FORM_DATA_KEY] = {} # Should be initialized elsewhere, but safeguard

    form_data_dict: Dict[str, Any] = cast(Dict[str, Any], user_storage[FORM_DATA_KEY])

    default_value: Any = None
    if input_type == 'select':
        if options:
            if isinstance(options, list) and options:
                first_option: Any = options[0] # Can be str or dict
                if isinstance(first_option, dict) and select_value_key:
                    default_value = cast(Dict[str, Any],first_option).get(select_value_key)
                else:
                    default_value = cast(str, first_option) # Assumes first_option is a valid value type (e.g. str)
            elif isinstance(options, dict) and options: # options is Dict[value, label]
                default_value = next(iter(options.keys()), None)
        # If options is empty or None, default_value remains None (or whatever it was before)
    elif input_type == 'date':
        default_value = None # Dates are typically None or a specific date string
    elif input_type == 'radio':
        if isinstance(options, dict) and options: # options is Dict[value, label]
            default_value = next(iter(options.keys()), None)
        elif isinstance(options, list) and options: # options is List[value] or List[Dict]
            first_radio_option: Any = options[0]
            if isinstance(first_radio_option, dict) and select_value_key: # if options = List[Dict]
                 default_value = cast(Dict[str, Any], first_radio_option).get(select_value_key)
            else: # if options = List[value]
                default_value = cast(str, first_radio_option)
    else: # text input
        default_value = ''

    current_value: Any = form_data_dict.get(storage_key)
    if current_value is None and storage_key not in form_data_dict: # Only use default if key truly absent
        current_value = default_value
    has_error_val: bool = form_attempted and bool(error_message_for_field)
    actual_error_message: str = error_message_for_field or ''

    el: Optional[Element] = None
    with ui.column().classes('q-mb-sm full-width'): # Changed from q_mb_sm to q-mb-sm
        if input_type == 'date':
            date_value_from_storage: Any = current_value # Already retrieved with default handling
            displayed_value_in_input: str = ''
            value_for_datepicker: Optional[str] = None # Expects 'YYYY-MM-DD'
            dt_obj_intermediate: Optional[Union[date, datetime]] = None

            if isinstance(date_value_from_storage, str): # Assume it's 'YYYY-MM-DD' if string
                try:
                    # Parse using DATE_FORMAT_NICEGUI for consistency with how it's stored
                    dt_obj_intermediate = datetime.strptime(date_value_from_storage, DATE_FORMAT_NICEGUI)
                    value_for_datepicker = date_value_from_storage # Already in correct format
                except ValueError:
                    # If it's a string but not in 'YYYY-MM-DD', it might be an invalid manual entry
                    # or a different format. For display, show as is. Datepicker might not pick it up.
                    displayed_value_in_input = date_value_from_storage
            elif isinstance(date_value_from_storage, datetime):
                dt_obj_intermediate = date_value_from_storage
                value_for_datepicker = dt_obj_intermediate.strftime(DATE_FORMAT_NICEGUI)
            elif isinstance(date_value_from_storage, date):
                dt_obj_intermediate = date_value_from_storage
                value_for_datepicker = dt_obj_intermediate.strftime(DATE_FORMAT_NICEGUI)

            # If successfully parsed, format for display
            if dt_obj_intermediate:
                displayed_value_in_input = dt_obj_intermediate.strftime(DATE_FORMAT_DISPLAY)


            ui.label(label_text).classes('text-caption q-mb-xs')
            date_input_element: ui.input = ui.input(value=displayed_value_in_input) \
                .props(f"readonly clearable outlined dense error-message='{actual_error_message}' error={has_error_val}").classes('full-width')
            menu_ref: Optional[ui.menu] = None # To store the menu reference

            with date_input_element.add_slot('append'):
                cal_icon = ui.icon('edit_calendar').classes('cursor-pointer')

            with ui.menu().props('no-parent-event') as menu:
                menu_ref = menu # Assign the menu instance
                date_options_parts: List[str] = []
                if date_min_max:
                    min_d, max_d = date_min_max
                    if min_d: date_options_parts.append(f"date >= '{min_d.strftime('%Y/%m/%d')}'")
                    if max_d: date_options_parts.append(f"date <= '{max_d.strftime('%Y/%m/%d')}'")
                # Construct props string carefully if date_options_parts is empty
                options_prop_val = f':options="date => {" && ".join(date_options_parts)}"' if date_options_parts else ""

                def on_date_change(e_date_event: ValueChangeEventArguments, sk_arg: str = storage_key,
                                   inp_el_arg: ui.input = date_input_element, display_fmt_arg: str = DATE_FORMAT_DISPLAY,
                                   # menu_arg: ui.menu = menu_ref # This lambda captures menu_ref from outer scope
                                   ) -> None:
                    new_date_val: Optional[str] = cast(Optional[str], e_date_event.value) # This is 'YYYY-MM-DD'
                    form_data_dict[sk_arg] = new_date_val # Store in NiceGUI standard format

                    displayed_val_on_change: str = ''
                    if new_date_val:
                        try: # Parse from NiceGUI format, display in user format
                            dt_obj = datetime.strptime(new_date_val, DATE_FORMAT_NICEGUI)
                            displayed_val_on_change = dt_obj.strftime(display_fmt_arg)
                        except ValueError: # Should not happen if date picker provides valid format
                            displayed_val_on_change = new_date_val # Fallback
                    inp_el_arg.set_value(displayed_val_on_change)
                    if menu_ref: menu_ref.close()


                ui.date(value=value_for_datepicker, on_change=on_date_change).props(options_prop_val if options_prop_val else None)
            
            cal_icon.on('click', lambda: menu_ref.open() if menu_ref else None) # Connect icon click to open menu
            el = date_input_element

        elif input_type == 'text':
            text_input_element: ui.input = ui.input(
                label=label_text, value=str(form_data_dict.get(storage_key) or ''), 
                on_change=lambda e, sk=storage_key: form_data_dict.update({sk: e.value}))
            text_input_element.classes('full-width').props(f"outlined dense error-message='{actual_error_message}' error={has_error_val}")
            el = text_input_element
        elif input_type == 'select' and options is not None:
            current_value_for_select = form_data_dict.get(storage_key)
            if storage_key in [ETHNICITY_KEY, RELIGION_KEY] and current_value_for_select is None:
                if isinstance(options, list) and options:
                    current_value_for_select = options[0]
                    form_data_dict[storage_key] = current_value_for_select # Explicitly set back if it was None
                    print(f"DEBUG: Forcibly set '{storage_key}' to '{current_value_for_select}' \
                          in create_field because it was None.")
            # For select, if current_value is not among the options, it might not display correctly.
            # NiceGUI usually handles this by showing nothing selected or the value itself if not found.
            select_element: ui.select = ui.select(
                options, label=label_text, value=current_value,
                on_change=lambda e, sk=storage_key: form_data_dict.update({sk: e.value})
            ).classes('full-width').props(f"outlined dense error-message='{actual_error_message}' error={has_error_val}")

            if isinstance(options, list) and len(options) > 0 and isinstance(options[0], dict):
                if select_display_key: select_element.props(f"option-label='{select_display_key}'")
                if select_value_key: select_element.props(f"option-value='{select_value_key}'")
            el = select_element
        elif input_type == 'radio' and options is not None:
            # ui.radio expects options as Dict[value, label] or List[value]
            # If current_value from storage isn't a key in options (for dict) or in options (for list),
            # it might not select anything initially.
            radio_element: ui.radio = ui.radio(
                options, value=current_value, # Pass label_text to radio for overall label
                on_change=lambda e, sk=storage_key: form_data_dict.update({sk: e.value})).props("inline")
            if has_error_val: ui.label(actual_error_message).classes('text-negative text-caption q-pl-sm') # q_pl_sm to q-pl-sm
            el = radio_element
        # Add other input types if necessary
    
    # Determine the correct way to retrieve value for validation based on input type
    value_retrieval_strategy: ValidationArgsFuncType
    if input_type == 'date':
        # For date, validator_func expects a date object or None
        def get_date_value_for_validation(data_dict_val: Dict[str, Any], key_val: str) -> Optional[date]:
            val_from_storage_val: Any = data_dict_val.get(key_val) # This is 'YYYY-MM-DD' string or None
            if isinstance(val_from_storage_val, str):
                try:
                    return datetime.strptime(val_from_storage_val, DATE_FORMAT_NICEGUI).date()
                except ValueError:
                    return None # Invalid date string for validation
            # It should ideally not be date/datetime object if stored as string, but handle defensively
            elif isinstance(val_from_storage_val, date): return val_from_storage_val
            elif isinstance(val_from_storage_val, datetime): return val_from_storage_val.date()
            return None
        value_retrieval_strategy = get_date_value_for_validation
    else:
        # For other types, validator_func typically gets the raw stored value
        value_retrieval_strategy = lambda data_dict_lambda, key_lambda: data_dict_lambda.get(key_lambda)

    # The 'error_prefix' is a general prefix for the message, not the field label itself.
    # Field-specific context for error messages is usually part of the validator's return message.
    validator_entry: ValidatorEntryType = (storage_key, validation_func, value_retrieval_strategy, label_text) # Using label_text as prefix
    return el, validator_entry


# --- Helper functions for render_step5 ---
def format_display_value(field_key: str,
                         field_value: Any,
                         internal_date_format: str, # e.g., DATE_FORMAT_NICEGUI
                         ui_date_format: str) -> str: # e.g., DATE_FORMAT_DISPLAY
    if isinstance(field_value, bool):
        return "**Có**" if field_value else "Không"

    # List of keys that store dates as strings in 'internal_date_format'
    date_keys_list: List[str] = [
        DOB_KEY, ID_PASSPORT_ISSUE_DATE_KEY, PARTY_DATE_KEY,
        YOUTH_DATE_KEY
    ]
    if field_key in date_keys_list and isinstance(field_value, str) and field_value:
        try:
            # Parse from the internal storage format, display in UI format
            return datetime.strptime(field_value, internal_date_format).strftime(ui_date_format)
        except ValueError:
            return f"**{field_value}** (Lỗi định dạng)" # Indicate format error if stored string is wrong

    if field_value is None or (isinstance(field_value, str) and not field_value.strip()):
        # Check for specific "Chưa vào" or "Không" values that are meaningful "empty" states for some fields
        if field_key in [PARTY_MEMBERSHIP_KEY, YOUTH_MEMBERSHIP_KEY] and field_value == "Chưa vào":
            return f"**{str(field_value)}**"
        # For ethnicity/religion, the default first option might be a valid "empty" like "Kinh" or "Không"
        # These should be displayed if they are the stored value.
        # The `create_field` initialization and `_initialize_form_data` set these.
        # So, if `field_value` is that default (e.g. "Kinh"), it should be shown.
        # The `(Chưa điền)` should only be for truly absent or empty string values for most text fields.

        # If it's a selection where the first option is like "Không có" (from para.degrees)
        # and this is the actual stored value, it should be displayed.
        if field_key == EDUCATION_HIGHEST_KEY and field_value == getattr(para, 'degrees', [""])[0]:
             return f"**{str(field_value)}**"


        return "<em>(Chưa điền)</em>" # Fallback for truly empty or None for other fields

    return f"**{str(field_value)}**"


def get_label_for_key(field_key: str) -> str:
    labels_map: Dict[str, str] = {
        STEP0_ANS_KEY: 'Nộp cho cơ quan Nhà nước/Quân đội',
        FULL_NAME_KEY: 'Họ và tên',
        GENDER_KEY: 'Giới tính',
        DOB_KEY: 'Ngày sinh',
        ID_PASSPORT_NUM_KEY: 'Số CMND/CCCD',
        ID_PASSPORT_ISSUE_DATE_KEY: 'Ngày cấp CMND/CCCD',
        ID_PASSPORT_ISSUE_PLACE_KEY: 'Nơi cấp CMND/CCCD',
        HEALTH_KEY: 'Tình hình sức khoẻ',
        HEIGHT_KEY: 'Chiều cao (cm)',
        WEIGHT_KEY: 'Cân nặng (kg)',
        REGISTERED_ADDRESS_KEY: 'Địa chỉ hộ khẩu',
        PHONE_KEY: 'Số điện thoại',
        EMERGENCY_CONTACT_COMBINED_KEY: 'Khi cần báo tin cho',
        EMERGENCY_PLACE_KEY: 'Địa chỉ báo tin',
        SAME_ADDRESS1_KEY: 'Nơi báo tin giống địa chỉ hộ khẩu',
        EDUCATION_HIGHEST_KEY: 'Bằng cấp cao nhất',
        EDUCATION_MAJOR_KEY: 'Chuyên ngành đào tạo',
        WORK_DF_KEY: 'III. Quá trình công tác',
        PARTY_MEMBERSHIP_KEY: 'Đảng viên ĐCSVN',
        PARTY_DATE_KEY: 'Ngày kết nạp Đảng',
        YOUTH_MEMBERSHIP_KEY: 'Đoàn viên TNCS',
        YOUTH_DATE_KEY: 'Ngày kết nạp Đoàn',
        ETHNICITY_KEY: 'Dân tộc',
        RELIGION_KEY: 'Tôn giáo',
        DAD_NAME_KEY: 'Họ tên Bố',
        DAD_AGE_KEY: 'Tuổi Bố',
        DAD_JOB_KEY: 'Nghề nghiệp Bố',
        MOM_NAME_KEY: 'Họ tên Mẹ',
        MOM_AGE_KEY: 'Tuổi Mẹ',
        MOM_JOB_KEY: 'Nghề nghiệp Mẹ',
        SPOUSE_NAME_KEY: 'Họ tên Vợ/Chồng',
        SPOUSE_AGE_KEY: 'Tuổi Vợ/Chồng',
        SPOUSE_JOB_KEY: 'Nghề nghiệp Vợ/Chồng',
        SIBLINGS_KEY: 'Anh chị em ruột',
        CHILDREN_KEY: 'Các con',
    }
    return labels_map.get(field_key, field_key.replace('_KEY', '').replace('_', ' ').title())

# --- Helper to initialize form_data structure ---
def initialize_form_data(form_data_to_populate: Dict[str, Any]) -> None:
    """Populates the provided dictionary with default form field values."""
    form_data_to_populate[STEP0_ANS_KEY] = 'Không'
    # Step 1
    form_data_to_populate[FULL_NAME_KEY] = ""
    form_data_to_populate[GENDER_KEY] = ""
    form_data_to_populate[DOB_KEY] = None
    form_data_to_populate[ID_PASSPORT_NUM_KEY] = ""
    form_data_to_populate[ID_PASSPORT_ISSUE_DATE_KEY] = None
    form_data_to_populate[ID_PASSPORT_ISSUE_PLACE_KEY] = ""
    form_data_to_populate[HEALTH_KEY] = ""
    form_data_to_populate[HEIGHT_KEY] = ""
    form_data_to_populate[WEIGHT_KEY] = ""
    # Step 2
    form_data_to_populate[REGISTERED_ADDRESS_KEY] = ""
    form_data_to_populate[PHONE_KEY] = ""
    form_data_to_populate[EMERGENCY_CONTACT_COMBINED_KEY] = ""
    form_data_to_populate[EMERGENCY_PLACE_KEY] = ""
    form_data_to_populate[SAME_ADDRESS1_KEY] = False
    # Step 3
    degrees_options: List[str] = getattr(para, 'degrees', [""])
    form_data_to_populate[EDUCATION_HIGHEST_KEY] = degrees_options[0] if degrees_options else ""
    form_data_to_populate[EDUCATION_MAJOR_KEY] = ""
    form_data_to_populate[WORK_DF_KEY] = []
    # Step 4
    form_data_to_populate[PARTY_MEMBERSHIP_KEY] = "Chưa vào"
    form_data_to_populate[PARTY_DATE_KEY] = None
    form_data_to_populate[YOUTH_MEMBERSHIP_KEY] = "Chưa vào"
    form_data_to_populate[YOUTH_DATE_KEY] = None
    ethnic_groups: List[str] = getattr(para, 'ethnic_groups_vietnam', ETHNIC_OPTIONS_DEFAULT_FOR_INIT)
    form_data_to_populate[ETHNICITY_KEY] = ethnic_groups[0] if ethnic_groups else ETHNIC_OPTIONS_DEFAULT_FOR_INIT[0]
    religion_opts: List[str] = getattr(para, 'religion_options', RELIGION_OPTIONS_DEFAULT_FOR_INIT)
    form_data_to_populate[RELIGION_KEY] = religion_opts[0] if religion_opts else RELIGION_OPTIONS_DEFAULT_FOR_INIT[0]
    # Family Info
    form_data_to_populate[DAD_NAME_KEY] = ""
    form_data_to_populate[DAD_AGE_KEY] = ""
    form_data_to_populate[DAD_JOB_KEY] = ""
    form_data_to_populate[MOM_NAME_KEY] = ""
    form_data_to_populate[MOM_AGE_KEY] = ""
    form_data_to_populate[MOM_JOB_KEY] = ""
    form_data_to_populate[SPOUSE_NAME_KEY] = ""
    form_data_to_populate[SPOUSE_AGE_KEY] = ""
    form_data_to_populate[SPOUSE_JOB_KEY] = ""
    form_data_to_populate[SIBLINGS_KEY] = []
    form_data_to_populate[CHILDREN_KEY] = []

# --- PDF Data Mapping Utility ---
def _split_date_for_pdf(date_str: Optional[str],
                        internal_format_str: str) -> Tuple[str, str, str]:
    """Helper to parse a date string (YYYY-MM-DD) and split into d, m, y for PDF."""
    if date_str:
        try:
            dt_obj = datetime.strptime(date_str, internal_format_str)
            return dt_obj.strftime('%d'), dt_obj.strftime('%m'), dt_obj.strftime('%Y')
        except ValueError:
            pass # Invalid date string
    return '', '', ''

def generate_pdf_data_mapping(
    form_data_app: Dict[str, Any],
    date_format_nicegui_app: str,
    max_work_entries_pdf: int = 5,
    max_siblings_pdf: int = 5, # Define max limits for loops
    max_children_pdf: int = 5
) -> Dict[str, Any]:
    """
    Transforms data from the application's format into a dictionary
    where keys are the PDF form field names.
    """
    from copy import copy
    data_for_pdf: Dict[str, Any] = {}
    # --- Section 1: Basic Information & Health ---
    full_name_val: str = form_data_app.get(FULL_NAME_KEY, '')
    data_for_pdf[PDF_FULL_NAME_P1_KEY] = copy(full_name_val)
    data_for_pdf[PDF_FULL_NAME_P2_KEY] = copy(full_name_val)
    
    data_for_pdf[PDF_GENDER_KEY] = form_data_app.get(GENDER_KEY, '')
    data_for_pdf[PDF_ID_NUM_KEY] = form_data_app.get(ID_PASSPORT_NUM_KEY, '')
    data_for_pdf[PDF_ID_ISSUE_PLACE_KEY] = form_data_app.get(ID_PASSPORT_ISSUE_PLACE_KEY, '')
    
    data_for_pdf[PDF_HEALTH_KEY] = form_data_app.get(HEALTH_KEY, '')
    data_for_pdf[PDF_HEIGHT_KEY] = form_data_app.get(HEIGHT_KEY, '')
    data_for_pdf[PDF_WEIGHT_KEY] = form_data_app.get(WEIGHT_KEY, '')

    dob_string = form_data_app.get(DOB_KEY)
    day, month, year = _split_date_for_pdf(dob_string, date_format_nicegui_app)
    data_for_pdf[PDF_DOB_DAY_P1_KEY], data_for_pdf[PDF_DOB_MONTH_P1_KEY], data_for_pdf[PDF_DOB_YEAR_P1_KEY] = day, month, year
    data_for_pdf[PDF_DOB_DAY_P2_KEY], data_for_pdf[PDF_DOB_MONTH_P2_KEY], data_for_pdf[PDF_DOB_YEAR_P2_KEY] = day, month, year

    id_issue_date_string = form_data_app.get(ID_PASSPORT_ISSUE_DATE_KEY)
    data_for_pdf[PDF_ID_ISSUE_DAY_KEY], data_for_pdf[PDF_ID_ISSUE_MONTH_KEY], data_for_pdf[PDF_ID_ISSUE_YEAR_KEY] = \
        _split_date_for_pdf(id_issue_date_string, date_format_nicegui_app)

    # --- Section 2: Addresses & Contact ---
    registered_address_val = form_data_app.get(REGISTERED_ADDRESS_KEY, '')
    data_for_pdf[PDF_REGISTERED_ADDRESS_P1_KEY] = registered_address_val
    data_for_pdf[PDF_REGISTERED_ADDRESS_P2_KEY] = registered_address_val
    data_for_pdf[PDF_PHONE_MOBILE_KEY] = form_data_app.get(PHONE_KEY, '')
    data_for_pdf[PDF_EMERGENCY_CONTACT_DETAILS_KEY] = form_data_app.get(EMERGENCY_CONTACT_COMBINED_KEY, '')
    data_for_pdf[PDF_EMERGENCY_CONTACT_ADDRESS_KEY] = form_data_app.get(EMERGENCY_PLACE_KEY, '')

    # --- Section 3: Education & Work ---
    data_for_pdf[PDF_HIGHEST_EDUCATION_KEY] = form_data_app.get(EDUCATION_HIGHEST_KEY, '')
    data_for_pdf[PDF_SPECIALIZED_AREA_KEY] = form_data_app.get(EDUCATION_MAJOR_KEY, '')

    work_history_list_app = cast(List[Dict[str, Any]], form_data_app.get(WORK_DF_KEY, []))
    for i in range(max_work_entries_pdf):
        pdf_idx = i + 1
        if i < len(work_history_list_app):
            entry = work_history_list_app[i]
            from_date, to_date = entry.get(WORK_FROM_DATE_KEY, ""), entry.get(WORK_TO_DATE_KEY, "")
            data_for_pdf[f'{PDF_WORK_FROM_TO_KEY}{pdf_idx}'] = f"{from_date} - {to_date}" if from_date or to_date else ""
            data_for_pdf[f'{PDF_WORK_TASK_KEY}{pdf_idx}'] = entry.get(WORK_TASK_KEY, "")
            data_for_pdf[f'{PDF_WORK_UNIT_KEY}{pdf_idx}'] = entry.get(WORK_UNIT_KEY, "")
            data_for_pdf[f'{PDF_WORK_ROLE_KEY}{pdf_idx}'] = entry.get(WORK_ROLE_KEY, "")
        else:
            data_for_pdf[f'{PDF_WORK_FROM_TO_KEY}{pdf_idx}'] = ""
            data_for_pdf[f'{PDF_WORK_TASK_KEY}{pdf_idx}'] = ""
            data_for_pdf[f'{PDF_WORK_UNIT_KEY}{pdf_idx}'] = ""
            data_for_pdf[f'{PDF_WORK_ROLE_KEY}{pdf_idx}'] = ""

    # --- Section 4: Clearance & Family Data ---
    if form_data_app.get(PARTY_MEMBERSHIP_KEY) == "Đã vào":
        party_date_string = form_data_app.get(PARTY_DATE_KEY)
        data_for_pdf[PDF_PARTY_ADM_DAY_KEY], data_for_pdf[PDF_PARTY_ADM_MONTH_KEY], data_for_pdf[PDF_PARTY_ADM_YEAR_KEY] = \
            _split_date_for_pdf(party_date_string, date_format_nicegui_app)
            
    if form_data_app.get(YOUTH_MEMBERSHIP_KEY) == "Đã vào":
        youth_date_string = form_data_app.get(YOUTH_DATE_KEY)
        data_for_pdf[PDF_YOUTH_ADM_DAY_KEY], data_for_pdf[PDF_YOUTH_ADM_MONTH_KEY], data_for_pdf[PDF_YOUTH_ADM_YEAR_KEY] = \
            _split_date_for_pdf(youth_date_string, date_format_nicegui_app)
    
    data_for_pdf[PDF_ETHNICITY_KEY] = form_data_app.get(ETHNICITY_KEY, '')
    data_for_pdf[PDF_RELIGION_KEY] = form_data_app.get(RELIGION_KEY, '')
    
    # Parents and Spouse
    data_for_pdf[PDF_DAD_NAME_KEY] = form_data_app.get(DAD_NAME_KEY, '')
    data_for_pdf[PDF_DAD_AGE_KEY] = form_data_app.get(DAD_AGE_KEY, '')
    data_for_pdf[PDF_DAD_JOB_KEY] = form_data_app.get(DAD_JOB_KEY, '')
    data_for_pdf[PDF_MOM_NAME_KEY] = form_data_app.get(MOM_NAME_KEY, '')
    data_for_pdf[PDF_MOM_AGE_KEY] = form_data_app.get(MOM_AGE_KEY, '')
    data_for_pdf[PDF_MOM_JOB_KEY] = form_data_app.get(MOM_JOB_KEY, '')
    data_for_pdf[PDF_SPOUSE_NAME_KEY] = form_data_app.get(SPOUSE_NAME_KEY, '')
    data_for_pdf[PDF_SPOUSE_AGE_KEY] = form_data_app.get(SPOUSE_AGE_KEY, '')
    data_for_pdf[PDF_SPOUSE_JOB_KEY] = form_data_app.get(SPOUSE_JOB_KEY, '')

    # Siblings
    siblings_list = cast(List[Dict[str, Any]], form_data_app.get(SIBLINGS_KEY, []))
    for i in range(max_siblings_pdf):
        pdf_idx = i + 1
        if i < len(siblings_list):
            entry = siblings_list[i]
            # Assuming you have one field for 'Tên, tuổi, chỗ ở, nghề nghiệp, trình độ'
            sibling_info = f"{entry.get('name', '')}, {entry.get('age', '')} tuổi. Nghề nghiệp: {entry.get('job', '')}. Chỗ ở: {entry.get('address', '')}"
            data_for_pdf[f'{PDF_SIBLING_INFO_KEY}{pdf_idx}'] = sibling_info
        else:
            data_for_pdf[f'{PDF_SIBLING_INFO_KEY}{pdf_idx}'] = ""

    # Children
    children_list = cast(List[Dict[str, Any]], form_data_app.get(CHILDREN_KEY, []))
    for i in range(max_children_pdf):
        pdf_idx = i + 1
        if i < len(children_list):
            entry = children_list[i]
            data_for_pdf[f'{PDF_CHILD_NAME_KEY}{pdf_idx}'] = entry.get('name', '')
            data_for_pdf[f'{PDF_CHILD_AGE_KEY}{pdf_idx}'] = entry.get('age', '')
            data_for_pdf[f'{PDF_CHILD_JOB_KEY}{pdf_idx}'] = entry.get('job', '')
        else:
            data_for_pdf[f'{PDF_CHILD_NAME_KEY}{pdf_idx}'] = ""
            data_for_pdf[f'{PDF_CHILD_AGE_KEY}{pdf_idx}'] = ""
            data_for_pdf[f'{PDF_CHILD_JOB_KEY}{pdf_idx}'] = ""
            
    return data_for_pdf