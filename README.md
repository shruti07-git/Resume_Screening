# Resume_Screening
A simple yet powerful Resume Screening Web  built with **Flask** and **SpaCy**.  
It automatically **extracts**, **analyzes**, and **ranks resumes** based on a given **job description (JD)** using **TF-IDF cosine similarity** and **skill matching**.

---

🚀 Features

- 📤 Upload multiple resumes (`.pdf`, `.docx`, `.txt`, `.html`)
- 🧠 Extracts key information:
  - Candidate Name
  - Email ID
  - Phone Number
  - Skills
- ⚙️ Automatically ranks resumes by relevance to the given **Job Description**
- 📊 View detailed ranked results in a browser
- ⬇️ Download results as a CSV file
- 🧾 Preview resumes in plain text directly from the web UI

  💻 Tech Stack
- **Backend:** Flask
- **NLP:** SpaCy (`en_core_web_sm`)
- **ML / Ranking:** Scikit-learn (TF-IDF + Cosine Similarity)
- **Parsing:** PyPDF2, python-docx, BeautifulSoup
- **Frontend:** HTML, Bootstrap
  


*Create and activate a virtual environment
python -m venv venv
source venv/bin/activate    # On Mac/Linux
venv\Scripts\activate       # On Windows

*Install dependencies
pip install -r requirements.txt

*Download SpaCy model
python -m spacy download en_core_web_sm

*Run the Flask app
python app.py

*Then open your browser and go to 👉 http://127.0.0.1:5000
