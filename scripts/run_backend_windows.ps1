Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location "$PSScriptRoot\..\backend"
.\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
