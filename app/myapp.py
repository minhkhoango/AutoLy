#!/usr/bin/env python3
from nicegui import ui, app
from nicegui.element import Element
from nicegui.events import ValueChangeEventArguments
from datetime import date, datetime
from typing import List, Dict, Any, Optional, Callable, Tuple, Union, cast, TypeAlias

# Assuming validation.py and para.py are in the same directory or accessible in PYTHONPATH
from validation import Vl
import para # Your lists of options
from fillpdf import fillpdfs  # type: ignore[import]
import tempfile
import os
from pathlib import Path

from utils import generate_pdf_data_mapping

# --- Type Aliases ---
ValidationFuncType: TypeAlias = Callable[[Any], Tuple[bool, str]]
# Function that takes a value (Any type for flexibility) and returns a tuple of (is_valid: bool, error_message: str)

ValidationArgsFuncType: TypeAlias = Callable[[Any], Any]
# Functions that returns the argments (value) to be validated

ValidatorEntryType: TypeAlias = Tuple[str, ValidationFuncType, ValidationArgsFuncType, str]

# --- Constants and Configuration ---
DATE_FORMAT_NICEGUI: str = '%Y-%m-%d'
DATE_FORMAT_DISPLAY: str = '%d/%m/%Y'
STEP_KEY: str = 'step'
NEED_CLEARANCE_KEY: str = 'need_clearance'
WORK_DF_KEY: str = 'work_df'
SAME_ADDRESS1_KEY: str = 'same_address1'
SAME_ADDRESS2_KEY: str = 'same_address2'
STEP0_ANS_KEY: str = 'step0_ans'
PARTY_MEMBERSHIP_KEY: str = 'party_membership'
PARTY_DATE_KEY: str = 'party_date'
YOUTH_MEMBERSHIP_KEY: str = 'youth_membership'
YOUTH_DATE_KEY: str = 'youth_date'
FAMILY_INVOLVEMENT_KEY: str = 'family_involvement'
ETHNICITY_STEP4_KEY: str = 'ethnicity_step4'
RELIGION_STEP4_KEY: str = 'religion_step4'
ETHNIC_OPTIONS_DEFAULT_FOR_INIT: List[str] = ["Kinh", "Tày", "Thái", "Mường", "Khác"]
RELIGION_OPTIONS_DEFAULT_FOR_INIT: List[str] = ["Không", "Phật giáo", "Công giáo", "Khác"]
FAM_NAME_KEY: str = 'fam_name'
FAM_RELATION_KEY: str = 'fam_relation'
FAM_ROLE_KEY: str = 'fam_role'
FAM_PERIOD_KEY: str = 'fam_period'
# Keys for form data and attempted submission state
FORM_DATA_KEY: str = 'form_data'
FORM_ATTEMPTED_SUBMISSION_KEY: str = 'form_attempted_submission'

# --- PDF Template Path (remains in autoly_app.py or a config file it reads) ---
PDF_TEMPLATE_PATH: str = "assets/Mau-so-yeu-ly-lich-TEMPLATE.pdf" # Ensure this path is correct

# --- Global Runtime State (Not persisted in app.storage.user) ---
global_current_validators: List[ValidatorEntryType] = []
global_validation_error_messages: Dict[str, str] = {}

