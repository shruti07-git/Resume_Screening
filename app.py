# app.py
import os
import shutil
import io
from flask import Flask, request, render_template, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
import pandas as pd
from resume_ranker import rank_uploaded_resumes, allowed_file as rr_allowed_file

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'html', 'htm'}

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret-key")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB total (adjust as needed)

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return rr_allowed_file(filename)  # use helper from resume_ranker

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    jd = request.form.get('jd', '').strip()
    files = request.files.getlist('resumes')   # ✅ get ALL uploaded files

    if not jd:
        flash("Please paste a job description.", "warning")
        return redirect(url_for('index'))

    if not files or len(files) == 0:
        flash("Please upload at least one resume file.", "danger")
        return redirect(url_for('index'))

    # Clear previous uploads
    if os.path.exists(UPLOAD_FOLDER):
        for f in os.listdir(UPLOAD_FOLDER):
            os.remove(os.path.join(UPLOAD_FOLDER, f))
    else:
        os.makedirs(UPLOAD_FOLDER)

    saved_files = []
    for f in files:
        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            f.save(save_path)
            saved_files.append(save_path)

    if not saved_files:
        flash("No valid resume files were uploaded. Allowed: pdf, docx, txt, html, htm", "danger")
        return redirect(url_for('index'))

    # Rank all uploaded resumes
    from resume_ranker import rank_uploaded_resumes
    ranked = rank_uploaded_resumes(UPLOAD_FOLDER, jd)

    return render_template('results.html', jd=jd, ranked=ranked)


@app.route('/download')
def download():
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], "ranking_results.csv")
    if not os.path.exists(csv_path):
        flash("No results file found. Please upload and rank resumes first.", "warning")
        return redirect(url_for('index'))
    return send_file(csv_path, as_attachment=True, download_name="resume_ranking_results.csv")

@app.route('/view_resume')
def view_resume():
    # returns plain text of a resume for preview (safe: reads from uploads)
    filepath = request.args.get('path', '')
    if not filepath:
        return "No file specified.", 400
    # ensure path inside uploads
    uploads_abs = os.path.abspath(app.config['UPLOAD_FOLDER'])
    target_abs = os.path.abspath(filepath)
    if not target_abs.startswith(uploads_abs):
        return "Unauthorized path", 403
    if not os.path.exists(target_abs):
        return "File not found", 404

    # we'll re-use resume_ranker.extract_text_from_file to get cleaned text
    from resume_ranker import extract_text_from_file
    text = extract_text_from_file(target_abs)
    return "<pre style='white-space:pre-wrap'>{}</pre>".format(text.replace("<", "&lt;").replace(">", "&gt;"))

if __name__ == '__main__':
    app.run(debug=True, port=5000)

