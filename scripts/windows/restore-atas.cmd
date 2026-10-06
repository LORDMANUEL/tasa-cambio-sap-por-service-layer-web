@echo off
setlocal
cd /d "%~dp0\..\.."
if "%~1"=="" (
  echo Uso:
  echo   restore-atas.cmd "C:\ruta\atas-backup-AAAAMMDD-HHMMSS.zip"
  echo.
  echo IMPORTANTE: cierre Atas antes de restaurar.
  exit /b 2
)
if exist "runtime\python\python.exe" (
  "runtime\python\python.exe" -m scripts.restore_backup "%~1" --yes
) else if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m scripts.restore_backup "%~1" --yes
) else (
  py -3 -m scripts.restore_backup "%~1" --yes
)
exit /b %ERRORLEVEL%
