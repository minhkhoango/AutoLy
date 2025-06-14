# myapp.py

# ===================================================================
# 1. IMPORTS
# ===================================================================
from nicegui import ui, app
from typing import (
    Any, Callable, List, Dict, Optional, Tuple, TypedDict, Union,
    TypeAlias, cast
)

# Assuming validation.py and para.py are in the same directory or accessible in PYTHONPATH
from validation import (
    ValidatorFunc,
    required, required_choice, match_pattern, min_length
)
from fillpdf import fillpdfs  # type: ignore[import]
import tempfile
import os
from pathlib import Path
from typing import Pattern
from typing_extensions import NotRequired
import re

# --- Patterns ---
FULL_NAME_PATTERN: Pattern[str] = re.compile(r'^[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴĐÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸ ]+$')
PHONE_PATTERN: Pattern[str] = re.compile(r'^0\d{9}$')
ID_NUMBER_PATTERN: Pattern[str] = re.compile(r'^(?:\d{9}|\d{12})$')
NUMERIC_PATTERN: Pattern[str] = re.compile(r'^\d+$')
# --- NEW/REFINED PATTERNS ---
EDUCATION_HS_PATTERN: Pattern[str] = re.compile(r'^\d{1,2}/\d{2}$')
SALARY_PATTERN: Pattern[str] = re.compile(r'^[\d,.]+$') # Allows for numbers, commas, and dots
DATE_MMYYYY_PATTERN: Pattern[str] = re.compile(r'^(0[1-9]|1[0-2])/\d{4}$')

# Import the new, powerful schema and utilities
from utils import (
    AppSchema, FormField,
    STEP_KEY, FORM_DATA_KEY, NEEDS_CLEARANCE_KEY,
    FORM_ATTEMPTED_SUBMISSION_KEY, CURRENT_STEP_ERRORS_KEY,
    PDF_TEMPLATE_PATH, PDF_FILENAME,
    create_field, initialize_form_data, generate_pdf_data_mapping
)

# --- Modernized Type Aliases ---
SimpleValidatorEntry: TypeAlias = Tuple[str, List[ValidatorFunc]]
DataframeColumnRules: TypeAlias = Dict[str, List[ValidatorFunc]]
DataframeValidatorEntry: TypeAlias = Tuple[str, DataframeColumnRules]
ValidationEntry: TypeAlias = Union[SimpleValidatorEntry, DataframeValidatorEntry]

# --- Blueprint TypedDicts ---
# This makes our STEPS_DEFINITION fully type-checked and self-documenting.
class FieldConfig(TypedDict):
    field: FormField
    validators: List[ValidatorFunc]

class DataframeConfig(TypedDict):
    field: FormField
    columns: Dict[str, Dict[str, str]]
    validators: DataframeColumnRules

class PanelInfo(TypedDict):
    """Defines the structure for a single panel within a tabbed layout."""
    label: str
    fields: List[FieldConfig]

class TabbedLayout(TypedDict):
    """Defines the structure for the entire tabbed layout object."""
    type: str
    tabs: Dict[str, PanelInfo]

class StepDefinition(TypedDict):
    id: int
    name: str
    title: str
    subtitle: str
    render_func: Callable[['StepDefinition'], None] # Points to the generic or a special renderer
    fields: List[FieldConfig]
    dataframes: List[DataframeConfig] # For complex list editors
    needs_clearance: Optional[bool]
    layout: NotRequired[TabbedLayout] # The key may not exist.

# ===================================================================
# 2. PRIVATE HELPER FUNCTIONS (The Specialists)
# ===================================================================

