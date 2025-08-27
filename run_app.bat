@echo off
setlocal

REM One-click runner for AI Resume Classifier
cd /d %~dp0

if not exist venv (
  echo Creating virtual environment...
  python -m venv venv
)

call venv\Scripts\activate

echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

set FLASK_APP=app.py
echo Starting Flask server at http://127.0.0.1:5001
flask run

endlocal
