# 📝 AutoLý – Vietnamese Background Form Filler

AutoLý is a streamlined web app that automates the tedious process of filling out the Vietnamese **Sơ yếu lý lịch** (personal background form). Powered by Streamlit and PyMuPDF, this tool lets users enter personal information, education history, work experience, and family details via a clean UI—and generates a ready-to-download, fully filled PDF based on an official government template.

![AutoLý Demo 1](./path_to_image1.png)
![AutoLý Demo 2](./path_to_image2.png)

---

## 🚀 Features

- 🧾 Fill out the official Vietnamese **Sơ yếu lý lịch** form via web
- 🖋 Dynamically populate personal, family, education, and work history
- 📄 View PDF preview directly in-browser
- 📥 One-click export to downloadable, styled PDF
- 📚 Vietnamese language & field examples provided as placeholders

---

## 🛠 Tech Stack

- **Frontend**: Streamlit
- **PDF Engine**: PyMuPDF (`fitz`)
- **Data Handling**: Pandas
- **Font Rendering**: Custom Times New Roman TTF embedding
- **Demo-ready**: Local demo runs out-of-the-box

---

## 🧰 Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/autoly.git
cd autoly