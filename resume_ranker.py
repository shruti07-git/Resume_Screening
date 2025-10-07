import os
import re
import pandas as pd
from bs4 import BeautifulSoup
import spacy
from spacy.matcher import PhraseMatcher
from tqdm import tqdm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from docx import Document
import PyPDF2

# =============================
# 1️⃣ Allowed File Checker
# =============================
def allowed_file(filename):
    allowed_extensions = {'pdf', 'doc', 'docx', 'txt'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


# =============================
# 2️⃣ Load SpaCy model
# =============================
nlp = spacy.load("en_core_web_sm")
stop_words = nlp.Defaults.stop_words


# =============================
# 3️⃣ Helper: Clean text
# =============================
def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = BeautifulSoup(text, "html.parser").get_text()
    text = text.lower()
    text = re.sub(r'\S*@\S*\s?', '', text)  # remove emails
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)  # remove URLs
    text = re.sub(r'[^a-z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# =============================
# 4️⃣ Extract text from any file type
# =============================
def extract_text_from_file(file_path):
    ext = file_path.split('.')[-1].lower()
    text = ""
    try:
        if ext == "pdf":
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text = " ".join(page.extract_text() or "" for page in reader.pages)
        elif ext == "docx":
            doc = Document(file_path)
            text = " ".join([p.text for p in doc.paragraphs])
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
    except Exception as e:
        print(f"⚠️ Error reading {file_path}: {e}")
    return text


# =============================
# 5️⃣ Extract Name, Email, Phone
# =============================
def extract_contact_info(text):
    name = "Not Found"
    email = "Not Found"
    phone = "Not Found"

    # Email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if email_match:
        email = email_match.group(0)

    # Phone (Indian + International formats)
    phone_match = re.search(r'(\+?\d{1,3}[-\s]?)?\d{10}', text)
    if phone_match:
        phone = phone_match.group(0)

    # Name: heuristic - first capitalized words before contact section
    lines = text.split('\n')
    for line in lines:
        if 2 <= len(line.split()) <= 4 and line.split()[0][0].isupper():
            name = line.strip()
            break

    return name, email, phone


# =============================
# 6️⃣ Skill Dictionary
# =============================
category_skills = {
    "INFORMATION-TECHNOLOGY": [
        "python", "java", "c++", "html", "css", "javascript", "sql", "mysql",
        "react", "node.js", "flask", "django", "aws", "azure", "git", "devops",
        "api development", "data structures", "algorithms", "machine learning",
        "software development", "linux", "docker"
    ],
    "HR": [
        "recruitment", "talent acquisition", "hr policies", "employee relations",
        "training and development", "onboarding", "performance management",
        "payroll", "hr analytics", "attendance management", "compliance", "interviewing"
    ],
    "Soft_skills": [
        "communication", "teamwork", "leadership", "problem solving",
        "adaptability", "creativity", "attention to detail", "time management",
        "collaboration", "critical thinking", "presentation", "analytical thinking"
    ]
}


# =============================
# 7️⃣ Build Matcher
# =============================
def build_skill_matcher(category_skills):
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    all_skills = sorted(set(skill.lower() for skills in category_skills.values() for skill in skills))
    patterns = [nlp.make_doc(skill) for skill in all_skills]
    matcher.add("SKILLS", patterns)
    return matcher, all_skills

matcher, all_known_skills = build_skill_matcher(category_skills)


# =============================
# 8️⃣ Extract Skills
# =============================
def extract_skills_from_text(text, matcher):
    doc = nlp(text.lower())
    matches = matcher(doc)
    matched_skills = set(doc[start:end].text.lower().strip() for _, start, end in matches)
    return sorted(matched_skills)


# =============================
# 9️⃣ Process Resumes
# =============================
def process_resumes(folder_path):
    resumes = []
    files = [os.path.join(folder_path, f) for f in os.listdir(folder_path)
             if f.lower().endswith(('pdf', 'docx', 'txt'))]
    for file_path in tqdm(files, desc="📄 Processing resumes"):
        raw_text = extract_text_from_file(file_path)
        cleaned = clean_text(raw_text)
        skills = extract_skills_from_text(cleaned, matcher)
        name, email, phone = extract_contact_info(raw_text)

        resumes.append({
            "file": os.path.basename(file_path),
            "name": name,
            "email": email,
            "phone": phone,
            "text": cleaned,
            "skills": skills
        })
    return resumes


# =============================
# 🔟 Rank Resumes
# =============================
def rank_resumes(resumes, jd_text):
    jd_clean = clean_text(jd_text)
    corpus = [jd_clean] + [r["text"] for r in resumes]

    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(corpus)
    similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    ranked_output = []
    for i, (r, score) in enumerate(sorted(zip(resumes, similarities), key=lambda x: x[1], reverse=True)):
        ranked_output.append({
            "rank": i + 1,
            "name": r["name"],
            "email": r["email"],
            "phone": r["phone"],
            "basename": r["file"],
            "score": round(float(score), 3),
            "skills": r["skills"] or ["No matched skills"]
        })
    return ranked_output


# =============================
# 1️⃣1️⃣ Main API for Flask
# =============================
def rank_uploaded_resumes(upload_folder, jd_text):
    resumes = process_resumes(upload_folder)
    if not resumes:
        print("⚠️ No resumes found in upload folder.")
        return []
    ranked = rank_resumes(resumes, jd_text)
    print(f"✅ Processed {len(ranked)} resumes successfully.")
    return ranked
