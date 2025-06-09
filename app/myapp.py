# myapp.py

# ===================================================================
# 1. IMPORTS
# All your `from nicegui import ...` etc. go here.
# ===================================================================
from nicegui import ui, app
from nicegui.element import Element
from nicegui.events import ValueChangeEventArguments
from datetime import date
from typing import Any, Callable, List, Dict, Optional, Tuple, TypedDict, cast

# Assuming validation.py and para.py are in the same directory or accessible in PYTHONPATH
from validation import Vl
import para # Your lists of options
from fillpdf import fillpdfs  # type: ignore[import]
import tempfile
import os
from pathlib import Path

# Import constants and shared utilities from utils.py
from utils import (
    generate_pdf_data_mapping, create_field,
    format_display_value, get_label_for_key,
    initialize_form_data,
    ValidatorEntryType, ValidationFuncType,
    # --- Core App Storage Keys ---
    DATE_FORMAT_NICEGUI, DATE_FORMAT_DISPLAY,
    STEP_KEY, FORM_DATA_KEY, NEEDS_CLEARANCE_KEY,
    FORM_ATTEMPTED_SUBMISSION_KEY, CURRENT_STEP_ERRORS_KEY,
    # --- Form Data Keys ---
    STEP0_ANS_KEY,
    # Step 1
    FULL_NAME_KEY, GENDER_KEY, DOB_KEY,
    ID_PASSPORT_NUM_KEY, ID_PASSPORT_ISSUE_DATE_KEY, ID_PASSPORT_ISSUE_PLACE_KEY,
    HEALTH_KEY, HEIGHT_KEY, WEIGHT_KEY, # New health keys
    # Step 2
    PLACE_OF_ORIGIN_KEY,
    BIRTH_PLACE_KEY, REGISTERED_ADDRESS_KEY, PHONE_KEY,
    EMERGENCY_CONTACT_COMBINED_KEY, EMERGENCY_PLACE_KEY,
    SAME_ADDRESS1_KEY, 
    # Step 3
    EDUCATION_HIGH_SCHOOL_KEY, EDUCATION_HIGHEST_KEY, EDUCATION_MAJOR_KEY,
    WORK_DF_KEY, WORK_FROM_DATE_KEY, WORK_TO_DATE_KEY,
    WORK_TASK_KEY, WORK_UNIT_KEY, WORK_ROLE_KEY,
    # Step 4 (NEW - Family)
    DAD_NAME_KEY, DAD_AGE_KEY, DAD_JOB_KEY,
    MOM_NAME_KEY, MOM_AGE_KEY, MOM_JOB_KEY,
    SPOUSE_NAME_KEY, SPOUSE_AGE_KEY, SPOUSE_JOB_KEY,
    SIBLINGS_KEY, CHILDREN_KEY,
    # Step 5 (Old Step 4 - Clearance)
    PARTY_MEMBERSHIP_KEY, PARTY_DATE_KEY, YOUTH_MEMBERSHIP_KEY, YOUTH_DATE_KEY,
    ETHNICITY_KEY, RELIGION_KEY,
    # Default options
    ETHNIC_OPTIONS_DEFAULT_FOR_INIT, RELIGION_OPTIONS_DEFAULT_FOR_INIT,
    PDF_TEMPLATE_PATH, PDF_FILENAME
)

# ===================================================================
# 2. HELPER & NAVIGATION FUNCTIONS
# (Functions that DON'T depend on STEPS_DEFINITION yet)
# ===================================================================

# --- Validation Execution Function ---
def execute_step_validators(
    validators_for_step: List[ValidatorEntryType],
    form_data: Dict[str, Any] # fetched from app.storage.user
) -> Tuple[bool, Dict[str, str]]:
    
    new_errors: Dict[str, str] = {}
    all_valid: bool = True
    
    for field_key, validator_func, validation_args_func, error_prefix in validators_for_step:
        # ValidationArgsFuncType expects an argument (the field_key/storage_key)
        value_to_validate: Any = validation_args_func(form_data, field_key)
        
        is_valid: bool
        msg: str
        is_valid, msg = validator_func(value_to_validate)
        if not is_valid:
            all_valid = False
            new_errors[field_key] = f"{error_prefix} {msg}"
    return all_valid, new_errors

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++ PDF GENERATION ORCHESTRATION (uses utils.generate_pdf_data_mapping)   ++
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
async def create_and_download_pdf() -> None:
    """
    Orchestrates PDF generation using the utility mapping function
    and handles NiceGUI interactions (storage, notifications, download).
    """
    user_storage = cast(Dict[str, Any], app.storage.user)
    if FORM_DATA_KEY not in user_storage or not user_storage[FORM_DATA_KEY]:
        ui.notify("Chưa có dữ liệu để tạo PDF. Vui lòng điền thông tin.", type='warning')
        return

    app_form_data: Dict[str, Any] = user_storage.get(FORM_DATA_KEY, {})
    
    # Call the utility function to get the mapped data
    data_to_fill_pdf: Dict[str, Any] = generate_pdf_data_mapping(
        form_data_app=app_form_data,
        date_format_nicegui_app=DATE_FORMAT_NICEGUI,
    )

    output_pdf_path_str: Optional[str] = None
    try:
        if not os.path.exists(PDF_TEMPLATE_PATH):
            ui.notify(f"Lỗi nghiêm trọng: Không tìm thấy file mẫu PDF tại '{PDF_TEMPLATE_PATH}'. \
                      Vui lòng kiểm tra lại cấu hình.", multi_line=True, close_button=True)
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
        ui.download(src=pdf_content_bytes, filename=PDF_FILENAME)
        ui.notify("Đã tạo PDF thành công! Kiểm tra mục tải xuống của bạn.", type='positive', close_button=True)

    except FileNotFoundError:
        ui.notify(f"Lỗi: File mẫu PDF '{PDF_TEMPLATE_PATH}' không tồn tại.", multi_line=True, close_button=True)
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi tạo PDF: {e}")
        import traceback
        traceback.print_exc()
        ui.notify(f"Đã xảy ra lỗi khi tạo PDF. Vui lòng thử lại hoặc liên hệ quản trị viên. Chi tiết: {e}", 
                  type='negative', multi_line=True, close_button=True)
    finally:
        if output_pdf_path_str and os.path.exists(output_pdf_path_str):
            try: os.remove(output_pdf_path_str)
            except Exception as e_del: print(f"Lỗi khi xóa file tạm '{output_pdf_path_str}': {e_del}")

