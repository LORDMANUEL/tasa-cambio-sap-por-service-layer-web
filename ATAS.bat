@echo off
setlocal
cd /d "%~dp0"
title Atas V5

if exist "runtime\python\python.exe" goto launch
if exist ".venv\Scripts\python.exe" goto launch

echo ================================================================
echo  ATAS V5
echo  Preparacion inicial desde codigo fuente
echo  Autor: Luis Manuel Fajardo Rivera - LORDMANUEL
echo ================================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\bootstrap.ps1"
if errorlevel 1 goto fail

:launch
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\windows\start-atas.ps1"
if errorlevel 1 goto fail
exit /b 0

:fail
echo [ERROR] Atas no pudo iniciar. Revise el mensaje anterior.
pause
exit /b 1