# --- Global Helper Function: create_field ---
def create_field(label_text: str, 
                 storage_key: str, 
                 validation_func: ValidationFuncType,
                 input_type: str ='text', 
                 options: Optional[Union[List[Any], Dict[Any, Any]]] = None, 
                 # Can be list of strings dicts, or a dict for radio
                 date_min_max: Optional[Tuple[Optional[date], Optional[date]]] = None,
                 select_display_key: Optional[str] = None,
                 select_value_key: Optional[str] = None) -> Optional[Element]:
    
    if FORM_DATA_KEY not in app.storage.user or \
       not isinstance(
           cast(Dict[str, Any], app.storage.user).get(FORM_DATA_KEY), dict): # Use .get for safer check before assignment
        app.storage.user[FORM_DATA_KEY] = {}

     # Typed reference to the form_data dictionary for most read operations
    form_data_dict: Dict[str, Any] = cast(Dict[str, Any], app.storage.user[FORM_DATA_KEY])

    default_value: Any = None # General value, overidden below based on input_type

    if input_type == 'select':
        if options:
            if isinstance(options, list) and len(options) > 0:
                first_option = options[0]
                if isinstance(first_option, dict) and select_value_key:
                    default_value = cast(Dict[str, Any], first_option).get(select_value_key) # Get value by key if dict
                elif isinstance(first_option, dict) and not select_value_key: # list of dicts but no value key specified, assume value is the dict itself or first val
                    default_value = first_option #  take first dict value
                else: # list of strings/numbers
                    default_value = first_option
            elif isinstance(options, dict) and options: # For ui.radio if options were a dict
                default_value = next(iter(options.keys())) # Get first key as default
            else:
                default_value = None 
    elif input_type == 'date':
        default_value = None
    elif input_type == 'text':
        default_value = ''
    elif input_type == 'radio':
        if options:
            if isinstance(options, dict) and options:
                default_value = next(iter(options.keys()), None) # Get first key as default
            elif isinstance(options, list) and options:
                default_value = options[0]
    else:
        default_value = ''
    # Default value for the field, can be overridden by existing form_data

    current_value: Any = form_data_dict.get(storage_key, default_value)
    
    error_msg_val: str = global_validation_error_messages.get(storage_key, '')
    
    # Ensure 'form_attempted_submission' key exists and is bool for safer access
    if FORM_ATTEMPTED_SUBMISSION_KEY not in app.storage.user or \
       not isinstance(cast(Dict[str, Any], app.storage.user).get(FORM_ATTEMPTED_SUBMISSION_KEY), bool):
        app.storage.user[FORM_ATTEMPTED_SUBMISSION_KEY] = False

    form_attempted: bool = cast(bool, app.storage.user[FORM_ATTEMPTED_SUBMISSION_KEY])
    has_error_val: bool = form_attempted and (storage_key in global_validation_error_messages)

    el: Optional[Element] = None # Initialize element to None
    with ui.column().classes('q-mb-sm full-width'):
        if input_type == 'date':
            date_value_from_storage: Any = current_value # This can be 'YYYY-MM-DD' str, None, or other types if manually set
            displayed_value_in_input: str = ''
            value_for_datepicker: Optional[str] = None # For ui.date's 'value' prop: 'YYYY-MM-DD' or None
            dt_obj_intermediate: Optional[Union[date, datetime]] = None


            if isinstance(date_value_from_storage, str):
                try:
                    dt_obj_intermediate = datetime.strptime(date_value_from_storage, DATE_FORMAT_NICEGUI)
                    value_for_datepicker = date_value_from_storage # Already in correct string format
                except ValueError:
                    displayed_value_in_input = date_value_from_storage # Show invalid string as is
                    # value_for_datepicker remains None, datepicker will be empty or show last valid
            elif isinstance(date_value_from_storage, datetime):
                dt_obj_intermediate = date_value_from_storage
                value_for_datepicker = dt_obj_intermediate.strftime(DATE_FORMAT_NICEGUI)
            elif isinstance(date_value_from_storage, date):
                dt_obj_intermediate = date_value_from_storage
                value_for_datepicker = dt_obj_intermediate.strftime(DATE_FORMAT_NICEGUI)
            # If date_value_from_storage is None or an unhandled type, dt_obj_intermediate remains None.

            if dt_obj_intermediate:
                displayed_value_in_input = dt_obj_intermediate.strftime(DATE_FORMAT_DISPLAY)
            # If date_value_from_storage was None, displayed_value_in_input remains ''.
            # If it was an invalid string, displayed_value_in_input holds that invalid string.

            ui.label(label_text).classes('text-caption q-mb-xs') # Consistent label styling
            date_input_element: ui.input = ui.input(value=displayed_value_in_input) \
                .props(f"readonly clearable outlined dense error-message='{error_msg_val}' error={has_error_val}") \
                .classes('full-width')
            
            with date_input_element.add_slot('append'):
                ui.icon('edit_calendar').classes('cursor-pointer').on('click', lambda: menu.open())

            menu: ui.menu
            with ui.menu().props('no-parent-event') as menu_instance:
                menu = menu_instance
                date_options_parts: List[str] = []
                if date_min_max:
                    min_d, max_d = date_min_max
                    if min_d: date_options_parts.append(f"date >= '{min_d.strftime('%Y/%m/%d')}'")
                    if max_d: date_options_parts.append(f"date <= '{max_d.strftime('%Y/%m/%d')}'")

                date_picker_props_str: str = f':options="date => {" && ".join(date_options_parts)}"' \
                    if date_options_parts else ''
                
                # Using ValueChangeEventArguments as per our discussion
                def on_date_change(e_date: ValueChangeEventArguments, 
                                   sk_param: str = storage_key,
                                   inp_el_param: ui.input = date_input_element,
                                   fmt_param: str = DATE_FORMAT_DISPLAY, 
                                   mnu_param: ui.menu = menu) -> None:
                    
                    new_date_val_str: Optional[str] = cast(Optional[str], e_date.value) # e_date.value is 'YYYY-MM-DD' string or None
                    app.storage.user[FORM_DATA_KEY][sk_param] = new_date_val_str

                    displayed_val: str = ''
                    if new_date_val_str:
                        try:
                            dt_obj_on_change = datetime.strptime(new_date_val_str, DATE_FORMAT_NICEGUI)
                            displayed_val = dt_obj_on_change.strftime(fmt_param)
                        except ValueError: # Should not happen if ui.date provides correct format
                            displayed_val = new_date_val_str

                    inp_el_param.set_value(displayed_val)
                    mnu_param.close()

                ui.date(value=value_for_datepicker, on_change=on_date_change) \
                    .props(date_picker_props_str if date_picker_props_str else None) # type: ignore
                
            el = date_input_element

        elif input_type == 'text':
            # For text, current_value is '' if not set, str('') is ''. str(None) is 'None'.
            # Default for text is '', so str(current_value) is fine.
            text_input_element: ui.input = ui.input(
                label=label_text, 
                value=str(current_value),
                on_change=lambda e, 
                sk=storage_key: cast(Dict[str, Any], app.storage.user[FORM_DATA_KEY]).update({sk: e.value}))
            
            text_input_element.classes('full-width')
            text_input_element.props(f"outlined dense error-message='{error_msg_val}' error={has_error_val}")
            el = text_input_element
            
        elif input_type == 'select' and options is not None:
            try:
                print(f"Attempting to create ui.select for: {label_text}") # Debug print
                print(f"  Options type: {type(options)}") # Debug print
                print(f"  Options value (first 5): {options[:5] if isinstance(options, list) else options}") # Debug print
                print(f"  Current_value type: {type(current_value)}") # Debug print
                print(f"  Current_value value: {current_value}") # Debug print

                select_element: ui.select = ui.select(
                    options, label=label_text, 
                    value=current_value,
                    on_change=lambda e, sk=storage_key: 
                        cast(Dict[str, Any], app.storage.user[FORM_DATA_KEY]).update({sk: e.value})
                ) 
                select_element.classes('full-width') 
                select_element.props(f"outlined dense error-message='{error_msg_val}' error={has_error_val}")
                
                if isinstance(options, list) and len(options) > 0 and isinstance(options[0], dict):
                    if select_display_key: select_element.props(f"option-label='{select_display_key}'")
                    if select_value_key: select_element.props(f"option-value='{select_value_key}'")
                el = select_element
            
            except Exception as e:
                print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                print(f"CRITICAL ERROR creating ui.select for key '{storage_key}' with label '{label_text}':")
                print(f"  Options type was: {type(options)}")
                # Avoid printing huge lists, just show a snippet if it's a list
                if isinstance(options, list):
                    print(f"  Options value (first 5 if list): {options[:5]}")
                else:
                    print(f"  Options value: {options}")
                print(f"  Current_value type was: {type(current_value)}, Current_value value: {current_value}")
                print(f"  Exception type: {type(e)}")
                print(f"  Exception message: {e}")
                import traceback
                traceback.print_exc() # This will print the specific traceback for this spot
                print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                # You can either re-raise the exception or create a placeholder UI element
                # raise # Uncomment to let the original ASGI error also appear after this detailed print
                el = ui.label(f"Error creating select: {label_text}. Check console.").classes('text-negative q-pa-md')

        elif input_type == 'radio' and options is not None: # Added basic radio button support
            # Quasar radio options are typically label:value pairs in a list of dicts, or a simple list for values.
            # For simplicity, assuming `options` is a dict like {'Label1': 'val1', 'Label2': 'val2'} for ui.radio
            # or a list of values. If it's a dict, ui.radio handles it as value:label by default for its `options` prop.
            # We are using it as {'val1': 'Label1', ...} in render_step0, so it aligns.
            radio_element: ui.radio = ui.radio(
                options, value=current_value,
                on_change=lambda e, sk=storage_key: 
                    cast(Dict[str, Any], app.storage.user[FORM_DATA_KEY]).update({sk: e.value})
            ) 
            radio_element.props(f"error-message='{error_msg_val}' error={has_error_val} inline") # Added inline for radio
            el = radio_element
    
    val_args_func_impl: ValidationArgsFuncType
    if input_type == 'date':
        def get_value_for_validation(key_for_val: str = storage_key) -> Optional[date]:
            form_data_for_val = cast(Dict[str, Any], app.storage.user[FORM_DATA_KEY])
            val_from_storage: Any = form_data_for_val.get(key_for_val, None)

            if isinstance(val_from_storage, str):
                try:
                    return datetime.strptime(val_from_storage, DATE_FORMAT_NICEGUI).date()
                except ValueError:
                    return None # Invalid date string
            elif isinstance(val_from_storage, date): # If it was somehow stored as date object
                return val_from_storage
            elif isinstance(val_from_storage, datetime):
                return val_from_storage.date() # If it was somehow stored as datetime object
            return None
        val_args_func_impl = get_value_for_validation
    else:
        val_args_func_impl = lambda sk=storage_key: \
            cast(Dict[str, Any], app.storage.user[FORM_DATA_KEY]).get(sk)
    
    global_current_validators.append((storage_key, validation_func, val_args_func_impl, '⚠️'))
    return el

