@echo off
setlocal
cd /d "%~dp0\..\.."
if not exist "runtime\python\python.exe" (echo [ERROR] Runtime Python embebido no encontrado.& pause& exit /b 1)
if not exist ".env" copy /Y ".env.example" ".env" >nul
start "SAP FX Control Center Server" /min "runtime\python\python.exe" -m app.run_server
timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:8787/
exit /b 0
