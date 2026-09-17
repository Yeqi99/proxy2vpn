@echo off
cd /d "%~dp0\..\.."
set "P2V_PY=python"
if exist ".venv\Scripts\python.exe" set "P2V_PY=.venv\Scripts\python.exe"
"%P2V_PY%" -m proxy2vpn down
pause
