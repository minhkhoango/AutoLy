# myapp.py

# ===================================================================
# 1. IMPORTS
# ===================================================================
import calendar
from nicegui import ui, app
from typing import (
    Any, TypedDict,
    TypeAlias, cast
)
from collections.abc import Callable
from passlib.context import CryptContext

# Assuming validation.py and para.py are in the same directory or accessible in PYTHONPATH
from validation import (
    ValidatorFunc,
    required, required_choice, match_pattern, is_within_date_range, is_date_after
)
import fitz
import tempfile
from pathlib import Path
from typing_extensions import NotRequired
import re
from re import Pattern
from datetime import datetime, date
# from dateutil.relativedelta import relativedelta
import logging

# Import the new, powerful schema and utilities
from form_data_builder import FormUseCaseType, FormTemplate, FORM_TEMPLATE_REGISTRY
from utils import (
    AppSchema, FormField,
    STEP_KEY, FORM_DATA_KEY, SELECTED_USE_CASE_KEY, # <-- ADD THIS
    FORM_ATTEMPTED_SUBMISSION_KEY, CURRENT_STEP_ERRORS_KEY,
)
from validation import EMAIL_PATTERN

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

# ===================================================================
# 2. SECURE AUTH & IN-MEMORY DATABASE
# ===================================================================

# This is our temporary user database. In a real app, this would be a database table.
# Passwords should be hashed, but for the MVP, plaintext is fine to see the mechanism.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# This is the "Hotel Register". It holds ALL data for ALL logged-in users.
# Key: username, Value: that user's entire data dictionary.
USER_DATABASE: dict[str, dict[str, Any]] = {}

def get_current_user() -> str | None:
    """Safely retrieves the username from the user's session storage."""
    user_storage = cast(dict[str, Any], app.storage.user)
    return cast(str | None, user_storage.get('username'))

# --- NEW: Password verification function ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compares a plain password to a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

# --- NEW: Password hashing function ---
def get_password_hash(password: str) -> str:
    """Creates a hash from a plain password."""
    return pwd_context.hash(password)

# ===================================================================
# 3. CENTRALIZED DATA HELPERS (Now user-aware)
# ===================================================================
def get_user_storage() -> dict[str, Any]:
    """
    Retrieves the data dictionary for the currently logged-in user from the global store.
    """
    username = get_current_user()
    if not username:
        # This should not happen on a protected page, but as a safeguard:
        raise PermissionError("Attempted to access user storage without being logged in.")
    
    if username not in USER_DATABASE:
        USER_DATABASE[username] = {}
    
    return USER_DATABASE[username]

def get_form_data() -> dict[str, Any]:
    """
    Now fetches form_data from the correct user's slot in the
    global USER_DATABASE.
    """
    user_storage = get_user_storage()
    if not isinstance(user_storage.get(FORM_DATA_KEY), dict):
        user_storage[FORM_DATA_KEY] = {}
    return cast(dict[str, Any], user_storage[FORM_DATA_KEY])

def initialize_form_data_if_new(username: str) -> None:
    """
    This now only runs during signup to create the initial data structure
    for a brand new user.
    """
    user_storage = USER_DATABASE.get(username, {})
    
    # This function is now simpler. It's just for setting up the form defaults.
    # The main user record is created in the signup handler.
    form_data: dict[str, Any] = {}
    user_storage['form_data'] = form_data
    
    # Initialize all step-related data
    user_storage['form_data'][STEP_KEY] = 0
    user_storage['form_data'][SELECTED_USE_CASE_KEY] = None
    user_storage['form_data'][FORM_ATTEMPTED_SUBMISSION_KEY] = False
    user_storage['form_data'][CURRENT_STEP_ERRORS_KEY] = {}
    
    # Populate the form_data dictionary with all field defaults
    for field in AppSchema.get_all_fields():
        form_data[field.key] = field.default_value
    
    # Initialize dataframe fields as empty lists
    form_data[AppSchema.TRAINING_DATAFRAME.key] = []
    form_data[AppSchema.WORK_DATAFRAME.key] = []
    
    

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