# --- Navigation Functions ---
def next_step() -> None:
    current_step: int = cast(int, cast(Dict[str, Any], app.storage.user).get(STEP_KEY, 0))
    current_step += 1
    app.storage.user[STEP_KEY] = current_step
    app.storage.user[FORM_ATTEMPTED_SUBMISSION_KEY] = False
    
    global_current_validators.clear()
    global_validation_error_messages.clear()
    
    needs_clearance_val: bool = cast(bool, cast(Dict[str, Any], app.storage.user).get(NEED_CLEARANCE_KEY, False))
    if current_step == 4 and not needs_clearance_val:
        app.storage.user[STEP_KEY] = current_step + 1 # Skip to step 5
    
    update_step_content.refresh()

def prev_step() -> None:
    current_step: int = cast(int, cast(Dict[str, Any], app.storage.user).get(STEP_KEY, 0))
    if current_step > 0:
        current_step -= 1
        app.storage.user[STEP_KEY] = current_step
        app.storage.user[FORM_ATTEMPTED_SUBMISSION_KEY] = False
        
        global_current_validators.clear()
        global_validation_error_messages.clear()
        
        needs_clearance_val: bool = cast(bool, cast(Dict[str, Any], app.storage.user).get(NEED_CLEARANCE_KEY, False))
        # Original logic: if current_step == 4 (after decrementing)
        # This means if we were on step 5 and go back, new current_step is 4.
        if app.storage.user[STEP_KEY] == 4 and not needs_clearance_val: # Check the new current step
             app.storage.user[STEP_KEY] = current_step - 1 # Skip back from step 4 to step 3
        
        update_step_content.refresh()

def run_validators_and_update_error_messages() -> bool:
    global_validation_error_messages.clear()
    all_valid: bool = True
    
    for field_key, validator_func, validation_args_func, error_prefix in global_current_validators:
        # ValidationArgsFuncType expects an argument (the field_key/storage_key)
        value_to_validate: Any = validation_args_func(field_key)
        
        is_valid: bool
        msg: str
        is_valid, msg = validator_func(value_to_validate)
        if not is_valid:
            all_valid = False
            global_validation_error_messages[field_key] = f"{error_prefix} {msg}"
    return all_valid

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++ PDF GENERATION ORCHESTRATION (uses utils.generate_pdf_data_mapping)   ++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
async def create_and_download_pdf() -> None:
    """
    Orchestrates PDF generation using the utility mapping function
    and handles NiceGUI interactions (storage, notifications, download).
    """
    if FORM_DATA_KEY not in app.storage.user or not app.storage.user[FORM_DATA_KEY]:
        ui.notify("Chưa có dữ liệu để tạo PDF. Vui lòng điền thông tin.", type='warning')
        return

    form_data_main_app: Dict[str, Any] = cast(Dict[str, Any], app.storage.user).get(FORM_DATA_KEY, {})
    
    # Call the utility function to get the mapped data
    data_to_fill_pdf: Dict[str, Any] = generate_pdf_data_mapping(
        form_data_app=form_data_main_app,
        date_format_nicegui_app=DATE_FORMAT_NICEGUI,
        work_df_key_app=WORK_DF_KEY,
        same_address1_key_app=SAME_ADDRESS1_KEY,
        party_membership_key_app=PARTY_MEMBERSHIP_KEY,
        party_date_key_app=PARTY_DATE_KEY,
        ethnicity_step4_key_app=ETHNICITY_STEP4_KEY,
        religion_step4_key_app=RELIGION_STEP4_KEY,
        max_work_entries_pdf=5 # Adjust if your PDF supports a different number
    )

    output_pdf_path_str: Optional[str] = None
    try:
        if not os.path.exists(PDF_TEMPLATE_PATH):
            ui.notify(f"Lỗi nghiêm trọng: Không tìm thấy file mẫu PDF tại '{PDF_TEMPLATE_PATH}'. Vui lòng kiểm tra lại cấu hình.", multi_line=True, close_button=True)
            return

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmpfile_obj:
            output_pdf_path_str = tmpfile_obj.name
        
        fillpdfs.write_fillable_pdf(    # type: ignore
            input_pdf_path=PDF_TEMPLATE_PATH,
            output_pdf_path=output_pdf_path_str,
            data_dict=data_to_fill_pdf,
            flatten=True
        )
        
        pdf_content_bytes: bytes = Path(output_pdf_path_str).read_bytes()
        
        ui.download(src=pdf_content_bytes, filename="SoYeuLyLich_DaDien.pdf")
        ui.notify("Đã tạo PDF thành công! Kiểm tra mục tải xuống của bạn.", type='positive', close_button=True)

    except FileNotFoundError:
        ui.notify(f"Lỗi: File mẫu PDF '{PDF_TEMPLATE_PATH}' không tồn tại.", multi_line=True, close_button=True)
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi tạo PDF: {e}")
        import traceback
        traceback.print_exc()
        ui.notify(f"Đã xảy ra lỗi khi tạo PDF. Vui lòng thử lại hoặc liên hệ quản trị viên. Chi tiết: {e}", type='negative', multi_line=True, close_button=True)
    finally:
        if output_pdf_path_str and os.path.exists(output_pdf_path_str):
            try:
                os.remove(output_pdf_path_str)
            except Exception as e_del: # pragma: no cover
                print(f"Lỗi khi xóa file tạm '{output_pdf_path_str}': {e_del}")


# --- UI Rendering Functions for Each Step ---