def _validate_simple_field(
    field_key: str, validator_list: List[ValidatorFunc],
    form_data: Dict[str, Any], errors: Dict[str, str]
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
    form_data: Dict[str, Any], errors: Dict[str, str]
) -> bool:
    """
    Validates all cells within a dataframe field.
    Returns True if the entire dataframe is valid, False otherwise.
    Appends cell-specific error messages to the `errors` dictionary.
    """
    is_dataframe_valid: bool = True
    dataframe_value: List[Dict[str, Any]] = form_data.get(dataframe_key, [])
    
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
    validators_for_step: List[ValidationEntry],
    form_data: Dict[str, Any] # fetched from app.storage.user
) -> Tuple[bool, Dict[str, str]]:
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
    
    new_errors: Dict[str, str] = {}
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

_is_handling_confirmation: bool = False # Global flag to prevent re-entr

def _get_current_step_def() -> Optional[StepDefinition]:
    """Retrieves the full definition dictionary for the current step."""
    user_storage = cast(Dict[str, Any], app.storage.user)
    current_step_id: int = user_storage.get(STEP_KEY, 0)
    for step_def in STEPS_DEFINITION:
        if step_def['id'] == current_step_id:
            return step_def
    return None

def _handle_step_confirmation() -> None:
    """The core logic for validating a step and moving to the next."""
    global _is_handling_confirmation
    if _is_handling_confirmation: return
    _is_handling_confirmation = True

    try:
        user_storage = cast(Dict[str, Any], app.storage.user)
        current_step_def = _get_current_step_def()
        if not current_step_def: return

        # --- Build the list of validators dynamically from the step definition ---
        validators_for_step: List[ValidationEntry] = []
        for field_conf in current_step_def.get('fields', []):
            validators_for_step.append((field_conf['field'].key, field_conf['validators']))

        for df_conf in current_step_def.get('dataframes', []):
            validators_for_step.append((df_conf['field'].key, df_conf['validators']))
        # ---

        current_form_data = user_storage.get(FORM_DATA_KEY, {})
        all_valid, new_errors = execute_step_validators(validators_for_step, current_form_data)

        user_storage[FORM_ATTEMPTED_SUBMISSION_KEY] = True # Always set to true on click
        user_storage[CURRENT_STEP_ERRORS_KEY] = new_errors

        if all_valid:
            # check if we just finished step 0
            current_step_id = user_storage.get(STEP_KEY, 0)
            if current_step_id == 0:
                needs_clearance = (current_form_data.get(AppSchema.STEP0_ANS.key) == 'Có')
                user_storage[NEEDS_CLEARANCE_KEY] = needs_clearance

            ui.notify("Thông tin hợp lệ!", type='positive')
            next_step()
        else:
            for error in new_errors.values():
                ui.notify(error, type='negative')
            # Refresh the current step to show the new error messages
            update_step_content.refresh()
    finally:
        _is_handling_confirmation = False

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
    
    # Call the utility function to get the mapped data
    data_to_fill_pdf: Dict[str, Any] = generate_pdf_data_mapping()

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


# ===================================================================
# 3. THE NEW, GENERIC UI RENDERING ENGINE
# ===================================================================

# --- Special Component Renderers ---
# For complex UI parts like the dynamic list editor.
def _render_dataframe_editor(df_conf: DataframeConfig) -> None:
    """Renders a dynamic list editor for things like Work History, Siblings, etc."""
    ui.label(df_conf['field'].label).classes('text-subtitle1 q-mt-md q-mb-sm')
    
    user_storage = cast(Dict[str, Any], app.storage.user)
    form_data = cast(Dict[str, Any], user_storage[FORM_DATA_KEY])
    dataframe_key = df_conf['field'].key
    
    @ui.refreshable
    def render_rows() -> None:
        # Get the most up-to-date list from storage
        dataframe = cast(List[Dict[str, Any]], form_data.get(dataframe_key, []))
        form_attempted: bool = user_storage.get(FORM_ATTEMPTED_SUBMISSION_KEY, False)
        current_errors: Dict[str, str] = user_storage.get(CURRENT_STEP_ERRORS_KEY, {})
        
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

    user_storage = cast(Dict[str, Any], app.storage.user)
    current_step_errors: Dict[str, str] = user_storage.get(CURRENT_STEP_ERRORS_KEY, {})
    form_attempted: bool = user_storage.get(FORM_ATTEMPTED_SUBMISSION_KEY, False)

    # --- RENDERER LOGIC ---
    # This function creates the actual fields. We'll call it repeatedly.
    def render_field_list(fields_to_render: List[FieldConfig]) -> None:
        for field_conf in fields_to_render:
            create_field(
                field_definition=field_conf['field'],
                error_message=current_step_errors.get(field_conf['field'].key),
                form_attempted=form_attempted
            )

    # --- LAYOUT DISPATCHER ---
    # Check if a special layout is defined for this step
    if (layout_data := step_def.get('layout')) and layout_data.get('type') == 'tabs':
        # BRANCH 1: Render a tabbed layout
        # The walrus operator (:=) assigns the result of .get() to layout_data.
        # Now, inside this block, Pylance knows layout_data is a valid dict.

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

        ui.button("Xác nhận & Tiếp tục →", on_click=lambda: _handle_step_confirmation()) \
            .props('color=primary unelevated')
        