# In myapp.py
_is_handling_confirmation: bool = False # Global flag to prevent re-entr
def _handle_step_confirmation(
    validators_for_step: List[ValidatorEntryType],
    success_message: str = "Thông tin hợp lệ!") -> None:
    global _is_handling_confirmation

    if _is_handling_confirmation: return
    _is_handling_confirmation = True
    try:
        user_storage = cast(Dict[str, Any], app.storage.user)
        current_form_data = cast(Dict[str, Any], user_storage.get(FORM_DATA_KEY, {}))
        all_valid, new_errors = execute_step_validators(validators_for_step, current_form_data)
        if all_valid:
            user_storage[CURRENT_STEP_ERRORS_KEY] = {}
            user_storage[FORM_ATTEMPTED_SUBMISSION_KEY] = False
            ui.notify(success_message, type='positive', position='top-right', duration=2000)
            next_step() # This is the goal!
        else:
            user_storage[FORM_ATTEMPTED_SUBMISSION_KEY] = True
            user_storage[CURRENT_STEP_ERRORS_KEY] = new_errors
            ui.notify('Vui lòng sửa các lỗi trong biểu mẫu.', type='negative', position='top-right')
    finally:
        _is_handling_confirmation = False


# ===================================================================
# 3. UI RENDER FUNCTIONS (THE BUILDING BLOCKS)
# Define all the parts of your UI first.
# ===================================================================
# --- UI Rendering Functions for Each Step ---

@ui.refreshable
def render_step2() -> None:
    ui.label('Liên lạc & Địa chỉ').classes('text-h6 q-mb-sm')
    ui.markdown('Chúng tôi cần thông tin liên lạc và địa chỉ để liên hệ với bạn khi cần thiết.')
    
    validators_for_step2: List[ValidatorEntryType] = []
    user_storage: Dict[str, Any] = cast(Dict[str, Any], app.storage.user)
    current_form_data: Dict[str, Any] = cast(Dict[str, Any], user_storage[FORM_DATA_KEY])
    current_step_errors: Dict[str, str] = user_storage.get(CURRENT_STEP_ERRORS_KEY, {})
    form_attempted: bool = user_storage.get(FORM_ATTEMPTED_SUBMISSION_KEY, False)


    def _add_field(label: str, key: str, val_func: ValidationFuncType, **kwargs: Any)-> Optional[Element]:
        element, validator_entry = create_field(
            label_text=label, storage_key=key, validation_func=val_func,
            error_message_for_field=current_step_errors.get(key),
            form_attempted=form_attempted, **kwargs)
        validators_for_step2.append(validator_entry)
        return element
    
    # --- Field Creation using the helper ---
    if user_storage[NEEDS_CLEARANCE_KEY]:
        _add_field('Nguyên quán (Nơi sinh của bố)', PLACE_OF_ORIGIN_KEY, Vl.validate_address)

    if user_storage[NEEDS_CLEARANCE_KEY]:
        _add_field('Khi cần báo tin cho ai (Tên, Quan hệ)', \
                EMERGENCY_CONTACT_COMBINED_KEY, Vl.validate_emergency_contact)
        
        emergency_place_input: Optional[Element] = _add_field(
            'Địa chỉ báo tin (Ở đâu)', EMERGENCY_PLACE_KEY, Vl.validate_emergency_contact_address)

        def toggle_emergency_address(is_same: bool, 
                                    target_input_el: Optional[Element] = \
                                    emergency_place_input) -> None:
            if is_same:
                addr_to_copy: Any = current_form_data.get(REGISTERED_ADDRESS_KEY, '')
                current_form_data[EMERGENCY_PLACE_KEY] = addr_to_copy
                if target_input_el and isinstance(target_input_el, ui.input):
                    target_input_el.set_value(addr_to_copy)
                    target_input_el.props('disable').update()
            else:
                if target_input_el: target_input_el.props(remove='disable').update()
        
        def handle_checkbox_change(event: ValueChangeEventArguments) -> None:
            new_checkbox_value: bool = cast(bool, event.value)
            # Ensure you are updating the correct dictionary reference from user_storage
            form_data_from_storage = cast(Dict[str, Any], app.storage.user[FORM_DATA_KEY])
            form_data_from_storage[SAME_ADDRESS1_KEY] = new_checkbox_value
            toggle_emergency_address(new_checkbox_value) 

        form_data_s2: Dict[str, Any] = cast(Dict[str, Any], app.storage.user[FORM_DATA_KEY])
        ui.checkbox('Nơi báo tin giống địa chỉ hộ khẩu',
                    value=cast(bool, form_data_s2.get(SAME_ADDRESS1_KEY, False)),
                    on_change=handle_checkbox_change) \
            .classes('q-mb-sm')

        if form_data_s2.get(SAME_ADDRESS1_KEY, False) and emergency_place_input:
            if isinstance(emergency_place_input, ui.input): emergency_place_input.props('disable')

    with ui.row().classes('w-full q-mt-lg justify-between items-center'):
        ui.button("← Quay lại", on_click=prev_step).props('flat color=grey')
        ui.button("Xác nhận & Tiếp tục →", on_click=lambda:_handle_step_confirmation(
                      validators_for_step2,"Thông tin liên lạc & địa chỉ hợp lệ!")
            ).props('color=primary unelevated')