@ui.refreshable
def render_step0() -> None:
    ui.label('Bắt đầu hồ sơ – Bạn đang nộp cho ai?').classes('text-h6 q-mb-md')
    ui.markdown('Bạn đang chuẩn bị nộp hồ sơ cho công ty tư nhân, hay cơ quan nhà nước/quân đội?')
    
    options_step0: Dict[str, str] = {'Không': 'Không (Công ty tư nhân)', 'Có': 'Có (Cơ quan Nhà nước/Quân đội)'}
    
    form_data_ref: Dict[str, Any] = cast(Dict[str, Any], app.storage.user[FORM_DATA_KEY])
    
    # Ensure key exists with a default if not set by create_field or initialization
    current_val_step0: str = cast(str, form_data_ref.get(STEP0_ANS_KEY, 'Không'))

    ui.radio(options_step0, value=current_val_step0,
             on_change=lambda e: cast(Dict[str, Any], app.storage.user[FORM_DATA_KEY]).update({STEP0_ANS_KEY: e.value})) \
        .props('inline')
    
    def _on_next_step0() -> None:
        current_form_data_on_next = cast(Dict[str, Any], app.storage.user[FORM_DATA_KEY])
        ans: Any = current_form_data_on_next.get(STEP0_ANS_KEY)
        app.storage.user[NEED_CLEARANCE_KEY] = (ans == 'Có')
        next_step()

    ui.button("Xác nhận & Tiếp tục →", on_click=_on_next_step0).classes('q-mt-md').props('color=primary unelevated')

@ui.refreshable
def render_step1() -> None:
    ui.label('Thông tin cá nhân').classes('text-h6 q-mb-sm')
    ui.markdown('Hãy điền thông tin cá nhân cơ bản nhé. Đừng lo, bạn có thể chỉnh sửa lại sau.')
    global_current_validators.clear()

    create_field('Họ và tên (IN HOA)', 'full_name', Vl.validate_full_name)
    create_field('Nam/Nữ', 'gender', Vl.validate_gender, input_type='select', options=['', 'Nam', 'Nữ'])
    create_field('Ngày sinh', 'dob', Vl.validate_dob, input_type='date',
                 date_min_max=(date(1900, 1, 1), date.today()))

    ui.separator().classes('q-my-md')
    ui.label("CMND/CCCD").classes('text-subtitle1 q-mb-xs')

    with ui.row().classes('w-full no-wrap q-gutter-x-md items-start'):
        with ui.column().classes('col'):
            create_field('Số CMND/CCCD', 'id_passport_num', Vl.validate_id_number)
        with ui.column().classes('col-auto').style('min-width: 200px;'):
            create_field('Cấp ngày', 'id_passport_issue_date', Vl.validate_id_issue_date, 
                         input_type='date', date_min_max=(date(1900, 1, 1), date.today()))
        with ui.column().classes('col'):
            create_field('Nơi cấp', 'id_passport_issue_place', Vl.validate_id_issue_place)
    
    with ui.row().classes('w-full q-mt-lg justify-between items-center'):
        ui.button("← Quay lại", on_click=prev_step).props('flat color=grey')
        def _on_confirm_step1() -> None:
            app.storage.user[FORM_ATTEMPTED_SUBMISSION_KEY] = True
            all_valid: bool = run_validators_and_update_error_messages()
            if all_valid:
                ui.notify("Thông tin cá nhân hợp lệ!", type='positive', position='top-right', duration=2000)
                next_step()
            else:
                ui.notify('Vui lòng sửa các lỗi trong biểu mẫu.', type='negative', position='top-right')
                render_step1.refresh()
        ui.button("Xác nhận & Tiếp tục →", on_click=_on_confirm_step1).props('color=primary unelevated')

@ui.refreshable
def render_step2() -> None:
    ui.label('Liên lạc & Địa chỉ').classes('text-h6 q-mb-sm')
    ui.markdown('Chúng tôi cần thông tin liên lạc và địa chỉ để liên hệ với bạn khi cần thiết.')
    global_current_validators.clear()

    form_data_s2: Dict[str, Any] = cast(Dict[str, Any], app.storage.user[FORM_DATA_KEY])

    create_field('Địa chỉ hộ khẩu', 'registered_address', Vl.validate_address)

    create_field('Số điện thoại', 'phone', Vl.validate_phone)
    create_field('Email', 'email', Vl.validate_email)
    create_field('Khi cần báo tin cho ai (Tên, Quan hệ)', 'emergency_contact_combined', Vl.validate_emergency_contact)
    emergency_place_input: Optional[Element] = create_field('Địa chỉ báo tin (Ở đâu)', 'emergency_place', Vl.validate_emergency_contact_address)

    def toggle_emergency_address(value: bool, 
                                 regist_addr_key: str = 'registered_address', 
                                 emerg_place_key: str = 'emergency_place', 
                                 input_el: Optional[Element] = None) -> None:
        local_form_data = cast(Dict[str, Any], app.storage.user[FORM_DATA_KEY])
        local_form_data[SAME_ADDRESS2_KEY] = value
        if value:
            regist_addr_val: Any = local_form_data.get(regist_addr_key, '')
            local_form_data[emerg_place_key] = regist_addr_val
            if input_el: 
                if isinstance(input_el, ui.input):
                    input_el.set_value(regist_addr_val)
                input_el.props('disable')
                input_el.update()
        else:
            if input_el: 
                input_el.props(remove='disable')
                input_el.update()

    ui.checkbox('Nơi báo tin giống địa chỉ hộ khẩu',
                value=cast(bool, form_data_s2.get(SAME_ADDRESS2_KEY, False)),
                on_change=lambda e: toggle_emergency_address(e.value, input_el=emergency_place_input)) \
        .classes('q-mb-sm')

    if form_data_s2.get(SAME_ADDRESS2_KEY, False) and emergency_place_input:
        emergency_place_input.props('disable')

    with ui.row().classes('w-full q-mt-lg justify-between items-center'):
        ui.button("← Quay lại", on_click=prev_step).props('flat color=grey')
        def _on_confirm_step2() -> None:
            app.storage.user[FORM_ATTEMPTED_SUBMISSION_KEY] = True
            all_valid: bool = run_validators_and_update_error_messages()
            if all_valid:
                ui.notify("Thông tin liên lạc hợp lệ!", type='positive', position='top-right', duration=2000)
                next_step()
            else:
                ui.notify('Vui lòng sửa các lỗi trong biểu mẫu.', type='negative', position='top-right')
                render_step2.refresh()
        ui.button("Xác nhận & Tiếp tục →", on_click=_on_confirm_step2).props('color=primary unelevated')