def render_review_step(step_def: 'StepDefinition') -> None:
    """A special renderer for the final review step."""
    ui.label(step_def['title']).classes('text-h6 q-mb-md') 
    ui.markdown(step_def['subtitle'])
    
    # ... Your detailed review display logic would go here ...
    ui.label("Review UI is under construction.").classes('text-center text-grey')

    ui.button("Tạo PDF", on_click=create_and_download_pdf).props('color=green unelevated').classes('q-mt-md q-mb-lg')
    with ui.row().classes('w-full justify-start items-center'): 
        ui.button("← Quay lại & Chỉnh sửa", on_click=prev_step).props('flat color=grey')

# ===================================================================
# 4. DEFINE THE BLUEPRINT
# ++ NEW "ROBO-TAX" APPLICATION FLOW BLUEPRINT ++
# ===================================================================
# ===================================================================
# 4. THE APPLICATION BLUEPRINT (NOW MORE POWERFUL)
# ===================================================================

# --- Smart, Reusable Validator Lists ---
# For things that are truly identical, like names and ages of people
name_validators: List[ValidatorFunc] = [
    required("Vui lòng điền đầy đủ họ và tên."),
    min_length(2, "Họ và tên quá ngắn."),
    match_pattern(FULL_NAME_PATTERN, "Họ và tên phải viết hoa, không chứa số hoặc ký tự đặc biệt."),
]
age_validators: List[ValidatorFunc] = [
    required("Vui lòng điền tuổi."),
    match_pattern(NUMERIC_PATTERN, "Tuổi phải là một con số."),
]

