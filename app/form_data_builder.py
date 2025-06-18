from __future__ import annotations
from enum import Enum, auto
from typing import TypedDict

# ===================================================================
# 1. DEFINE THE "PRODUCTS" - OUR DOSSIER TYPES
# ===================================================================
# This Enum provides type-safe identifiers for each dossier path.
# No more magic strings like "Có" or "Không".

class FormUseCaseType(Enum):
    PRIVATE_SECTOR = auto()
    # STATE_EMPLOYEE = auto()          # POSTPONED
    # STATE_CIVIL_SERVANT = auto()     # POSTPONED
    # MINISTRY_DEFENSE = auto()        # POSTPONED
    # MINISTRY_PUBLIC_SECURITY = auto()# POSTPONED

# ===================================================================
# 2. DEFINE THE "BLUEPRINT" FOR EACH PRODUCT
# ===================================================================
# This structure defines the unique assembly line for each dossier type.
class FormTemplate(TypedDict):
    """A blueprint for a specific recruitment dossier."""
    name: str
    description: str
    # The ordered sequence of step IDs required for this specific dossier.
    step_sequence: list[int]
    # The offical form name, for reference or future use.
    gov_form_code: str | None

# ===================================================================
# 3. BUILD THE "FACTORY" - THE REGISTRY OF ALL BLUEPRINTS
# ===================================================================
# This registry is the heart of the new architecture. It maps a FormUseCaseType
# to its specific blueprint. The step_ids are derived directly from the
# legal analysis in your PDF.

FORM_TEMPLATE_REGISTRY: dict[FormUseCaseType, FormTemplate] = {
    FormUseCaseType.PRIVATE_SECTOR: {
        'name': "Hồ sơ Doanh nghiệp Tư nhân",
        'description':  "Một CV/resume hiện đại, linh hoạt, tập trung vào kỹ năng và kinh nghiệm. Không theo mẫu nhà nước.",
        'gov_form_code': None,
        'step_sequence': [
            # Core Info
            1, 3, 5, 6, 7, 8,
            # Basic Family Info
            9, 
            # Review
            16,
        ],
    },
}