def execute_step_validators(
    step_def: StepDefinition,
    form_data: dict[str, Any]
) -> tuple[bool, dict[str, str]]:
    """
    Executes all validators for a given step by reading the rules directly
    from the step's definition blueprint. This is the correct, type-safe implementation.
    """
    new_errors: dict[str, str] = {}
    is_step_valid: bool = True

    # Validate the simple fields defined directly in the step
    for field_conf in step_def.get('fields', []):
        if not _validate_simple_field(field_conf['field'].key, field_conf['validators'], form_data, new_errors):
            is_step_valid = False
            
    # Validate the more complex dataframe fields
    for df_conf in step_def.get('dataframes', []):
        if not _validate_dataframe_field(df_conf['field'].key, df_conf['validators'], form_data, new_errors):
            is_step_valid = False

    return is_step_valid, new_errors

# ===================================================================
# 3. CORE LOGIC & NAVIGATION
# ===================================================================

async def _handle_step_confirmation(button: ui.button) -> None:
    """The core logic for validating a step and moving to the next."""
    button.disable()
    try:
        form_data = get_form_data()
        current_step_id = form_data.get(STEP_KEY, 0)
        current_step_def = STEPS_BY_ID.get(current_step_id)
        if not current_step_def: return

        # This now passes the correct argument type (StepDefinition) and is type-safe.
        all_valid, new_errors = execute_step_validators(current_step_def, form_data)

        form_data[FORM_ATTEMPTED_SUBMISSION_KEY] = True
        form_data[CURRENT_STEP_ERRORS_KEY] = new_errors

        if all_valid:
            if current_step_id == 0:
                form_data[SELECTED_USE_CASE_KEY] = form_data.get(AppSchema.FORM_TEMPLATE_SELECTOR.key)
            ui.notify("Thông tin hợp lệ!", type='positive')
            next_step()
        else:
            # --- THIS IS THE FIX ---
            # Instead of one generic message, we loop through the actual errors.
            for error_message in new_errors.values():
                ui.notification(error_message, type='negative', multi_line=True)
            # We still refresh the UI to highlight the fields themselves.
            update_step_content.refresh()
    finally:
        button.enable()

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
        selected_use_case = FormUseCaseType[cast(str, form_data.get(SELECTED_USE_CASE_KEY))]

        # 2. --- DRAW ALL DATA ---
        # Process simple fields
        for field in AppSchema.get_all_fields():
            if field.pdf_columns:
                continue  # This correctly skips only the dataframe fields.
            
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
        raise


async def create_and_download_pdf(button: ui.button) -> None:
    button.disable()
    output_pdf_path_obj = None
    try:
        form_data = get_form_data()
        selected_use_case_name = form_data.get(SELECTED_USE_CASE_KEY)
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
                output_pdf_path_obj.unlink()
            except Exception as e_del:
                print(f"Lỗi khi xóa file tạm: {e_del}")

# ===================================================================
# 4. UI RENDERING ENGINE
# ===================================================================

