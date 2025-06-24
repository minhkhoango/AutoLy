# myapp.py

# ===================================================================
# 1. IMPORTS
# ===================================================================
from nicegui import ui, app
from typing import (
    Any, TypedDict,
    TypeAlias, cast
)
from collections.abc import Callable

# Assuming validation.py and para.py are in the same directory or accessible in PYTHONPATH
from validation import (
    ValidatorFunc,
    required, required_choice, match_pattern, is_within_date_range, is_date_after
)
import fitz
import tempfile
from pathlib import Path
import os
from typing_extensions import NotRequired
import re
from re import Pattern
from datetime import datetime

# Import the new, powerful schema and utilities
from form_data_builder import FormUseCaseType, FormTemplate, FORM_TEMPLATE_REGISTRY
from utils import (
    AppSchema, FormField,
    STEP_KEY, FORM_DATA_KEY, SELECTED_USE_CASE_KEY, # <-- ADD THIS
    FORM_ATTEMPTED_SUBMISSION_KEY, CURRENT_STEP_ERRORS_KEY,
    initialize_form_data, get_form_data
)

# ===================================================================
# 2. NEW: AUTH & MULTI-USER DATA STORE (The "Hotel Front Desk")
# ===================================================================

# This is our temporary user database. In a real app, this would be a database table.
# Passwords should be hashed, but for the MVP, plaintext is fine to see the mechanism.
ALLOWED_USERS: dict[str, str] = {
    'user1': 'pass1',
    'user2': 'pass2',
    'autoly_dev': 'autoly_dev_pass'
}

USER_DATA_STORE: dict[str, dict[str, Any]] = {}

def get_current_user() -> str | None:
    """Safely retrieves the username from the user's session storage."""
    user_storage = cast(dict[str, Any], app.storage.user)
    return cast(str | None, user_storage.get('username'))

# ===================================================================
# 3. CENTRALIZED DATA HELPERS (Now user-aware)
# ===================================================================

def get_user_storage() -> dict[str, Any]:
    """
    This is the core of our multi-user strategy.
    It retrieves the data dictionary for the currently logged-in user.
    If the user has no data yet, it initializes their "slot" in the store.
    """
    username = get_current_user()
    if not username:
        # This should not happen on a protected page, but as a safeguard:
        raise PermissionError("Attempted to access user storage without being logged in.")
    
    if username not in USER_DATA_STORE:
        USER_DATA_STORE[username] = {}
    
    return USER_DATA_STORE[username]

def get_form_data() -> dict[str, Any]:
    """
    MODIFIED: Now fetches form_data from the correct user's slot in the
    global USER_DATA_STORE.
    """
    user_storage = get_user_storage()
    if not isinstance(user_storage.get(FORM_DATA_KEY), dict):
        user_storage[FORM_DATA_KEY] = {}
    return cast(dict[str, Any], user_storage[FORM_DATA_KEY])

def initialize_form_data() -> None:
    """
    MODIFIED: Populates form_data with defaults within the specific
    logged-in user's data store.
    """
    user_storage = get_user_storage()

    if user_storage:
        return

    # Set up the structure for a new user
    user_storage[STEP_KEY] = 0
    user_storage[SELECTED_USE_CASE_KEY] = None
    user_storage[FORM_ATTEMPTED_SUBMISSION_KEY] = False
    user_storage[CURRENT_STEP_ERRORS_KEY] = {}


    form_data = get_form_data()
    if form_data: # Don't re-initialize if data already exists
        return
    
    for field in AppSchema.get_all_fields():
        if field.key not in form_data:
            form_data[field.key] = field.default_value
    
    form_data[AppSchema.TRAINING_DATAFRAME.key] = []
    form_data[AppSchema.WORK_DATAFRAME.key] = []
    form_data[AppSchema.CHILD_DATAFRAME.key] = []
    
    

# --- Modernized Type Aliases ---
SimpleValidatorEntry: TypeAlias = tuple[str, list[ValidatorFunc]]
DataframeColumnRules: TypeAlias = dict[str, list[ValidatorFunc]]
DataframeValidatorEntry: TypeAlias = tuple[str, DataframeColumnRules]
ValidationEntry: TypeAlias = SimpleValidatorEntry | DataframeValidatorEntry

# --- Blueprint TypedDicts ---
# This makes our STEPS_DEFINITION fully type-checked and self-documenting.
class FieldConfig(TypedDict):
    field: FormField
    validators: list[ValidatorFunc]

class DataframeConfig(TypedDict):
    field: FormField
    columns: dict[str, dict[str, str]]
    validators: DataframeColumnRules

class PanelInfo(TypedDict):
    """Defines the structure for a single panel within a tabbed layout."""
    label: str
    fields: list[FieldConfig]