@ui.refreshable
def render_step3() -> None:
    ui.label('Học vấn & Kinh nghiệm làm việc').classes('text-h6 q-mb-sm')
    ui.markdown('Bạn đã học và làm việc ở đâu? Chia sẻ để chúng tôi hiểu thêm về bạn.')

    user_storage: Dict[str, Any] = cast(Dict[str, Any], app.storage.user)
    current_form_data: Dict[str, Any] = cast(Dict[str, Any], user_storage[FORM_DATA_KEY])
    current_step_errors: Dict[str, str] = user_storage.get(CURRENT_STEP_ERRORS_KEY, {})
    form_attempted: bool = user_storage.get(FORM_ATTEMPTED_SUBMISSION_KEY, False)
    validators_for_step3: List[ValidatorEntryType] = []

    validate_not_empty_local: ValidationFuncType = lambda x: (True, '') if x and isinstance(x, str) \
        and x.strip() else (False, 'Vui lòng không để trống.')
    para_degrees_list: List[str] = getattr(para, 'degrees', [''])
    first_degree_option: str = para_degrees_list[0] if para_degrees_list else ''
    validate_degree_local: ValidationFuncType = lambda x: (True, '') if x and x != first_degree_option \
        else (False, 'Vui lòng chọn bằng cấp.')

    with ui.row().classes('w-full q-gutter-md q-mb-md items-start'):
        _, edu_validator_entry = create_field(
            'Bằng cấp cao nhất', EDUCATION_HIGHEST_KEY, validate_degree_local,
                     input_type='select', options=para_degrees_list, 
                     error_message_for_field=current_step_errors.get(EDUCATION_HIGHEST_KEY),
                     form_attempted=form_attempted
        ) 
        validators_for_step3.append(edu_validator_entry)
        _, spec_validator_entry = create_field(
            'Chuyên ngành đào tạo', EDUCATION_MAJOR_KEY, validate_not_empty_local,
            error_message_for_field=current_step_errors.get(EDUCATION_MAJOR_KEY), 
            form_attempted=form_attempted
        )
        validators_for_step3.append(spec_validator_entry)

    ui.separator().classes('q-my-md')
    ui.label("Quá trình công tác").classes('text-subtitle1 q-mt-md q-mb-sm')
    if WORK_DF_KEY not in current_form_data or not isinstance(current_form_data.get(WORK_DF_KEY), list):
        current_form_data[WORK_DF_KEY] = []
    work_history_container: ui.column = ui.column().classes('w-full')
    
    # Forward declare the refreshable function variable if needed for add/remove, or rely on its global scope
    # render_work_history_rows_actual: Optional[Callable[[],None]] = None 

    @ui.refreshable
    def render_work_history_rows() -> None:
        work_history_container.clear()
        with work_history_container:
            form_data_render = cast(Dict[str, Any], user_storage[FORM_DATA_KEY])
            current_work_df_list = cast(List[Dict[str, Any]], form_data_render.get(WORK_DF_KEY, []))

            if not current_work_df_list:
                ui.label("Chưa có kinh nghiệm làm việc nào được thêm.").classes(
                    "text-italic text-grey q-pa-md text-center full-width")

            for i, entry_dict in enumerate(current_work_df_list):
                with ui.row().classes('w-full items-center q-gutter-x-sm q-mb-xs'):
                    def _update_work_entry(e: ValueChangeEventArguments, index_val: int, key_val: str) -> None:
                        upd_form_data = cast(Dict[str, Any], user_storage[FORM_DATA_KEY])
                        upd_work_list = cast(List[Dict[str, Any]], upd_form_data[WORK_DF_KEY])
                        if 0 <= index_val < len(upd_work_list):
                             upd_work_list[index_val][key_val] = e.value

                    ui.input('Từ (tháng/năm)', value=str(entry_dict.get(WORK_FROM_DATE_KEY, "")),
                             on_change=lambda ev, idx=i: _update_work_entry(ev, idx, WORK_FROM_DATE_KEY)) \
                        .props('dense outlined mask="##/####" fill-mask placeholder="MM/YYYY"').classes('col')
                    
                    ui.input('Đến (tháng/năm)', value=str(entry_dict.get(WORK_TO_DATE_KEY, "")),
                             on_change=lambda ev, idx=i: _update_work_entry(ev, idx, WORK_TO_DATE_KEY)) \
                        .props('dense outlined mask="##/####" fill-mask placeholder="MM/YYYY"').classes('col')
                    
                    ui.input('Nhiệm vụ công tác (ghi ngắn gọn)', value=str(entry_dict.get(WORK_TASK_KEY, "")),
                             on_change=lambda ev, idx=i: _update_work_entry(ev, idx, WORK_TASK_KEY)) \
                        .props('dense outlined').classes('col-3')
                    
                    ui.input('Đơn vị công tác', value=str(entry_dict.get(WORK_UNIT_KEY, "")),
                             on_change=lambda ev, idx=i: _update_work_entry(ev, idx, WORK_UNIT_KEY)) \
                        .props('dense outlined').classes('col')
                    
                    ui.input('Chức vụ', value=str(entry_dict.get(WORK_ROLE_KEY, "")),
                             on_change=lambda ev, idx=i: _update_work_entry(ev, idx, WORK_ROLE_KEY)) \
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
            {WORK_FROM_DATE_KEY: "", WORK_TO_DATE_KEY: "", 
             WORK_UNIT_KEY: "", WORK_ROLE_KEY: ""})
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
        ui.button("Xác nhận & Tiếp tục →", on_click=lambda: _handle_step_confirmation(
                      validators_for_step3, "Thông tin học vấn & kinh nghiệm hợp lệ!"))\
                        .props('color=primary unelevated')

