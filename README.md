# AutoLý

AutoLý is a small Python application that generates the Vietnamese **Sơ yếu lý lịch** PDF from a web form.  It uses [NiceGUI](https://github.com/zauberzeug/nicegui) for the interface and PyMuPDF to draw text onto a template PDF.

## Features

- Step‑based form: personal info, contact details, education history, work history and more.  Steps are defined in `app/myapp.py` and follow the sequence described in `app/form_data_builder.py`.
- Centralised field definitions in `app/utils.py` (`AppSchema`) including PDF coordinates for each field.
- Validation helpers in `app/validation.py` ensure the entered data is consistent.
- PDF generation via `render_text_on_pdf` (see `app/myapp.py` lines 205‑299) writes all data to `assets/TEMPLATE-V2.pdf` using the `NotoSans-Regular.ttf` font.
- A helper page `tools/coordinate_picker.html` lets you find coordinates on your own template PDF.

## Requirements

Python 3.11 or newer is recommended.  Install dependencies with:

```bash
pip install -r requirements.txt
```

## Running

Execute the NiceGUI application directly:

```bash
python app/myapp.py
```

NiceGUI will start Uvicorn on port 8080.  Navigate to `http://localhost:8080` in your browser and follow the steps.  The final step allows you to download a filled PDF.

## Project Layout

```
app/
  myapp.py              # main NiceGUI application
  utils.py              # form field schema and session helpers
  form_data_builder.py  # blueprint describing form steps and PDF template
  validation.py         # reusable validators
  para.py               # option lists (provinces, etc.)
assets/
  TEMPLATE-V2.pdf       # blank form template
  NotoSans-Regular.ttf  # font used when rendering the PDF
tools/
  coordinate_picker.html # utility for locating PDF coordinates
```

---

This project currently ships a single template for private-sector dossiers.  You can extend `FORM_TEMPLATE_REGISTRY` in `form_data_builder.py` to support additional templates or step sequences.
