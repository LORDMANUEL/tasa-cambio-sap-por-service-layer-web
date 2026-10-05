@echo off
setlocal
cd /d "%~dp0\..\.."
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\windows\start-atas.ps1"
exit /b %ERRORLEVEL%