class TabbedLayout(TypedDict):
    """Defines the structure for the entire tabbed layout object."""
    type: str
    tabs: dict[str, PanelInfo]

class StepDefinition(TypedDict):
    id: int
    name: str
    title: str
    subtitle: str
    render_func: Callable[['StepDefinition'], None] # Points to the generic or a special renderer
    fields: list[FieldConfig]
    dataframes: list[DataframeConfig] # For complex list editors
    needs_clearance: bool | None
    layout: NotRequired[TabbedLayout] # The key may not exist.

# ===================================================================
# 2. PRIVATE HELPER FUNCTIONS (The Specialists)
# ===================================================================

def _validate_simple_field(
    field_key: str, validator_list: list[ValidatorFunc],
    form_data: dict[str, Any], errors: dict[str, str]
) -> bool:
    """
    Validates a single, simple form field.
    Returns True if valid, False otherwise.
    Appends error messages to the `errors` dictionary if invalid.
    """
    is_field_valid: bool = True
    value_to_validate: Any = form_data.get(field_key)

    for validator_func in validator_list:
        is_valid, msg = validator_func(value_to_validate, form_data)
        if not is_valid:
            is_field_valid = False
            # Assign the error message and stop validating this field
            if field_key not in errors:
                errors[field_key] = msg
            break
    return is_field_valid

def _validate_dataframe_field(
    dataframe_key: str, column_rules: DataframeColumnRules,
    form_data: dict[str, Any], errors: dict[str, str]
) -> bool:
    """
    Validates all cells within a dataframe field.
    Returns True if the entire dataframe is valid, False otherwise.
    Appends cell-specific error messages to the `errors` dictionary.
    """
    is_dataframe_valid: bool = True
    dataframe_value: list[dict[str, Any]] = form_data.get(dataframe_key, [])
    
    for row_index, row_data in enumerate(dataframe_value):
        for col_key, validator_list in column_rules.items():
            cell_value = row_data.get(col_key)
            for validator_func in validator_list:
                is_valid, msg = validator_func(cell_value, row_data)
                if not is_valid:
                    is_dataframe_valid = False
                    # Create a unique key for the error: "dataframe_key_rowIndex_colKey"
                    error_key: str = f"{dataframe_key}_{row_index}_{col_key}"
                    if error_key not in errors:
                        errors[error_key] = msg
                    break  # Stop validating this cell on the first error
    return is_dataframe_valid

# --- Validation Execution Function ---
def execute_step_validators(
    validators_for_step: list[ValidationEntry],
    form_data: dict[str, Any] # fetched from app.storage.user
) -> tuple[bool, dict[str, str]]:
    """
    Executes all validators for a given step by dispatching to specialized helpers.
    
    Args:
        validators_for_step: A list of validation rules for the current step.
        form_data: The dictionary containing all current user input.

    Returns:
        A tuple containing:
        - A boolean indicating if the entire step is valid.
        - A dictionary of error messages, with keys corresponding to the
          invalid fields or cells.
    """
    new_errors: dict[str, str] = {}
    is_step_valid: bool = True
    for entry in validators_for_step:
        field_key, rules = entry
        if isinstance(rules, dict):
            if not _validate_dataframe_field(field_key, rules, form_data, new_errors):
                is_step_valid = False
        else:
            if not _validate_simple_field(field_key, rules, form_data, new_errors):
                is_step_valid = False
    return is_step_valid, new_errors

# ===================================================================
# 3. CORE LOGIC & NAVIGATION
# ===================================================================

async def _handle_step_confirmation(button: ui.button) -> None:
    """The core logic for validating a step and moving to the next."""
    button.disable()
    try:
        user_storage = get_user_storage()
        current_step_id = user_storage.get(STEP_KEY, 0)
        current_step_def = STEPS_BY_ID.get(current_step_id)
        if not current_step_def: return

        validators_for_step: list[ValidationEntry] = []
        def collect_validators(fields_config: list[FieldConfig]):
            for field_conf in fields_config:
                validators_for_step.append((field_conf['field'].key, field_conf['validators']))

        if (layout := current_step_def.get('layout')) and layout.get('type') == 'tabs':
            if (tabs := layout.get('tabs')):
                for panel_info in tabs.values():
                    collect_validators(panel_info.get('fields', []))
        else:
            collect_validators(current_step_def.get('fields', []))

        for df_conf in current_step_def.get('dataframes', []):
            validators_for_step.append((df_conf['field'].key, df_conf['validators']))

        current_form_data = get_form_data()
        all_valid, new_errors = execute_step_validators(validators_for_step, current_form_data)

        user_storage[FORM_ATTEMPTED_SUBMISSION_KEY] = True
        user_storage[CURRENT_STEP_ERRORS_KEY] = new_errors

        if all_valid:
            if current_step_id == 0:
                selected_use_case_name = current_form_data.get(AppSchema.FORM_TEMPLATE_SELECTOR.key)
                user_storage[SELECTED_USE_CASE_KEY] = selected_use_case_name
            ui.notify("Thông tin hợp lệ!", type='positive')
            next_step()
        else:
            for error in new_errors.values():
                ui.notification(error, type='negative')
            update_step_content.refresh()
    finally:
        button.enable()
