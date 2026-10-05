@echo off
setlocal
cd /d "%~dp0"
title Atas V5

rem ================================================================
rem Atas launcher universal
rem - Portable / instalado: usa runtime\python embebido.
rem - Codigo fuente: prepara .venv mediante scripts\bootstrap.ps1.
rem ================================================================

if exist "runtime\python\python.exe" goto packaged
goto source

:packaged
if not exist "scripts\windows\start-atas.cmd" goto fail
call "scripts\windows\start-atas.cmd"
exit /b %ERRORLEVEL%

:source
cls
echo ================================================================
echo  ATAS V5
echo  Automatizacion local de tasa de cambio para SAP Business One
echo  Autor: Luis Manuel Fajardo Rivera - LORDMANUEL
echo  GitHub: https://github.com/LORDMANUEL/tasa-cambio-sap-por-service-layer-web
echo ================================================================
if not exist ".prepared_v5" goto prepare
if not exist ".venv\Scripts\python.exe" goto prepare
goto start_source

:prepare
echo [INFO] Preparando Atas por primera vez...
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\bootstrap.ps1
if errorlevel 1 goto fail

:start_source
if not exist ".venv\Scripts\python.exe" goto fail
powershell -NoProfile -Command "try { $r=Invoke-RestMethod -Uri 'http://127.0.0.1:8787/health' -TimeoutSec 1; if($r.status -eq 'ok'){exit 0}else{exit 1} } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
  start "Atas V5 Server" /min cmd /c ".venv\Scripts\python.exe -m app.run_server"
  echo [INFO] Levantando servidor local...
  timeout /t 3 /nobreak >nul
) else (
  echo [INFO] Atas ya estaba ejecutandose. No se inicio un segundo servidor.
)
start "" http://127.0.0.1:8787/
exit /b 0

:fail
echo [ERROR] No se pudo preparar o iniciar Atas V5.
pause
exit /b 1
