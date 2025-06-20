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
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader, PdfWriter
import tempfile
import io
from pathlib import Path
import os
from typing_extensions import NotRequired
import re
from re import Pattern
import datetime

# Import the new, powerful schema and utilities
from form_data_builder import FormUseCaseType, FormTemplate, FORM_TEMPLATE_REGISTRY
from utils import (
    AppSchema, FormField,
    STEP_KEY, FORM_DATA_KEY, SELECTED_USE_CASE_KEY, # <-- ADD THIS
    FORM_ATTEMPTED_SUBMISSION_KEY, CURRENT_STEP_ERRORS_KEY,
    create_field, initialize_form_data, get_form_data
)

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
        
        # --- BRANCH 1: Handle Dataframe Validation ---
        if isinstance(rules, dict):
            if not _validate_dataframe_field(field_key, rules, form_data, new_errors):
                is_step_valid = False

        # --- BRANCH 2: Handle Simple Field Validation ---
        else: 
            if not _validate_simple_field(field_key, rules, form_data, new_errors):
                is_step_valid = False

    return is_step_valid, new_errors

# ===================================================================
# 3. CORE LOGIC & NAVIGATION
# ===================================================================

# The handler is now async and accepts the button it needs to control
async def _handle_step_confirmation(button: ui.button) -> None:
    """The core logic for validating a step and moving to the next."""
    button.disable()

    try:
        user_storage = cast(dict[str, Any], app.storage.user)
        current_step_id = user_storage.get(STEP_KEY, 0)
        current_step_def = STEPS_BY_ID.get(current_step_id)
        
        if not current_step_def: return

        # --- Build the list of validators dynamically from the step definition ---
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
        # ---

        current_form_data = get_form_data()
        all_valid, new_errors = execute_step_validators(validators_for_step, current_form_data)

        user_storage[FORM_ATTEMPTED_SUBMISSION_KEY] = True # Always set to true on click
        user_storage[CURRENT_STEP_ERRORS_KEY] = new_errors

        if all_valid:
            if current_step_id == 0:
                selected_use_case_name = current_form_data.get(AppSchema.FORM_TEMPLATE_SELECTOR.key)
    
                # Store the string name directly. No conversion. No confusion.
                user_storage[SELECTED_USE_CASE_KEY] = selected_use_case_name
            
            ui.notify("Thông tin hợp lệ!", type='positive')
            next_step()
        else:
            for error in new_errors.values():
                ui.notification(error, type='negative')
            update_step_content.refresh()
    finally:
        button.enable()

