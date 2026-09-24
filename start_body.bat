@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul 2>&1
set PYTHONUTF8=1
set "BODY_PYTHON=body_venv\Scripts\python.exe"
if not exist "%BODY_PYTHON%" goto :create_body_venv
"%BODY_PYTHON%" -c "import sys" >nul 2>&1
if not errorlevel 1 goto :body_venv_ready
echo [*] Repairing invalid Body virtual environment...

:create_body_venv
echo [*] Creating the independent Body virtual environment...
py -3.11 -m venv --clear body_venv
if errorlevel 1 py -3 -m venv --clear body_venv
if errorlevel 1 (
  echo [ERROR] Could not create body_venv. Install Python 3.11 or newer.
  exit /b 1
)

:body_venv_ready
"%BODY_PYTHON%" -m pip install -q --upgrade pip
"%BODY_PYTHON%" -m pip install -q -r body_requirements.txt
if not defined BODY_PYTHON (
  echo [ERROR] No Python environment found. Run start.bat once first.
  exit /b 1
)
echo Starting standalone PandoraBOX Body Runtime...
echo Body management page: http://127.0.0.1:8766/
"%BODY_PYTHON%" -m body_runtime_host
endlocal
