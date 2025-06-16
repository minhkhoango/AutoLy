from __future__ import annotations
from enum import Enum, auto
from typing import List, Dict, TypedDict

# ===================================================================
# 1. DEFINE THE "PRODUCTS" - OUR DOSSIER TYPES
# ===================================================================
# This Enum provides type-safe identifiers for each dossier path.
# No more magic strings like "Có" or "Không".

class FormUseCaseType(Enum):
    PRIVATE_SECTOR = auto()
    STATE_EMPLOYEE = auto()          # Viên chứ
    STATE_CIVIL_SERVANT = auto()     # Công chức
    MINISTRY_DEFENSE = auto()        # Bộ Quốc phòng (BQP)
    MINISTRY_PUBLIC_SECURITY = auto()# Bộ Công an (BCA)

# ===================================================================
# 2. DEFINE THE "BLUEPRINT" FOR EACH PRODUCT
# ===================================================================
# This structure defines the unique assembly line for each dossier type.
class FormTemplate(TypedDict):
    """A blueprint for a specific recruitment dossier."""
    name: str
    description: str
    # The ordered sequence of step IDs required for this specific dossier.
    step_sequence: List[int]
    # The offical form name, for reference or future use.
    gov_form_code: str | None

# ===================================================================
# 3. BUILD THE "FACTORY" - THE REGISTRY OF ALL BLUEPRINTS
# ===================================================================
# This registry is the heart of the new architecture. It maps a FormUseCaseType
# to its specific blueprint. The step_ids are derived directly from the
# legal analysis in your PDF.

FORM_TEMPLATE_REGISTRY: Dict[FormUseCaseType, FormTemplate] = {
    FormUseCaseType.PRIVATE_SECTOR: {
        'name': "Hồ sơ Doanh nghiệp Tư nhân",
        'description':  "Một CV/resume hiện đại, linh hoạt, tập trung vào kỹ năng và kinh nghiệm. Không theo mẫu nhà nước.",
        'gov_form_code': None,
        'step_sequence': [
            # Core Info
            1, 2, 3, 5, 6, 7, 8,
            # Basic Family Info
            9, 10,
            # Emergency Contact & Review
            15, 16
        ],
    },
    FormUseCaseType.STATE_EMPLOYEE: {
        'name': "Hồ sơ Viên chức",
        'description': "Hồ sơ chuẩn theo quy định cho viên chức, sử dụng Mẫu HS02-VC/BNV.",
        'gov_form_code': "Mẫu HS02-VC/BNV (Thông tư 07/2019/TT-BNV)",
        'step_sequence': [
            # Core Info
            1, 2, 3, 4, 5, 6, 7,
            # Full Family & Political Info
            8, 9, 10, 11, 12, 13, 14,
            # Emergency Contact & Review
            15, 16
        ],
    },
    FormUseCaseType.MINISTRY_PUBLIC_SECURITY: {
        'name': "Hồ sơ Bộ Công an (BCA)",
        'description': "Hồ sơ thẩm tra lý lịch chi tiết và bắt buộc theo Mẫu A-BCA(X01)-2020.",
        # The BCA form is non-negotiable and requires exhaustive, multi-generational data.
        'gov_form_code': "Mẫu A-BCA(X01)-2020",
        'step_sequence': [
            # Note: This is a simplified representation. A real BCA implementation
            # would require many NEW, highly detailed steps not in your current list.
            # For now, we assume it requires all existing steps as a baseline.
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16
            # In reality, you'd add steps 17 (Spouse's Family), 18 (Grandparents), etc.
        ],
    },
}