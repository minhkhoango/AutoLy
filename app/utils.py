import datetime
import fitz
import pandas as pd # Make sure pandas is imported
import re
import streamlit as st

def safe_day(date_obj: datetime.date, slash=False) -> str:
    return_str = ''
    if pd.isna(date_obj): # Handle if date_obj itself might be NA (though less likely for date types from streamlit)
        return ''
    if date_obj:
        return_str = f'{date_obj.day:02} / ' if slash else f'{date_obj.day:02}'
    return return_str

def safe_month(date_obj: datetime.date, slash=False) -> str:
    return_str = ''
    if pd.isna(date_obj): # Handle if date_obj itself might be NA
        return ''
    if date_obj:
        return_str = f'{date_obj.month:02} / ' if slash else f'{date_obj.month:02}'
    return return_str

def safe_year(date_obj: datetime.date) -> str:
    if pd.isna(date_obj): # Handle if date_obj itself might be NA
        return ''
    return f'{date_obj.year:04}' if date_obj else '' # Changed to :04 for 4-digit year

def to_str(value) -> str:
    """Converts a value to string, handling pandas NA or None."""
    if pd.isna(value) or value is None:
        return ""
    return str(value)

CURRENT_YEAR = datetime.date.today().year
DATE_RE  = re.compile(fr"^(0?[1-9]|1[0-2])/((19\d{{2}})|(20[0-2]\d)|{CURRENT_YEAR})$")
YEAR_RE  = re.compile(fr"^((19\d{{2}})|(20[0-2]\d)|{CURRENT_YEAR})$")

def _ensure_df(obj) -> pd.DataFrame:
    """Accept a DataFrame, a Streamlit data_editor payload, or any row/col dict."""
    if isinstance(obj, pd.DataFrame):
        return obj

    # Streamlit payload shape: {"data": {col: list, ...}, ...}
    if isinstance(obj, dict) and "data" in obj:
        obj = obj["data"]

    # now obj is a {col: list} dict that may be ragged -> pad it
    max_len = max((len(v) for v in obj.values()), default=0)
    padded = {k: v + [None]*(max_len - len(v)) for k, v in obj.items()}
    return pd.DataFrame(padded)

def validate_tables(
    family_df: pd.DataFrame,
    edu_df: pd.DataFrame,
    work_df: pd.DataFrame,
) -> list[str]:
    """
    Return a list of error strings. Empty list ⇒ everything is valid.
    Raises no Streamlit calls, so you can unit-test it offline.
    """
    def _is_blank(val) -> bool:
        return val is None or str(val).strip() == ""

    def _validate_row(row: pd.Series, col_rules: dict[str, re.Pattern | None]):
        for col, pattern in col_rules.items():
            cell = str(row.get(col, "")).strip()
            if _is_blank(cell):
                yield f"🟥 '{col}' không được để trống."
            elif pattern and not pattern.fullmatch(cell):
                yield f"🟥 '{col}' sai định dạng: {cell}"

    family_df = _ensure_df(family_df)
    edu_df    = _ensure_df(edu_df)
    work_df   = _ensure_df(work_df)

    family_rules = {
        "Quan hệ": None,
        "Họ và tên": None,
        "Năm sinh": YEAR_RE,
        "Nghề nghiệp": None,
        "Nơi công tác": None,
    }
    period_rules = {
        "Từ (tháng/năm)": DATE_RE,
        "Đến (tháng/năm)": DATE_RE,
    }

    errors: list[str] = []

    for i, r in family_df.dropna(how="all").iterrows():
        row_errs = list(_validate_row(r, family_rules))
        if row_errs:
            errors.append(f"**Gia đình – dòng {i+1}**:\n" + "  \n".join(row_errs))

    for i, r in edu_df.dropna(how="all").iterrows():
        row_errs = list(_validate_row(r, period_rules))
        if row_errs:
            errors.append(f"**Đào tạo – dòng {i+1}**:\n" + "  \n".join(row_errs))

    for i, r in work_df.dropna(how="all").iterrows():
        row_errs = list(_validate_row(r, period_rules))
        if row_errs:
            errors.append(f"**Công tác – dòng {i+1}**:\n" + "  \n".join(row_errs))

    return errors

