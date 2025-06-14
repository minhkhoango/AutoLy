# validators.py
from __future__ import annotations
import re
from typing import Any, Callable, Dict, Optional, Pattern, Tuple

# --- Type Aliases ---
ValidationResult = Tuple[bool, str]
# The validator now gets the value and the entire form_data dict for context
ValidatorFunc = Callable[[Optional[Any], Dict[str, Any]], ValidationResult]

# --- Regex Patterns (centralized) ---
FULL_NAME_PATTERN: Pattern[str] = re.compile(r'^[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴĐÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸ ]+$')
PHONE_PATTERN: Pattern[str] = re.compile(r'^0\d{9}$')
EMAIL_PATTERN: Pattern[str] = re.compile(r'^[^@]+@[^@]+\.[^@]+$')
ID_NUMBER_PATTERN: Pattern[str] = re.compile(r'^(?:\d{9}|\d{12})$')
YEAR_PATTERN: Pattern[str] = re.compile(r'^\d{4}$')
NUMERIC_PATTERN: Pattern[str] = re.compile(r'^\d+$')

# ===================================================================
# GENERIC VALIDATOR GENERATORS (Our Reusable Building Blocks)
# ===================================================================

def required(message: str = "Vui lòng không để trống trường này.") -> ValidatorFunc:
    """Ensures a value is not None, not an empty string, and not just whitespace."""
    def validator(value: Optional[Any], form_data: Dict[str, Any]) -> ValidationResult:
        if value is None:
            return False, message
        if isinstance(value, str) and not value.strip():
            return False, message
        if isinstance(value, (list, dict)) and not value: # For dataframes
            return False, message
        return True, ""
    return validator

def required_choice(message: str = "Vui lòng thực hiện lựa chọn.") -> ValidatorFunc:
    """Ensures a value from a select/radio is not None or empty/whitespace."""
    def validator(value: Optional[Any], form_data: Dict[str, Any]) -> ValidationResult:
        if value is None or (isinstance(value, str) and not value.strip()):
            return False, message
        return True, ""
    return validator

def match_pattern(pattern: Pattern[str], message: str) -> ValidatorFunc:
    """Ensures a string value matches a regex pattern."""
    def validator(value: Optional[Any], form_data: Dict[str, Any]) -> ValidationResult:
        # This validator should only run if the field is not empty.
        # Chain it with required() to validate non-empty fields.
        if not value or not isinstance(value, str):
            return True, "" # Don't fail on empty values, that's `required`'s job.
        if not pattern.match(value.strip()):
            return False, message
        return True, ""
    return validator

def min_length(length: int, message: str) -> ValidatorFunc:
    """Ensures a string has a minimum length."""
    def validator(value: Optional[Any], form_data: Dict[str, Any]) -> ValidationResult:
        if not value or not isinstance(value, str):
            return True, ""
        if len(value.strip()) < length:
            return False, message
        return True, ""
    return validator