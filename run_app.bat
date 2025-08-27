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
set PORT=5001

REM Check if the port is in use and kill the process
for /f "tokens=5" %%a in ('netstat -a -n -o ^| findstr :%PORT%') do (
    echo Killing process using port %PORT% with PID %%a
    taskkill /PID %%a /F
)

echo Starting Flask server at http://127.0.0.1:%PORT%
flask run --port %PORT%

endlocal