## MENTOR NOTE: This is the new, dedicated step for family information.
@ui.refreshable
def render_step4() -> None:
    ui.label('Hoàn cảnh gia đình').classes('text-h6 q-mb-sm')
    ui.markdown('Kê khai thông tin về bố, mẹ, vợ/chồng, và các anh chị em ruột.')

    user_storage = cast(Dict[str, Any], app.storage.user)
    form_data = cast(Dict[str, Any], user_storage[FORM_DATA_KEY])
    # For this step, we'll assume simple text validation. You can make it more complex if needed.
    validators_for_step4: List[ValidatorEntryType] = []

    def _add_field(label: str, key: str, val_func: ValidationFuncType, **kwargs: Any) -> None:
        _, validator_entry = create_field(
            label_text=label, storage_key=key, validation_func=val_func,
            # No error display for simplicity in this new step, but you can add it.
            **kwargs
        )
        validators_for_step4.append(validator_entry)

    # Parents Info
    with ui.card().classes('w-full q-mb-md'):
        with ui.card_section():
            ui.label("Thông tin Bố & Mẹ").classes('text-subtitle1')
            with ui.row().classes('w-full q-gutter-md'):
                _add_field("Họ tên Bố", DAD_NAME_KEY, Vl.validate_text_input_required)
                _add_field("Tuổi Bố", DAD_AGE_KEY, Vl.validate_text_input_required)
                _add_field("Nghề nghiệp Bố", DAD_JOB_KEY, Vl.validate_text_input_required)
            with ui.row().classes('w-full q-gutter-md q-mt-sm'):
                _add_field("Họ tên Mẹ", MOM_NAME_KEY, Vl.validate_text_input_required)
                _add_field("Tuổi Mẹ", MOM_AGE_KEY, Vl.validate_text_input_required)
                _add_field("Nghề nghiệp Mẹ", MOM_JOB_KEY, Vl.validate_text_input_required)

    # Siblings Info (Dynamic List)
    ui.label("Anh chị em ruột").classes('text-subtitle1 q-mt-md')
    if SIBLINGS_KEY not in form_data: form_data[SIBLINGS_KEY] = []
    
    @ui.refreshable
    def render_sibling_rows() -> None:
        # This dynamic UI pattern is similar to work history
        for i, entry in enumerate(cast(List[Dict[str, str]], form_data[SIBLINGS_KEY])):
            with ui.row().classes('w-full items-center q-gutter-x-sm'):
                def update_sibling(e: ValueChangeEventArguments, 
                                   idx: int, key: str): form_data[SIBLINGS_KEY][idx][key] = e.value
                ui.input('Họ tên', value=entry.get('name', ''), on_change=lambda e, idx=i: update_sibling(e, idx, 'name')).props('dense outlined').classes('col')
                ui.input('Tuổi', value=entry.get('age', ''), on_change=lambda e, idx=i: update_sibling(e, idx, 'age')).props('dense outlined').classes('col-2')
                ui.input('Nghề nghiệp', value=entry.get('job', ''), on_change=lambda e, idx=i: update_sibling(e, idx, 'job')).props('dense outlined').classes('col')
                ui.input('Chỗ ở', value=entry.get('address', ''), on_change=lambda e, idx=i: update_sibling(e, idx, 'address')).props('dense outlined').classes('col')
                ui.button(icon='delete', on_click=lambda _, idx=i: (form_data[SIBLINGS_KEY].pop(idx), render_sibling_rows.refresh()), color='negative').props('flat dense round')
        ui.button("Thêm anh chị em", on_click=lambda: (form_data[SIBLINGS_KEY].append({}), render_sibling_rows.refresh()), icon='add').props('outline color=primary')
    
    render_sibling_rows()

    # Spouse and Children
    ui.label("Vợ/Chồng và các con").classes('text-subtitle1 q-mt-md')
    with ui.card().classes('w-full q-mb-md'):
        with ui.card_section():
            with ui.row().classes('w-full q-gutter-md'):
                _add_field("Họ tên Vợ/Chồng", SPOUSE_NAME_KEY, Vl.validate_text_input_required)
                _add_field("Tuổi Vợ/Chồng", SPOUSE_AGE_KEY, Vl.validate_text_input_required)
                _add_field("Nghề nghiệp Vợ/Chồng", SPOUSE_JOB_KEY, Vl.validate_text_input_required)
    
    if CHILDREN_KEY not in form_data: form_data[CHILDREN_KEY] = []
    # Similar dynamic UI for children
    @ui.refreshable
    def render_child_rows() -> None:
        for i, entry in enumerate(cast(List[Dict[str, str]], form_data[CHILDREN_KEY])):
            with ui.row().classes('w-full items-center q-gutter-x-sm'):
                def update_child(e: ValueChangeEventArguments, 
                                 idx: int, key: str): form_data[CHILDREN_KEY][idx][key] = e.value
                ui.input('Họ tên con', value=entry.get('name', ''), on_change=lambda e, idx=i: update_child(e, idx, 'name')).props('dense outlined').classes('col')
                ui.input('Tuổi', value=entry.get('age', ''), on_change=lambda e, idx=i: update_child(e, idx, 'age')).props('dense outlined').classes('col-2')
                ui.input('Nghề nghiệp', value=entry.get('job', ''), on_change=lambda e, idx=i: update_child(e, idx, 'job')).props('dense outlined').classes('col')
                ui.button(icon='delete', on_click=lambda _, idx=i: (form_data[CHILDREN_KEY].pop(idx), render_child_rows.refresh()), color='negative').props('flat dense round')
        ui.button("Thêm con", on_click=lambda: (form_data[CHILDREN_KEY].append({}), render_child_rows.refresh()), icon='add').props('outline color=primary')

    render_child_rows()

    with ui.row().classes('w-full q-mt-lg justify-between items-center'):
        ui.button("← Quay lại", on_click=prev_step).props('flat color=grey')
        ui.button("Xác nhận & Tiếp tục →", on_click=lambda: _handle_step_confirmation(validators_for_step4, "Thông tin gia đình hợp lệ!")).props('color=primary unelevated')

@ui.refreshable
def render_step5() -> None:
    # ... MENTOR NOTE: This is the old render_step4, now renamed to render_step5_clearance
    user_storage = cast(Dict[str, Any], app.storage.user)

    # ... The rest of the function is the same as the old render_step4
    current_form_data = cast(Dict[str, Any], user_storage[FORM_DATA_KEY])
    current_step_errors: Dict[str, str] = user_storage.get(CURRENT_STEP_ERRORS_KEY, {})
    form_attempted: bool = user_storage.get(FORM_ATTEMPTED_SUBMISSION_KEY, False)
    validators_for_step5: List[ValidatorEntryType] = []

    def _add_field(label: str, key: str, val_func: ValidationFuncType, **kwargs: Any) -> None:
        _, validator_entry = create_field(
            label_text=label, storage_key=key, validation_func=val_func,
            error_message_for_field=current_step_errors.get(key),
            form_attempted=form_attempted, **kwargs)
        validators_for_step5.append(validator_entry)

    ui.label('Thông tin bổ sung cho Nhà nước/Quân đội').classes('text-h6 q-mb-sm')
    with ui.expansion("A. Thông tin Đoàn/Đảng", icon='groups').classes('w-full q-mb-md shadow-1 rounded-borders'):
        with ui.column().classes('q-pa-md'):
            _add_field("Đoàn viên?", YOUTH_MEMBERSHIP_KEY, Vl.validate_choice_made, input_type='select', options=["Chưa vào", "Đã vào"])
            if current_form_data.get(YOUTH_MEMBERSHIP_KEY) == "Đã vào":
                _add_field("Ngày kết nạp Đoàn", YOUTH_DATE_KEY, Vl.validate_date_required, input_type='date')
            _add_field("Đảng viên?", PARTY_MEMBERSHIP_KEY, Vl.validate_choice_made, input_type='select', options=["Chưa vào", "Đã vào"])
            if current_form_data.get(PARTY_MEMBERSHIP_KEY) == "Đã vào":
                _add_field("Ngày kết nạp Đảng", PARTY_DATE_KEY, Vl.validate_date_required, input_type='date')
        
    with ui.row().classes('w-full q-mt-lg justify-between items-center'):
        ui.button("← Quay lại", on_click=prev_step).props('flat color=grey')
        ui.button("Xác nhận & Tiếp tục →", on_click=lambda: _handle_step_confirmation(validators_for_step5, "Thông tin bổ sung hợp lệ!")).props('color=primary unelevated')