### RENDER PDF FUNCTION ###
def render_text_on_pdf(
    template_path: str | Path,
    form_data: dict[str, Any],
    form_template: FormTemplate,
    output_path: str | Path,
) -> None:
    """
    The new rendering engine. It draws text onto a multi-page PDF based
    on coordinates defined in AppSchema and page mappings in the FormTemplate.
    """
    FONT_PATH: Path = Path("./fonts/NotoSans-Regular.ttf") # Make sure this font exists
    FONT_NAME: str = "NotoSans"
    FONT_SIZE: int = 10
    LINE_HEIGHT: int = 25 # For dataframe rows

    if not FONT_PATH.exists():
        raise FileNotFoundError(f"Font not found at {FONT_PATH}")
    
    try:
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
    except Exception:
        pass # Font already registered

    template_pdf = PdfReader(template_path)
    output_writer = PdfWriter()

    # Create an overlay for each page that needs text
    overlays: dict[int, io.BytesIO] = {}

    def get_or_create_canvas(page_num: int) -> canvas.Canvas:
        """Manages one canvas per page."""
        page_index = page_num - 1
        if page_index not in overlays:
            overlays[page_index] = io.BytesIO()
            new_canvas = canvas.Canvas(overlays[page_index], 
                                        template_pdf.pages[page_index].mediabox)
            new_canvas.setFont(FONT_NAME, FONT_SIZE)
            return new_canvas
        # This part is tricky, might need to re-read the stream. For simplicity, we create one and use it.
        # A more robust solution might store canvas objects instead of BytesIO streams.
        # This implementation assumes we process all fields for a page at once.
        return canvas.Canvas(overlays[page_index], 
                             pagesize=template_pdf.pages[page_index].mediabox)
    
    user_storage = cast(dict[str, Any], app.storage.user)
    selected_use_case = FormUseCaseType[cast(str, user_storage.get(SELECTED_USE_CASE_KEY))]

    # 1. RENDER SIMPLE FIELDS
    for field in AppSchema.get_all_fields():
        if not field.pdf_coords or field.key in form_template['dataframe_page_map']:
            continue # Skip fields without coords or dataframe fields

        coords = field.pdf_coords.get(selected_use_case)
        if not coords:
            continue

        ### Assume all simple fields on page 1 ###
        can = get_or_create_canvas(page_num=1)
        value = form_data.get(field.key, '')

        if field.ui_type == 'date' and field.split_date:
            day, month, year = '', '', ''
            if value:
                try: 
                    dt_obj = datetime.strptime(str(value), '%Y-%m-%d')
                    day, month, year = dt_obj.strftime('%d'), dt_obj.strftime('%m'), dt_obj.strftime('%Y')
                except ValueError: 
                    pass # Let it render empty strings if date is invalid

            # Now, check the format of the coordinates
            if len(coords) == 2 and isinstance(coords[0], list):
                typed_coords = cast(tuple[list[float], float], coords)
                # This is your new format: ([x1, x2, x3], y)
                x_coords, y = typed_coords
                if len(x_coords) == 3:
                    can.drawString(x_coords[0], y, day)
                    can.drawString(x_coords[1], y, month)
                    can.drawString(x_coords[2], y, year)
                else:
                    print(f"WARNING: Coords for date field '{field.key}' are malformed. Expected 3 X-coordinates.")
            
            else:
                x, y = coords
                can.drawString(x, y, str(value))
        
        # 2. RENDER DATAFRAME FIELDS

        for df_key, page_num in form_template['dataframe_page_map'].items():
            df_field = getattr(AppSchema, df_key.upper(), None)
            if not df_field or not df_field.pdf_coords: 
                continue
            coords: tuple[float, float] = df_field.pdf_coords.get(selected_use_case)
            if not coords: 
                continue

            can = get_or_create_canvas(page_num)
            start_x, start_y = coords

            dataframe_data = cast(list[dict[str, str]], form_data.get(df_key, []))

             # This is a simple example for the work dataframe. You'll need to make this more generic
            # or have specific logic for each dataframe type.
            if df_key == AppSchema.WORK_DATAFRAME.key:
                for i, row in enumerate(dataframe_data):
                    y_pos = start_y - (i * LINE_HEIGHT)
                    from_to = f"{row.get('work_from','')} - {row.get('work_to','')}"
                    unit = row.get('work_unit', '')
                    role = row.get('work_role', '')
                    can.drawString(start_x, y_pos, from_to)
                    can.drawString(start_x + 150, y_pos, unit) # Adjust x spacing
                    can.drawString(start_x + 350, y_pos, role) # Adjust x spacing

            if df_key == AppSchema.TRAINING_DATAFRAME.key:
                for i, row in enumerate(dataframe_data):
                    y_pos = start_y - (i * LINE_HEIGHT)
                    from_to = f"{row.get('training_from','')} - {row.get('training_to','')}"
                    unit = row.get('training_unit', '')
                    field = row.get('training_field', '')
                    cert = row.get('training_certificate', '')
                    can.drawString(start_x, y_pos, from_to)
                    can.drawString(start_x + 150, y_pos, unit)
                    can.drawString(start_x + 300, y_pos, field)
                    can.drawString(start_x + 400, y_pos, cert)

    # Save all canvases
    for overlay in overlays.values():
        c = canvas.Canvas(overlay)
        c.save()

    # Merge overlays with the template
    for page_index, overlay_stream in overlays.items():
        overlay_stream.seek(0)
        overlay_pdf = PdfReader(overlay_stream)
        page = template_pdf.pages[page_index]
        page.merge_page(overlay_pdf.pages[0])
    
    output_writer.append(template_pdf)
    
    with open(output_path, "wb") as f:
        output_writer.write(f)

async def create_and_download_pdf(button: ui.button) -> None:
    """Orchestrates PDF generation using the direct rendering method."""
    button.disable()
    try:
        user_storage = cast(dict[str, Any], app.storage.user)
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

        template_path = form_template['pdf_template_path']
        if not os.path.exists(template_path):
            ui.notify(f"Lỗi: Không tìm thấy file mẫu PDF tại '{template_path}'.", type='negative')
            return

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmpfile_obj:
            output_pdf_path_str = tmpfile_obj.name
        
        render_text_on_pdf(
            template_path=template_path,
            form_data=form_data,
            form_template=form_template,
            output_path=output_pdf_path_str
        )

        pdf_content_bytes: bytes = Path(output_pdf_path_str).read_bytes()
        ui.download(src=pdf_content_bytes, filename="SoYeuLyLich_DaDien.pdf")
        ui.notify("Đã tạo PDF thành công!", type='positive')

    except Exception as e:
        print(f"Lỗi nghiêm trọng khi tạo PDF: {e}")
        import traceback
        traceback.print_exc()
        ui.notify(f"Đã xảy ra lỗi khi tạo PDF. Chi tiết: {e}", type='negative', multi_line=True)
    finally:
        button.enable()
        if 'output_pdf_path_str' in locals() and os.path.exists(output_pdf_path_str):
            try: os.remove(output_pdf_path_str)
            except Exception as e_del: print(f"Lỗi khi xóa file tạm: {e_del}")