# ===================================================================
# Replace your entire old render_text_on_pdf function with this one
# ===================================================================
def render_text_on_pdf(
    template_path: Path,
    form_data: dict[str, Any],
    form_template: FormTemplate,
    output_path: Path,
) -> None:
    """
    Renders form data onto a template PDF using the robust PyMuPDF (fitz) library.
    This is the final, production-ready engine.
    """
    try:
        # 1. --- SETUP ---
        PROJECT_ROOT = Path(__file__).resolve().parent.parent
        FONT_PATH: str = str(PROJECT_ROOT / "assets" / "NotoSans-Regular.ttf")
        # We now know the original template is fine, no need for the "-CLEAN" version.
        TEMPLATE_FILE: Path = template_path 

        FONT_NAME: str = "NotoSans"
        FONT_SIZE: int = 10
        LINE_HEIGHT: float = 21.5

        if not Path(FONT_PATH).exists():
            raise FileNotFoundError(f"CRITICAL: Font not found at {FONT_PATH}")
        if not TEMPLATE_FILE.exists():
            raise FileNotFoundError(f"CRITICAL: Template not found at {TEMPLATE_FILE}")

        doc = fitz.open(TEMPLATE_FILE)
        user_storage = get_user_storage()
        selected_use_case = FormUseCaseType[cast(str, user_storage.get(SELECTED_USE_CASE_KEY))]

        # 2. --- DRAW ALL DATA ---
        # Process simple fields
        for field in AppSchema.get_all_fields():
            # --- THIS IS THE CRITICAL FIX ---
            # Instead of hasattr, check if pdf_columns has a value.
            # If it's None or an empty list, this will be False.
            if field.pdf_columns:
                continue  # This correctly skips only the dataframe fields.
            # --- END FIX ---
            
            if not field.pdf_coords:
                continue

            coords = field.pdf_coords.get(selected_use_case)
            if not coords:
                continue
            
            page = doc[0] # All simple fields are on page 1 (index 0)
            value = form_data.get(field.key, '')

            # Use a consistent 'insert' method for all text
            def insert(point: tuple[float, float], text: str):
                page.insert_text(point, text, fontname=FONT_NAME, fontfile=FONT_PATH, fontsize=FONT_SIZE)

            if field.ui_type == 'date' and field.split_date and value:
                try:
                    dt_obj = datetime.strptime(str(value), '%Y-%m-%d')
                    day, month, year = dt_obj.strftime('%d'), dt_obj.strftime('%m'), dt_obj.strftime('%Y')
                    x_coords, y = cast(tuple[list[float], float], coords)
                    if len(x_coords) == 3:
                        insert((x_coords[0], y), day)
                        insert((x_coords[1], y), month)
                        insert((x_coords[2], y), year)
                except (ValueError, TypeError):
                    pass
            else:
                x, y = cast(tuple[float, float], coords)
                insert((x, y), str(value))

        # Process multi-row dataframe fields
        for df_key, page_num in form_template['dataframe_page_map'].items():
            page = doc[page_num - 1]
            
            df_field = getattr(AppSchema, df_key.upper(), None)
            if not df_field or not df_field.pdf_coords: continue
            coords = df_field.pdf_coords.get(selected_use_case)
            if not coords: continue
                
            start_x, start_y = cast(tuple[float, float], coords)
            dataframe_data = cast(list[dict[str, Any]], form_data.get(df_key, []))
            pdf_columns = getattr(df_field, 'pdf_columns', [])

            for i, row in enumerate(dataframe_data):
                y_pos = start_y + (i * LINE_HEIGHT)
                for col_def in pdf_columns:
                    text = col_def['transformer'](row) if 'transformer' in col_def else str(row.get(col_def['key'], ''))
                    point = fitz.Point(start_x + col_def['x_offset'], y_pos)
                    page.insert_text(point, text, fontname=FONT_NAME, fontfile=FONT_PATH, fontsize=FONT_SIZE-2)

        # 3. --- SAVE THE MODIFIED DOCUMENT ---
        doc.save(output_path, garbage=4, deflate=True, clean=True)
        print(f"✅ PDF successfully generated with Fitz engine and saved to {output_path}")

    except Exception as e:
        print(f"!!! PDF GENERATION FAILED with an exception: {e}")
        import traceback
        traceback.print_exc()
    # finally:
        # if 'doc' in locals() and doc.is_open:
        #     doc.close()


