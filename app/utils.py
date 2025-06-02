# utils.py

from datetime import datetime
from typing import Dict, Any, List, Optional, cast

# This function is now a pure data transformation utility.
# It takes application data and configuration for mapping,
# and returns a dictionary ready for PDF filling.

def generate_pdf_data_mapping(
    form_data_app: Dict[str, Any],
    # Configuration/constants needed for mapping:
    date_format_nicegui_app: str,
    work_df_key_app: str,
    same_address1_key_app: str,
    party_membership_key_app: str,
    party_date_key_app: str,
    ethnicity_step4_key_app: str,
    religion_step4_key_app: str,
    # Add any other specific keys from form_data_app that this function
    # needs to know by name, if they aren't hardcoded as PDF field names below.
    # Or rely on form_data_app having consistent keys for direct .get() calls
    # if the PDF field names (e.g. 'full_name') match those keys.
    max_work_entries_pdf: int = 5 # Default, can be overridden by the caller
) -> Dict[str, Any]:
    """
    Transforms data from the application's format into a dictionary
    where keys are the PDF form field names.
    """
    data_for_pdf: Dict[str, Any] = {}

    # --- Section 1: Basic Information ---
    # Assuming PDF field name in your template is 'full_name'
    data_for_pdf['full_name'] = form_data_app.get('full_name', '')
    # Assuming PDF field 'id_number' for app key 'id_passport_num'
    data_for_pdf['id_number'] = form_data_app.get('id_passport_num', '')
    data_for_pdf['id_issue_place'] = form_data_app.get('id_passport_issue_place', '')

    # Date of Birth (dob)
    # Assuming PDF fields: dob_day, dob_month, dob_year
    dob_str_app: Optional[str] = form_data_app.get('dob')
    if dob_str_app:
        try:
            dt_obj = datetime.strptime(dob_str_app, date_format_nicegui_app)
            data_for_pdf['dob_day'] = dt_obj.strftime('%d')
            data_for_pdf['dob_month'] = dt_obj.strftime('%m')
            data_for_pdf['dob_year'] = dt_obj.strftime('%Y')
        except ValueError: # pragma: no cover
            data_for_pdf['dob_day'], data_for_pdf['dob_month'], data_for_pdf['dob_year'] = '', '', ''
    else:
        data_for_pdf['dob_day'], data_for_pdf['dob_month'], data_for_pdf['dob_year'] = '', '', ''

    # ID Issue Date
    # Assuming PDF fields: id_issue_day, id_issue_month, id_issue_year
    id_issue_date_str_app: Optional[str] = form_data_app.get('id_passport_issue_date')
    if id_issue_date_str_app:
        try:
            dt_obj = datetime.strptime(id_issue_date_str_app, date_format_nicegui_app)
            data_for_pdf['id_issue_day'] = dt_obj.strftime('%d')
            data_for_pdf['id_issue_month'] = dt_obj.strftime('%m')
            data_for_pdf['id_issue_year'] = dt_obj.strftime('%Y')
        except ValueError: # pragma: no cover
             data_for_pdf['id_issue_day'], data_for_pdf['id_issue_month'], data_for_pdf['id_issue_year'] = '', '', ''
    else:
        data_for_pdf['id_issue_day'], data_for_pdf['id_issue_month'], data_for_pdf['id_issue_year'] = '', '', ''
        
    # Gender
    data_for_pdf['gender'] = form_data_app.get('gender')


    # --- Section 2: Addresses & Contact ---
    data_for_pdf['registered_address'] = form_data_app.get('registered_address', '')

    if form_data_app.get(same_address1_key_app):
        # If current address is the same as permanent, use the same value
        data_for_pdf['current_address'] = data_for_pdf['registered_address']
    else:
        data_for_pdf['current_address'] = form_data_app.get('current_address', '')
    # Assuming PDF fields: phone_mobile, email_address, emergency_contact_details, emergency_contact_address
    
    data_for_pdf['phone_mobile'] = form_data_app.get('phone', '')
    data_for_pdf['email_address'] = form_data_app.get('email', '')
    data_for_pdf['emergency_contact_details'] = form_data_app.get('emergency_contact_combined', '')
    data_for_pdf['emergency_contact_address'] = form_data_app.get('emergency_place', '')

    # --- Section 3: Education & Work ---
    data_for_pdf['highest_education'] = form_data_app.get('highest_education', '')
    data_for_pdf['specialized_area'] = form_data_app.get('specialized_area', '')

    # Work History using work_df_key_app
    work_history_list_app: List[Dict[str, Any]] = cast(List[Dict[str, Any]], form_data_app.get(work_df_key_app, []))
    
    for i in range(max_work_entries_pdf):
        idx: int = i + 1 # PDF fields are typically 1-indexed
        if i < len(work_history_list_app):
            entry: Dict[str, Any] = work_history_list_app[i]
            from_date, to_date = entry.get("Từ (tháng/năm)", ""), entry.get("Đến (tháng/năm)", "")
            work_desc: str = entry.get("Nhiệm vụ công tácg", "")
            work_place: str = entry.get("Đơn vị công tác", "")
            work_role: str = entry.get("Chức vụ", "")

            data_for_pdf[f'work_from_to_{idx}'] = f"{from_date}-{to_date}" if from_date and to_date else ""
            data_for_pdf[f'work_desc_{idx}'] = work_desc if work_desc else ""
            data_for_pdf[f'work_place_{idx}'] = work_place if work_place else ""
            data_for_pdf[f'work_role_{idx}'] = work_role if work_role else ""
        else:
            data_for_pdf[f'work_from_to_{idx}'] = ""
            data_for_pdf[f'work_desc_{idx}'] = ""
            data_for_pdf[f'work_place_{idx}'] = ""
            data_for_pdf[f'work_role_{idx}'] = ""

    # --- Section 4: Step 4 Data (Clearance-related) ---
    if form_data_app.get(party_membership_key_app) == "Đã vào":
        party_date_str_app: Optional[str] = form_data_app.get(party_date_key_app)
        if party_date_str_app:
            try:
                dt_obj = datetime.strptime(party_date_str_app, date_format_nicegui_app)
                data_for_pdf['party_adm_day'] = dt_obj.strftime('%d')
                data_for_pdf['party_adm_month'] = dt_obj.strftime('%m')
                data_for_pdf['party_adm_year'] = dt_obj.strftime('%Y')
            except ValueError: # pragma: no cover
                data_for_pdf['party_adm_day'], data_for_pdf['party_adm_month'], data_for_pdf['party_adm_year'] = '', '', ''
        else:
             data_for_pdf['party_adm_day'], data_for_pdf['party_adm_month'], data_for_pdf['party_adm_year'] = '', '', ''


    if 'party_adm_day' not in data_for_pdf: data_for_pdf['party_adm_day'] = ''
    if 'party_adm_month' not in data_for_pdf: data_for_pdf['party_adm_month'] = ''
    if 'party_adm_year' not in data_for_pdf: data_for_pdf['party_adm_year'] = ''
    
    # ... (Similar logic for Youth Union if needed) ...

    data_for_pdf['ethnicity'] = form_data_app.get(ethnicity_step4_key_app, '')
    data_for_pdf['religion'] = form_data_app.get(religion_step4_key_app, '')
    
    # IMPORTANT: Continue to map ALL other fields from your PDF template.
    # For any field in your PDF, there should be a corresponding entry here
    # data_for_pdf['pdf_field_name_you_set_in_acrobat'] = form_data_app.get('corresponding_app_storage_key', 'default_value_if_missing')

    return data_for_pdf