STEPS_DEFINITION: List[StepDefinition] = [
    # --- Onboarding ---
    {
        'id': 0, 'name': 'start', 'needs_clearance': None,
        'title': 'Bắt đầu',
        'subtitle': 'Chào mừng! Hãy cho chúng tôi biết bạn đang chuẩn bị hồ sơ cho loại hình tổ chức nào.',
        'render_func': render_generic_step,
        'fields': [
            {'field': AppSchema.STEP0_ANS, 'validators': [required_choice("Vui lòng chọn một mục.")]}
        ],
        'dataframes': []
    },

    # --- Core Identity & Contact ---
    {
        'id': 1, 'name': 'core_identity', 'needs_clearance': None,
        'title': 'Thông tin cá nhân',
        'subtitle': 'Tuyệt vời! Giờ hãy bắt đầu với một vài thông tin định danh cơ bản của bạn.',
        'render_func': render_generic_step,
        'fields': [
            {'field': AppSchema.FULL_NAME, 'validators': name_validators},
            {'field': AppSchema.GENDER, 'validators': [required_choice("Vui lòng chọn giới tính.")]},
            {'field': AppSchema.DOB, 'validators': [required('Vui lòng chọn ngày sinh.')]},
            {'field': AppSchema.BIRTH_PLACE, 'validators': [required("Vui lòng điền nơi sinh.")]},
        ],
        'dataframes': []
    },
    {
        'id': 2, 'name': 'official_id', 'needs_clearance': None,
        'title': 'Giấy tờ tuỳ thân',
        'subtitle': 'Tiếp theo, vui lòng cung cấp thông tin trên Căn cước công dân hoặc CMND của bạn.',
        'render_func': render_generic_step,
        'fields': [
            {'field': AppSchema.ID_PASSPORT_NUM, 'validators': [required("Vui lòng điền số CMND/CCCD."), 
                                                                match_pattern(ID_NUMBER_PATTERN, "CMND/CCCD phải có 9 hoặc 12 chữ số.")]},
            {'field': AppSchema.ID_PASSPORT_ISSUE_DATE, 'validators': [required("Vui lòng chọn ngày cấp.")]},
            {'field': AppSchema.ID_PASSPORT_ISSUE_PLACE, 'validators': [required('Vui lòng điền nơi cấp CMND/CCCD.')]},
        ],
        'dataframes': []
    },
    {
        'id': 3, 'name': 'contact', 'needs_clearance': None,
        'title': 'Thông tin liên lạc chính',
        'subtitle': 'Chúng tôi cần địa chỉ và số điện thoại để có thể liên lạc với bạn khi cần.',
        'render_func': render_generic_step,
        'fields': [
            # <<< FIXED
            {'field': AppSchema.REGISTERED_ADDRESS, 'validators': [required("Vui lòng điền địa chỉ hộ khẩu.")]},
            {'field': AppSchema.PHONE, 'validators': [required('Vui lòng điền số điện thoại.'), 
                                                      match_pattern(PHONE_PATTERN, "Số điện thoại phải có 10 chữ số, bắt đầu bằng 0.")]},
        ],
        'dataframes': []
    },
    {
        'id': 4, 'name': 'origin_info', 'needs_clearance': True,
        'title': 'Nguồn gốc & Tôn giáo',
        'subtitle': 'Hãy chia sẻ một chút về dân tộc và tôn giáo của bạn.',
        'render_func': render_generic_step,
        'fields': [
            # <<< FIXED
            {'field': AppSchema.ETHNICITY, 'validators': [required_choice("Vui lòng chọn dân tộc.")]},
            {'field': AppSchema.RELIGION, 'validators': [required_choice("Vui lòng chọn tôn giáo.")]},
            {'field': AppSchema.PLACE_OF_ORIGIN, 'validators': [required("Vui lòng điền nguyên quán.")]},
        ],
        'dataframes': []
    },

    # --- Professional Background ---
    {
        'id': 5, 'name': 'education', 'needs_clearance': None,
        'title': 'Học vấn & Chuyên môn',
        'subtitle': 'Quá trình học tập đã định hình nên con người bạn.',
        'render_func': render_generic_step,
        'fields': [
            # <<< REFINED
            {'field': AppSchema.EDUCATION_HIGH_SCHOOL, 'validators': [required_choice("Vui lòng điền lộ trình học cấp ba.")]},
            {'field': AppSchema.EDUCATION_HIGHEST, 'validators': [required_choice("Vui lòng chọn bằng cấp cao nhất.")]},
            {'field': AppSchema.EDUCATION_MAJOR, 'validators': []}, # Optional
            {'field': AppSchema.EDUCATION_FORMAT, 'validators': [required_choice("Vui lòng chọn loại hình đào tạo.")]},
            {'field': AppSchema.FOREIGN_LANGUAGE, 'validators': []}, # Optional
        ],
        'dataframes': []
    },
    {
        'id': 6, 'name': 'work_history', 'needs_clearance': None,
        'title': 'Quá trình Công tác',
        'subtitle': 'Liệt kê quá trình làm việc của bạn từ trước đến nay, bắt đầu từ gần nhất.',
        'render_func': render_generic_step,
        'fields': [],
        'dataframes': [{
            'field': AppSchema.WORK_DATAFRAME,
            'columns': {
                'work_from': {'label': 'Từ (MM/YYYY)', 'props': 'dense outlined mask="##/####"'},
                'work_to': {'label': 'Đến (MM/YYYY)', 'props': 'dense outlined mask="##/####"'},
                'work_task': {'label': 'Nhiệm vụ', 'classes': 'col-3'},
                'work_unit': {'label': 'Đơn vị'},
                'work_role': {'label': 'Chức vụ'}
            },
            # <<< REFINED
            'validators': {
                'work_from': [required('Bắt buộc'), match_pattern(DATE_MMYYYY_PATTERN, 'Định dạng MM/YYYY')],
                'work_to': [required('Bắt buộc'), match_pattern(DATE_MMYYYY_PATTERN, 'Định dạng MM/YYYY')],
                'work_task': [required('Bắt buộc')],
                'work_unit': [required('Bắt buộc')],
                'work_role': [required('Bắt buộc')],
            }
        }]
    },
    {
        'id': 7, 'name': 'awards', 'needs_clearance': None,
        'title': 'Khen thưởng & Kỷ luật',
        'subtitle': 'Nếu có bất kỳ khen thưởng hoặc kỷ luật nào đáng chú ý, hãy liệt kê ở đây.',
        'render_func': render_generic_step,
        'fields': [
            # <<< FIXED
            {'field': AppSchema.AWARD, 'validators': [required_choice("Vui lòng chọn khen thưởng.")]},
            {'field': AppSchema.DISCIPLINE, 'validators': []},
        ],
        'dataframes': []
    },
    
    # --- Family Background ---
    {
        'id': 8, 'name': 'parents_basic', 'needs_clearance': None,
        'title': 'Thông tin Bố Mẹ',
        'subtitle': 'Phần này dành cho thông tin cơ bản về bố và mẹ của bạn.',
        'render_func': render_generic_step,
        'fields': [],
        'dataframes': [],
        'layout': {
            'type': 'tabs',
            'tabs': {
                'dad_panel': {
                    'label': 'Thông tin cơ bản về bố',
                    'fields': [
                        {'field': AppSchema.DAD_NAME, 'validators': name_validators},
                        {'field': AppSchema.DAD_AGE, 'validators': age_validators},
                        {'field': AppSchema.DAD_JOB, 'validators': [required("Vui lòng điền nghề nghiệp của Bố.")]},
                    ]
                },
                'mom_panel': {
                    'label': 'Thông tin cơ bản về mẹ',
                    'fields': [
                        {'field': AppSchema.MOM_NAME, 'validators': name_validators},
                        {'field': AppSchema.MOM_AGE, 'validators': age_validators},
                        {'field': AppSchema.MOM_JOB, 'validators': [required("Vui lòng điền nghề nghiệp của Mẹ.")]},
                    ]
                }
            }
        }
    },
    {
        'id': 9, 'name': 'siblings', 'needs_clearance': True,
        'title': 'Anh Chị Em ruột',
        'subtitle': 'Vui lòng kê khai thông tin về các anh, chị, em ruột của bạn (nếu có).',
        'render_func': render_generic_step,
        'fields': [],
        'dataframes': [{
            'field': AppSchema.SIBLING_DATAFRAME,
            'columns': {
                'sibling_name': {'label': 'Họ và tên'},
                'sibling_age': {'label': 'Tuổi', 'classes': 'col-2'},
                'sibling_job': {'label': 'Nghề nghiệp'},
                'sibling_address': {'label': 'Nơi ở', 'classes': 'col-3'}
            },
            # <<< FIXED
            'validators': {
                'sibling_name': [required('Bắt buộc')],
                'sibling_age': [required('Bắt buộc'), match_pattern(NUMERIC_PATTERN, "Phải là số.")],
                'sibling_job': [required('Bắt buộc')],
                'sibling_address': [required('Bắt buộc')],
            }
        }]
    },
    {
        'id': 10, 'name': 'spouse_and_children', 'needs_clearance': True,
        'title': 'Vợ/Chồng & Các con',
        'subtitle': 'Hãy cung cấp thông tin về gia đình nhỏ của bạn (nếu có).',
        'render_func': render_generic_step,
        'fields': [
            # Optional fields are correct with '[]'
            {'field': AppSchema.SPOUSE_NAME, 'validators': []}, 
            {'field': AppSchema.SPOUSE_AGE, 'validators': []},
            {'field': AppSchema.SPOUSE_JOB, 'validators': []},
        ],
        'dataframes': [{
            'field': AppSchema.CHILD_DATAFRAME,
            'columns': {
                'child_name': {'label': 'Họ và tên con'},
                'child_age': {'label': 'Tuổi con', 'classes': 'col-2'},
                'child_job': {'label': 'Học tập/Công tác'}
            },
            # <<< FIXED
            'validators': {
                'child_name': [required('Bắt buộc')],
                'child_age': [required('Bắt buộc'), match_pattern(NUMERIC_PATTERN, "Phải là số.")],
                'child_job': [required('Bắt buộc')],
            }
        }]
    },

    # --- GOVERNMENT/MILITARY CLEARANCE SECTION ---
    {
        'id': 11, 'name': 'gov_political_class', 'needs_clearance': True,
        'title': 'Kê khai Thành phần',
        'subtitle': 'Bước này là yêu cầu riêng cho hồ sơ Nhà nước.',
        'render_func': render_generic_step,
        'fields': [
            # <<< FIXED
            {'field': AppSchema.SOCIAL_STANDING, 'validators': [required_choice("Vui lòng chọn thành phần bản thân.")]},
            {'field': AppSchema.FAMILY_STANDING, 'validators': [required_choice("Vui lòng chọn thành phần gia đình.")]},
        ],
        'dataframes': []
    },
    {
        'id': 12, 'name': 'gov_affiliation', 'needs_clearance': True,
        'title': 'Thông tin Đảng/Đoàn & Lương', 
        'subtitle': 'Cung cấp thông tin về quá trình tham gia Đoàn, Đảng và mức lương.',
        'render_func': render_generic_step,
        'fields': [
            {'field': AppSchema.YOUTH_DATE, 'validators': []},
            {'field': AppSchema.PARTY_DATE, 'validators': []},
            # <<< REFINED
            {'field': AppSchema.CURRENT_SALARY, 'validators': [required("Vui lòng điền mức lương."), 
                                                               match_pattern(SALARY_PATTERN, "Lương phải là một con số.")]},
        ],
        'dataframes': []
    },
    {
        'id': 13, 'name': 'gov_parents_history', 'needs_clearance': True,
        'title': 'Lịch sử Gia đình (chi tiết)',
        'subtitle': 'Để phục vụ công tác thẩm tra, vui lòng kê khai chi tiết quá trình hoạt động của bố mẹ qua các thời kỳ lịch sử.',
        'render_func': render_generic_step, # No longer needs a custom renderer
        'fields': [],
        'dataframes': [],
        'layout': {
            'type': 'tabs',
            'tabs': {
                'dad_panel': {
                    'label': 'Thông tin Bố',
                    'fields': [
                        {'field': AppSchema.DAD_PRE_AUGUST_REVOLUTION, 'validators': [required("Vui lòng điền hoạt động của Bố trước CM tháng 8.")]},
                        {'field': AppSchema.DAD_DURING_FRENCH_WAR, 'validators': [required("Vui lòng điền hoạt động của Bố trong kháng chiến chống Pháp.")]},
                        {'field': AppSchema.DAD_FROM_1955_PRESENT, 'validators': [required("Vui lòng điền hoạt động của Bố từ 1955 đến nay.")]},
                    ]
                },
                'mom_panel': {
                    'label': 'Thông tin Mẹ',
                    'fields': [
                        {'field': AppSchema.MOM_PRE_AUGUST_REVOLUTION, 'validators': [required("Vui lòng điền hoạt động của Mẹ trước CM tháng 8.")]},
                        {'field': AppSchema.MOM_DURING_FRENCH_WAR, 'validators': [required("Vui lòng điền hoạt động của Mẹ trong kháng chiến chống Pháp.")]},
                        {'field': AppSchema.MOM_FROM_1955_PRESENT, 'validators': [required("Vui lòng điền hoạt động của Mẹ từ 1955 đến nay.")]},
                    ]
                }
            }
        }
    },
    
    # --- Miscellaneous & Finalization ---
    {
        'id': 14, 'name': 'health_and_military', 'needs_clearance': True,
        'title': 'Sức khỏe & Quân sự',
        'subtitle': 'Một vài thông tin cuối về sức khoẻ và nghĩa vụ quân sự (nếu có).',
        'render_func': render_generic_step,
        'fields': [
            # <<< REFINED: No more reusing 'validate_age'!
            {'field': AppSchema.HEALTH, 'validators': [required("Vui lòng điền tình trạng sức khỏe.")]},
            {'field': AppSchema.HEIGHT, 'validators': [required("Điền chiều cao (cm)."), match_pattern(NUMERIC_PATTERN, "Phải là số.")]},
            {'field': AppSchema.WEIGHT, 'validators': [required("Điền cân nặng (kg)."), match_pattern(NUMERIC_PATTERN, "Phải là số.")]},
            {'field': AppSchema.JOIN_ARMY_DATE, 'validators': []}, 
            {'field': AppSchema.LEAVE_ARMY_DATE, 'validators': []},
        ],
        'dataframes': [],
    },
    {
        'id': 15, 'name': 'emergency_contact', 'needs_clearance': None,
        'title': 'Liên hệ Khẩn cấp',
        'subtitle': 'Cuối cùng, cho chúng tôi biết thông tin người cần báo tin khi khẩn cấp.',
        'render_func': render_generic_step,
        'fields': [
            # <<< FIXED
            {'field': AppSchema.EMERGENCY_CONTACT_DETAILS, 'validators': [required("Vui lòng điền tên người cần báo tin.")]},
            {'field': AppSchema.SAME_ADDRESS_AS_REGISTERED, 'validators': []}, 
            {'field': AppSchema.EMERGENCY_CONTACT_PLACE, 'validators': [required("Vui lòng điền địa chỉ người báo tin.")]},
        ],
        'dataframes': [], 
    },
    # --- Final Step ---
    {
        'id': 16, 'name': 'review', 'needs_clearance': None,
        'title': 'Xem lại & Hoàn tất',
        'subtitle': 'Kiểm tra lại toàn bộ thông tin. Nếu chính xác, bạn có thể tạo file PDF.',
        'render_func': render_review_step,
        'fields': [], 
        'dataframes': []
    },
]

# ===================================================================
# 5. NAVIGATION ENGINE & MAIN UI CONTROLLER
# ===================================================================

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

    if current_index >= len(STEPS_DEFINITION) - 1:
        return

    # Iterate forward from the current position to find the next valid step
    next_index: int = current_index + 1
    while next_index < len(STEPS_DEFINITION):
        next_step_candidate = STEPS_DEFINITION[next_index]

        if next_step_candidate[NEEDS_CLEARANCE_KEY] and not needs_clearance_val:
            next_index += 1
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

    if current_index <= 0:
        return
    
    prev_index: int = current_index - 1
    while prev_index >= 0:
        prev_step_candidate = STEPS_DEFINITION[prev_index]

        if prev_step_candidate[NEEDS_CLEARANCE_KEY] and not needs_clearance_val:
            prev_index -= 1
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
    user_storage = cast(Dict[str, Any], app.storage.user)
    if not user_storage: # Check if session needs initialization
        user_storage[STEP_KEY] = 0
        user_storage[FORM_DATA_KEY] = {}
        initialize_form_data()        
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