async def create_and_download_pdf(button: ui.button) -> None:
    button.disable()
    output_pdf_path_obj = None
    try:
        user_storage = get_user_storage()
        form_data = get_form_data()
        selected_use_case_name = user_storage.get(SELECTED_USE_CASE_KEY)
        if not selected_use_case_name:
            ui.notify("Lỗi: Không xác định được loại hồ sơ.", type='negative')
            return

        selected_use_case = FormUseCaseType[selected_use_case_name]
        form_template = FORM_TEMPLATE_REGISTRY.get(selected_use_case)
        if not form_template:
            ui.notify("Lỗi: Không tìm thấy blueprint cho hồ sơ.", type='negative')
            return

        template_path_obj = Path(form_template['pdf_template_path'])
        if not template_path_obj.exists():
            ui.notify(f"Lỗi: Không tìm thấy file mẫu PDF tại '{template_path_obj}'.", type='negative')
            return

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmpfile_obj:
            output_pdf_path_obj = Path(tmpfile_obj.name)

        render_text_on_pdf(
            template_path=template_path_obj,
            form_data=form_data,
            form_template=form_template,
            output_path=output_pdf_path_obj
        )

        pdf_content_bytes: bytes = output_pdf_path_obj.read_bytes()
        ui.download(src=pdf_content_bytes, filename="SoYeuLyLich_DaDien.pdf")
        ui.notify("Đã tạo PDF thành công!", type='positive')

    except Exception as e:
        print(f"Lỗi nghiêm trọng khi tạo PDF: {e}")
        import traceback
        traceback.print_exc()
        ui.notify(f"Đã xảy ra lỗi khi tạo PDF. Chi tiết: {e}", type='negative', multi_line=True)
    finally:
        button.enable()
        if output_pdf_path_obj and output_pdf_path_obj.exists():
            try:
                os.remove(output_pdf_path_obj)
            except Exception as e_del:
                print(f"Lỗi khi xóa file tạm: {e_del}")

# ===================================================================
# 4. UI RENDERING ENGINE
# ===================================================================

def _render_dataframe_editor(df_conf: DataframeConfig) -> None:
    """Renders a dynamic list editor for things like Work History, Siblings, etc."""
    ui.label(df_conf['field'].label).classes('text-subtitle1 q-mt-md q-mb-sm')
    user_storage = get_user_storage()
    form_data = get_form_data()
    dataframe_key = df_conf['field'].key
    @ui.refreshable
    def render_rows() -> None:
        dataframe = cast(list[dict[str, Any]], form_data.get(dataframe_key, []))
        form_attempted: bool = user_storage.get(FORM_ATTEMPTED_SUBMISSION_KEY, False)
        current_errors: dict[str, str] = user_storage.get(CURRENT_STEP_ERRORS_KEY, {})
        if not dataframe:
            ui.label(f"Chưa có mục nào được thêm.").classes("text-italic text-grey q-pa-md text-center full-width")
        for i, entry in enumerate(dataframe):
            with ui.row().classes('w-full items-center q-gutter-x-sm q-mb-xs'):
                for col_key, props in df_conf['columns'].items():
                    error_key = f'{dataframe_key}_{i}_{col_key}'
                    error_message = current_errors.get(error_key)
                    has_error = form_attempted and bool(error_message)

                    ui.input(props['label']) \
                        .bind_value(entry, col_key) \
                        .props(f"{props.get('props', 'dense outlined')} error-message='{error_message or ''}' error={has_error}")\
                        .classes(props.get('classes', 'col'))
                    
                with ui.column().classes('col-auto'):
                    ui.button(icon='delete', on_click=lambda _, idx=i: (dataframe.pop(idx), render_rows.refresh()), color='negative') \
                        .props('flat dense round padding=xs')
         # --- THE FIX: A DEDICATED, ROBUST FUNCTION ---
        def add_new_row() -> None:
            """
            Fetches the latest data, checks for corruption, fixes it if needed,
            and then appends the new row.
            """
            # 1. Get the most current data directly from the source of truth.
            data_list_any = get_form_data().get(dataframe_key)

            # 2. Check for corruption. If it's not a list, fix it.
            if not isinstance(data_list_any, list):
                # This is the self-healing part. We overwrite the bad string.
                data_list_any = []
                get_form_data()[dataframe_key] = data_list_any

            typed_list = cast(list[dict[str, Any]], data_list_any)
            # 3. Now that we are SURE it's a list, append safely.
            typed_list.append({})
            
            # 4. Refresh the UI to show the new empty row.
            render_rows.refresh()

        ui.button(f"Thêm thông tin", on_click=add_new_row, icon='add') \
            .classes('q-mt-sm').props('outline color=primary')
    render_rows()