def _render_dataframe_editor(df_conf: DataframeConfig) -> None:
    """
    Renders a dynamic list of cards by reading the data structure
    directly from the AppSchema.
    """
    # 1. Get the main definition for the entire dataframe from the config.
    main_df_field = df_conf['field']
    ui.label(df_conf['field'].label).classes('text-subtitle1 q-mt-md q-mb-sm')
    dataframe_key = main_df_field.key

    # 2. Get the column definitions from the SSoT: AppSchema.
    if not main_df_field.row_schema:
        ui.label(f"Lỗi cấu hình: Dataframe '{main_df_field.key}' không có row_schema.").classes('text-negative')
        return
    
    column_definitions: list[FormField] = [
        field for field in main_df_field.row_schema.__dict__.values()
        if isinstance(field, FormField)
    ]

    @ui.refreshable
    def render_cards() -> None:
        form_data = get_form_data()
        data_list = cast(list[dict[str, Any]], form_data.get(dataframe_key, []))
        if not data_list:
            ui.label("Chưa có mục nào được thêm.").classes("text-italic text-grey q-pa-md text-center full-width")
        for i, row_data in enumerate(data_list):
            # The card now has a subtle border and shadow for depth
            with ui.card().classes('w-full q-mb-md').props("bordered flat"):
                # Clean header with flexbox for alignment
                with ui.card_section().classes('w-full !py-2'):
                    with ui.row().classes('w-full justify-between items-center no-wrap'):
                        ui.label(f"{main_df_field.label} #{i + 1}").classes('text-bold text-body1')
                        ui.button(icon='delete_outline', on_click=lambda _, idx=i: (data_list.pop(idx), render_cards.refresh()), color='grey-6').props('flat dense round padding=xs')
                
                ui.separator()
                
                # Two-column layout for the fields
                with ui.card_section():
                    date_fields = [f for f in column_definitions if f.ui_type == 'date']
                    other_fields = [f for f in column_definitions if f.ui_type != 'date']

                    with ui.row().classes('w-full'):
                        for col_field_def in date_fields:
                            # Each date component lives in a 'col' to space them evenly.
                            with ui.column().classes('col'):
                                create_field(
                                    field_definition=col_field_def,
                                    data_source=row_data,
                                    error_key_prefix=f"{dataframe_key}_{i}_"
                                )
                        # Right column for all other text/select inputs
                        for col_field_def in other_fields:
                            create_field(
                                field_definition=col_field_def,
                                data_source=row_data,
                                error_key_prefix=f"{dataframe_key}_{i}_"
                            )

    def add_new_row() -> None:
        form_data = get_form_data()
        data_list: list[dict[str, Any]] = form_data.setdefault(dataframe_key, [])
        data_list.append({})
        render_cards.refresh()

    render_cards()
    ui.button(f"Thêm {df_conf['field'].label}", on_click=add_new_row, icon='add').classes('q-mt-sm').props('outline color=primary')

# ===================================================================
# UI CREATION HELPERS (Moved from utils.py)
# ===================================================================

# myapp.py

# REPLACE THE ENTIRE FUNCTION WITH THIS
def _create_composite_date_input(
    field: FormField,
    data_source: dict[str, Any],
    current_errors: dict[str, str],
    error_key: str,
    form_attempted: bool
) -> None:
    """
    A robust, schema-aware date picker that correctly handles and saves
    both full 'YYYY-MM-DD' dates and partial 'MM/YYYY' dates.
    This version uses explicit, readable event handlers instead of complex lambdas.
    """
    # 1. Parse the initial value from the data source
    stored_value = data_source.get(field.key)
    d, m, y = None, None, None
    if isinstance(stored_value, str):
        try:
            if '/' in stored_value and not field.include_day:
                m_str, y_str = stored_value.split('/')
                m, y = int(m_str), int(y_str)
            elif '-' in stored_value and field.include_day:
                dt_obj = datetime.strptime(stored_value, '%Y-%m-%d').date()
                d, m, y = dt_obj.day, dt_obj.month, dt_obj.year
        except (ValueError, TypeError, IndexError):
            pass # Start with a blank slate if parsing fails

    # 2. Use a plain Python dictionary for local state.
    state = {'d': d, 'm': m, 'y': y}

    # 3. The sync function remains the brain.
    def sync_model() -> None:
        if not (state['y'] and state['m']):
            data_source[field.key] = None
            return

        if field.include_day:
            if state['d']:
                try:
                    data_source[field.key] = date(state['y'], state['m'], state['d']).strftime('%Y-%m-%d')
                except ValueError:
                    data_source[field.key] = None # Invalid date (e.g., Feb 30)
            else:
                data_source[field.key] = None
        else:
            data_source[field.key] = f"{state['m']:02d}/{state['y']}"

    # 4. EXPLICIT HANDLERS - This is the core fix.
    
    # This refreshable container will hold just the day selector
    @ui.refreshable
    def day_select_container() -> None:
        # We define the handler inside so it has access to 'state'
        def handle_day_change(e: Any) -> None:
            state['d'] = e.value
            sync_model()
            
        day_options = list(range(1, calendar.monthrange(state['y'], state['m'])[1] + 1)) if state['y'] and state['m'] else []
        is_error = form_attempted and current_errors.get(error_key) and not state['d']
        ui.select(day_options, value=state['d'], label='Ngày', on_change=handle_day_change).classes('col').props(f"outlined dense error={is_error}")

    def handle_month_year_change() -> None:
        """A single handler for both month and year changes."""
        # If the date is now invalid (e.g., from Mar 31 to Feb), fix the day.
        if field.include_day and state['y'] and state['m']:
            max_days = calendar.monthrange(state['y'], state['m'])[1]
            if state['d'] and state['d'] > max_days:
                state['d'] = max_days
        
        # We must tell the day selector to re-render its options.
        day_select_container.refresh()
        sync_model()

    def handle_month_select(e: Any) -> None:
        state['m'] = e.value
        handle_month_year_change()

    def handle_year_select(e: Any) -> None:
        state['y'] = e.value
        handle_month_year_change()

    # 5. Build the component using the new, clean handlers.
    with ui.column().classes('w-full no-wrap'):
        ui.label(field.label).classes('text-caption q-mb-xs')
        with ui.row().classes('w-full items-start no-wrap'):
            if field.include_day:
                day_select_container()

            is_m_error = form_attempted and current_errors.get(error_key) and not state['m']
            ui.select(list(range(1, 13)), value=state['m'], label='Tháng', on_change=handle_month_select).classes('col').props(f"outlined dense error={is_m_error}")

            is_y_error = form_attempted and current_errors.get(error_key) and not state['y']
            ui.select(list(range(date.today().year, 1900, -1)), value=state['y'], label='Năm', on_change=handle_year_select).classes('col').props(f"outlined dense error={is_y_error}")

