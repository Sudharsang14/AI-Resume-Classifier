@echo off
setlocal

REM One-click runner for AI Resume Classifier
cd /d %~dp0

REM Create virtual environment if missing
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Upgrade pip and install dependencies
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Set Flask environment
set FLASK_APP=app.py
set FLASK_RUN_PORT=5001

echo Starting Flask server at http://127.0.0.1:6000
flask run

endlocal