# ===================================================================
# UI CREATION HELPERS (Moved from utils.py)
# ===================================================================
def _create_text_input(field: FormField, current_value: Any) -> ui.input:
    return ui.input(
        label=field.label,
        value=str(current_value),
        on_change=lambda e: get_form_data().update({field.key: e.value})
    ).classes('full-width').props("outlined dense")

def _create_select_input(field: FormField, current_value: Any) -> ui.select:
    return ui.select(
        options=field.options or [],
        label=field.label,
        value=current_value,
        on_change=lambda e: get_form_data().update({field.key: e.value})
    ).classes('full-width').props("outlined dense")

def _create_radio_input(field: FormField, current_value: Any) -> ui.radio:
    return ui.radio(
        options=field.options or [],
        value=current_value,
        on_change=lambda e: get_form_data().update({field.key: e.value})
    ).props("dense")

def _create_date_input(field: FormField, current_value: Any) -> ui.date:
    # THE FIX: ui.date does not have a 'label'. We return only the element.
    # The label is handled by the calling function `create_field`.
    return ui.date(
        value=current_value,
        on_change=lambda e: get_form_data().update({field.key: e.value})
    ).props("outlined dense").classes('full-width')

def _create_textarea_input(field: FormField, current_value: Any) -> ui.textarea:
    return ui.textarea(
        label=field.label,
        value=str(current_value),
        on_change=lambda e: get_form_data().update({field.key: e.value})
    ).classes('full-width').props("outlined dense")

def _create_checkbox_input(field: FormField, current_value: Any) -> ui.checkbox:
    return ui.checkbox(
        text=field.label,
        value=bool(current_value),
        on_change=lambda e: get_form_data().update({field.key: e.value})
    )

# myapp.py

def create_field(field_definition: FormField) -> None:
    """
    Creates a UI element based on a FormField definition.
    This is a dispatcher, delegating to a map of creator functions.
    It also handles label creation and error display centrally.
    """
    form_data = get_form_data()
    user_storage = get_user_storage()
    current_value = form_data.get(field_definition.key, field_definition.default_value)

    # Get the error state for this specific field
    form_attempted: bool = user_storage.get(FORM_ATTEMPTED_SUBMISSION_KEY, False)
    current_errors: dict[str, str] = user_storage.get(CURRENT_STEP_ERRORS_KEY, {})
    error_message: str | None = current_errors.get(field_definition.key) if form_attempted else None
    has_error = bool(error_message)

    # --- Element Creator Map ---
    creator_map: dict[str, Callable[[FormField, Any], Any]] = {
        'text': _create_text_input,
        'select': _create_select_input,
        'radio': _create_radio_input,
        'date': _create_date_input,
        'textarea': _create_textarea_input,
        'checkbox': _create_checkbox_input,
    }

    # --- Dispatcher Logic ---
    creator = creator_map.get(field_definition.ui_type)
    if not creator:
        raise ValueError(f"Unsupported UI type: {field_definition.ui_type}")

    # Handle elements that need a manual label
    if field_definition.ui_type in ['date', 'radio', 'checkbox']:
        ui.label(field_definition.label).classes('text-caption q-mb-xs')

    # Create the element
    element = creator(field_definition, current_value)

    # Apply error props to the correct underlying input for all types
    # For most components, this is direct. For ui.date, it's a child.
    element.props(f"error-message='{error_message or ""}' error={has_error}")

# --- THE GENERIC STEP RENDERER ---
def render_generic_step(step_def: StepDefinition) -> None:
    """
    Renders a full step UI based on its definition in the blueprint.
    This function can now handle both simple vertical layouts and
    complex tabbed layouts, driven entirely by the step's data structure.
    """
    ui.label(step_def['title']).classes('text-h6 q-mb-xs')
    ui.markdown(step_def['subtitle'])
    def render_field_list(fields_to_render: list[FieldConfig]) -> None:
        for field_conf in fields_to_render:
            create_field(field_definition=field_conf['field'])
    if (layout_data := step_def.get('layout')) and layout_data.get('type') == 'tabs':
        if tab_data := layout_data.get('tabs'):
            with ui.tabs().classes('w-fill') as tabs:
                for panel_key, panel_info in tab_data.items():
                    ui.tab(name=panel_key, label=panel_info['label'])
            with ui.tab_panels(tabs, value=list(tab_data.keys())[0]).classes('w-full q-mt-md'):
                for panel_key, panel_info in tab_data.items():
                    with ui.tab_panel(name=panel_key):
                        render_field_list(panel_info.get('fields', []))
    else:
        render_field_list(step_def.get('fields', []))
    for df_conf in step_def.get('dataframes', []):
        _render_dataframe_editor(df_conf)
    with ui.row().classes('w-full q-mt-lg justify-between items-center'):
        if step_def['id'] > 0:
            ui.button("← Quay lại", on_click=lambda: prev_step()).props('flat color=grey')
        else:
            ui.label()
        confirm_button = ui.button("Xác nhận & Tiếp tục →").props('color=primary unelevated')
        confirm_button.on('click', lambda: _handle_step_confirmation(confirm_button))