# ===================================================================
# 4. UI RENDERING ENGINE
# ===================================================================
def _render_dataframe_editor(df_conf: DataframeConfig) -> None:
    """Renders a dynamic list editor for things like Work History, Siblings, etc."""
    ui.label(df_conf['field'].label).classes('text-subtitle1 q-mt-md q-mb-sm')
    
    user_storage = cast(dict[str, Any], app.storage.user)
    form_data = get_form_data()
    dataframe_key = df_conf['field'].key
    
    @ui.refreshable
    def render_rows() -> None:
        # Get the most up-to-date list from storage
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

                    ui.input(props['label'], value=str(entry.get(col_key, "")),
                             on_change=lambda e, idx=i, k=col_key: dataframe[idx].update({k: e.value})) \
                        .props(f"{props.get('props', 'dense outlined')} error-message='{error_message or ''}' error={has_error}")\
                        .classes(props.get('classes', 'col'))
                
                with ui.column().classes('col-auto'):
                    ui.button(icon='delete', on_click=lambda _, idx=i: (dataframe.pop(idx), render_rows.refresh()), color='negative') \
                        .props('flat dense round padding=xs')
        
        ui.button(f"Thêm thông tin", on_click=lambda: (dataframe.append({}), render_rows.refresh()), icon='add') \
            .classes('q-mt-sm').props('outline color=primary')

    render_rows()

# In myapp.py

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
        # BRANCH 2: Render the default simple layout
        render_field_list(step_def.get('fields', []))

    for df_conf in step_def.get('dataframes', []):
        _render_dataframe_editor(df_conf)

    # Render navigation buttons
    with ui.row().classes('w-full q-mt-lg justify-between items-center'):
        # The first step (id=0) should not have a "Back" button.
        if step_def['id'] > 0:
            ui.button("← Quay lại", on_click=prev_step).props('flat color=grey')
        else:
            ui.label() # Placeholder to keep alignment
        
        confirm_button = ui.button("Xác nhận & Tiếp tục →").props('color=primary unelevated')
        confirm_button.on('click', lambda: _handle_step_confirmation(confirm_button))
        
def render_emergency_contact_step(step_def: StepDefinition) -> None:
    """A special renderer for the emergency contact step with clean, reactive logic."""
    ui.label(step_def['title']).classes('text-h6 q-mb-xs')
    ui.markdown(step_def['subtitle'])

    form_data = get_form_data()

    # 1. The first field is simple, no changes needed.
    create_field(field_definition=AppSchema.EMERGENCY_CONTACT_DETAILS)

    emergency_place_input = ui.input(
        label=AppSchema.EMERGENCY_CONTACT_PLACE.label,
    ).classes('full-width').props('outlined dense').bind_value(
        form_data, AppSchema.EMERGENCY_CONTACT_PLACE.key
    )
    
    def visibility_transformer(is_checked: bool | None) -> bool:
        return not bool(is_checked)

    # We still use bind_visibility_from because it's a clean, declarative way to handle visibility.
    emergency_place_input.bind_visibility_from(
        form_data, AppSchema.SAME_ADDRESS_AS_REGISTERED.key,
        backward=visibility_transformer
    )

    # This function is now our single controller for the logic.
    # Its ONLY job is to change the data model and UI *properties* (like readonly).
    # It does NOT call .set_value().
    def sync_address_state(is_checked: bool) -> None:
        """Updates the data model based on the checkbox state."""
        if is_checked:
            # ACTION: Update the data model.
            registered_address = form_data.get(AppSchema.REGISTERED_ADDRESS.key, '')
            form_data[AppSchema.EMERGENCY_CONTACT_PLACE.key] = registered_address
            # ACTION: Change a UI property to give user feedback.
            emergency_place_input.props('readonly')
        else:
            # ACTION: Update the data model.
            form_data[AppSchema.EMERGENCY_CONTACT_PLACE.key] = ''
            # ACTION: Change a UI property.
            emergency_place_input.props(remove='readonly')

    
    # 3. Create the checkbox and link its on_change event to our new controller function.
    ui.checkbox(AppSchema.SAME_ADDRESS_AS_REGISTERED.label) \
        .bind_value(form_data, AppSchema.SAME_ADDRESS_AS_REGISTERED.key) \
        .on('update:model-value', lambda e: sync_address_state(e.args[0]))

    # 4. Initialize the state ONCE on load.
    #    No more fake event objects. We just call the function with the initial data.
    initial_state_is_checked = form_data.get(AppSchema.SAME_ADDRESS_AS_REGISTERED.key, False)
    sync_address_state(initial_state_is_checked)

    # Render navigation buttons (no changes here)
    with ui.row().classes('w-full q-mt-lg justify-between items-center'):
        if step_def['id'] > 0:
            ui.button("← Quay lại", on_click=prev_step).props('flat color=grey')
        else:
            ui.label()

        confirm_button = ui.button("Xác nhận & Tiếp tục →").props('color=primary unelevated')
        confirm_button.on('click', lambda: _handle_step_confirmation(confirm_button))