@ui.refreshable
def render_step6() -> None:
    # ... MENTOR NOTE: This is the old render_step5, now with added sections for new data.
    ui.label('Hoàn thành & Xem lại').classes('text-h6 q-mb-md') 
    ui.markdown("Vui lòng kiểm tra lại toàn bộ thông tin của bạn.") 
    user_storage: Dict[str, Any] = cast(Dict[str, Any], app.storage.user)
    form_data: Dict[str, Any] = user_storage.get(FORM_DATA_KEY, {})

    # Section 1: Personal and Health
    with ui.card().classes('w-full q-mb-md shadow-2'):
        with ui.card_section().classes('bg-grey-2'): ui.label("I. Thông tin cá nhân").classes('text-subtitle1 text-weight-medium')
        ui.separator()
        with ui.card_section().classes('q-gutter-y-sm'):
            personal_keys = [FULL_NAME_KEY, GENDER_KEY, DOB_KEY, ID_PASSPORT_NUM_KEY, ID_PASSPORT_ISSUE_DATE_KEY, ID_PASSPORT_ISSUE_PLACE_KEY, HEALTH_KEY, HEIGHT_KEY, WEIGHT_KEY]
            for key in personal_keys:
                with ui.row():
                    ui.label(f"{get_label_for_key(key)}:").classes('col-4 text-grey-8')
                    ui.markdown(format_display_value(key, form_data.get(key), DATE_FORMAT_NICEGUI, DATE_FORMAT_DISPLAY)).classes('col-8 text-weight-bold')

    # Section 2: Contact (unchanged)
    with ui.card().classes('w-full q-mb-md shadow-2'):
        with ui.card_section().classes('bg-grey-2'): ui.label("II. Liên lạc & Địa chỉ").classes('text-subtitle1 text-weight-medium')
        ui.separator()
        with ui.card_section().classes('q-gutter-y-sm'):
            contact_keys = [REGISTERED_ADDRESS_KEY, PHONE_KEY, EMERGENCY_CONTACT_COMBINED_KEY, EMERGENCY_PLACE_KEY]
            for key in contact_keys:
                with ui.row():
                    ui.label(f"{get_label_for_key(key)}:").classes('col-4 text-grey-8')
                    ui.markdown(format_display_value(key, form_data.get(key), DATE_FORMAT_NICEGUI, DATE_FORMAT_DISPLAY)).classes('col-8 text-weight-bold')

    # Section 3: Education & Work (work history part is unchanged)
    # ... education and work history review ...
    
    # Section 4: Family
    with ui.card().classes('w-full q-mb-md shadow-2'):
        with ui.card_section().classes('bg-grey-2'): ui.label("IV. Hoàn cảnh gia đình").classes('text-subtitle1 text-weight-medium')
        ui.separator()
        with ui.card_section().classes('q-gutter-y-sm'):
            family_keys = [DAD_NAME_KEY, DAD_AGE_KEY, DAD_JOB_KEY, MOM_NAME_KEY, MOM_AGE_KEY, MOM_JOB_KEY, SPOUSE_NAME_KEY, SPOUSE_AGE_KEY, SPOUSE_JOB_KEY]
            for key in family_keys:
                with ui.row():
                    ui.label(f"{get_label_for_key(key)}:").classes('col-4 text-grey-8')
                    ui.markdown(format_display_value(key, form_data.get(key), DATE_FORMAT_NICEGUI, DATE_FORMAT_DISPLAY)).classes('col-8 text-weight-bold')
            # Display siblings and children lists
            # ... (add loops for siblings and children here) ...
    
    # Section 5: Clearance Info (if applicable)
    if user_storage.get(NEEDS_CLEARANCE_KEY, False):
        with ui.card().classes('w-full q-mb-md shadow-2'):
            with ui.card_section().classes('bg-grey-2'): ui.label("V. Thông tin bổ sung").classes('text-subtitle1 text-weight-medium')
            ui.separator()
            with ui.card_section().classes('q-gutter-y-sm'):
                clearance_keys = [PARTY_MEMBERSHIP_KEY, PARTY_DATE_KEY, YOUTH_MEMBERSHIP_KEY, YOUTH_DATE_KEY, ETHNICITY_KEY, RELIGION_KEY]
                for key in clearance_keys:
                    with ui.row():
                        ui.label(f"{get_label_for_key(key)}:").classes('col-4 text-grey-8')
                        ui.markdown(format_display_value(key, form_data.get(key), DATE_FORMAT_NICEGUI, DATE_FORMAT_DISPLAY)).classes('col-8 text-weight-bold')

    ui.button("Tạo PDF", on_click=create_and_download_pdf).props('color=green unelevated').classes('q-mt-md q-mb-lg') 
    with ui.row().classes('w-full justify-start items-center'): 
        ui.button("← Quay lại & Chỉnh sửa", on_click=prev_step).props('flat color=grey')

@ui.refreshable
def render_step_start() -> None:
    ui.label('Bắt đầu').classes('text-h6 q-mb-md')
    ui.markdown('Chào mừng bạn đến với AutoLý! Để bắt đầu, hãy cho chúng tôi biết bạn đang chuẩn bị hồ sơ cho loại hình tổ chức nào nhé.')

    options_step0: Dict[str, str] = {'Không': 'Không (Công ty tư nhân)', 'Có': 'Có (Cơ quan Nhà nước/Quân đội)'}
    user_storage = cast(Dict[str, Any], app.storage.user)
    form_data_s0: Dict[str, Any] = cast(Dict[str, Any], user_storage[FORM_DATA_KEY])
    current_val_step0: str = cast(str, form_data_s0.get(STEP0_ANS_KEY, 'Không'))

    ui.radio(options_step0, value=current_val_step0,
             on_change=lambda e: form_data_s0.update({STEP0_ANS_KEY: e.value})) \
        .props('inline')
    
    def _on_next_step0() -> None:
        ans: Any = form_data_s0.get(STEP0_ANS_KEY)
        user_storage[NEEDS_CLEARANCE_KEY] = (ans == 'Có')
        next_step()

    ui.button("Xác nhận & Tiếp tục →", on_click=_on_next_step0)\
        .classes('q-mt-md').props('color=primary unelevated')

