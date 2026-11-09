@echo off
cd /d "%~dp0"
setlocal

REM Start the same Brain code as FLUX without replacing its local profile or data.
set "LUMINA_CONFIG_PATH=config_Flux.json"

call BrainOnly.bat
endlocal