def render_review_step(step_def: 'StepDefinition') -> None:
    """A special renderer for the final review step."""
    ui.label(step_def['title']).classes('text-h6 q-mb-md') 
    ui.markdown(step_def['subtitle'])
    
    # ... Your detailed review display logic would go here ...
    ui.label("Review UI is under construction.").classes('text-center text-grey')
    
    pdf_button = ui.button("Tạo PDF").props('color=green unelevated').classes('q-mt-md q-mb-lg')
    pdf_button.on('click', lambda: create_and_download_pdf(pdf_button))

    with ui.row().classes('w-full justify-start items-center'): 
        ui.button("← Quay lại & Chỉnh sửa", on_click=prev_step).props('flat color=grey')

# ===================================================================
# 5. DEFINE THE BLUEPRINT & NAVIGATION ENGINE
# ===================================================================
# --- Patterns ---
FULL_NAME_PATTERN: Pattern[str] = re.compile(r'^[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴĐÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸ ]+$')
PHONE_PATTERN: Pattern[str] = re.compile(r'^0\d{9}$')
ID_NUMBER_PATTERN: Pattern[str] = re.compile(r'^(?:\d{9}|\d{12})$')
NUMERIC_PATTERN: Pattern[str] = re.compile(r'^\d+$')
SALARY_PATTERN: Pattern[str] = re.compile(r"^\d+$|^\d{1,3}(?:[.,]\d{3})*$")
DATE_MMYYYY_PATTERN: Pattern[str] = re.compile(r'^(0[1-9]|1[0-2])/\d{4}$')

# --- Smart, Reusable Validator Lists ---

age_validators: list[ValidatorFunc] = [
    required("Vui lòng điền năm sinh."),
    match_pattern(NUMERIC_PATTERN, "Năm sinh phải là một con số."),
]

