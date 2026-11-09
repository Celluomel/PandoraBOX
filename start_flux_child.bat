@echo off
cd /d "%~dp0"
setlocal

REM Start the same Brain code as FLUX without replacing its local profile or data.
set "LUMINA_CONFIG_PATH=config_Flux.json"
set "LUMINA_NETWORK_ROLE=child"
set "BRAIN_API_HOST=127.0.0.1"
set "BRAIN_API_PORT=8767"

call BrainOnly.bat
endlocal
