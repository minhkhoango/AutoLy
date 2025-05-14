# 📝 AutoLý – Vietnamese Background Form Filler | Trình điền Sơ yếu lý lịch tự động

**AutoLý** is a fast, user-friendly app for filling out Vietnam’s official *Sơ yếu lý lịch* (background form). Just enter your information into a web form and download a ready-to-submit PDF, fully formatted and localized.

**AutoLý** là công cụ đơn giản giúp bạn điền *Mẫu Sơ yếu lý lịch* nhanh chóng. Nhập thông tin vào giao diện web, bấm nút, và nhận ngay file PDF hoàn chỉnh – đúng mẫu và dễ in.

---

## 🚀 Features | Tính năng

- 🧾 Fill the official Vietnamese government background form | Điền đúng mẫu chuẩn Nhà nước
- 📋 Input personal, family, academic, and work history | Nhập thông tin cá nhân, quan hệ gia đình, học vấn, công tác
- 📄 Preview the filled PDF in-browser | Xem trước file PDF trực tiếp trên trang web
- 📥 Download formatted PDF with one click | Tải file PDF đã điền đầy đủ
- 🇻🇳 Vietnamese placeholders & UX hints | Hướng dẫn và ví dụ nội dung dễ hiểu

---

## 🛠 Tech Stack | Công nghệ sử dụng

| Purpose            | Technology         |
|--------------------|--------------------|
| Web UI             | Streamlit          |
| PDF Processing     | PyMuPDF (fitz)     |
| Data Handling      | Pandas             |
| Font Rendering     | Custom TTF font    |

---

## 🧰 Installation | Hướng dẫn cài đặt

### 1. Clone the repo | Tải mã nguồn

```bash
git clone https://github.com/your-username/autoly.git
cd autoly
2. Install dependencies | Cài thư viện cần thiết
bash
Copy
Edit
pip install -r requirements.txt
Dependencies:

streamlit

pymupdf

pandas

3. Add the required files | Thêm file cần thiết
Put these files into the project folder:

Mau-so-yeu-ly-lich-2-copy.pdf: official blank form template (not included)

font-times-new-roman/SVN-Times New Roman 2.ttf: Vietnamese-compatible font

▶️ Run the App | Chạy ứng dụng
bash
Copy
Edit
streamlit run autoly_app.py
Then go to: http://localhost:8501

🧪 Example Use Cases | Các tình huống sử dụng
🏫 Students filling internship/job forms | Sinh viên nộp hồ sơ thực tập / xin việc

🧑‍💼 New employee onboarding | Nhân sự khai báo lý lịch

🧾 Admin simplification for individuals | Rút gọn thủ tục hành chính cho cá nhân

📂 Project Structure | Cấu trúc dự án
perl
Copy
Edit
.
├── autoly_app.py                     # Main Streamlit app
├── utils.py                          # PDF generation logic
├── Mau-so-yeu-ly-lich-2-copy.pdf    # Official form template (not included)
├── font-times-new-roman/
│   └── SVN-Times New Roman 2.ttf     # Font with Vietnamese support
├── requirements.txt
└── README.md
⚠️ Notes | Lưu ý
This app is for personal or internal use. The official template and font are not included in the public repo.

You can customize the PDF template or add .docx export if needed.

🙌 Acknowledgments | Ghi nhận
Built by a Vietnamese student to simplify one of the most annoying tasks—filling out the same form every semester.

Được phát triển bởi một sinh viên Việt Nam, nhằm giảm bớt nỗi khổ mỗi lần phải điền lại Sơ yếu lý lịch cho trường học hoặc cơ quan.

📃 License | Giấy phép
MIT License. See LICENSE.

🖼 Screenshots | Ảnh minh họa
Giao diện điền form	Xem trước file PDF

python
Copy
Edit

Let me know if you'd like to:

- Replace the image paths with relative GitHub links after upload
- Add a `.gitignore`
- Deploy it via Streamlit Cloud (I'll generate `streamlit_app.py` or help with secrets/config)

Ready to copy straight into your GitHub `README.md` file.