STEPS_BY_ID: dict[int, StepDefinition] = {
    0: {
        'id': 0, 'name': 'dossier_selector',
        'title': 'Chọn Loại Hồ Sơ Cần Chuẩn Bị',
        'subtitle': 'Bắt đầu bằng cách chọn loại hồ sơ bạn cần. Hệ thống sẽ tự động tạo các bước cần thiết cho bạn.',
        'render_func': render_generic_step,
        'fields': [{'field': AppSchema.FORM_TEMPLATE_SELECTOR, 'validators': [required_choice("Vui lòng chọn một loại hồ sơ.")]}],
        'dataframes': [], 'needs_clearance': None
    },
    1: {
        'id': 1, 'name': 'core_identity', 'title': 'Thông tin cá nhân', 'subtitle': 'Bắt đầu với thông tin định danh cơ bản của bạn.',
        'render_func': render_generic_step, 'needs_clearance': None,
        'fields': [
            {'field': AppSchema.FULL_NAME, 'validators': [required("Vui lòng điền đầy đủ họ và tên."), match_pattern(FULL_NAME_PATTERN, "Họ và tên phải viết hoa, không chứa số hoặc ký tự đặc biệt.")]},
            {'field': AppSchema.GENDER, 'validators': [required_choice("Vui lòng chọn giới tính.")]},
            {'field': AppSchema.DOB, 'validators': [required('Vui lòng chọn ngày sinh.'),
                                                    is_within_date_range(message="Ngày sinh phải trong khoảng từ 01/01/1900 đến hôm nay.")]},
            {'field': AppSchema.BIRTH_PLACE, 'validators': [required("Vui lòng điền nơi sinh.")]},
        ], 'dataframes': []
    },
    2: {
        'id': 2, 'name': 'official_id', 'title': 'Giấy tờ tuỳ thân', 'subtitle': 'Cung cấp thông tin trên Căn cước công dân hoặc CMND của bạn.',
        'render_func': render_generic_step, 'needs_clearance': None,
        'fields': [
            {'field': AppSchema.ID_PASSPORT_NUM, 'validators': [required("Vui lòng điền số CMND/CCCD."), match_pattern(ID_NUMBER_PATTERN, "CMND/CCCD phải có 9 hoặc 12 chữ số.")]},
            {'field': AppSchema.ID_PASSPORT_ISSUE_DATE, 'validators': [required("Vui lòng chọn ngày cấp.")]},
            {'field': AppSchema.ID_PASSPORT_ISSUE_PLACE, 'validators': [required('Vui lòng điền nơi cấp CMND/CCCD.')]},
        ], 'dataframes': []
    },
    3: {
        'id': 3, 'name': 'contact', 'title': 'Thông tin liên lạc', 'subtitle': 'Địa chỉ và số điện thoại để liên lạc khi cần.',
        'render_func': render_generic_step, 'needs_clearance': None,
        'fields': [
            {'field': AppSchema.REGISTERED_ADDRESS, 'validators': [required("Vui lòng điền địa chỉ hộ khẩu.")]},
            {'field': AppSchema.PHONE, 'validators': [required('Vui lòng điền số điện thoại.'), match_pattern(PHONE_PATTERN, "Số điện thoại phải có 10 chữ số, bắt đầu bằng 0.")]},
        ], 'dataframes': []
    },
    4: {
        'id': 4, 'name': 'origin_info', 'title': 'Nguồn gốc & Tôn giáo', 'subtitle': 'Thông tin về dân tộc và tôn giáo của bạn.',
        'render_func': render_generic_step, 'needs_clearance': True,
        'fields': [
            {'field': AppSchema.ETHNICITY, 'validators': [required_choice("Vui lòng chọn dân tộc.")]},
            {'field': AppSchema.RELIGION, 'validators': [required_choice("Vui lòng chọn tôn giáo.")]},
            # {'field': AppSchema.PLACE_OF_ORIGIN, 'validators': [required("Vui lòng điền nguyên quán.")]},
        ], 'dataframes': []
    },
    5: {
        'id': 5, 'name': 'education', 'title': 'Học vấn & Chuyên môn', 'subtitle': 'Quá trình học tập, đào tạo định hình nên con người bạn.',
        'render_func': render_generic_step, 'needs_clearance': None,
        'fields': [
            {'field': AppSchema.EDUCATION_HIGH_SCHOOL, 'validators': [required_choice("Vui lòng chọn lộ trình học cấp ba.")]},
        ], 
        'dataframes': [{'field': AppSchema.TRAINING_DATAFRAME, 'columns': {'training_from': {'label': 'Từ (MM/YYYY)', 'props': 'dense outlined mask="##/####"'}, 
                                                                           'training_to': {'label': 'Đến (MM/YYYY)', 'props': 'dense outlined mask="##/####"'}, 
                                                                           'training_unit': {'label': 'Tên trường hoặc cơ sở đào tạo'}, 
                                                                           'training_field': {'label': 'Ngành học'},
                                                                           'training_format': {'label': 'Hình thức đào tạo'},
                                                                           'training_certificate': {'label': 'Văn bằng chứng chỉ'}}, 
                                                                           'validators': {'training_from': [required('Vui lòng điền thời gian bắt đầu.'), match_pattern(DATE_MMYYYY_PATTERN, 'Dùng định dạng MM/YYYY')], 
                                                                                      'training_to': [required('Vui lòng điền thời gian kết thúc.'), match_pattern(DATE_MMYYYY_PATTERN, 'Dùng định dạng MM/YYYY'), is_date_after('work_from', 'Ngày kết thúc phải sau ngày bắt đầu.')], 
                                                                                      'training_unit': [required('Vui lòng điền tên trường hoặc cơ sở đào tạo.')], 
                                                                                      'training_field': [required('Vui lòng điền ngành học.')],
                                                                                      'training_format': [required('Vui lòng điền hình thức đào tạo.')],
                                                                                      'training_certificate': [required('Vui lòng điền văn bằng chứng chỉ.')]}}]
    },
    6: {
        'id': 6, 'name': 'work_history', 'title': 'Quá trình Công tác', 'subtitle': 'Liệt kê quá trình làm việc, bắt đầu từ gần nhất.',
        'render_func': render_generic_step, 'needs_clearance': None, 'fields': [],
        'dataframes': [{'field': AppSchema.WORK_DATAFRAME, 'columns': {'work_from': {'label': 'Từ (MM/YYYY)', 'props': 'dense outlined mask="##/####"'}, 
                                                                       'work_to': {'label': 'Đến (MM/YYYY)', 'props': 'dense outlined mask="##/####"'}, 
                                                                       'work_unit': {'label': 'Đơn vị'}, 
                                                                       'work_role': {'label': 'Chức vụ'}}, 
                                                                       'validators': {'work_from': [required('Vui lòng điền thời gian bắt đầu.'), match_pattern(DATE_MMYYYY_PATTERN, 'Dùng định dạng MM/YYYY')], 
                                                                                      'work_to': [required('Vui lòng điền thời gian kết thúc.'), match_pattern(DATE_MMYYYY_PATTERN, 'Dùng định dạng MM/YYYY'), is_date_after('work_from', 'Ngày kết thúc phải sau ngày bắt đầu.')], 
                                                                                      'work_unit': [required('Vui lòng điền đơn vị.')], 
                                                                                      'work_role': [required('Vui lòng điền chức vụ.')]}}]
    },
    7: {
        'id': 7, 'name': 'awards', 'title': 'Khen thưởng & Kỷ luật', 'subtitle': 'Liệt kê các khen thưởng hoặc kỷ luật đáng chú ý.',
        'render_func': render_generic_step, 'needs_clearance': None,
        'fields': [
            {'field': AppSchema.AWARD, 'validators': [required_choice("Vui lòng chọn khen thưởng.")]},
            {'field': AppSchema.DISCIPLINE, 'validators': []},
        ], 'dataframes': []
    },
    8: {
        'id': 8, 'name': 'parents_basic', 'title': 'Thông tin Bố Mẹ', 'subtitle': 'Thông tin cơ bản về bố và mẹ của bạn.',
        'render_func': render_generic_step, 'needs_clearance': None, 'fields': [], 'dataframes': [],
        'layout': {'type': 'tabs', 'tabs': {'dad_panel': {'label': 'Thông tin Bố', 'fields': [{'field': AppSchema.DAD_NAME, 'validators': [required("Vui lòng điền họ tên Bố")]}, {'field': AppSchema.DAD_AGE, 'validators': age_validators}, {'field': AppSchema.DAD_JOB, 'validators': [required("Vui lòng điền nghề nghiệp của Bố.")]}]}, 'mom_panel': {'label': 'Thông tin Mẹ', 'fields': [{'field': AppSchema.MOM_NAME, 'validators': [required("Vui lòng điền họ tên Mẹ")]}, {'field': AppSchema.MOM_AGE, 'validators': age_validators}, {'field': AppSchema.MOM_JOB, 'validators': [required("Vui lòng điền nghề nghiệp của Mẹ.")]}]}}}
    },
    9: {
        'id': 9, 'name': 'siblings', 'title': 'Anh Chị Em ruột', 'subtitle': 'Kê khai thông tin về các anh, chị, em ruột (nếu có).',
        'render_func': render_generic_step, 'needs_clearance': True, 'fields': [],
        'dataframes': [{'field': AppSchema.SIBLING_DATAFRAME, 'columns': {'sibling_name': {'label': 'Họ và tên'}, 'sibling_age': {'label': 'Năm sinh', 'classes': 'col-2'}, 'sibling_job': {'label': 'Nghề nghiệp'}, 'sibling_address': {'label': 'Nơi ở', 'classes': 'col-3'}}, 'validators': {'sibling_name': [required('Vui lòng điền tên.')], 'sibling_age': [required('Vui lòng điền tuổi.'), match_pattern(NUMERIC_PATTERN, "Tuổi phải là số.")], 'sibling_job': [required('Vui lòng điền nghề nghiệp.')], 'sibling_address': [required('Vui lòng điền địa chỉ.')]}}]
    },
    10: {
        'id': 10, 'name': 'spouse_and_children', 'title': 'Vợ/Chồng & Các con', 'subtitle': 'Cung cấp thông tin về gia đình nhỏ của bạn (nếu có).',
        'render_func': render_generic_step, 'needs_clearance': True,
        'fields': [{'field': AppSchema.SPOUSE_NAME, 'validators': []}, {'field': AppSchema.SPOUSE_AGE, 'validators': []}, {'field': AppSchema.SPOUSE_JOB, 'validators': []}],
        'dataframes': [{'field': AppSchema.CHILD_DATAFRAME, 'columns': {'child_name': {'label': 'Họ và tên con'}, 'child_age': {'label': 'Tuổi con', 'classes': 'col-2'}, 'child_job': {'label': 'Học tập/Công tác'}}, 'validators': {'child_name': [required('Vui lòng điền tên con.')], 'child_age': [required('Vui lòng điền tuổi con.'), match_pattern(NUMERIC_PATTERN, "Tuổi phải là số.")], 'child_job': [required('Vui lòng điền nghề nghiệp con.')]}}]
    },
    11: {
        'id': 11, 'name': 'gov_political_class', 'title': 'Kê khai Thành phần', 'subtitle': 'Yêu cầu riêng cho hồ sơ Nhà nước.',
        'render_func': render_generic_step, 'needs_clearance': True,
        'fields': [
            {'field': AppSchema.SOCIAL_STANDING, 'validators': [required_choice("Vui lòng chọn thành phần bản thân.")]},
            {'field': AppSchema.FAMILY_STANDING, 'validators': [required_choice("Vui lòng chọn thành phần gia đình.")]},
        ], 'dataframes': []
    },
    12: {
        'id': 12, 'name': 'gov_affiliation', 'title': 'Thông tin Đảng/Đoàn & Lương', 'subtitle': 'Cung cấp thông tin về quá trình tham gia Đoàn, Đảng.',
        'render_func': render_generic_step, 'needs_clearance': True,
        'fields': [
            {'field': AppSchema.YOUTH_DATE, 'validators': []},
            {'field': AppSchema.PARTY_DATE, 'validators': []},
            {'field': AppSchema.CURRENT_SALARY, 'validators': [required("Vui lòng điền mức lương."), match_pattern(SALARY_PATTERN, "Lương phải là số.")]},
        ], 'dataframes': []
    },
    13: {
        'id': 13, 'name': 'gov_parents_history', 'title': 'Lịch sử Gia đình (chi tiết)', 'subtitle': 'Kê khai chi tiết quá trình hoạt động của bố mẹ qua các thời kỳ.',
        'render_func': render_generic_step, 'needs_clearance': True, 'fields': [], 'dataframes': [],
        'layout': {'type': 'tabs', 'tabs': {'dad_panel': {'label': 'Thông tin Bố', 'fields': [{'field': AppSchema.DAD_PRE_AUGUST_REVOLUTION, 'validators': [required("Vui lòng điền hoạt động của Bố.")]}, {'field': AppSchema.DAD_DURING_FRENCH_WAR, 'validators': [required("Vui lòng điền hoạt động của Bố.")]}, {'field': AppSchema.DAD_FROM_1955_PRESENT, 'validators': [required("Vui lòng điền hoạt động của Bố.")]}]}, 
                                            'mom_panel': {'label': 'Thông tin Mẹ', 'fields': [{'field': AppSchema.MOM_PRE_AUGUST_REVOLUTION, 'validators': [required("Vui lòng điền hoạt động của Mẹ.")]}, {'field': AppSchema.MOM_DURING_FRENCH_WAR, 'validators': [required("Vui lòng điền hoạt động của Mẹ.")]}, {'field': AppSchema.MOM_FROM_1955_PRESENT, 'validators': [required("Vui lòng điền hoạt động của Mẹ.")]}]}}}
    },
    14: {
        'id': 14, 'name': 'health_and_military', 'title': 'Sức khỏe & Quân sự', 'subtitle': 'Thông tin về sức khoẻ và nghĩa vụ quân sự (nếu có).',
        'render_func': render_generic_step, 'needs_clearance': True,
        'fields': [
            {'field': AppSchema.HEALTH, 'validators': [required("Vui lòng điền tình trạng sức khỏe.")]},
            {'field': AppSchema.HEIGHT, 'validators': [required("Điền chiều cao (cm)."), match_pattern(NUMERIC_PATTERN, "Phải là số.")]},
            {'field': AppSchema.WEIGHT, 'validators': [required("Điền cân nặng (kg)."), match_pattern(NUMERIC_PATTERN, "Phải là số.")]},
            {'field': AppSchema.JOIN_ARMY_DATE, 'validators': []},
            {'field': AppSchema.LEAVE_ARMY_DATE, 'validators': []},
        ], 'dataframes': [],
    },
    15: {
        'id': 15, 'name': 'emergency_contact', 'title': 'Liên hệ Khẩn cấp', 'subtitle': 'Người cần báo tin khi khẩn cấp.',
        'render_func': render_emergency_contact_step, 'needs_clearance': None,
        'fields': [
            {'field': AppSchema.EMERGENCY_CONTACT_DETAILS, 'validators': [required("Vui lòng điền tên người cần báo tin.")]},
            {'field': AppSchema.SAME_ADDRESS_AS_REGISTERED, 'validators': []},
            {'field': AppSchema.EMERGENCY_CONTACT_PLACE, 'validators': [lambda value, data: (True, '') if data.get(AppSchema.SAME_ADDRESS_AS_REGISTERED.key) else required("Vui lòng điền địa chỉ người báo tin.")(value, data)]},
        ], 'dataframes': [],
    },
    16: {
        'id': 16, 'name': 'review', 'title': 'Xem lại & Hoàn tất', 'subtitle': 'Kiểm tra lại toàn bộ thông tin và tạo file PDF.',
        'render_func': render_review_step, 'needs_clearance': None, 'fields': [], 'dataframes': []
    },
}