def create_text_input(f: FormField, v: Any, data_source: dict[str, Any]) -> ui.input:
    """Creates a standard text input field bound to the data source."""
    return ui.input(label=f.label, value=v, on_change=lambda e: data_source.update({f.key: e.value}))

def create_select_input(f: FormField, v: Any, data_source: dict[str, Any]) -> ui.select:
    """Creates a dropdown select field bound to the data source."""
    # assert type(f.options) == dict[str, str]
    return ui.select(options=f.options or [], label=f.label, value=v, on_change=lambda e: data_source.update({f.key: e.value}))

def create_radio_buttons(f: FormField, v: Any, data_source: dict[str, Any]) -> ui.radio:
    """Creates a set of radio buttons bound to the data source."""
    # assert type(f.options) == dict[str, str]
    return ui.radio(options=f.options or [], value=v, on_change=lambda e: data_source.update({f.key: e.value}))

def create_textarea_input(f: FormField, v: Any, data_source: dict[str, Any]) -> ui.textarea:
    """Creates a multi-line text area bound to the data source."""
    return ui.textarea(label=f.label, value=v, on_change=lambda e: data_source.update({f.key: e.value}))

def create_checkbox_input(f: FormField, v: Any, data_source: dict[str, Any]) -> ui.checkbox:
    """Creates a checkbox bound to the data source."""
    return ui.checkbox(text=f.label, value=bool(v), on_change=lambda e: data_source.update({f.key: e.value}))

def create_field(field_definition: FormField,
                 data_source: dict[str, Any] | None = None,
                 error_key_prefix: str = "") -> None:
    """
    Creates a UI element based on a FormField definition. Now accepts an
    optional data_source to bind to, for use in dataframe cards.
    """
    # If no specific data_source is given, default to the main form_data
    if data_source is None:
        data_source = get_form_data()

    # Ensure the field has a default value in the data_source if it's missing
    if field_definition.key not in data_source:
        data_source[field_definition.key] = field_definition.default_value

    current_value = data_source.get(field_definition.key)
    user_storage = get_form_data()
    form_attempted: bool = user_storage.get(FORM_ATTEMPTED_SUBMISSION_KEY, False)
    current_errors: dict[str, str] = user_storage.get(CURRENT_STEP_ERRORS_KEY, {})

    # Construct the unique error key for this field
    error_key = f"{error_key_prefix}{field_definition.key}"
    error_message: str | None = current_errors.get(error_key) if form_attempted else None
    has_error = bool(error_message)

    # --- UI Construction ---
    with ui.column().classes('w-full no-wrap q-mb-sm'):
        # For certain types, we provide the label manually above the element
        
        if field_definition.ui_type == 'date':
            _create_composite_date_input(field_definition, data_source, 
            current_errors, error_key, form_attempted)
        else:
            # --- Element Creator Map ---
            creator_map: dict[str, Callable[..., Any]] = {
                'text': create_text_input,
                'select': create_select_input,
                'radio': create_radio_buttons,
                'textarea': create_textarea_input,
                'checkbox': create_checkbox_input,
            }
            creator = creator_map.get(field_definition.ui_type)
            if not creator:
                raise ValueError(f"Unsupported UI type: {field_definition.ui_type}")

            # Create the element, now explicitly passing all dependencies.
            element = creator(field_definition, current_value, data_source)

            if field_definition.ui_type != 'date':
                element.props(f"outlined dense error-message='{error_message or ""}' error={has_error}").classes('w-full')