def render_review_step(step_def: 'StepDefinition') -> None:
    """A special renderer for the final review step."""
    ui.label(step_def['title']).classes('text-h6 q-mb-md')
    ui.markdown(step_def['subtitle'])
    ui.label("Review UI is under construction.").classes('text-center text-grey')
    pdf_button = ui.button("Tạo PDF").props('color=green unelevated').classes('q-mt-md q-mb-lg')
    pdf_button.on('click', lambda: create_and_download_pdf(pdf_button))
    with ui.row().classes('w-full justify-start items-center'):
        ui.button("← Quay lại & Chỉnh sửa", on_click=lambda: prev_step()).props('flat color=grey')

# ===================================================================
# 5. DEFINE THE BLUEPRINT & NAVIGATION ENGINE
# ===================================================================
FULL_NAME_PATTERN: Pattern[str] = re.compile(r'^[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴĐÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸ ]+$')
PHONE_PATTERN: Pattern[str] = re.compile(r'^0\d{9}$')
ID_NUMBER_PATTERN: Pattern[str] = re.compile(r'^(?:\d{9}|\d{12})$')
NUMERIC_PATTERN: Pattern[str] = re.compile(r'^\d+$')
SALARY_PATTERN: Pattern[str] = re.compile(r"^\d+$|^\d{1,3}(?:[.,]\d{3})*$")
DATE_MMYYYY_PATTERN: Pattern[str] = re.compile(r'^(0[1-9]|1[0-2])/\d{4}$')
age_validators: list[ValidatorFunc] = [required("Vui lòng điền năm sinh."), match_pattern(NUMERIC_PATTERN, "Năm sinh phải là một con số.")]
STEPS_BY_ID: dict[int, StepDefinition] = {
    0: {'id': 0, 'name': 'dossier_selector', 'title': 'Chọn Loại Hồ Sơ Cần Chuẩn Bị', 'subtitle': 'Bắt đầu bằng cách chọn loại hồ sơ bạn cần. Hệ thống sẽ tự động tạo các bước cần thiết cho bạn.', 'render_func': render_generic_step, 'fields': [{'field': AppSchema.FORM_TEMPLATE_SELECTOR, 'validators': [required_choice("Vui lòng chọn một loại hồ sơ.")]}], 'dataframes': [], 'needs_clearance': None},
    1: {'id': 1, 'name': 'core_identity', 'title': 'Thông tin cá nhân', 'subtitle': 'Bắt đầu với thông tin định danh cơ bản của bạn.', 'render_func': render_generic_step, 'needs_clearance': None, 'fields': [{'field': AppSchema.FULL_NAME, 'validators': [required("Vui lòng điền đầy đủ họ và tên."), match_pattern(FULL_NAME_PATTERN, "Họ và tên phải viết hoa, không chứa số hoặc ký tự đặc biệt.")]}, {'field': AppSchema.GENDER, 'validators': [required_choice("Vui lòng chọn giới tính.")]}, {'field': AppSchema.DOB, 'validators': [required('Vui lòng chọn ngày sinh.'), is_within_date_range(message="Ngày sinh phải trong khoảng từ 01/01/1900 đến hôm nay.")]}], 'dataframes': []},
    3: {'id': 3, 'name': 'contact', 'title': 'Địa chỉ & thông tin liên lạc', 'subtitle': 'Địa chỉ và số điện thoại để liên lạc khi cần.', 'render_func': render_generic_step, 'needs_clearance': None, 'fields': [{'field': AppSchema.BIRTH_PLACE, 'validators': [required("Vui lòng điền nơi sinh.")]}, {'field': AppSchema.REGISTERED_ADDRESS, 'validators': [required("Vui lòng điền địa chỉ hộ khẩu.")]}, {'field': AppSchema.PHONE, 'validators': [required('Vui lòng điền số điện thoại.'), match_pattern(PHONE_PATTERN, "Số điện thoại phải có 10 chữ số, bắt đầu bằng 0.")]}], 'dataframes': []},
    5: {'id': 5, 'name': 'education', 'title': 'Học vấn & Chuyên môn', 'subtitle': 'Quá trình học tập, đào tạo định hình nên con người bạn.', 'render_func': render_generic_step, 'needs_clearance': None, 'fields': [{'field': AppSchema.EDUCATION_HIGH_SCHOOL, 'validators': [required_choice("Vui lòng chọn lộ trình học cấp ba.")]}], 'dataframes': [{'field': AppSchema.TRAINING_DATAFRAME, 'columns': {'training_from': {'label': 'Từ (MM/YYYY)', 'props': 'dense outlined mask="##/####"'}, 'training_to': {'label': 'Đến (MM/YYYY)', 'props': 'dense outlined mask="##/####"'}, 'training_unit': {'label': 'Tên trường hoặc cơ sở đào tạo'}, 'training_field': {'label': 'Ngành học'}, 'training_format': {'label': 'Hình thức đào tạo'}, 'training_certificate': {'label': 'Văn bằng chứng chỉ'}}, 'validators': {'training_from': [required('Vui lòng điền thời gian bắt đầu.'), match_pattern(DATE_MMYYYY_PATTERN, 'Dùng định dạng MM/YYYY')], 'training_to': [required('Vui lòng điền thời gian kết thúc.'), match_pattern(DATE_MMYYYY_PATTERN, 'Dùng định dạng MM/YYYY'), is_date_after('training_from', 'Ngày kết thúc phải sau ngày bắt đầu.')], 'training_unit': [required('Vui lòng điền tên trường hoặc cơ sở đào tạo.')], 'training_field': [required('Vui lòng điền ngành học.')], 'training_certificate': [required('Vui lòng điền văn bằng chứng chỉ.')]}}]},
    6: {'id': 6, 'name': 'work_history', 'title': 'Quá trình Công tác', 'subtitle': 'Liệt kê quá trình làm việc, bắt đầu từ gần nhất.', 'render_func': render_generic_step, 'needs_clearance': None, 'fields': [], 'dataframes': [{'field': AppSchema.WORK_DATAFRAME, 'columns': {'work_from': {'label': 'Từ (MM/YYYY)', 'props': 'dense outlined mask="##/####"'}, 'work_to': {'label': 'Đến (MM/YYYY)', 'props': 'dense outlined mask="##/####"'}, 'work_unit': {'label': 'Đơn vị'}, 'work_role': {'label': 'Chức vụ'}}, 'validators': {'work_from': [required('Vui lòng điền thời gian bắt đầu.'), match_pattern(DATE_MMYYYY_PATTERN, 'Dùng định dạng MM/YYYY')], 'work_to': [required('Vui lòng điền thời gian kết thúc.'), match_pattern(DATE_MMYYYY_PATTERN, 'Dùng định dạng MM/YYYY'), is_date_after('work_from', 'Ngày kết thúc phải sau ngày bắt đầu.')], 'work_unit': [required('Vui lòng điền đơn vị.')], 'work_role': [required('Vui lòng điền chức vụ.')]}}]},
    7: {'id': 7, 'name': 'awards', 'title': 'Khen thưởng & Kỷ luật', 'subtitle': 'Liệt kê các khen thưởng hoặc kỷ luật đáng chú ý.', 'render_func': render_generic_step, 'needs_clearance': None, 'fields': [{'field': AppSchema.AWARD, 'validators': [required_choice("Vui lòng chọn khen thưởng.")]}, {'field': AppSchema.DISCIPLINE, 'validators': []}], 'dataframes': []},
    16: {'id': 16, 'name': 'review', 'title': 'Xem lại & Hoàn tất', 'subtitle': 'Kiểm tra lại toàn bộ thông tin và tạo file PDF.', 'render_func': render_review_step, 'needs_clearance': None, 'fields': [], 'dataframes': []},
}

