@echo off
cd /d "%~dp0backend"
if not exist venv (
  echo Creating backend virtual environment and installing requirements...
  python -m venv venv
  call venv\Scripts\python.exe -m pip install --upgrade pip
  call venv\Scripts\pip.exe install -r requirements.txt
)
echo Starting SafeSphere FastAPI backend...
call venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
pause
