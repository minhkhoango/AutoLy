# app/utils.py
from __future__ import annotations
from typing import (
    Any, NotRequired, TypedDict,
    TypeAlias,
)
from collections.abc import Callable
from dataclasses import dataclass

from .para import (
    vn_province, degrees, education_format,
    education_high_school, ethnic_groups_vietnam,
    religion, work_position, awards_titles
)
from .form_data_builder import FormUseCaseType, FORM_TEMPLATE_REGISTRY
from .validation import ValidatorFunc

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
    split_date: bool = True # For PDF rendering
    default_value: Any = ''
    include_day: bool = True
    pdf_coords: dict[FormUseCaseType, tuple[float, float] | tuple[list[float], float]] | None = None
    pdf_columns: list[PDFColumn] | None = None
    row_schema: type | None = None
    max_length: int | None = None

class DataframePDFColumn(TypedDict):
    """Defines how to map a single dataframe column """
    key: str # The key from the form's dataframe row (work_task)
    pdf_field_prefix: str # The predfix for the pdf field (work_task_)
    # The magic
    transformer: NotRequired[Callable[[dict[str, Any]], str]]

SimpleValidatorEntry: TypeAlias = tuple[str, list[ValidatorFunc]]
DataframeColumnRules: TypeAlias = dict[str, list[ValidatorFunc]]
DataframeValidatorEntry: TypeAlias = tuple[str, DataframeColumnRules]
ValidationEntry: TypeAlias = SimpleValidatorEntry | DataframeValidatorEntry

class FieldConfig(TypedDict):
    field: FormField
    validators: list[ValidatorFunc]

class DataframeConfig(TypedDict):
    field: FormField
    validators: DataframeColumnRules

class PanelInfo(TypedDict):
    label: str
    fields: list[FieldConfig]

class TabbedLayout(TypedDict):
    type: str
    tabs: dict[str, PanelInfo]

class StepDefinition(TypedDict):
    id: int
    name: str
    title: str
    subtitle: str
    fields: list[FieldConfig]
    dataframes: list[DataframeConfig]
    needs_clearance: bool | None
    layout: NotRequired[TabbedLayout]

# ===================================================================
# 2. THE APPLICATION SCHEMA (Single Source of Truth)
# ===================================================================

class AppSchema:
    """
    Defines all fields used in the application. Each field is an instance
    of the FormField dataclass, containing all its necessary metadata.
    """
    class TrainingRow:
        FROM = FormField(key='training_from', label='Từ (MM/YYYY)', ui_type='date', default_value=None, include_day=False)
        TO = FormField(key='training_to', label='Đến (MM/YYYY)', ui_type='date', default_value=None, include_day=False)
        UNIT = FormField(key='training_unit', label='Tên trường/Cơ sở đào tạo', ui_type='text', max_length=26)
        FIELD = FormField(key='training_field', label='Ngành học', ui_type='text', max_length=21)
        FORMAT = FormField(key='training_format', label='Hình thức', ui_type='select',
                            options=education_format, default_value='Chính quy')
        CERTIFICATE = FormField(key='training_certificate', label='Văn bằng/Chứng chỉ', ui_type='select', options=degrees, default_value='Không có')

    class WorkRow:
        FROM = FormField(key='work_from', label='Từ (MM/YYYY)', ui_type='date', default_value=None, include_day=False)
        TO = FormField(key='work_to', label='Đến (MM/YYYY)', ui_type='date', default_value=None, include_day=False)
        UNIT = FormField(key='work_unit', label='Đơn vị công tác', ui_type='text', max_length=50)
        ROLE = FormField(key='work_role', label='Chức vụ', ui_type='select',
                        options=work_position, default_value="Thực tập")

    FULL_NAME = FormField(key='full_name', label='HỌ VÀ TÊN (viết hoa)', max_length=30,
                          pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (214.52, 179.88)})
    GENDER = FormField(key='gender', label='Giới tính', ui_type='radio', options=['Nam', 'Nữ'], default_value='Nam',
                       pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (436.02, 179.88)})
    DOB = FormField(key='dob', label='Ngày sinh', ui_type='date', default_value=None,
                    pdf_coords={FormUseCaseType.PRIVATE_SECTOR: ([152.52, 202.02, 242.02], 201.5)})
    BIRTH_PLACE = FormField(key='birth_place', label='Nơi sinh', ui_type='select', options=vn_province, default_value='Hà Nội',
                            pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (332.06, 201.5)})
    REGISTERED_ADDRESS = FormField(key='registered_address', label='Địa chỉ hộ khẩu', default_value='', max_length=55,
                                   pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (259.06, 244.83)})
    PHONE = FormField(key='phone', label='Số điện thoại', max_length=10,
                      pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (209.06, 287.46)})
    ETHNICITY = FormField(key='ethnicity', label='Dân tộc', ui_type='select', options=ethnic_groups_vietnam, default_value='Kinh',
                          pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (150.06, 309.56)})
    RELIGION = FormField(key='religion', label='Tôn giáo', ui_type='select', options=religion, default_value='Không',
                         pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (312.06, 309.56)})
    EDUCATION_HIGH_SCHOOL = FormField(key='education_high_school', label='Lộ trình hoàn thành cấp ba', ui_type='select', options=education_high_school, default_value='12/12',
                                      pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (202.56, 352.56)})
    AWARD = FormField(key='award', label='Khen thưởng', ui_type='select', options=awards_titles, default_value='Không có',
                      pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (222.06, 417.06)})
    DISCIPLINE = FormField(key='discipline', label='Kỷ luật', default_value='Không có', max_length=50,
                           pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (377.06, 417.06)})

    TRAINING_DATAFRAME = FormField(
        key='training_dataframe', label='Quá trình đào tạo', ui_type='dataframe',
        row_schema=TrainingRow,
        default_value=[],
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
        row_schema=WorkRow,
        default_value=[],
        pdf_coords={FormUseCaseType.PRIVATE_SECTOR: (62, 414)},
        pdf_columns=[
            PDFColumn(key='work_from', x_offset=0,
                      transformer=lambda row: f"{row.get('work_from','')} - {row.get('work_to','')}"),
            PDFColumn(key='work_unit', x_offset=76.5),
            PDFColumn(key='work_role', x_offset=353),
        ]
    )

    FORM_TEMPLATE_SELECTOR = FormField(key='form_template_selector', label='Tổ chức bạn đang nộp hồ sơ cho:', ui_type='radio',
        options={use_case.name: template['name'] for use_case, template in FORM_TEMPLATE_REGISTRY.items()},
        default_value=next(iter(FORM_TEMPLATE_REGISTRY.keys())).name
    )

    @classmethod
    def get_all_fields(cls) -> list[FormField]:
        return [
            field_instance for field_instance in cls.__dict__.values()
            if isinstance(field_instance, FormField)
        ]

# ===================================================================
# 3. CENTRALIZED CONSTANTS & SESSION MANAGEMENT
# ===================================================================

STEP_KEY: str = 'step'
FORM_DATA_KEY: str = 'form_data'
SELECTED_USE_CASE_KEY: str = 'selected_use_case'
FORM_ATTEMPTED_SUBMISSION_KEY: str = 'form_attempted_submission'
CURRENT_STEP_ERRORS_KEY: str = 'current_step_errors'
DATE_FORMAT_STORAGE: str = '%Y-%m-%d'