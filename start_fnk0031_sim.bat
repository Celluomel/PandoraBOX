@echo off
setlocal
cd /d "%~dp0"
if "%FNK0031_SIM_HOST%"=="" set "FNK0031_SIM_HOST=127.0.0.1"
if "%FNK0031_SIM_PORT%"=="" set "FNK0031_SIM_PORT=9100"
if exist "body_venv\Scripts\python.exe" (
  body_venv\Scripts\python.exe -m body_runtime_host.robot_sim --host "%FNK0031_SIM_HOST%" --port "%FNK0031_SIM_PORT%"
) else (
  python -m body_runtime_host.robot_sim --host "%FNK0031_SIM_HOST%" --port "%FNK0031_SIM_PORT%"
)
