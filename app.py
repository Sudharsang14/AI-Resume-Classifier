from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
import os, re, io, csv, json
from datetime import datetime
from werkzeug.utils import secure_filename

# Text extraction
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document as DocxDocument

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt'}

app = Flask(__name__)
app.secret_key = "super-secret-key-change-me"

PASSWORD = "123456"

# Load role rules
with open(os.path.join("models", "rules.json"), "r", encoding="utf-8") as f:
    ROLE_RULES = json.load(f)

def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == ".pdf":
            return pdf_extract_text(file_path) or ""
        elif ext == ".docx":
            doc = DocxDocument(file_path)
            return "\n".join(p.text for p in doc.paragraphs)
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
    except Exception:
        return ""
    return ""

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(\+?\d{1,3}[-.\s]?)?(\d{10})\b")
YEAR_RE = re.compile(r"(\d{1,2})\s*\+?\s*years", re.I)

SECTION_HINTS = ["education", "experience", "projects", "skills", "certifications", "summary", "objective"]

def est_years_experience(text):
    years = 0
    for m in YEAR_RE.finditer(text):
        try:
            years = max(years, int(m.group(1)))
        except:
            pass
    return years

def detect_name(text):
    for line in text.splitlines():
        line = line.strip()
        if len(line) > 3 and not EMAIL_RE.search(line) and not PHONE_RE.search(line):
            tokens = re.findall(r"[A-Za-z][A-Za-z\-']*", line)
            if tokens:
                return " ".join(tokens[:4])
    return "Unknown"

def ats_score(text, target_role):
    text_lower = text.lower()
    score = 0
    details = []

    # Contact info
    has_email = bool(EMAIL_RE.search(text))
    has_phone = bool(PHONE_RE.search(text))
    if has_email:
        score += 8
    else:
        details.append("Missing email")
    if has_phone:
        score += 6
    else:
        details.append("Missing phone")

    # Sections
    found_sections = sum(1 for s in SECTION_HINTS if s in text_lower)
    score += min(found_sections * 4, 20)

    # Education
    edu_terms = ["b.e", "btech", "b.tech", "bachelor", "master", "m.e", "mtech",
                 "university", "degree", "bsc", "msc", "be ", "bs ", "ms "]
    has_edu = any(t in text_lower for t in edu_terms)
    if has_edu:
        score += 12
    else:
        details.append("Education unclear")

    # Experience heuristic
    years = est_years_experience(text_lower)
    score += min(years * 3, 18)

    # Role-match keywords
    role_info = ROLE_RULES.get(target_role, {})
    role_keywords = [kw.lower() for kw in role_info.get("keywords", [])]
    role_hits = sum(1 for kw in role_keywords if kw in text_lower)
    score += min(role_hits * 2, 24)

    # ATS friendliness heuristics
    if len(text.strip()) < 400:
        details.append("Low text content (possible image-only PDF)")
        score -= 10

    # Normalize
    score = max(0, min(100, score))

    decision = "Hire" if score >= 75 else ("Consider" if score >= 55 else "Not a fit")
    missing_keywords = [kw for kw in role_keywords if kw not in text_lower][:8]
    flags = ", ".join(details) if details else ""

    return {
        "score": score,
        "decision": decision,
        "has_email": has_email,
        "has_phone": has_phone,
        "has_education": has_edu,
        "years_experience": years,
        "missing_keywords": missing_keywords,
        "flags": flags
    }

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        if password == PASSWORD and name:
            session["user"] = name
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials. Hint: use the provided password.", "error")
    return render_template("login.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", roles=list(ROLE_RULES.keys()))

@app.route("/single", methods=["GET", "POST"])
def single():
    if "user" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        role = request.form.get("role")
        f = request.files.get("resume")
        if not f or not f.filename:
            flash("Please upload a resume.", "error")
            return redirect(request.url)
        if not allowed_file(f.filename):
            flash("Unsupported file type. Use PDF, DOCX or TXT.", "error")
            return redirect(request.url)
        filename = secure_filename(f.filename)
        upload_path = os.path.join("uploads", filename)
        os.makedirs("uploads", exist_ok=True)
        f.save(upload_path)
        text = extract_text(upload_path)
        result = ats_score(text, role)
        name = detect_name(text)
        return render_template("single_result.html", role=role, filename=filename, name=name, result=result)
    return render_template("single.html", roles=list(ROLE_RULES.keys()))

@app.route("/bulk", methods=["GET", "POST"])
def bulk():
    if "user" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        role = request.form.get("role")
        files = request.files.getlist("resumes")
        if not files or len(files) == 0:
            flash("Please upload one or more resumes.", "error")
            return redirect(request.url)
        os.makedirs("uploads", exist_ok=True)
        results = []
        for f in files:
            if not f or not f.filename:
                continue
            if not allowed_file(f.filename):
                continue
            filename = secure_filename(f.filename)
            path = os.path.join("uploads", filename)
            f.save(path)
            text = extract_text(path)
            res = ats_score(text, role)
            name = detect_name(text)
            results.append({
                "filename": filename,
                "name": name,
                "role": role,
                "score": res["score"],
                "decision": res["decision"],
                "years_experience": res["years_experience"],
                "has_email": res["has_email"],
                "has_phone": res["has_phone"],
                "has_education": res["has_education"],
                "missing_keywords": ";".join(res["missing_keywords"]),
                "flags": res["flags"]
            })
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_name = f"bulk_results_{timestamp}.csv"
        csv_path = os.path.join("downloads", csv_name)
        os.makedirs("downloads", exist_ok=True)
        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=list(results[0].keys()) if results else [
                "filename","name","role","score","decision","years_experience",
                "has_email","has_phone","has_education","missing_keywords","flags"
            ])
            writer.writeheader()
            for row in results:
                writer.writerow(row)
        session["last_csv"] = csv_path
        return render_template("bulk_result.html", role=role, results=results, csv_file=os.path.basename(csv_path))
    return render_template("bulk.html", roles=list(ROLE_RULES.keys()))

@app.route("/download_csv")
def download_csv():
    if "user" not in session:
        return redirect(url_for("login"))
    csv_path = session.get("last_csv")
    if not csv_path or not os.path.exists(csv_path):
        flash("No CSV available. Please run a bulk analysis first.", "error")
        return redirect(url_for("bulk"))
    return send_file(csv_path, as_attachment=True)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("downloads", exist_ok=True)

    # ✅ Use environment-based port to avoid conflicts
    port = int(os.environ.get("PORT", 6000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