@ui.refreshable
def render_step3() -> None:
    ui.label('Học vấn & Kinh nghiệm làm việc').classes('text-h6 q-mb-sm')
    ui.markdown('Bạn đã học và làm việc ở đâu? Chia sẻ để chúng tôi hiểu thêm về bạn.')
    global_current_validators.clear()
    ui.separator().classes('q-my-md')

    validate_not_empty_local: ValidationFuncType = \
        lambda x_val: (True, '') if x_val and isinstance(x_val, str) and x_val.strip() else \
                  (False, 'Vui lòng không để trống trường này.')
    
    para_degrees_list: List[str] = getattr(para, 'degrees', [])
    first_degree_option_val: str = para_degrees_list[0] if para_degrees_list else ""
    
    validate_degree_local: ValidationFuncType = \
        lambda x_val: (True, '') if x_val and x_val != first_degree_option_val else \
                  (False, 'Vui lòng chọn bằng cấp.')

    with ui.row().classes('w-full q-gutter-md q-mb-md items-start'):
        create_field('Bằng cấp cao nhất', 'highest_education', validate_degree_local,
                     input_type='select', options=para_degrees_list, select_value_key=None) 
        create_field('Chuyên ngành đào tạo', 'specialized_area', validate_not_empty_local)

    ui.label("Quá trình công tác").classes('text-subtitle1 q-mt-md q-mb-sm')
    
    form_data_s3: Dict[str, Any] = cast(Dict[str, Any], app.storage.user[FORM_DATA_KEY])
    if WORK_DF_KEY not in form_data_s3 or not isinstance(form_data_s3.get(WORK_DF_KEY), list):
        form_data_s3[WORK_DF_KEY] = []
    
    work_history_container: ui.column = ui.column().classes('w-full')
    
    # Forward declare the refreshable function variable if needed for add/remove, or rely on its global scope
    # render_work_history_rows_actual: Optional[Callable[[],None]] = None 

    @ui.refreshable
    def render_work_history_rows() -> None:
        work_history_container.clear()
        with work_history_container:
            current_form_data_render = cast(Dict[str, Any], app.storage.user[FORM_DATA_KEY])
            current_work_df_list = cast(List[Dict[str, Any]], current_form_data_render.get(WORK_DF_KEY, []))

            if not current_work_df_list:
                ui.label("Chưa có kinh nghiệm làm việc nào được thêm.").classes(
                    "text-italic text-grey q-pa-md text-center full-width")

            for i, entry_dict in enumerate(current_work_df_list):
                with ui.row().classes('w-full items-center q-gutter-x-sm q-mb-xs'):
                    def _update_work_entry(e: ValueChangeEventArguments, index_val: int, key_val: str) -> None:
                        form_data_for_update = cast(Dict[str, Any], app.storage.user[FORM_DATA_KEY])
                        work_list_for_update = cast(List[Dict[str, Any]], form_data_for_update[WORK_DF_KEY])
                        if 0 <= index_val < len(work_list_for_update):
                             work_list_for_update[index_val][key_val] = e.value

                    ui.input('Từ (tháng/năm)', value=str(entry_dict.get("Từ (tháng/năm)", "")),
                             on_change=lambda ev, idx=i: _update_work_entry(ev, idx, "Từ (tháng/năm)")) \
                        .props('dense outlined mask="##/####" fill-mask placeholder="MM/YYYY"').classes('col')
                    
                    ui.input('Đến (tháng/năm)', value=str(entry_dict.get("Đến (tháng/năm)", "")),
                             on_change=lambda ev, idx=i: _update_work_entry(ev, idx, "Đến (tháng/năm)")) \
                        .props('dense outlined mask="##/####" fill-mask placeholder="MM/YYYY"').classes('col')
                    
                    ui.input('Nhiệm vụ công tác (ghi ngắn gọn)', value=str(entry_dict.get("Nhiệm vụ công tác", "")),
                             on_change=lambda ev, idx=i: _update_work_entry(ev, idx, "Nhiệm vụ công tác")) \
                        .props('dense outlined').classes('col-3')
                    
                    ui.input('Đơn vị công tác', value=str(entry_dict.get("Đơn vị công tác", "")),
                             on_change=lambda ev, idx=i: _update_work_entry(ev, idx, "Đơn vị công tác")) \
                        .props('dense outlined').classes('col')
                    
                    ui.input('Chức vụ', value=str(entry_dict.get("Chức vụ", "")),
                             on_change=lambda ev, idx=i: _update_work_entry(ev, idx, "Chức vụ")) \
                        .props('dense outlined').classes('col')
                    
                    with ui.column().classes('col-auto'):
                        ui.button(icon='delete', on_click=lambda _, idx=i: remove_work_entry(idx), color='negative') \
                            .props('flat dense round padding=xs')
            
            ui.button("Thêm kinh nghiệm", on_click=add_work_entry, icon='add')\
                .classes('q-mt-sm').props('outline color=primary')
    
    # nonlocal render_work_history_rows_actual
    # render_work_history_rows_actual = render_work_history_rows # Assign the actual function

    def add_work_entry() -> None:
        form_data_add = cast(Dict[str, Any], app.storage.user[FORM_DATA_KEY])
        work_df_add = cast(List[Dict[str, Any]], form_data_add[WORK_DF_KEY])
        work_df_add.append(
            {"Từ (tháng/năm)": "", "Đến (tháng/năm)": "", "Đơn vị công tác": "", "Chức vụ": ""})
        render_work_history_rows.refresh() # Call refresh on the @ui.refreshable function directly
    
    def remove_work_entry(index_to_remove: int) -> None:
        form_data_remove = cast(Dict[str, Any], app.storage.user[FORM_DATA_KEY])
        work_df_remove = cast(List[Dict[str, Any]], form_data_remove[WORK_DF_KEY])
        if 0 <= index_to_remove < len(work_df_remove):
            del work_df_remove[index_to_remove]
        render_work_history_rows.refresh()

    render_work_history_rows() # Initial render

    with ui.row().classes('w-full q-mt-lg justify-between items-center'):
        ui.button("← Quay lại", on_click=prev_step).props('flat color=grey')
        def _on_confirm_step3() -> None:
            app.storage.user[FORM_ATTEMPTED_SUBMISSION_KEY] = True
            all_valid: bool = run_validators_and_update_error_messages()
            if all_valid:
                ui.notify("Thông tin học vấn & kinh nghiệm hợp lệ!", type='positive', 
                          position='top-right', duration=2000)
                next_step()
            else:
                ui.notify('Vui lòng sửa các lỗi trong biểu mẫu.', type='negative', position='top-right')
                render_step3.refresh()
        ui.button("Xác nhận & Tiếp tục →", on_click=_on_confirm_step3).props('color=primary unelevated')


def validate_choice_made(value_selected: Optional[str]) -> Tuple[bool, str]:
    """
    Validates that a choice has been made (value is not None or empty/whitespace).
    Suitable for mandatory select/radio fields where all options are valid data points.
    """
    if value_selected and value_selected.strip():
        return True, ""
    return False, "Vui lòng thực hiện lựa chọn cho mục này."

def validate_text_input_required(text_value: Optional[str]) -> Tuple[bool, str]:
    """Validates that a text input is not empty or just whitespace."""
    if text_value and text_value.strip():
        return True, ""
    return False, "Vui lòng không để trống trường này."