def _get_current_form_template() -> FormTemplate | None:
    """Looks up the blueprint for the user's selected form use case."""
    user_storage = cast(dict[str, Any], app.storage.user)
    
    # The value stored is now the STRING NAME of the Enum (e.g., 'PRIVATE_SECTOR')
    use_case_value_str = user_storage.get(SELECTED_USE_CASE_KEY)
    if not use_case_value_str:
        return None

    try:
        # Get the Enum member by its string name. This is the correct way.
        selected_use_case = FormUseCaseType[use_case_value_str]
        return FORM_TEMPLATE_REGISTRY.get(selected_use_case)
    except ValueError:
        # If the name (e.g., "PRIVATE_SECTOR") doesn't exist in the enum
        return None

def next_step() -> None:
    """Navigates to the next step based on the selected template's defined sequence."""
    user_storage = cast(dict[str, Any], app.storage.user)
    current_step_id: int = cast(int, user_storage.get(STEP_KEY, 0))

    # If we are at the selector step, the "next" step is the *first* in the sequence.
    if current_step_id == 0:
        form_template = _get_current_form_template()
        if form_template and form_template['step_sequence']:
            user_storage[STEP_KEY] = form_template['step_sequence'][0]
        else:
            user_storage[STEP_KEY] = 0 # Fallback
    else:
        # If we are in the middle of a sequence, find the next step.
        form_template = _get_current_form_template()
        if not form_template:
            user_storage[STEP_KEY] = 0 # Should not happen, but safe fallback
            update_step_content.refresh()
            return

        step_sequence: list[int] = form_template['step_sequence']
        try:
            current_index = step_sequence.index(current_step_id)
            if current_index < len(step_sequence) - 1:
                user_storage[STEP_KEY] = step_sequence[current_index + 1]
            # If it's the last step, we do nothing. The "Next" button shouldn't exist.
        except ValueError:
            # If the current step isn't in the sequence, go back to the start.
            user_storage[STEP_KEY] = 0

    # Reset validation state for the new step
    user_storage[FORM_ATTEMPTED_SUBMISSION_KEY] = False
    user_storage[CURRENT_STEP_ERRORS_KEY] = {}
    update_step_content.refresh()