def fill_so_yeu_ly_lich(form_data: dict):
    # Top-level personal info
    full_name         = to_str(form_data['full_name'])
    gender            = to_str(form_data['gender'])
    common_name       = to_str(form_data['common_name'])
    dob               = form_data['dob'] # Date objects handled by safe_day/month/year
    birth_place       = to_str(form_data['birth_place'])
    origin            = to_str(form_data['origin'])
    residence         = to_str(form_data['residence'])
    current_address   = to_str(form_data['current_address'])
    phone             = to_str(form_data['phone'])
    email             = to_str(form_data['email'])
    ethnicity         = to_str(form_data['ethnicity'])
    religion          = to_str(form_data['religion'])
    family_standing   = to_str(form_data['family_standing'])
    id_number         = to_str(form_data['id_number'])
    id_issue_date     = form_data['id_issue_date'] # Date objects
    id_issue_place    = to_str(form_data['id_issue_place'])

    # Party / organization dates & roles
    doan_date         = form_data['doan_date'] # Date objects
    dang_join_date    = form_data['dang_join_date'] # Date objects
    dang_official_date= form_data['dang_official_date'] # Date objects
    work_org          = to_str(form_data['work_org'])
    work_position     = to_str(form_data['work_position'])

    # Academic credentials & achievements
    academic_title    = to_str(form_data['academic_title'])
    academic_year     = form_data['academic_year'] # Date object
    awards            = to_str(form_data['awards'])
    discipline        = to_str(form_data['discipline'])
    strengths         = to_str(form_data['strengths'])

    # Education – nested dicts
    bachelor_field    = to_str(form_data['bachelor']['field'])
    bachelor_major    = to_str(form_data['bachelor']['major'])
    bachelor_school   = to_str(form_data['bachelor']['school'])

    master_field      = to_str(form_data['master']['field'])
    master_major      = to_str(form_data['master']['major'])
    master_school     = to_str(form_data['master']['school'])

    phd_field         = to_str(form_data['phd']['field'])
    phd_major         = to_str(form_data['phd']['major'])
    phd_school        = to_str(form_data['phd']['school'])

    # Skills & levels
    foreign_language  = to_str(form_data['foreign_language'])
    it_level          = to_str(form_data['it_level'])
    politics_level    = to_str(form_data['politics_level'])

    # DataFrames
    family_df         = form_data['family_df']
    edu_df            = form_data['edu_df']
    work_df           = form_data['work_df']

    # Open the original template
    # Ensure the template PDF file is in the same directory or provide the full path
    try:
        doc = fitz.open('Mau-so-yeu-ly-lich-2-copy.pdf')
    except Exception as e:
        print(f"Error opening PDF template: {e}")
        # Optionally, re-raise or handle as appropriate for your Streamlit app
        # For example, you might want to show an error in the Streamlit UI
        # st.error(f"Không thể mở file PDF mẫu: {e}")
        return

    page = doc[0]
    fontname = "TimesNewRoman"
    # Ensure the font file is in the specified path or a system-accessible location
    fontfile = "font-times-new-roman\SVN-Times New Roman 2 italic.ttf" # Check this path

    try:
        page.insert_font(fontname=fontname, fontfile=fontfile)
    except Exception as e:
        print(f"Error inserting font: {e}. Using default font.")
        # Fallback or further error handling if font is critical
        fontname = "helv" # Example: fallback to a standard PDF font like Helvetica

    # Define a wrapper for inserting text that handles NA values
    def in_stylized_text(pos: tuple, txt: any, size=11, color=(0, 0, 0)):
        # Convert txt to string, ensuring NA/None becomes an empty string
        text_to_insert = to_str(txt)
        page.insert_text(pos, text_to_insert,
                     fontname=fontname,
                     fontsize=size,
                     color=color,
                     overlay=True)

    # Draw text at specific (x, y) coordinates
    # --- Họ, Tên, Dân tộc, Tôn giáo --------------------------
    in_stylized_text((197, 257), full_name)
    in_stylized_text((434, 257), gender)
    in_stylized_text((185, 280), common_name)

    in_stylized_text((136, 303), safe_day(dob))
    in_stylized_text((200, 303), safe_month(dob))
    in_stylized_text((263, 303), safe_year(dob))

    in_stylized_text((130, 326), birth_place)
    in_stylized_text((155, 349), origin)
    in_stylized_text((245, 372), residence)
    in_stylized_text((166, 395), current_address)
    in_stylized_text((178, 418), phone)
    in_stylized_text((304, 418), email)
    in_stylized_text((128, 441), ethnicity)
    in_stylized_text((273, 441), religion)

    # --- 10. Thành phần gia đình -------------------------------------------
    in_stylized_text((195, 464), family_standing)

    # --- 11. CMND / CCCD ----------------------------------------------------
    in_stylized_text((184, 487), id_number)
    in_stylized_text((316, 487), safe_day(id_issue_date))
    in_stylized_text((334, 487), safe_month(id_issue_date))
    in_stylized_text((353, 487), safe_year(id_issue_date))
    in_stylized_text((436, 487), id_issue_place)

    # --- 12. Trình độ chuyên môn -------------------------------------------
    in_stylized_text((110, 556), bachelor_field)
    in_stylized_text((288, 556), bachelor_major)
    in_stylized_text((450, 556), bachelor_school)

    in_stylized_text((110, 602), master_field)
    in_stylized_text((288, 602), master_major)
    in_stylized_text((450, 602), master_school)

    in_stylized_text((110, 648), phd_field)
    in_stylized_text((288, 648), phd_major)
    in_stylized_text((450, 648), phd_school)

    # --- 13. Ngoại ngữ & Tin học -------------------------------------------
    in_stylized_text((189, 670), foreign_language)
    in_stylized_text((338, 670), it_level)

    # --- 14. Lý luận chính trị ---------------------------------------------
    in_stylized_text((218, 693), politics_level)

    # --- 15. TNCS HCM -------------------------------------------------------
    in_stylized_text((215, 716), safe_day(doan_date))
    in_stylized_text((232, 716), safe_month(doan_date))
    in_stylized_text((249, 716), safe_year(doan_date))

    # --- 16. Đảng CSVN ----------------------------------------------------
    in_stylized_text((205, 739), safe_day(dang_join_date))
    in_stylized_text((223, 739), safe_month(dang_join_date))
    in_stylized_text((240, 739), safe_year(dang_join_date))

    # Combining date parts for dang_official_date
    dang_official_date_str = f'{safe_day(dang_official_date, slash=True)}{safe_month(dang_official_date, slash=True)}{safe_year(dang_official_date)}'
    # Only insert if the combined string is not empty (i.e., date was provided)
    if dang_official_date_str.replace("/", "").strip(): # Check if it's more than just slashes/spaces
         in_stylized_text((355, 739), dang_official_date_str)


    # --- 17. Cơ quan công tác hiện nay (nếu có) --------------------------
    in_stylized_text((266, 762), work_org)

    # --- 18. Chức vụ hiện nay --------------------------------------------
    in_stylized_text((224, 785), work_position)

    # Move to the second page
    if len(doc) > 1:
        page = doc[1]
        try:
            page.insert_font(fontname=fontname, fontfile=fontfile)
        except Exception as e:
            print(f"Error inserting font on page 2: {e}. Using default font.")
            fontname = "helv" # Fallback for page 2 as well
    else:
        print("Warning: PDF has only one page. Content for page 2 will not be added.")
        # Decide how to handle this: maybe save and return, or skip page 2 content
        doc.save("Mau-so-yeu-ly-lich-2_filled.pdf")
        print("PDF saved (single page).")
        return


    # --- 19. Học vị, học hàm ---------------------------------------------
    in_stylized_text((337, 68), academic_title)
    in_stylized_text((460, 68), academic_year)

    # --- 20. Khen thưởng ------------------------------------------------
    in_stylized_text((161, 91), awards)

    # --- 21. Kỷ luật ----------------------------------------------------
    in_stylized_text((133, 114), discipline)

    # --- 22. Sở trường -------------------------------------------------
    in_stylized_text((147, 136), strengths)

    # =======================================================================
    # II. Quan hệ gia đình  (family_df rows)  -------------------------------
    row_step      = 14
    y_family_base = 215

    for idx, row_data in family_df.iterrows():
        y = y_family_base + idx * row_step
        # Use .get(column_name) to avoid KeyError if a column is missing,
        # and to_str will handle None or pd.NA if the column exists but value is missing.
        in_stylized_text((85, y), to_str(row_data.get("Quan hệ")))
        in_stylized_text((140, y), to_str(row_data.get("Họ và tên")))
        in_stylized_text((275, y), to_str(row_data.get("Năm sinh")))
        in_stylized_text((345, y), to_str(row_data.get("Nghề nghiệp")))
        in_stylized_text((440, y), to_str(row_data.get("Nơi công tác")))

    # =====================================================================
    # III. Quá trình đào tạo, bồi dưỡng  (edu_df rows)  --------------------
    row_step      = 23
    y_edu_base    = 380

    for idx, row_data in edu_df.iterrows():
        y = y_edu_base + idx * row_step
        from_date = to_str(row_data.get("Từ (tháng/năm)")) # Corrected key
        to_date = to_str(row_data.get("Đến (tháng/năm)")) # Corrected key
        date_range_str = f'{from_date}-{to_date}' if from_date or to_date else ""

        in_stylized_text((69, y), date_range_str)
        in_stylized_text((155, y), to_str(row_data.get("Trường / Cơ sở đào tạo")))
        in_stylized_text((275, y), to_str(row_data.get("Ngành học (viết ngắn)")))
        in_stylized_text((370, y), to_str(row_data.get("Hình thức (chính quy)")))
        in_stylized_text((455, y), to_str(row_data.get("Văn bằng / Chứng chỉ")))

    # =====================================================================
    # IV. Quá trình công tác  (work_df rows)  ------------------------------
    row_step      = 23
    y_work_base = 590

    for idx, row_data in work_df.iterrows():
        y = y_work_base + idx * row_step
        from_date = to_str(row_data.get("Từ (tháng/năm)")) # Corrected key
        to_date = to_str(row_data.get("Đến (tháng/năm)"))   # Corrected key
        date_range_str = f'{from_date}-{to_date}' if from_date or to_date else ""

        in_stylized_text((69, y), date_range_str)
        in_stylized_text((170, y), to_str(row_data.get("Đơn vị công tác")))
        in_stylized_text((425, y), to_str(row_data.get("Chức vụ")))

    # --- Convert document to bytes and close ---
    pdf_bytes = None
    try:
        pdf_bytes = doc.write()
    except Exception as e:
        print(f'Error writing PDF to bytes: {e}') # Server-side log
        # pdf_bytes remains None
    finally:
        if doc: # Ensure doc was successfully opened before trying to close
            doc.close()

    return pdf_bytes