def _get_current_form_template() -> FormTemplate | None:
    """Looks up the blueprint for the user's selected form use case."""
    user_storage = get_user_storage()
    use_case_value_str = user_storage.get(SELECTED_USE_CASE_KEY)
    if not use_case_value_str:
        return None
    try:
        selected_use_case = FormUseCaseType[use_case_value_str]
        return FORM_TEMPLATE_REGISTRY.get(selected_use_case)
    except KeyError:
        return None


def next_step() -> None:
    """Navigates to the next step based on the selected template's defined sequence."""
    user_storage = get_user_storage()
    current_step_id: int = cast(int, user_storage.get(STEP_KEY, 0))
    form_template = _get_current_form_template()
    if not form_template:
        user_storage[STEP_KEY] = 0
        update_step_content.refresh()
        return
    step_sequence: list[int] = form_template['step_sequence']
    if current_step_id == 0:
        if step_sequence:
            user_storage[STEP_KEY] = step_sequence[0]
        else:
            user_storage[STEP_KEY] = 0
    else:
        try:
            current_index = step_sequence.index(current_step_id)
            if current_index < len(step_sequence) - 1:
                user_storage[STEP_KEY] = step_sequence[current_index + 1]
        except ValueError:
            user_storage[STEP_KEY] = 0
    user_storage[FORM_ATTEMPTED_SUBMISSION_KEY] = False
    user_storage[CURRENT_STEP_ERRORS_KEY] = {}
    update_step_content.refresh()


