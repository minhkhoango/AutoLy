# tests/test_validation.py
from __future__ import annotations

import sys
from pathlib import Path
from datetime import date
from typing import Any

# This is a standard way to make the `app` directory importable
# without having to install the project in editable mode.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.validation import (
    required,
    match_pattern,
    is_within_date_range,
    is_date_after,
    max_length,
    PHONE_PATTERN,
)

# Test data is just a dummy dict for context, as our validators require it.
FORM_DATA: dict[str, Any] = {}

def test_max_length_validator() -> None:
    """Tests the `max_length` validator."""
    validator = max_length(10, "Cannot exceed 10 characters.")

    # --- Passing Cases ---
    is_valid_under, _ = validator("12345", FORM_DATA)
    assert is_valid_under, "Should pass for a string under the limit"

    is_valid_exact, _ = validator("1234567890", FORM_DATA)
    assert is_valid_exact, "Should pass for a string at the exact limit"

    # --- Failing Cases ---
    is_invalid_over, _ = validator("12345678901", FORM_DATA)
    assert not is_invalid_over, "Should fail for a string over the limit"

    # --- Edge Cases ---
    is_valid_empty, _ = validator("", FORM_DATA)
    assert is_valid_empty, "Should pass for an empty string (not its responsibility)"

    is_valid_none, _ = validator(None, FORM_DATA)
    assert is_valid_none, "Should pass for None (not its responsibility)"

def test_required_validator() -> None:
    """Tests the `required` validator for various empty/non-empty cases."""
    validator = required("This field is required.")

    # --- Failing Cases ---
    is_valid_none, _ = validator(None, FORM_DATA)
    assert not is_valid_none, "Should fail for None"

    is_valid_empty_str, _ = validator("", FORM_DATA)
    assert not is_valid_empty_str, "Should fail for empty string"

    is_valid_whitespace, _ = validator("   ", FORM_DATA)
    assert not is_valid_whitespace, "Should fail for whitespace-only string"

    is_valid_empty_list, _ = validator([], FORM_DATA)
    assert not is_valid_empty_list, "Should fail for empty list"

    # --- Passing Cases ---
    is_valid_str, _ = validator("some value", FORM_DATA)
    assert is_valid_str, "Should pass for a valid string"

    is_valid_zero, _ = validator(0, FORM_DATA)
    assert is_valid_zero, "Should pass for the number 0"

    is_valid_list, _ = validator(["item"], FORM_DATA)
    assert is_valid_list, "Should pass for a non-empty list"


def test_match_pattern_validator() -> None:
    """Tests the `match_pattern` validator with the phone number pattern."""
    validator = match_pattern(PHONE_PATTERN, "Invalid phone number.")

    # --- Passing Cases ---
    is_valid_phone, _ = validator("0987654321", FORM_DATA)
    assert is_valid_phone, "Should pass for a valid 10-digit phone number"

    # --- Failing Cases ---
    is_valid_short, _ = validator("12345", FORM_DATA)
    assert not is_valid_short, "Should fail for a number that is too short"

    is_valid_long, _ = validator("01234567890", FORM_DATA)
    assert not is_valid_long, "Should fail for a number that is too long"

    is_valid_chars, _ = validator("0987abcde", FORM_DATA)
    assert not is_valid_chars, "Should fail for a number with characters"

    # --- Edge Cases ---
    # `match_pattern` should ignore empty values; that's `required`'s job.
    is_valid_empty, _ = validator("", FORM_DATA)
    assert is_valid_empty, "Should pass for an empty string (not its responsibility)"

    is_valid_none, _ = validator(None, FORM_DATA)
    assert is_valid_none, "Should pass for None (not its responsibility)"


def test_is_within_date_range_validator() -> None:
    """Tests the date range validator."""
    min_d = date(2020, 1, 1)
    max_d = date(2020, 12, 31)
    validator = is_within_date_range(min_date=min_d, max_date=max_d)

    # --- Passing Cases ---
    is_valid_middle, _ = validator("2020-06-15", FORM_DATA)
    assert is_valid_middle, "Should pass for a date in the middle of the range"

    is_valid_start, _ = validator("2020-01-01", FORM_DATA)
    assert is_valid_start, "Should pass for a date on the start boundary"

    is_valid_end, _ = validator("2020-12-31", FORM_DATA)
    assert is_valid_end, "Should pass for a date on the end boundary"

    # --- Failing Cases ---
    is_valid_before, _ = validator("2019-12-31", FORM_DATA)
    assert not is_valid_before, "Should fail for a date before the range"

    is_valid_after, _ = validator("2021-01-01", FORM_DATA)
    assert not is_valid_after, "Should fail for a date after the range"


def test_is_date_after_validator() -> None:
    """Tests that one MM/YYYY date is after another."""
    # This validator checks 'work_to' against 'work_from'
    validator = is_date_after('work_from', "End date must be after start date.")

    # --- Passing Case ---
    row_data_valid = {'work_from': '01/2022', 'work_to': '06/2022'}
    is_valid, _ = validator(row_data_valid['work_to'], row_data_valid)
    assert is_valid, "Should pass when 'to' date is after 'from' date"

    # --- Failing Cases ---
    row_data_before = {'work_from': '06/2022', 'work_to': '01/2022'}
    is_invalid_before, _ = validator(row_data_before['work_to'], row_data_before)
    assert not is_invalid_before, "Should fail when 'to' date is before 'from' date"

    row_data_same = {'work_from': '06/2022', 'work_to': '06/2022'}
    is_invalid_same, _ = validator(row_data_same['work_to'], row_data_same)
    assert not is_invalid_same, "Should fail when 'to' date is the same as 'from' date"
