@echo off
cd /d "%~dp0\..\.."
set "P2V_PY=python"
if exist ".venv\Scripts\python.exe" set "P2V_PY=.venv\Scripts\python.exe"
if not exist "%USERPROFILE%\.proxy2vpn\config.json" "%P2V_PY%" -m proxy2vpn init
if errorlevel 1 goto end
"%P2V_PY%" -m proxy2vpn up --assets artifacts\x86_64
:end
pause