@ui.refreshable
def render_step_core_identity() -> None:
    ui.label('Thông tin cá nhân').classes('text-h6 q-mb-sm')
    ui.markdown('Tuyệt vời! Giờ hãy bắt đầu với một vài thông tin định danh cơ bản của bạn.')
    
    current_validators: List[ValidatorEntryType] = []
    user_storage = cast(Dict[str, Any], app.storage.user)
    current_step_errors: Dict[str, str] = user_storage.get(CURRENT_STEP_ERRORS_KEY, {})
    form_attempted: bool = user_storage.get(FORM_ATTEMPTED_SUBMISSION_KEY, False)

    def _add_field(label: str, key: str, val_func: ValidationFuncType, **kwargs: Any)-> Optional[Element]:
        element, validator_entry = create_field(
            label_text=label, storage_key=key, validation_func=val_func,
            error_message_for_field=current_step_errors.get(key),
            form_attempted=form_attempted, **kwargs)
        current_validators.append(validator_entry)
        return element
    
    _add_field('Họ và tên (IN HOA)', FULL_NAME_KEY, Vl.validate_full_name)
    _add_field('Nam/Nữ', GENDER_KEY, Vl.validate_gender, 
               input_type='select', options=['', 'Nam', 'Nữ'])
    _add_field('Ngày sinh', DOB_KEY, Vl.validate_dob, input_type='date',
                 date_min_max=(date(1900, 1, 1), date.today()))
    _add_field('Nơi sinh', BIRTH_PLACE_KEY, Vl.validate_address)
    
    with ui.row().classes('w-full q-mt-lg justify-between items-center'):
        ui.button("← Quay lại", on_click=prev_step).props('flat color=grey')
        ui.button("Xác nhận & Tiếp tục →",
                  on_click=lambda: _handle_step_confirmation(
                      current_validators)).props('color=primary unelevated')
    
@ui.refreshable
def render_step_official_id() -> None:
    ui.label('Giấy tờ tuỳ thân').classes('text-h6 q-mb-sm')
    ui.markdown('Tiếp theo, vui lòng cung cấp thông tin trên Căn cước công dân hoặc CMND của bạn.')

    current_validators: List[ValidatorEntryType] = []
    user_storage = cast(Dict[str, Any], app.storage.user)
    current_step_errors: Dict[str, str] = user_storage.get(CURRENT_STEP_ERRORS_KEY, {})
    form_attempted: bool = user_storage.get(FORM_ATTEMPTED_SUBMISSION_KEY, False)

    def _add_field(label: str, key: str, val_func: ValidationFuncType, **kwargs: Any)-> Optional[Element]:
        element, validator_entry = create_field(
            label_text=label, storage_key=key, validation_func=val_func,
            error_message_for_field=current_step_errors.get(key),
            form_attempted=form_attempted, **kwargs)
        current_validators.append(validator_entry)
        return element
    
    _add_field('Số CMND/CCCD', ID_PASSPORT_NUM_KEY, Vl.validate_id_number)
    _add_field('Cấp ngày', ID_PASSPORT_ISSUE_DATE_KEY, Vl.validate_id_issue_date,
                input_type='date', date_min_max=(date(1900, 1, 1), date.today()))
    _add_field('Nơi cấp', ID_PASSPORT_ISSUE_PLACE_KEY, Vl.validate_id_issue_place)

    with ui.row().classes('w-full q-mt-lg justify-between items-center'):
        ui.button("← Quay lại", on_click=prev_step).props('flat color=grey')
        ui.button("Xác nhận & Tiếp tục →",
                  on_click=lambda: _handle_step_confirmation(
                      current_validators)).props('color=primary unelevated')

@ui.refreshable
def render_step_contact() -> None:
    ui.label("Thông in liên lạc chính").classes('text-h6 q-mb-sm')
    ui.markdown('Chúng tôi cần địa chỉ và số điện thoại để có thể liên lạc với bạn khi cần. \
                Thông tin này sẽ được bảo mật.')

    current_validators: List[ValidatorEntryType] = []
    user_storage = cast(Dict[str, Any], app.storage.user)
    current_step_errors: Dict[str, str] = user_storage.get(CURRENT_STEP_ERRORS_KEY, {})
    form_attempted: bool = user_storage.get(FORM_ATTEMPTED_SUBMISSION_KEY, False)

    def _add_field(label: str, key: str, val_func: ValidationFuncType, **kwargs: Any)-> Optional[Element]:
        element, validator_entry = create_field(
            label_text=label, storage_key=key, validation_func=val_func,
            error_message_for_field=current_step_errors.get(key),
            form_attempted=form_attempted, **kwargs)
        current_validators.append(validator_entry)
        return element
    
    _add_field('Địa chỉ hộ khẩu', REGISTERED_ADDRESS_KEY, Vl.validate_address)
    _add_field('Số điện thoại', PHONE_KEY, Vl.validate_phone)

    with ui.row().classes('w-full q-mt-lg justify-between items-center'):
        ui.button("← Quay lại", on_click=prev_step).props('flat color=grey')
        ui.button("Xác nhận & Tiếp tục →",
                  on_click=lambda: _handle_step_confirmation(
                      current_validators)).props('color=primary unelevated')

@ui.refreshable
def render_step_origin_info() -> None:
    current_validators: List[ValidatorEntryType] = []
    user_storage = cast(Dict[str, Any], app.storage.user)
    current_step_errors: Dict[str, str] = user_storage.get(CURRENT_STEP_ERRORS_KEY, {})
    form_attempted: bool = user_storage.get(FORM_ATTEMPTED_SUBMISSION_KEY, False)

    def _add_field(label: str, key: str, val_func: ValidationFuncType, **kwargs: Any)-> Optional[Element]:
        element, validator_entry = create_field(
            label_text=label, storage_key=key, validation_func=val_func,
            error_message_for_field=current_step_errors.get(key),
            form_attempted=form_attempted, **kwargs)
        current_validators.append(validator_entry)
        return element
    
    _add_field("Dân tộc", ETHNICITY_KEY, Vl.validate_choice_made, input_type='select', 
               options=para.ethnic_groups_vietnam)
    _add_field("Tôn giáo", RELIGION_KEY, Vl.validate_choice_made, input_type='select', 
               options=para.religion_options)

    if user_storage.get(NEEDS_CLEARANCE_KEY, False):
        _add_field('Nguyên quán (Nơi sinh của bố)', PLACE_OF_ORIGIN_KEY, Vl.validate_address)
    
    with ui.row().classes('w-full q-mt-lg justify-between items-center'):
        ui.button("← Quay lại", on_click=prev_step).props('flat color=grey')
        ui.button("Xác nhận & Tiếp tục →",
                  on_click=lambda: _handle_step_confirmation(
                      current_validators)).props('color=primary unelevated')

