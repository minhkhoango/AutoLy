# app/step_definitions.py
from __future__ import annotations

from .utils import AppSchema, StepDefinition
from .validation import (
    required, required_choice, match_pattern, is_within_date_range, is_date_after,
    max_length, FULL_NAME_PATTERN, PHONE_PATTERN, DATE_MMYYYY_PATTERN
)

STEPS_BY_ID: dict[int, StepDefinition] = {
    0: {
        'id': 0, 'name': 'dossier_selector', 'title': 'Chọn Loại Hồ Sơ',
        'subtitle': 'Chọn loại hồ sơ bạn cần, hệ thống sẽ tạo các bước cần thiết.',
        'fields': [{'field': AppSchema.FORM_TEMPLATE_SELECTOR, 'validators': [required_choice("Vui lòng chọn một loại hồ sơ.")]}],
        'dataframes': [], 'needs_clearance': None
    },
    1: {
        'id': 1, 'name': 'core_identity', 'title': 'Thông tin cá nhân',
        'subtitle': 'Thông tin định danh cơ bản của bạn.', 'needs_clearance': None,
        'fields': [
            {'field': AppSchema.FULL_NAME, 'validators': [
                required("Vui lòng điền họ tên."),
                match_pattern(FULL_NAME_PATTERN, "Họ tên phải viết hoa."),
                max_length(30, "Họ tên không được vượt quá 30 ký tự.")
            ]},
            {'field': AppSchema.GENDER, 'validators': [required_choice("Vui lòng chọn giới tính.")]},
            {'field': AppSchema.DOB, 'validators': [required('Vui lòng điền ngày sinh.'), is_within_date_range()]},
            {'field': AppSchema.BIRTH_PLACE, 'validators': [required("Vui lòng chọn nơi sinh.")]}
        ],
        'dataframes': []
    },
    3: {
        'id': 3, 'name': 'contact', 'title': 'Địa chỉ & liên lạc',
        'subtitle': 'Địa chỉ và số điện thoại để liên lạc khi cần.', 'needs_clearance': None,
        'fields': [
            {'field': AppSchema.REGISTERED_ADDRESS, 'validators': [
                required("Vui lòng điền địa chỉ hộ khẩu."),
                max_length(55, "Địa chỉ không được vượt quá 55 ký tự.")
            ]},
            {'field': AppSchema.PHONE, 'validators': [
                required('Vui lòng điền số điện thoại.'),
                match_pattern(PHONE_PATTERN, "Số điện thoại không hợp lệ."),
                max_length(10, "Số điện thoại phải có 10 chữ số.")
            ]}
        ],
        'dataframes': []
    },
    5: {
        'id': 5, 'name': 'education', 'title': 'Học vấn & Chuyên môn',
        'subtitle': 'Quá trình học tập và đào tạo.', 'needs_clearance': None,
        'fields': [{'field': AppSchema.EDUCATION_HIGH_SCHOOL, 'validators': [required_choice("Vui lòng chọn lộ trình học cấp ba.")]}],
        'dataframes': [{
            'field': AppSchema.TRAINING_DATAFRAME,
            'validators': {
                'training_from': [required('Điền thời gian bắt đầu.'), match_pattern(DATE_MMYYYY_PATTERN, 'Dùng định dạng MM/YYYY')],
                'training_to': [required('Điền thời gian kết thúc.'), match_pattern(DATE_MMYYYY_PATTERN, 'Dùng định dạng MM/YYYY'), is_date_after('training_from', 'Ngày kết thúc phải sau ngày bắt đầu.')],
                'training_unit': [required('Điền tên trường.'), max_length(26, "Tên trường không được vượt quá 26 ký tự.")],
                'training_field': [required('Điền ngành học.'), max_length(21, "Ngành học không được vượt quá 21 ký tự.")],
            }
        }]
    },
    6: {
        'id': 6, 'name': 'work_history', 'title': 'Quá trình Công tác',
        'subtitle': 'Liệt kê quá trình làm việc, bắt đầu từ gần nhất.', 'needs_clearance': None,
        'fields': [],
        'dataframes': [{
            'field': AppSchema.WORK_DATAFRAME,
            'validators': {
                'work_from': [required('Điền thời gian bắt đầu.'), match_pattern(DATE_MMYYYY_PATTERN, 'Dùng định dạng MM/YYYY')],
                'work_to': [required('Điền thời gian kết thúc.'), match_pattern(DATE_MMYYYY_PATTERN, 'Dùng định dạng MM/YYYY'), is_date_after('work_from', 'Ngày kết thúc phải sau ngày bắt đầu.')],
                'work_unit': [required('Điền đơn vị.'), max_length(50, "Tên đơn vị không được vượt quá 50 ký tự.")],
            }
        }]
    },
    7: {
        'id': 7, 'name': 'awards', 'title': 'Khen thưởng & Kỷ luật',
        'subtitle': 'Thông tin về khen thưởng và kỷ luật (nếu có).', 'needs_clearance': None,
        'fields': [
            {'field': AppSchema.AWARD, 'validators': [required_choice("Vui lòng chọn khen thưởng.")]},
            {'field': AppSchema.DISCIPLINE, 'validators': [max_length(150, "Nội dung không được vượt quá 150 ký tự.")]}
        ],
        'dataframes': []
    },
    16: {
        'id': 16, 'name': 'review', 'title': 'Xem lại & Hoàn tất',
        'subtitle': 'Kiểm tra lại toàn bộ thông tin và tạo file PDF.', 'needs_clearance': None,
        'fields': [], 'dataframes': []
    },
}