@echo off
setlocal
cd /d "%~dp0"
title SAP FX Control Center V5
cls
echo ================================================================
echo  SAP FX CONTROL CENTER V5
echo  Plataforma local de tasa de cambio para SAP Business One
echo ================================================================
if not exist ".prepared_v5" goto prepare
if not exist ".venv\Scripts\python.exe" goto prepare
goto start
:prepare
echo [INFO] Preparando la aplicacion por primera vez...
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\bootstrap.ps1
if errorlevel 1 goto fail
:start
if not exist ".venv\Scripts\python.exe" goto fail
start "SAP FX V5 SERVER" /min cmd /c ".venv\Scripts\python.exe -m app.run_server"
echo [INFO] Levantando servidor local...
timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:8787/
echo [OK] Panel abierto en http://127.0.0.1:8787/
echo Puede cerrar esta ventana. El servidor continua ejecutandose.
timeout /t 2 /nobreak >nul
exit /b 0
:fail
echo [ERROR] No se pudo preparar o iniciar SAP FX Control Center V5.
pause
exit /b 1