def validate_date_required(date_value: Optional[date]) -> Tuple[bool, str]:
    """Validates that a date has been selected."""
    if date_value: # Assuming create_field's arg func for date returns date object or None
        return True, ""
    return False, "Vui lòng chọn ngày."


@ui.refreshable
def render_step4() -> None:
    global_current_validators.clear()
    form_data_s4: Dict[str, Any] = cast(Dict[str, Any], app.storage.user[FORM_DATA_KEY])

    # --- 1. Handle Optional Step ---
    # If clearance is not needed, this step is optional.
    if not cast(bool, cast(Dict[str, Any], app.storage.user).get(NEED_CLEARANCE_KEY, False)):
        with ui.column().classes('items-center q-pa-md'):
            ui.icon('info', size='lg', color='info').classes('q-mb-sm')
            ui.label("Bước này không bắt buộc cho lựa chọn của bạn.").classes('text-subtitle1 text-info q-mb-md')
        with ui.row().classes('w-full q-mt-md justify-between items-center'):
            ui.button("← Quay lại", on_click=prev_step).props('flat color=grey')
            ui.button("Bỏ qua & Tiếp tục →", on_click=next_step).props('color=primary unelevated')
        return # Stop rendering further if the step is skipped

    # --- 2. Main Content for Step 4 (If Clearance is Needed) ---
    ui.label('Thông tin bổ sung cho Nhà nước/Quân đội').classes('text-h6 q-mb-sm')
    ui.markdown('Các thông tin dưới đây là bắt buộc nếu bạn nộp hồ sơ vào cơ quan Nhà nước/Quân đội.')

    # --- Section A: Party & Youth Union Information ---
    with ui.expansion("A. Thông tin Đảng/Đoàn", icon='groups').classes('w-full q-mb-md shadow-1 rounded-borders'):
        with ui.column().classes('q-pa-md'):
            # Party Membership: "Chưa vào" (Not a member) is a valid final answer.
            # Default is "Chưa vào". Validation ensures a choice is actively registered.
            create_field(
                label_text="Đảng viên Đảng CSVN?",
                storage_key=PARTY_MEMBERSHIP_KEY,
                validation_func=validate_choice_made,
                input_type='select',
                options=["Chưa vào", "Đã vào"]
            )
            if form_data_s4.get(PARTY_MEMBERSHIP_KEY) == "Đã vào":
                create_field("Ngày kết nạp Đảng", PARTY_DATE_KEY, validate_date_required, input_type='date')

            # Youth Union Membership: "Chưa vào" (Not a member) is a valid final answer.
            create_field(
                label_text="Đoàn viên TNCS Hồ Chí Minh?",
                storage_key=YOUTH_MEMBERSHIP_KEY,
                validation_func=validate_choice_made,
                input_type='select',
                options=["Chưa vào", "Đã vào"]
            )
            if form_data_s4.get(YOUTH_MEMBERSHIP_KEY) == "Đã vào":
                create_field("Ngày kết nạp Đoàn", YOUTH_DATE_KEY, validate_date_required, input_type='date')

    # --- Section B: Ethnicity & Religion ---
    with ui.expansion("B. Dân tộc & Tôn giáo", icon='public').classes('w-full q-mb-md shadow-1 rounded-borders'):
        with ui.column().classes('q-pa-md'):
            ethnic_options: List[str] = getattr(para, 'ethnic_groups_vietnam', ETHNIC_OPTIONS_DEFAULT_FOR_INIT)
            religion_options: List[str] = getattr(para, 'religion_options', RELIGION_OPTIONS_DEFAULT_FOR_INIT)

            # Ethnicity: Default 'Kinh' is a valid choice.
            create_field(
                label_text="Dân tộc",
                storage_key=ETHNICITY_STEP4_KEY,
                validation_func=validate_choice_made,
                input_type='select',
                options=ethnic_options
            )
            # Religion: Default 'Không' (No religion) is a valid choice.
            create_field(
                label_text="Tôn giáo",
                storage_key=RELIGION_STEP4_KEY,
                validation_func=validate_choice_made,
                input_type='select',
                options=religion_options
            )

    # --- Section C: Family Involvement ---
    with ui.expansion("C. Gia đình (chỉ điền nếu có người thân liên quan trực tiếp đến cách mạng/quân đội)", icon='family_restroom')\
        .classes('w-full q-mb-md shadow-1 rounded-borders'):
        with ui.column().classes('q-pa-md'):
            # Family Involvement: "Không" (No such family members) is a valid final answer.
            # Radio options for Yes/No.
            radio_options_fam: Dict[str, str] = {"Không": "Không có", "Có": "Có người thân"} # Clearer labels
            create_field(
                label_text="Gia đình có người thân (bố, mẹ, vợ/chồng, anh chị em ruột) từng/đang tham gia cách mạng, phục vụ trong quân đội hoặc giữ chức vụ trong cơ quan Nhà nước?",
                storage_key=FAMILY_INVOLVEMENT_KEY,
                validation_func=validate_choice_made, # Ensures "Không" or "Có" is selected
                input_type='radio',
                options=radio_options_fam  # ui.radio will use keys as values, values as labels
            )
            
            if form_data_s4.get(FAMILY_INVOLVEMENT_KEY) == "Có":
                ui.markdown("Vui lòng kê khai thông tin người thân đó:").classes("text-caption q-mt-sm")
                create_field("Họ tên người thân", FAM_NAME_KEY, validate_text_input_required)
                create_field("Quan hệ với bạn", FAM_RELATION_KEY, validate_text_input_required)
                create_field("Hoạt động/Chức vụ chính", FAM_ROLE_KEY, validate_text_input_required)
                create_field("Thời gian hoạt động/giữ chức vụ (VD: 1965-1975 hoặc 2000-nay)", FAM_PERIOD_KEY, validate_text_input_required)

    # --- 3. Navigation Buttons ---
    with ui.row().classes('w-full q-mt-lg justify-between items-center'):
        ui.button("← Quay lại", on_click=prev_step).props('flat color=grey')
        def _on_confirm_step4() -> None:
            app.storage.user[FORM_ATTEMPTED_SUBMISSION_KEY] = True # Mark attempt
            all_valid: bool = run_validators_and_update_error_messages()
            if all_valid:
                ui.notify("Thông tin bổ sung hợp lệ!", type='positive', position='top-right', duration=2000)
                next_step()
            else:
                ui.notify('Vui lòng kiểm tra và sửa các lỗi trong biểu mẫu.', type='negative', position='top-right')
                render_step4.refresh() # Refresh to display error messages on fields
        ui.button("Xác nhận & Tiếp tục →", on_click=_on_confirm_step4).props('color=primary unelevated')


