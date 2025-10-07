
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
from rapidfuzz import fuzz  # For fuzzy skill matching

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
        print(f"⚠ Error reading {file_path}: {e}")
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

    # Phone
    phone_match = re.search(r'(\+?\d{1,3}[-\s]?)?\d{10}', text)
    if phone_match:
        phone = phone_match.group(0)

    # Name (heuristic)
    lines = text.split('\n')
    for line in lines:
        if 2 <= len(line.split()) <= 4 and line.split()[0][0].isupper():
            name = line.strip()
            break

    return name, email, phone


# =============================
# 6️⃣ Category Skill Dictionary
# =============================
category_skills = {

    "EDUCATION": [
        "bachelor", "master", "phd", "mba", "btech", "mtech", "bsc", "msc",
        "b.com", "m.com", "bca", "mca", "degree", "diploma", "certificate", "certification",
        "course", "training", "licensed", "accredited", "certified",
        "distance learning", "online course", "academic research", "higher education"
    ],

    "ACCOUNTANT": [
        "accounting", "financial statements", "bookkeeping", "taxation", "auditing",
        "accounts payable", "accounts receivable", "tally", "gst", "vat", "tds",
        "balance sheet", "trial balance", "reconciliation", "sap", "quickbooks",
        "cost accounting", "financial reporting", "budgeting", "forecasting", "payroll",
        "erp", "ifrs", "accounting standards", "journal entries", "ledger",
        "excel modeling", "variance analysis", "financial data cleaning", "internal controls"
    ],

    "ADVOCATE": [
        "legal research", "litigation", "contracts", "corporate law", "criminal law",
        "civil law", "intellectual property", "drafting", "case management",
        "arbitration", "client consultation", "compliance", "legal documentation",
        "pleadings", "due diligence", "court procedures", "statutes", "tribunal",
        "advocacy", "judgments", "legal writing", "legal advisory", "regulatory compliance", "contract negotiation"
    ],

    "AGRICULTURE": [
        "crop management", "soil analysis", "irrigation", "fertilizers", "pesticides",
        "harvesting", "agronomy", "horticulture", "farm management", "animal husbandry",
        "plant breeding", "sustainability", "precision agriculture", "organic farming",
        "greenhouse", "agriculture machinery", "farm operations",
        "climate adaptation", "agricultural analytics", "drip irrigation", "farm automation"
    ],

    "APPAREL": [
        "fashion design", "textiles", "garment manufacturing", "pattern making",
        "merchandising", "fabric selection", "quality control", "trend analysis",
        "styling", "sewing", "production planning", "illustrator", "photoshop",
        "garment technology", "apparel sourcing", "cutting", "fitment", "sampling",
        "fashion marketing", "color theory", "design research", "fabric draping"
    ],

    "ARTS": [
        "painting", "drawing", "illustration", "graphic design", "creative writing",
        "digital art", "animation", "storyboarding", "adobe photoshop", "adobe illustrator",
        "color theory", "concept design", "fine arts", "visual storytelling", "sculpture",
        "multimedia", "mixed media", "typography",
        "creative direction", "portfolio development", "branding", "composition"
    ],

    "AUTOMOBILE": [
        "automobile engineering", "vehicle dynamics", "maintenance", "manufacturing",
        "quality assurance", "solidworks", "catia", "autocad", "engine design",
        "mechanical systems", "supply chain", "production planning", "assembly line",
        "automotive electronics", "powertrain", "chassis", "diagnostics",
        "vehicle testing", "emission control", "automotive safety", "telemetry"
    ],

    "AVIATION": [
        "aircraft maintenance", "aviation safety", "flight operations", "aerodynamics",
        "air traffic control", "logistics", "navigation", "ground handling",
        "airport operations", "aviation law", "meteorology", "aircraft systems",
        "flight planning", "aircraft maintenance engineering", "airline operations",
        "crew management", "flight scheduling", "aviation compliance"
    ],

    "BANKING": [
        "retail banking", "credit analysis", "loans", "financial analysis",
        "investment banking", "customer service", "risk management", "compliance",
        "anti money laundering", "financial modeling", "bank operations", "treasury",
        "relationship management", "credit risk", "asset liability management",
        "fraud detection", "financial regulations", "trade finance", "cross selling"
    ],

    "BPO": [
        "customer support", "call handling", "communication skills", "crm",
        "voice process", "non voice process", "data entry", "technical support",
        "ticketing", "problem solving", "email support", "chat support", "ivr",
        "multitasking", "customer satisfaction", "telemarketing", "issue resolution"
    ],

    "BUSINESS-DEVELOPMENT": [
        "sales strategy", "lead generation", "client acquisition", "negotiation",
        "relationship management", "market research", "presentation", "cold calling",
        "crm", "revenue growth", "proposal writing", "networking", "business planning",
        "sales pipeline", "go to market", "channel strategy", "dashboard", "insights", "kpi", "data storytelling",
        "stakeholder management", "forecasting", "competitive analysis", "customer retention"
    ],

    "CHEF": [
        "cooking", "menu planning", "food preparation", "baking", "pastry",
        "food safety", "haccp", "inventory management", "kitchen management",
        "culinary arts", "recipe development", "plating", "kitchen operations", "nutrition",
        "sanitation", "menu design", "food costing"
    ],

    "CONSTRUCTION": [
        "civil engineering", "autocad", "project management", "estimation",
        "quantity surveying", "structural design", "site supervision", "planning",
        "ms project", "primavera", "quality assurance", "health and safety", "blueprints",
        "construction management", "cost estimation",
        "contract management", "tendering", "risk assessment", "project scheduling"
    ],

    "CONSULTANT": [
        "business consulting", "strategy", "process improvement", "data analysis",
        "stakeholder management", "presentation", "project management",
        "market research", "financial analysis", "problem solving", "excel",
        "communication", "change management", "business transformation", "analytics",
        "data cleaning", "data validation", "business intelligence", "critical thinking"
    ],

    "DESIGNER": [
        "graphic design", "ui design", "ux design", "adobe photoshop", "illustrator",
        "figma", "adobe xd", "wireframing", "branding", "typography",
        "layout design", "user research", "creative thinking", "sketch", "invision",
        "design systems", "responsive design", "prototyping", "accessibility"
    ],

    "DIGITAL-MEDIA": [
        "social media marketing", "seo", "sem", "content creation", "digital marketing",
        "google analytics", "facebook ads", "instagram marketing", "campaign management",
        "copywriting", "email marketing", "video editing", "youtube", "tiktok",
        "content strategy", "influencer marketing", "performance marketing", "roi analysis"
    ],

    "ENGINEERING": [
        "mechanical engineering", "electrical engineering", "civil engineering",
        "autocad", "solidworks", "matlab", "simulation", "manufacturing",
        "maintenance", "design analysis", "product development", "industrial engineering",
        "finite element analysis", "plant design", "quality control", "root cause analysis"
    ],

    "FINANCE": [
        "financial analysis", "investment", "budgeting", "forecasting", "financial modeling",
        "valuation", "portfolio management", "risk management", "accounting", "capital markets",
        "derivatives", "asset management", "corporate finance",
        "cash flow analysis", "data reconciliation", "pandas", "excel", "statistical modeling"
    ],

    "FITNESS": [
        "personal training", "nutrition", "diet planning", "exercise physiology",
        "yoga", "strength training", "cardio", "fitness assessment", "rehabilitation",
        "weight management", "group fitness", "wellness coaching",
        "posture correction", "injury prevention", "client motivation"
    ],

    "HEALTHCARE": [
        "clinical research", "patient care", "nursing", "pharmacy", "diagnostics",
        "medical coding", "public health", "hospital administration", "medical records",
        "laboratory", "first aid", "emergency response", "healthcare operations",
        "telemedicine", "patient counseling", "data confidentiality"
    ],

    "HR": [
        "recruitment", "talent acquisition", "hr policies", "employee relations",
        "training and development", "onboarding", "performance management",
        "payroll", "hr analytics", "attendance management", "compliance", "interviewing",
        "succession planning", "learning & development", "soft skills", "communication",
        "stakeholder management", "conflict resolution"
    ],

    "INFORMATION-TECHNOLOGY": [
        "python", "java", "c++", "c#", "html", "css", "javascript", "typescript",
        "sql", "mysql", "postgresql", "mongodb", "react", "angular", "vue.js",
        "node.js", "express", "django", "flask", "aws", "azure", "gcp", "git", "github",
        "docker", "kubernetes", "devops", "rest api", "graphql", "linux", "bash",
        "machine learning", "data science", "tensorflow", "pytorch", "tableau", "power bi",
        "data cleaning", "data transformation", "data validation", "pandas", "numpy",
        "statistical analysis", "data preprocessing", "communication", "critical thinking",
        "stakeholder management", "etl", "spark", "databricks", "data governance", "bigquery", "cloud computing", "data architecture"
    ],

    "PUBLIC-RELATIONS": [
        "media relations", "press release", "event management", "communication",
        "brand management", "crisis management", "content writing", "campaign planning",
        "publicity", "stakeholder engagement", "social media", "influencer outreach",
        "public speaking", "strategic communication", "media monitoring"
    ],

    "SALES": [
        "sales strategy", "negotiation", "lead generation", "cold calling", "crm",
        "customer relationship", "pipeline management", "presentation",
        "b2b sales", "b2c sales", "closing deals", "retail sales", "sales operations",
        "communication skills", "objection handling", "product knowledge", "upselling"
    ],

    "TEACHER": [
        "lesson planning", "curriculum development", "classroom management",
        "assessment", "pedagogy", "communication", "student engagement",
        "education technology", "evaluation", "subject knowledge", "mentoring",
        "tutoring", "lesson delivery", "learning outcomes", "child psychology", "online teaching", "edtech tools"
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
# 9️⃣ Process Resumes (with JD filter)
# =============================
def process_resumes(folder_path, jd_skills):
    resumes = []
    files = [os.path.join(folder_path, f) for f in os.listdir(folder_path)
             if f.lower().endswith(('pdf', 'docx', 'txt'))]

    for file_path in tqdm(files, desc="📄 Processing resumes"):
        raw_text = extract_text_from_file(file_path)
        cleaned = clean_text(raw_text)
        skills = extract_skills_from_text(cleaned, matcher)
        name, email, phone = extract_contact_info(raw_text)

        # Only keep JD-relevant skills (fuzzy matching)
        relevant_skills = [s for s in skills if any(fuzz.ratio(s, j) > 85 for j in jd_skills)]

        resumes.append({
            "file": os.path.basename(file_path),
            "name": name,
            "email": email,
            "phone": phone,
            "text": cleaned,
            "skills": relevant_skills or ["No relevant skills"]
        })
    return resumes


# =============================
# 🔟 Rank Resumes (TF-IDF + Skill Overlap)
# =============================
def rank_resumes(resumes, jd_text, jd_skills):
    jd_clean = clean_text(jd_text)
    corpus = [jd_clean] + [r["text"] for r in resumes]

    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(corpus)
    similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    ranked_output = []
    for i, (r, score) in enumerate(sorted(zip(resumes, similarities), key=lambda x: x[1], reverse=True)):
        # Skill overlap weighting
        overlap = len(set(r["skills"]) & set(jd_skills))
        weighted_score = score + (0.05 * overlap)

        ranked_output.append({
            "rank": i + 1,
            "name": r["name"],
            "email": r["email"],
            "phone": r["phone"],
            "basename": r["file"],
            "score": round(float(weighted_score), 3),
            "skills": r["skills"]
        })
    return ranked_output


# =============================
# 1️⃣1️⃣ Main API for Flask
# =============================
def rank_uploaded_resumes(upload_folder, jd_text):
    jd_clean = clean_text(jd_text)
    jd_skills = extract_skills_from_text(jd_clean, matcher)

    resumes = process_resumes(upload_folder, jd_skills)
    if not resumes:
        print("⚠ No resumes found in upload folder.")
        return []

    ranked = rank_resumes(resumes, jd_text, jd_skills)
    print(f"✅ Processed {len(ranked)} resumes successfully.")
    return ranked


