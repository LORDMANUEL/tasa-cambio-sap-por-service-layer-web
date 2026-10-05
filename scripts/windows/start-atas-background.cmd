@echo off
setlocal
cd /d "%~dp0\..\.."
if not exist "runtime\python\python.exe" exit /b 1
if not exist ".env" copy /Y ".env.example" ".env" >nul
powershell -NoProfile -Command "try { $r=Invoke-RestMethod -Uri 'http://127.0.0.1:8787/health' -TimeoutSec 1; if($r.status -eq 'ok'){exit 0}else{exit 1} } catch { exit 1 }" >nul 2>&1
if errorlevel 1 start "Atas V5 Server" /min "runtime\python\python.exe" -m app.run_server
exit /b 0
