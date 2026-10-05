@echo off
setlocal
cd /d "%~dp0"
title Atas V5
cls
echo ================================================================
echo  ATAS V5
echo  Automatizacion local de tasa de cambio para SAP Business One
echo  Autor: LORDMANUEL
echo  GitHub: https://github.com/LORDMANUEL/tasa-cambio-sap-por-service-layer-web
echo ================================================================
if not exist ".prepared_v5" goto prepare
if not exist ".venv\Scripts\python.exe" goto prepare
".venv\Scripts\python.exe" -c "import fastapi,uvicorn,requests,bs4,dotenv,pydantic_settings,multipart,cryptography" >nul 2>&1
if errorlevel 1 goto prepare
goto start
:prepare
echo [INFO] Preparando Atas por primera vez...
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\bootstrap.ps1
if errorlevel 1 goto fail
:start
if not exist ".venv\Scripts\python.exe" goto fail
powershell -NoProfile -Command "try { $r=Invoke-RestMethod -Uri 'http://127.0.0.1:8787/health' -TimeoutSec 1; if($r.status -eq 'ok'){exit 0}else{exit 1} } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
  start "Atas V5 Server" /min cmd /c ".venv\Scripts\python.exe -m app.run_server"
  echo [INFO] Levantando servidor local...
  timeout /t 3 /nobreak >nul
) else (
  echo [INFO] Atas ya estaba ejecutándose. No se inició un segundo servidor.
)
start "" http://127.0.0.1:8787/
echo [OK] Atas abierto en http://127.0.0.1:8787/
echo Puede cerrar esta ventana. El servidor continua ejecutandose.
timeout /t 2 /nobreak >nul
exit /b 0
:fail
echo [ERROR] No se pudo preparar o iniciar Atas V5.
pause
exit /b 1
