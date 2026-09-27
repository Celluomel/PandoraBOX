@echo off
setlocal
rem Development launcher. On VENTUNO Q use start_ventuno_gateway.sh.
if "%FNK0031_BOARD_URL%"=="" set "FNK0031_BOARD_URL=http://fnk0031.local:9100"
if "%VENTUNO_GATEWAY_PORT%"=="" set "VENTUNO_GATEWAY_PORT=9100"
if "%VENTUNO_DEPLOY_DIR%"=="" set "VENTUNO_DEPLOY_DIR=C:\ProgramData\PandoraBOX\deployments"
python -m body_runtime_host.ventuno_gateway --board-url "%FNK0031_BOARD_URL%" --port "%VENTUNO_GATEWAY_PORT%" --deploy-dir "%VENTUNO_DEPLOY_DIR%"
