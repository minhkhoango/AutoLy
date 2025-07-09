# tests/test_navigation.py
from __future__ import annotations

import sys
from pathlib import Path

# Make the `app` directory importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.myapp import calculate_next_step_id, calculate_prev_step_id
from app.form_data_builder import FormTemplate

# Create a mock FormTemplate for testing purposes
MOCK_TEMPLATE: FormTemplate = {
    'name': "Test Template",
    'description': "A test template",
    'gov_form_code': None,
    'step_sequence': [1, 3, 5, 16], # A simple, predictable sequence
    'pdf_template_path': '',
    'dataframe_page_map': {}
}

def test_calculate_next_step() -> None:
    """Tests the logic for calculating the next step ID."""
    # From start (step 0)
    assert calculate_next_step_id(0, MOCK_TEMPLATE) == 1, "Should go from 0 to the first step in sequence"

    # From a middle step
    assert calculate_next_step_id(3, MOCK_TEMPLATE) == 5, "Should go from a middle step to the next"

    # From the last step
    assert calculate_next_step_id(16, MOCK_TEMPLATE) == 16, "Should stay on the last step"
    
    # From an unknown step
    assert calculate_next_step_id(99, MOCK_TEMPLATE) == 0, "Should go to start from an unknown step"

def test_calculate_prev_step() -> None:
    """Tests the logic for calculating the previous step ID."""
    # From a middle step
    assert calculate_prev_step_id(5, MOCK_TEMPLATE) == 3, "Should go from a middle step to the previous"

    # From the first step in sequence
    assert calculate_prev_step_id(1, MOCK_TEMPLATE) == 0, "Should go from the first step back to 0"

    # From the start (step 0)
    assert calculate_prev_step_id(0, MOCK_TEMPLATE) == 0, "Should stay on step 0"

    # From an unknown step
    assert calculate_prev_step_id(99, MOCK_TEMPLATE) == 0, "Should go to start from an unknown step"