@ui.refreshable
def render_step_education() -> None:
    current_validators: List[ValidatorEntryType] = []
    user_storage = cast(Dict[str, Any], app.storage.user)
    current_step_errors: Dict[str, str] = user_storage.get(CURRENT_STEP_ERRORS_KEY, {})
    form_attempted: bool = user_storage.get(FORM_ATTEMPTED_SUBMISSION_KEY, False)

    def _add_field(label: str, key: str, val_func: ValidationFuncType, **kwargs: Any)-> Optional[Element]:
        element, validator_entry = create_field(
            label_text=label, storage_key=key, validation_func=val_func,
            error_message_for_field=current_step_errors.get(key),
            form_attempted=form_attempted, **kwargs)
        current_validators.append(validator_entry)
        return element
    
    _add_field('Hoàn thành cấp 3 (12/12)', EDUCATION_HIGH_SCHOOL_KEY, Vl.validate_text_input_required)
    _add_field('Bằng cấp cao nhất', EDUCATION_HIGHEST_KEY, Vl.validate_choice_made, 
               input_type='select', options=para.degrees)
    _add_field('Ngoại ngữ (VD: Tiếng Anh - IELTS 7.5)', )


        with ui.row().classes('w-full q-gutter-md q-mb-md items-start'):
        _, edu_validator_entry = create_field(
            'Bằng cấp cao nhất', EDUCATION_HIGHEST_KEY, validate_degree_local,
                     input_type='select', options=para_degrees_list, 
                     error_message_for_field=current_step_errors.get(EDUCATION_HIGHEST_KEY),
                     form_attempted=form_attempted
        ) 
        validators_for_step3.append(edu_validator_entry)
        _, spec_validator_entry = create_field(
            'Chuyên ngành đào tạo', EDUCATION_MAJOR_KEY, validate_not_empty_local,
            error_message_for_field=current_step_errors.get(EDUCATION_MAJOR_KEY), 
            form_attempted=form_attempted
        )

@ui.refreshable
def render_step_work_history() -> None:
    pass

@ui.refreshable
def render_step_awards() -> None:
    pass

@ui.refreshable
def render_step_parents_basic() -> None:
    pass

@ui.refreshable
def render_step_siblings() -> None:
    pass

@ui.refreshable
def render_step_spouse_and_children() -> None:
    pass

@ui.refreshable
def render_step_gov_political_class() -> None:
    pass

@ui.refreshable
def render_step_gov_affiliation() -> None:
    pass

@ui.refreshable
def render_step_gov_parents_history() -> None:
    pass

@ui.refreshable
def render_step_health_and_military() -> None:
    ui.label("Sức khỏe chung").classes('text-subtitle1 q-mb-xs')
    current_validators: List[ValidatorEntryType] = []
    user_storage = cast(Dict[str, Any], app.storage.user)
    current_step_errors: Dict[str, str] = user_storage.get(CURRENT_STEP_ERRORS_KEY, {})
    form_attempted: bool = user_storage.get(FORM_ATTEMPTED_SUBMISSION_KEY, False)

    def _add_field(label: str, key: str, val_func: ValidationFuncType, **kwargs: Any)-> Optional[Element]:
        element, validator_entry = create_field(
            label_text=label, storage_key=key, validation_func=val_func,
            error_message_for_field=current_step_errors.get(key),
            form_attempted=form_attempted, **kwargs)
        current_validators.append(validator_entry)
        return element
    
    _add_field('Tình trạng sức khoẻ (Tốt)', HEALTH_KEY, Vl.validate_text_input_required) # Assuming a simple text validator
    _add_field('Chiều cao (cm)', HEIGHT_KEY, Vl.validate_text_input_required)
    _add_field('Cân nặng (kg)', WEIGHT_KEY, Vl.validate_text_input_required)
    
    with ui.row().classes('w-full q-mt-lg justify-between items-center'):
        ui.button("← Quay lại", on_click=prev_step).props('flat color=grey')
        ui.button("Xác nhận & Tiếp tục →",
                  on_click=lambda: _handle_step_confirmation(
                      current_validators)).props('color=primary unelevated')

@ui.refreshable
def render_step_emergency_contact() -> None:
    pass

@ui.refreshable
def render_step_review() -> None:
    pass
# ===================================================================
# 4. DEFINE THE BLUEPRINT
# ++ NEW "ROBO-TAX" APPLICATION FLOW BLUEPRINT ++
# ===================================================================
class StepDefinition(TypedDict):
    id: int
    name: str
    render_func: Callable[[], None]
    needs_clearance: Optional[bool]