def prev_step() -> None:
    """Navigates to the previous step in the sequence or back to the selector."""
    user_storage = get_user_storage()
    current_step_id: int = cast(int, user_storage.get(STEP_KEY, 0))
    form_template = _get_current_form_template()
    if not form_template:
        user_storage[STEP_KEY] = 0
        update_step_content.refresh()
        return
    step_sequence: list[int] = form_template['step_sequence']
    try:
        current_index = step_sequence.index(current_step_id)
        if current_index == 0:
            user_storage[STEP_KEY] = 0
        else:
            user_storage[STEP_KEY] = step_sequence[current_index - 1]
    except ValueError:
        user_storage[STEP_KEY] = 0
    user_storage[FORM_ATTEMPTED_SUBMISSION_KEY] = False
    user_storage[CURRENT_STEP_ERRORS_KEY] = {}
    update_step_content.refresh()
 
@ui.refreshable
def update_step_content() -> None:
    user_storage = get_user_storage()
    current_step_id: int = user_storage.get(STEP_KEY, 0)
    step_to_render = STEPS_BY_ID.get(current_step_id)
    if step_to_render:
        step_to_render['render_func'](step_to_render)
    else:
        ui.label(f"Lỗi: Bước không xác định ({current_step_id})").classes('text-negative text-h6')
        ui.button("Bắt đầu lại", on_click=lambda: (app.storage.user.clear(), ui.navigate.to('/'))).props('color=primary unelevated')

# ===================================================================
# 6. MAIN PAGE AND APP STARTUP
# ===================================================================

@ui.page('/login')
def login_page() -> None:
    """The page where users enter their credentials."""
    def attempt_login() -> None:
        username = username_input.value
        password = password_input.value
        if ALLOWED_USERS.get(username) == password:
            app.storage.user['username'] = username
            app.storage.user['authenticated'] = True
            # This is where we set up a new user's environment
            initialize_form_data()
            ui.navigate.to('/')
        else:
            ui.notify('Sai tên đăng nhập hoặc mật khẩu.', color='negative')

    with ui.card().classes('absolute-center'):
        ui.label('Đăng nhập vào AutoLý').classes('text-h6 self-center')
        username_input = ui.input('Tên đăng nhập').on('keydown.enter', attempt_login)
        password_input = ui.input('Mật khẩu', password=True, password_toggle_button=True).on('keydown.enter', attempt_login)
        ui.button('Đăng nhập', on_click=attempt_login).classes('self-center')


@ui.page('/')
def main_page() -> None:
    # This is the gatekeeper for our main application.
    user_storage = get_user_storage()
    if not user_storage.get('authenticated'):
        ui.navigate.to('/login')
        return
    
    def logout() -> None:
        # Clear the session cookie and redirect to login
        user_storage.clear()
        ui.navigate.to('/login')

    ui.query('body').style('background-color: #f0f2f5;')
    with ui.header(elevated=True).classes('bg-primary text-white q-pa-sm items-center'):
        ui.label("📝 AutoLý – Kê khai Sơ yếu lý lịch").classes('text-h5')
        ui.space()
        
        # User info and logout button
        with ui.row().classes('items-center'):
            ui.label(f"Xin chào, {get_current_user()}!").classes('q-mr-md')
            ui.button('Đăng xuất', on_click=logout, color='white', icon='logout').props('flat dense')
        
        # Debug menu remains, but now it shows the *entire* data store
        with ui.button(icon='bug_report', color='white').props('flat round dense'):
            with ui.menu().classes('bg-grey-2 shadow-3'):
                with ui.card().style("min-width: 450px; max-width: 90vw;"):
                    with ui.expansion("Toàn bộ dữ liệu người dùng (USER_DATA_STORE)", icon="storage").classes("w-full"):
                        # This shows the data for ALL users, demonstrating isolation.
                        ui.json_editor({'value': USER_DATA_STORE}).props('readonly')

    with ui.card().classes('q-mx-auto q-my-md q-pa-md shadow-4') \
                  .style('width: 95%; max-width: 900px;'):
        with ui.column().classes('w-full'):
            update_step_content()

if __name__ in {"__main__", "__mp_main__"}:
    # This check is now less critical as the path comes from the blueprint,
    # but it's a good sanity check for the default template on startup.
    default_template_path = Path(FORM_TEMPLATE_REGISTRY[FormUseCaseType.PRIVATE_SECTOR]['pdf_template_path'])
    if not default_template_path.exists():
        print(f"WARNING: Default PDF template not found at '{default_template_path}'. PDF generation may fail.")
    
    ui.run(storage_secret='a_secure_and_unique_secret_string_for_this_app!',
           uvicorn_reload_dirs='.', uvicorn_reload_includes='*.py')