# --- Generic step renderer now uses the new dataframe renderer ---
def render_generic_step(step_def: StepDefinition) -> None:
    """
    Renders a full step UI based on its definition in the blueprint.
    This function can now handle both simple vertical layouts and
    complex tabbed layouts, driven entirely by the step's data structure.
    """
    ui.label(step_def['title']).classes('text-h6 q-mb-xs')
    ui.markdown(step_def['subtitle'])

    # Render simple field
    for field_conf in step_def.get('fields', []):
        create_field(field_definition=field_conf['field'])

    # Render dataframe "block" editors
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
    0: {'id': 0, 'name': 'dossier_selector', 'title': 'Chọn Loại Hồ Sơ', 'subtitle': 'Chọn loại hồ sơ bạn cần, hệ thống sẽ tạo các bước cần thiết.', 'render_func': render_generic_step, 'fields': [{'field': AppSchema.FORM_TEMPLATE_SELECTOR, 'validators': [required_choice("Vui lòng chọn một loại hồ sơ.")]}], 'dataframes': [], 'needs_clearance': None},
    1: {'id': 1, 'name': 'core_identity', 'title': 'Thông tin cá nhân', 'subtitle': 'Thông tin định danh cơ bản của bạn.', 'render_func': render_generic_step, 'needs_clearance': None, 'fields': [
        {'field': AppSchema.FULL_NAME, 'validators': [required("Vui lòng điền họ tên."), match_pattern(FULL_NAME_PATTERN, "Họ tên phải viết hoa.")]},
        {'field': AppSchema.GENDER, 'validators': [required_choice("Vui lòng chọn giới tính.")]},
        {'field': AppSchema.DOB, 'validators': [required('Vui lòng điền ngày sinh.'), is_within_date_range()]},
        {'field': AppSchema.BIRTH_PLACE, 'validators': [required("Vui lòng chọn nơi sinh.")]}
    ], 'dataframes': []},
    3: {'id': 3, 'name': 'contact', 'title': 'Địa chỉ & liên lạc', 'subtitle': 'Địa chỉ và số điện thoại để liên lạc khi cần.', 'render_func': render_generic_step, 'needs_clearance': None, 'fields': [
        {'field': AppSchema.REGISTERED_ADDRESS, 'validators': [required("Vui lòng điền địa chỉ hộ khẩu.")]},
        {'field': AppSchema.PHONE, 'validators': [required('Vui lòng điền số điện thoại.'), match_pattern(PHONE_PATTERN, "Số điện thoại không hợp lệ.")]}
    ], 'dataframes': []},
    5: {'id': 5, 'name': 'education', 'title': 'Học vấn & Chuyên môn', 'subtitle': 'Quá trình học tập và đào tạo.', 'render_func': render_generic_step, 'needs_clearance': None, 'fields': [{'field': AppSchema.EDUCATION_HIGH_SCHOOL, 'validators': [required_choice("Vui lòng chọn lộ trình học cấp ba.")]}], 'dataframes': [
        {
            # Just point to the field in AppSchema. No more column definitions here!
            'field': AppSchema.TRAINING_DATAFRAME,
            # Validators are step-specific, so they stay here.
            'validators': {
                'training_from': [required('Điền thời gian bắt đầu.'), match_pattern(DATE_MMYYYY_PATTERN, 'Dùng định dạng MM/YYYY')],
                'training_to': [required('Điền thời gian kết thúc.'), match_pattern(DATE_MMYYYY_PATTERN, 'Dùng định dạng MM/YYYY'), is_date_after('training_from', 'Ngày kết thúc phải sau ngày bắt đầu.')],
                'training_unit': [required('Điền tên trường.')],
                'training_field': [required('Điền ngành học.')],
            }
        }
    ]},
    6: {'id': 6, 'name': 'work_history', 'title': 'Quá trình Công tác', 'subtitle': 'Liệt kê quá trình làm việc, bắt đầu từ gần nhất.', 'render_func': render_generic_step, 'needs_clearance': None, 'fields': [], 'dataframes': [
        {
            'field': AppSchema.WORK_DATAFRAME,
            'validators': {
                'work_from': [required('Điền thời gian bắt đầu.'), match_pattern(DATE_MMYYYY_PATTERN, 'Dùng định dạng MM/YYYY')],
                'work_to': [required('Điền thời gian kết thúc.'), match_pattern(DATE_MMYYYY_PATTERN, 'Dùng định dạng MM/YYYY'), is_date_after('work_from', 'Ngày kết thúc phải sau ngày bắt đầu.')],
                'work_unit': [required('Điền đơn vị.')],
            }
        }
    ]},
    # ... (rest of the steps are unchanged) ...
    7: {'id': 7, 'name': 'awards', 'title': 'Khen thưởng & Kỷ luật', 'subtitle': 'Thông tin về khen thưởng và kỷ luật (nếu có).', 'render_func': render_generic_step, 'needs_clearance': None, 'fields': [{'field': AppSchema.AWARD, 'validators': [required_choice("Vui lòng chọn khen thưởng.")]}, {'field': AppSchema.DISCIPLINE, 'validators': []}], 'dataframes': []},
    16: {'id': 16, 'name': 'review', 'title': 'Xem lại & Hoàn tất', 'subtitle': 'Kiểm tra lại toàn bộ thông tin và tạo file PDF.', 'render_func': render_review_step, 'needs_clearance': None, 'fields': [], 'dataframes': []},
}

