# validators.py
from __future__ import annotations
import re
from re import Pattern
from typing import Any
from collections.abc import Callable
from datetime import date, datetime

# --- Type Aliases ---
ValidationResult = tuple[bool, str]
# The validator now gets the value and the entire form_data dict for context
ValidatorFunc = Callable[[Any | None, dict[str, Any]], ValidationResult]

# --- Regex Patterns (centralized) ---
FULL_NAME_PATTERN: Pattern[str] = re.compile(r'^[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴĐÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸ ]+$')
PHONE_PATTERN: Pattern[str] = re.compile(r'^0\d{9}$')
EMAIL_PATTERN: Pattern[str] = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
ID_NUMBER_PATTERN: Pattern[str] = re.compile(r'^(?:\d{9}|\d{12})$')
YEAR_PATTERN: Pattern[str] = re.compile(r'^\d{4}$')
NUMERIC_PATTERN: Pattern[str] = re.compile(r'^\d+$')
DATE_FORMAT_STORAGE: str = '%Y-%m-%d' 

# ===================================================================
# GENERIC VALIDATOR GENERATORS (Our Reusable Building Blocks)
# ===================================================================

def required(message: str = "Vui lòng không để trống trường này.") -> ValidatorFunc:
    """Ensures a value is not None, not an empty string, and not just whitespace."""
    def validator(value: Any | None, form_data: dict[str, Any]) -> ValidationResult:
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
    def validator(value: Any | None, form_data: dict[str, Any]) -> ValidationResult:
        if value is None or (isinstance(value, str) and not value.strip()):
            return False, message
        return True, ""
    return validator

def match_pattern(pattern: Pattern[str], message: str) -> ValidatorFunc:
    """Ensures a string value matches a regex pattern."""
    def validator(value: Any | None, form_data: dict[str, Any]) -> ValidationResult:
        # This validator should only run if the field is not empty.
        # Chain it with required() to validate non-empty fields.
        if not value or not isinstance(value, str):
            return True, "" # Don't fail on empty values, that's `required`'s job.
        if not pattern.match(value.strip()):
            return False, message
        return True, ""
    return validator

def is_within_date_range(
    min_date: date | None = date(1900, 1, 1), max_date: date | None = date.today(),
    message: str = "Ngày chọn nằm ngoài khoảng cho phép."
) -> ValidatorFunc:
    """Ensures a date string is within the specified min/max range."""
    def validator(value: str | None, form_data: dict[str, Any]) -> ValidationResult:
        if not value:
            return True, ''
        try:
            dt_object = datetime.strptime(value, DATE_FORMAT_STORAGE).date()
            if (min_date and dt_object < min_date) or \
               (max_date and dt_object > max_date):
                return False, message
        except ValueError:
            # This could happen if the date string is malformed, though your sync logic should prevent it.
            return False, "Định dạng ngày không hợp lệ."
        return True, ''
    return validator

def is_date_after(other_field_key: str, message: str) -> ValidatorFunc:
    """
    Validates that a MM/YYYY date in one field comes after a MM/YYYY date
    in another field within the same row of data.
    """
    def validator(value: str | None, row_data: dict[str, Any]) -> ValidationResult:
        # `value` is the 'work_to' date
        other_value = row_data.get(other_field_key)

        # If either value is missing or not in the right format, another validator will catch it.
        if not value or not other_value or '/' not in value or '/' not in other_value:
            return True, ""
        
        try:
            # Convert MM/YYYY to a comparable format 
            to_month, to_year = map(int, value.split('/'))
            from_month, from_year = map(int, other_value.split('/'))

            if to_year < from_year or (to_year==from_year and to_month < from_month):
                return False, message
        except (ValueError, IndexError):
            return True, "" # Let the pattern validator handle format errors.
        
        return True, ""
    return validator