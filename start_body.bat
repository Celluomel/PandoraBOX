@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul 2>&1
set PYTHONUTF8=1
if defined ROS2_INSTALL_PATH if exist "%ROS2_INSTALL_PATH%\local_setup.bat" (
  echo [*] Loading ROS 2 environment from %ROS2_INSTALL_PATH%
  call "%ROS2_INSTALL_PATH%\local_setup.bat"
)
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
"%BODY_PYTHON%" -c "import websockets, imageio_ffmpeg, cv2, numpy, torch, mujoco, fastembed, serial" >nul 2>&1
if errorlevel 1 (
  echo [*] Body dependencies are missing or incomplete. Installing them...
  "%BODY_PYTHON%" -m pip install --upgrade pip
  if errorlevel 1 (
    echo [ERROR] Could not prepare pip in body_venv.
    exit /b 1
  )
  "%BODY_PYTHON%" -m pip install -r body_requirements.txt
  if errorlevel 1 (
    echo [ERROR] Body dependency installation failed.
    exit /b 1
  )
) else (
  echo [OK] Body dependencies already installed.
)

"%BODY_PYTHON%" -c "import websockets, imageio_ffmpeg, cv2, numpy, torch, mujoco, fastembed, serial" >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Body dependencies are still unavailable after installation.
  exit /b 1
)
echo Starting standalone PandoraBOX Body Runtime...
echo Body management page: http://127.0.0.1:8766/
"%BODY_PYTHON%" -m body_runtime_host
endlocal