def _get_current_form_template() -> FormTemplate | None:
    """Looks up the blueprint for the user's selected form use case."""
    form_data = get_form_data()
    use_case_value_str = form_data.get(SELECTED_USE_CASE_KEY)
    if not use_case_value_str:
        return None
    try:
        selected_use_case = FormUseCaseType[use_case_value_str]
        return FORM_TEMPLATE_REGISTRY.get(selected_use_case)
    except KeyError:
        return None

def next_step() -> None:
    """Navigates to the next step based on the selected template's defined sequence."""
    form_data = get_form_data()
    current_step_id = form_data.get(STEP_KEY, 0)
    
    form_template = _get_current_form_template()
    if not form_template:
        form_data[STEP_KEY] = 0
    else:
        step_sequence = form_template['step_sequence']
        if current_step_id == 0:
            form_data[STEP_KEY] = step_sequence[0] if step_sequence else 0
        else:
            try:
                current_index = step_sequence.index(current_step_id)
                if current_index < len(step_sequence) - 1:
                    form_data[STEP_KEY] = step_sequence[current_index + 1]
            except ValueError:
                form_data[STEP_KEY] = 0
    
    form_data[FORM_ATTEMPTED_SUBMISSION_KEY] = False
    update_step_content.refresh()


def prev_step() -> None:
    """Navigates to the previous step in the sequence or back to the selector."""
    form_data = get_form_data()
    current_step_id = form_data.get(STEP_KEY, 0)

    form_template = _get_current_form_template()
    if not form_template:
        form_data[STEP_KEY] = 0
    else:
        step_sequence = form_template['step_sequence']
        try:
            current_index = step_sequence.index(current_step_id)
            form_data[STEP_KEY] = step_sequence[current_index - 1] if current_index > 0 else 0
        except ValueError:
            form_data[STEP_KEY] = 0
            
    form_data[FORM_ATTEMPTED_SUBMISSION_KEY] = False
    update_step_content.refresh()
 