STEPS_DEFINITION: List[StepDefinition] = [
    # --- Onboarding ---
    {'id': 0, 'name': 'start', 'render_func': render_step_start, 'needs_clearance': None},

    # --- Core Identity & Contact ---
    {'id': 1, 'name': 'core_identity', 'render_func': render_step_core_identity, 'needs_clearance': None},
    {'id': 2, 'name': 'official_id', 'render_func': render_step_official_id, 'needs_clearance': None},
    {'id': 3, 'name': 'contact', 'render_func': render_step_contact, 'needs_clearance': None},
    {'id': 4, 'name': 'origin_info', 'render_func': render_step_origin_info, 'needs_clearance': None},

    # --- Professional Background ---
    {'id': 5, 'name': 'education', 'render_func': render_step_education, 'needs_clearance': None},
    {'id': 6, 'name': 'work_history', 'render_func': render_step_work_history, 'needs_clearance': None},
    {'id': 7, 'name': 'awards', 'render_func': render_step_awards, 'needs_clearance': None},
    
    # --- Family Background (Universal) ---
    {'id': 8, 'name': 'parents_basic', 'render_func': render_step_parents_basic, 'needs_clearance': None},
    {'id': 9, 'name': 'siblings', 'render_func': render_step_siblings, 'needs_clearance': None},
    {'id': 10, 'name': 'spouse_and_children', 'render_func': render_step_spouse_and_children, 'needs_clearance': None},

    # --- GOVERNMENT/MILITARY CLEARANCE SECTION (SKIPPED FOR PRIVATE) ---
    {'id': 11, 'name': 'gov_political_class', 'render_func': render_step_gov_political_class, 'needs_clearance': True},
    {'id': 12, 'name': 'gov_affiliation', 'render_func': render_step_gov_affiliation, 'needs_clearance': True},
    {'id': 13, 'name': 'gov_parents_history', 'render_func': render_step_gov_parents_history, 'needs_clearance': True},
    
    # --- Miscellaneous & Finalization ---
    {'id': 14, 'name': 'health_and_military', 'render_func': render_step_health_and_military, 'needs_clearance': None},
    {'id': 15, 'name': 'emergency_contact', 'render_func': render_step_emergency_contact, 'needs_clearance': None},
    {'id': 16, 'name': 'review', 'render_func': render_step_review, 'needs_clearance': None},
]

# --- Navigation Functions ---

def _get_current_step_index(current_step_id: int) -> int:
    """Finds the list index for a given step ID from the blueprint."""
    for i, step_def in enumerate(STEPS_DEFINITION):
        if step_def['id'] == current_step_id:
            return i
    return -1 # Should not happen in a normal flow


def next_step() -> None:
    user_storage = cast(Dict[str, Any], app.storage.user)
    current_step_id: int = cast(int, user_storage.get(STEP_KEY, 0))
    current_index = _get_current_step_index(current_step_id)
    needs_clearance_val: bool = cast(bool, user_storage.get(NEEDS_CLEARANCE_KEY, False))

    # Iterate forward from the current position to find the next valid step
    for i in range(current_index + 1, len(STEPS_DEFINITION)):
        next_step_candidate = STEPS_DEFINITION[i]
        if next_step_candidate[NEEDS_CLEARANCE_KEY] and not needs_clearance_val:
            continue # Skip and check next step
        user_storage[STEP_KEY] = next_step_candidate['id']
        user_storage[FORM_ATTEMPTED_SUBMISSION_KEY] = False
        user_storage[CURRENT_STEP_ERRORS_KEY] = {}
        update_step_content.refresh()
        return

def prev_step() -> None:
    user_storage = cast(Dict[str, Any], app.storage.user)
    current_step_id: int = cast(int, user_storage.get(STEP_KEY, 0))
    current_index = _get_current_step_index(current_step_id)
    needs_clearance_val: bool = cast(bool, user_storage.get(NEEDS_CLEARANCE_KEY, False))

    for i in range(current_index - 1, -1, -1):
        prev_step_candidate = STEPS_DEFINITION[i]
        if prev_step_candidate[NEEDS_CLEARANCE_KEY] and not needs_clearance_val:
            continue
        user_storage[STEP_KEY] = prev_step_candidate['id']
        user_storage[FORM_ATTEMPTED_SUBMISSION_KEY] = False
        user_storage[CURRENT_STEP_ERRORS_KEY] = {}
        update_step_content.refresh()
        return

# ===================================================================
# 5. DEFINE THE NAVIGATION ENGINE & UI CONTROLLER
# These functions USE the blueprint, so they must come after it.
# ===================================================================

# --- update_step_content, main_page, ui.run() ---
@ui.refreshable
def update_step_content() -> None:
    user_storage = cast(Dict[str, Any], app.storage.user)
    current_step_id: int = user_storage.get(STEP_KEY, 0)
    # Find the correct step definition from the blueprint
    step_to_render = next((step for step in STEPS_DEFINITION if step['id']==current_step_id), None)
    
    if step_to_render:
        step_to_render['render_func']()
    else:
        ui.label(f"Lỗi: Bước không xác định ({current_step_id})").classes('text-negative text-h6')
        def reset_app_fully() -> None:
            user_storage[STEP_KEY] = 0
            new_form_data_reset: Dict[str, Any] = {}
            initialize_form_data(new_form_data_reset)
            user_storage[FORM_DATA_KEY] = new_form_data_reset
            user_storage[FORM_ATTEMPTED_SUBMISSION_KEY] = False
            user_storage[NEEDS_CLEARANCE_KEY] = False
            user_storage[CURRENT_STEP_ERRORS_KEY] = {} # Reset errors
            update_step_content.refresh()
        ui.button("Bắt đầu lại", on_click=reset_app_fully).props('color=primary unelevated')

# ===================================================================
# 6. MAIN PAGE AND APP STARTUP
# ===================================================================
@ui.page('/')
def main_page() -> None:
    user_storage = cast(Dict[str, Any], app.storage.user)
    if STEP_KEY not in user_storage: # Check if session needs initialization
        user_storage.clear() 
        user_storage[STEP_KEY] = 0
        
        initial_form_data: Dict[str, Any] = {}
        initialize_form_data(initial_form_data)
        user_storage[FORM_DATA_KEY] = initial_form_data
        
        user_storage[FORM_ATTEMPTED_SUBMISSION_KEY] = False
        user_storage[NEEDS_CLEARANCE_KEY] = False
        user_storage[CURRENT_STEP_ERRORS_KEY] = {} # Initialize error store

    ui.query('body').style('background-color: #f0f2f5;')
    
    with ui.header(elevated=True).classes('bg-primary text-white q-pa-sm items-center'):
        ui.label("📝 AutoLý – Kê khai Sơ yếu lý lịch").classes('text-h5')
        ui.space()
        # Debug menu (ensure values are JSON serializable for ui.json_editor)
        with ui.button(icon='bug_report', color='white').props('flat round dense'):
            with ui.menu().classes('bg-grey-2 shadow-3'):
                with ui.card().style("min-width: 350px; max-width: 90vw;"):
                    ui.label(f"Step: {user_storage.get(STEP_KEY)}")
                    with ui.expansion("Form Data", icon="description").classes("w-full"):
                        ui.json_editor({'value': user_storage.get(FORM_DATA_KEY, {})}).props('readonly')
                    with ui.expansion("Step Errors", icon="error").classes("w-full"):
                        ui.json_editor({'value': user_storage.get(CURRENT_STEP_ERRORS_KEY, {})}).props('readonly')

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