@ui.refreshable
def render_step5() -> None:
    ui.label('Hoàn thành & Xem lại').classes('text-h6 q-mb-md') 
    ui.markdown("Vui lòng kiểm tra lại toàn bộ thông tin của bạn. Nếu có sai sót, bạn có thể quay lại các bước trước để chỉnh sửa.") 
    global_current_validators.clear() 

    form_data_s5: Dict[str, Any] = cast(Dict[str, Any], cast(Dict[str, Any], app.storage.user).get(FORM_DATA_KEY, {}))
    section_keys_map: Dict[str, List[str]] = { # Renamed to avoid conflict
        "I. Thông tin cá nhân": ['full_name', 'gender', 'dob', 'id_passport_num', 
                                 'id_passport_issue_date', 'id_passport_issue_place'],
        "II. Liên lạc & Địa chỉ": ['registered_address', SAME_ADDRESS1_KEY, 'current_address', 
                                    'phone', 'email', 'emergency_contact_combined', 
                                    SAME_ADDRESS2_KEY, 'emergency_place'],
        "III. Học vấn & Kinh nghiệm": ['highest_education', 'specialized_area'], 
    }
    step4_section_title_s5: str = "IV. Thông tin bổ sung (Nhà nước/Quân đội)" # Renamed
    step4_keys_list: List[str] = [ # Renamed
        PARTY_MEMBERSHIP_KEY, PARTY_DATE_KEY, YOUTH_MEMBERSHIP_KEY, YOUTH_DATE_KEY, 
        ETHNICITY_STEP4_KEY, RELIGION_STEP4_KEY, FAMILY_INVOLVEMENT_KEY, FAM_NAME_KEY, 
        FAM_RELATION_KEY, FAM_ROLE_KEY, FAM_PERIOD_KEY,
    ]

    for section_title, keys_in_section in section_keys_map.items():
        with ui.card().classes('w-full q-mb-md shadow-2'):
            with ui.card_section().classes('bg-grey-2'): 
                ui.label(section_title).classes('text-subtitle1 text-weight-medium')
            ui.separator()
            with ui.card_section().classes('q-gutter-y-sm'): 
                for key_str in keys_in_section:
                    # Ensure 'same_address' booleans which might not be created by create_field are shown
                    if key_str in form_data_s5 or key_str.startswith('same_address'): 
                        value_item: Any = form_data_s5.get(key_str)
                        with ui.row().classes('w-full items-center'):
                            ui.label(f"{get_label_for_key(key_str)}:").classes('col-xs-12 col-sm-4 text-grey-8') 
                            display_val_str: str = format_display_value(
                                key_str, value_item, DATE_FORMAT_NICEGUI, DATE_FORMAT_DISPLAY)
                            ui.markdown(display_val_str).classes('col-xs-12 col-sm-8 text-weight-bold')
    
    work_df_list_s5 = cast(List[Dict[str,Any]], form_data_s5.get(WORK_DF_KEY, []))
    if work_df_list_s5: # Simpler check if list is not empty
        with ui.card().classes('w-full q-mb-md shadow-2'):
            with ui.card_section().classes('bg-grey-2'):
                ui.label(get_label_for_key(WORK_DF_KEY)).classes('text-subtitle1 text-weight-medium')
            ui.separator()
            with ui.card_section():
                # No need for "if not form_data_s5[WORK_DF_KEY]" as outer if handles empty list
                with ui.list().props('dense separator'):
                    for i, entry_item in enumerate(work_df_list_s5): # Renamed entry
                        with ui.item().classes('q-py-sm'):
                            with ui.item_section():
                                ui.markdown(
                                    f"**{i+1}. Từ {entry_item.get('Từ (tháng/năm)', '-')} đến {entry_item.get('Đến (tháng/năm)', '-')}:**"
                                    f"<br>&nbsp;&nbsp;&nbsp;Đơn vị: {entry_item.get('Đơn vị công tác', '-') or '-'}"
                                    f"<br>&nbsp;&nbsp;&nbsp;Chức vụ: {entry_item.get('Chức vụ', '-') or '-'}")

    if cast(bool, cast(Dict[str, Any], app.storage.user).get(NEED_CLEARANCE_KEY, False)):
        with ui.card().classes('w-full q-mb-md shadow-2'):
            with ui.card_section().classes('bg-grey-2'):
                ui.label(step4_section_title_s5).classes('text-subtitle1 text-weight-medium')
            ui.separator()
            with ui.card_section().classes('q-gutter-y-sm'):
                any_step4_data_found: bool = False # Renamed
                for key_s4_item in step4_keys_list: # Renamed key
                    if key_s4_item in form_data_s5 and \
                       form_data_s5[key_s4_item] is not None and \
                       str(form_data_s5[key_s4_item]).strip() != "":
                        any_step4_data_found = True
                        with ui.row().classes('w-full items-center'):
                            ui.label(f"{get_label_for_key(key_s4_item)}:").classes('col-xs-12 col-sm-5 text-grey-8') 
                            display_val_s4: str = format_display_value( # Renamed
                                key_s4_item, form_data_s5[key_s4_item], DATE_FORMAT_NICEGUI, DATE_FORMAT_DISPLAY)
                            ui.markdown(display_val_s4).classes('col-xs-12 col-sm-7 text-weight-bold')
                if not any_step4_data_found:
                    ui.label("Không có thông tin bổ sung nào được điền.").classes("text-italic text-grey q-pa-sm")

    ui.button("Tạo PDF", on_click=create_and_download_pdf)\
        .props('color=green unelevated').classes('q-mt-md q-mb-lg') 
    with ui.row().classes('w-full justify-start items-center'): 
        ui.button("← Quay lại & Chỉnh sửa", on_click=prev_step).props('flat color=grey')

# --- Helper functions for render_step5 ---
def format_display_value(key_param: str, value_param: Any, 
                         date_format_nicegui_param: str, 
                         date_format_display_param: str) -> str:
    if isinstance(value_param, bool): 
        return "**Có**" if value_param else "Không" # Boolean values for 'same_addressX'
    
    date_keys_list: List[str] = ['dob', 'id_passport_issue_date', PARTY_DATE_KEY, YOUTH_DATE_KEY, 
                               'enlist_date', 'discharge_date'] # Use constants
    if key_param in date_keys_list and isinstance(value_param, str) and value_param: # Ensure value_param is not empty str
        try: 
            return datetime.strptime(value_param, date_format_nicegui_param).strftime(date_format_display_param)
        except ValueError: 
            return value_param # Return original if parsing fails but it's not empty
    
    if value_param is None or (isinstance(value_param, str) and not value_param.strip()): # Check for None or empty/whitespace string
        return "<em>(Chưa điền)</em>"
    
    return f"**{str(value_param)}**"

