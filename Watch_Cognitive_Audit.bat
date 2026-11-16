@echo off
setlocal
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [AUDIT] Python virtual environment is missing: venv\Scripts\python.exe
    exit /b 2
)

set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
echo [AUDIT] Passively recording cognitive execution; no chat turns are sent.
echo [AUDIT] Stop with Ctrl+C. Output: logs\cognitive_harness_audit.jsonl
"%~dp0venv\Scripts\python.exe" scripts\watch_cognitive_harness_audit.py --interval 30
exit /b %ERRORLEVEL%
