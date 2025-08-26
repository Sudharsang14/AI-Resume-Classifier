# AI Resume Classifier (Flask)

A professional-looking web app to analyze **single** or **bulk (1000+)** resumes and export bulk results to **CSV**. Includes a one-click Windows `run_app.bat`.

## Features
- Login page (password fixed to `123456` as requested).
- Dashboard to choose **Single** or **Bulk** analysis.
- Select **target job role** (Data Analyst, Data Engineer, Data Scientist, Full Stack Developer, DevOps Engineer, Tester, ML Engineer, AI Engineer).
- ATS-style scoring beyond simple skills checks (contact info, sections, education, experience heuristic, role keyword coverage, low-text flag).
- Bulk upload with CSV export.
- Tailwind UI via CDN for a clean, modern look.

> Note: The classifier is rule/heuristic-based for simplicity. You can later replace `ats_score()` with a trained model.

## Quick Start (Windows)
1. Install **Python 3.10+**.
2. Double click `run_app.bat` (or run it in Command Prompt).
3. Open http://127.0.0.1:5000 in your browser.
4. Login with your name and password `123456`.

## Manual Run
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
set FLASK_APP=app.py
flask run
```

## Project Structure
```
ai-resume-classifier/
  app.py
  requirements.txt
  models/
    rules.json
  templates/
    login.html
    dashboard.html
    single.html
    single_result.html
    bulk.html
    bulk_result.html
  static/
    css/styles.css
    js/main.js
  sample_resumes/
    data_analyst_anuj.txt
    data_engineer_meera.txt
    data_scientist_rahul.txt
    fullstack_arun.txt
    devops_sahana.txt
    tester_kavya.txt
    ml_engineer_ajay.txt
    ai_engineer_sridhar.txt
  uploads/            # created at runtime
  downloads/          # created at runtime
  run_app.bat
```

## Notes
- Supported file types: **PDF**, **DOCX**, **TXT**.
- The CSV is saved under `downloads/` and also offered via the **Download CSV** button after a bulk run.
- If some PDFs are image-only (scanned), they may get a **Low text content** flag. Consider adding OCR later.