def get_label_for_key(key_str_param: str) -> str:
    labels_map: Dict[str, str] = {
        'full_name': 'Họ và tên', 'gender': 'Giới tính', 'dob': 'Ngày sinh',
        'id_passport_num': 'Số CMND/CCCD', 'id_passport_issue_date': 'Ngày cấp CMND/CCCD',
        'id_passport_issue_place': 'Nơi cấp CMND/CCCD', 'registered_address': 'Địa chỉ hộ khẩu',
        'current_address': 'Chỗ ở hiện nay', SAME_ADDRESS1_KEY: 'Chỗ ở hiện nay giống hộ khẩu',
        'phone': 'Số điện thoại', 'email': 'Email',
        'emergency_contact_combined': 'Khi cần báo tin cho', 
        'emergency_place': 'Địa chỉ báo tin', SAME_ADDRESS2_KEY: 'Nơi báo tin giống chỗ ở hiện nay',
        'highest_education': 'Bằng cấp cao nhất', 'specialized_area': 'Chuyên ngành đào tạo',
        WORK_DF_KEY: 'III. Quá trình công tác',
        STEP0_ANS_KEY: 'Nộp cho cơ quan Nhà nước/Quân đội',
        PARTY_MEMBERSHIP_KEY: 'Đảng viên ĐCSVN', PARTY_DATE_KEY: 'Ngày kết nạp Đảng',
        YOUTH_MEMBERSHIP_KEY: 'Đoàn viên TNCS', YOUTH_DATE_KEY: 'Ngày kết nạp Đoàn',
        ETHNICITY_STEP4_KEY: 'Dân tộc', RELIGION_STEP4_KEY: 'Tôn giáo',
        FAMILY_INVOLVEMENT_KEY: 'Gia đình từng tham gia cách mạng/quân đội',
        FAM_NAME_KEY: 'Họ tên người thân (CM/QĐ)', FAM_RELATION_KEY: 'Quan hệ',
        FAM_ROLE_KEY: 'Hoạt động/Chức vụ', FAM_PERIOD_KEY: 'Thời gian',
    }
    return labels_map.get(key_str_param, key_str_param.replace('_', ' ').title())

# --- Helper to initialize form_data structure ---
def _initialize_form_data(form_data_dict_param: Dict[str, Any]) -> None:
    """Helper to initialize form_data structure with default values."""
    form_data_dict_param[STEP0_ANS_KEY] = 'Không'
    form_data_dict_param[WORK_DF_KEY] = []
    form_data_dict_param[SAME_ADDRESS1_KEY] = False
    form_data_dict_param[SAME_ADDRESS2_KEY] = False
    form_data_dict_param[PARTY_MEMBERSHIP_KEY] = "Chưa vào" # Default for step 4 conditional fields
    form_data_dict_param[PARTY_DATE_KEY] = None 
    form_data_dict_param[YOUTH_MEMBERSHIP_KEY] = "Chưa vào"
    form_data_dict_param[YOUTH_DATE_KEY] = None
    form_data_dict_param[FAMILY_INVOLVEMENT_KEY] = "Không"
    form_data_dict_param[ETHNICITY_STEP4_KEY] = 'Kinh'
    form_data_dict_param[RELIGION_STEP4_KEY] = "Không"
    form_data_dict_param[FAM_NAME_KEY] = ""
    form_data_dict_param[FAM_RELATION_KEY] = ""
    form_data_dict_param[FAM_ROLE_KEY] = ""
    form_data_dict_param[FAM_PERIOD_KEY] = ""


# --- update_step_content, main_page, ui.run() ---
@ui.refreshable
def update_step_content() -> None:
    current_step_val: int = cast(int, cast(Dict[str, Any], app.storage.user).get(STEP_KEY, 0))
    
    if current_step_val == 0: render_step0()
    elif current_step_val == 1: render_step1()
    elif current_step_val == 2: render_step2()
    elif current_step_val == 3: render_step3()
    elif current_step_val == 4: render_step4()
    elif current_step_val == 5: render_step5()
    else:
        ui.label(f"Lỗi: Bước không xác định ({current_step_val})").classes('text-negative text-h6')
        def reset_app_func() -> None:
            app.storage.user[STEP_KEY] = 0
            new_form_data_reset: Dict[str, Any] = {}
            _initialize_form_data(new_form_data_reset)
            app.storage.user[FORM_DATA_KEY] = new_form_data_reset
            app.storage.user[FORM_ATTEMPTED_SUBMISSION_KEY] = False
            app.storage.user[NEED_CLEARANCE_KEY] = False
            
            global_current_validators.clear()
            global_validation_error_messages.clear()
            update_step_content.refresh()
        ui.button("Bắt đầu lại", on_click=reset_app_func).props('color=primary unelevated')

@ui.page('/')
def main_page() -> None:
    if STEP_KEY not in app.storage.user: # Check if session needs initialization
        app.storage.user.clear() 
        app.storage.user[STEP_KEY] = 0
        
        initial_form_data: Dict[str, Any] = {}
        _initialize_form_data(initial_form_data)
        app.storage.user[FORM_DATA_KEY] = initial_form_data
        
        app.storage.user[FORM_ATTEMPTED_SUBMISSION_KEY] = False
        app.storage.user[NEED_CLEARANCE_KEY] = False

    ui.query('body').style('background-color: #f0f2f5;')
    
    with ui.header(elevated=True).classes('bg-primary text-white q-pa-sm items-center'):
        ui.label("📝 AutoLý – Kê khai Sơ yếu lý lịch").classes('text-h5')
        ui.space()
        # Debug menu (ensure values are JSON serializable for ui.json_editor)
        # Example for debug menu items
        # with ui.button(icon='bug_report', color='white').props('flat round dense'):
        #     with ui.menu().classes('bg-grey-2 shadow-3'):
        #         with ui.card().style("min-width: 350px; max-width: 90vw;"):
        #             ui.label(f"Step: {app.storage.user.get(STEP_KEY)}")
        #             ui.json_editor({'value': cast(Dict[str,Any], app.storage.user.get(FORM_DATA_KEY, {}))}).props('readonly')
        #             ui.json_editor({'value': global_validation_error_messages}).props('readonly')


    with ui.card().classes('q-mx-auto q-my-md q-pa-md shadow-4 rounded-borders') \
                  .style('width: 95%; max-width: 900px; min-height: 75vh; \
                          max-height: calc(100vh - 120px); display: flex; flex-direction: column;'):
        with ui.column().classes('col w-full q-pa-md scroll'):
            update_step_content()

# Ensure this is the last call, especially if uvicorn_reload_dirs is used.
if __name__ in {"__main__", "__mp_main__"}: # Standard NiceGUI practice for run
    if not os.path.exists(PDF_TEMPLATE_PATH):
        print(f"WARNING: PDF template not found at '{PDF_TEMPLATE_PATH}'. PDF generation will fail.")
        
    ui.run(storage_secret='a_secure_and_unique_secret_string_for_this_app!',
           uvicorn_reload_dirs='.', uvicorn_reload_includes='*.py')