def prev_step() -> None:
    """Navigates to the previous step in the sequence or back to the selector."""
    user_storage = cast(dict[str, Any], app.storage.user)
    current_step_id: int = cast(int, user_storage.get(STEP_KEY, 0))

    form_template = _get_current_form_template()
    if not form_template:
        user_storage[STEP_KEY] = 0
        update_step_content.refresh()
        return

    step_sequence: list[int] = form_template['step_sequence']
    try:
        current_index = step_sequence.index(current_step_id)
        # If we are at the first step of the sequence, "Back" goes to the selector.
        if current_index == 0:
            user_storage[STEP_KEY] = 0
        else:
            user_storage[STEP_KEY] = step_sequence[current_index - 1]
    except ValueError:
        # If current step is not in the sequence (e.g., something went wrong),
        # always return to the selector step.
        user_storage[STEP_KEY] = 0

    # Reset validation state for the new step
    user_storage[FORM_ATTEMPTED_SUBMISSION_KEY] = False
    user_storage[CURRENT_STEP_ERRORS_KEY] = {}
    update_step_content.refresh()
 
@ui.refreshable
def update_step_content() -> None:
    user_storage = cast(dict[str, Any], app.storage.user)
    current_step_id: int = user_storage.get(STEP_KEY, 0)
    # Find the correct step definition from the blueprint
    step_to_render = STEPS_BY_ID.get(current_step_id)
    
    if step_to_render:
        step_to_render['render_func'](step_to_render)
    else:
        # Error handling for an invalid step ID
        ui.label(f"Lỗi: Bước không xác định ({current_step_id})").classes('text-negative text-h6')
        ui.button("Bắt đầu lại", on_click=lambda: app.storage.user.clear()).props('color=primary unelevated')

# ===================================================================
# 6. MAIN PAGE AND APP STARTUP
# ===================================================================
@ui.page('/')
def main_page() -> None:
    user_storage = cast(dict[str, Any], app.storage.user)
    if not user_storage:
        user_storage[STEP_KEY] = 0
        user_storage[SELECTED_USE_CASE_KEY] = None
        
        user_storage[FORM_ATTEMPTED_SUBMISSION_KEY] = False
        user_storage[CURRENT_STEP_ERRORS_KEY] = {}

        # Initialize form_data and explicitly set the UI value to a string
        user_storage[FORM_DATA_KEY] = {}
        initialize_form_data()

    ui.query('body').style('background-color: #f0f2f5;')
    
    with ui.header(elevated=True).classes('bg-primary text-white q-pa-sm items-center'):
        ui.label("📝 AutoLý – Kê khai Sơ yếu lý lịch").classes('text-h5')
        ui.space()
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

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(storage_secret='a_secure_and_unique_secret_string_for_this_app!',
           uvicorn_reload_dirs='.', uvicorn_reload_includes='*.py')