@ui.refreshable
def update_step_content() -> None:
    form_data = get_form_data()
    current_step_id: int = form_data.get(STEP_KEY, 0)
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
        username = username_input.value.strip()
        password = password_input.value

        user_record = USER_DATABASE.get(username)
        # Check 1: Does the user exist?
        # Check 2: Does the password match the hash?
        if not user_record or not verify_password(password, user_record['hashed_password']):
            ui.notify('Sai tên đăng nhập hoặc mật khẩu.', color='negative')
            return

        # If successful, create the session "key card"
        app.storage.user['username'] = username
        app.storage.user['authenticated'] = True
        ui.navigate.to('/')

    with ui.card().classes('absolute-center'):
        ui.label('Đăng nhập AutoLý').classes('text-h6 self-center')
        username_input = ui.input('Email', on_change=lambda e: e.value.strip()).on('keydown.enter', attempt_login)
        password_input = ui.input('Mật khẩu', password=True, password_toggle_button=True).on('keydown.enter', attempt_login)
        ui.button('Đăng nhập', on_click=attempt_login).classes('self-center w-full')
        ui.label("Chưa có tài khoản?").classes('text-center self-center q-mt-md')
        ui.button('Đăng ký ngay', on_click=lambda: ui.navigate.to('/signup')).props('flat color=primary').classes('self-center w-full')

@ui.page('/signup')
def signup_page() -> None:
    """NEW: Page for users to create a new account."""
    async def attempt_signup() -> None:
        # --- Validation ---
        username = username_input.value.strip()
        password = password_input.value
        password_confirm = password_confirm_input.value

        errors = False
        if not EMAIL_PATTERN.match(username):
            username_input.error = "Vui lòng nhập email hợp lệ."
            errors = True
        if username in USER_DATABASE:
            username_input.error = "Email này đã được sử dụng."
            errors = True
        if len(password) < 8:
            password_input.error = "Mật khẩu phải có ít nhất 8 ký tự."
            errors = True
        if password != password_confirm:
            password_confirm_input.error = "Mật khẩu không khớp."
            errors = True
        
        if errors:
            return

        # --- Create User ---
        hashed_password = get_password_hash(password)
        USER_DATABASE[username] = {
            'hashed_password': hashed_password
        }
        initialize_form_data_if_new(username) # Setup the default form data for the new user
        
        logger.info(f"New user created: {username}")
        with ui.dialog() as dialog, ui.card():
            ui.label('Tạo tài khoản thành công! Bạn có thể đăng nhập ngay bây giờ.')
            ui.button('OK', on_click=lambda: (dialog.close(), ui.navigate.to('/login')))
        # Then we open the dialog we just defined.
        dialog.open()
            
    with ui.card().classes('absolute-center'):
        ui.label('Tạo tài khoản mới').classes('text-h6 self-center')
        username_input = ui.input('Email', on_change=lambda e: (e.value.strip(), setattr(username_input, 'error', None)))
        password_input = ui.input('Mật khẩu (ít nhất 8 ký tự)', password=True, password_toggle_button=True, on_change=lambda: setattr(password_input, 'error', None))
        password_confirm_input = ui.input('Xác nhận mật khẩu', password=True, on_change=lambda: setattr(password_confirm_input, 'error', None))
        ui.button('Đăng ký', on_click=attempt_signup).classes('self-center w-full q-mt-md')
        ui.button('Quay lại Đăng nhập', on_click=lambda: ui.navigate.to('/login')).props('flat color=primary').classes('self-center w-full')

@ui.page('/')
def main_page() -> None:
    # 1. First, check the browser's session cookie (the "key card").
    #    This check is cheap and doesn't require accessing the main data store.
    if not cast(dict[str, Any], app.storage.user).get('authenticated'):
        ui.navigate.to('/login')
        return

    def logout() -> None:
        # Correctly clear the session cookie to log the user out.
        # This does NOT delete their data in USER_DATA_STORE.
        app.storage.user.clear()
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
                    with ui.expansion("Toàn bộ dữ liệu người dùng (USER_DATABASE)", icon="storage").classes("w-full"):
                        # This shows the data for ALL users, demonstrating isolation.
                        ui.json_editor({'value': USER_DATABASE}).props('readonly')

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
    
    ui.run(storage_secret='mama_secret_code',
           uvicorn_reload_dirs='.', uvicorn_reload_includes='*.py')

