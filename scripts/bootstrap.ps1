$ErrorActionPreference='Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$py=Get-Command py -ErrorAction SilentlyContinue
if(-not $py){$py=Get-Command python -ErrorAction SilentlyContinue}
if(-not $py){winget install -e --id Python.Python.3.13 --accept-package-agreements --accept-source-agreements;$py=Get-Command py -ErrorAction SilentlyContinue}
$python=if($py -and $py.Name -eq 'py.exe'){'py'}else{'python'}
if(-not(Test-Path '.venv\Scripts\python.exe')){& $python -m venv .venv}
$vp='.\.venv\Scripts\python.exe'
& $vp -m pip install --upgrade pip
& $vp -m pip install -r requirements.txt
if(-not(Test-Path '.env')){Copy-Item '.env.example' '.env'}
& $vp -c "from app.config import get_settings;from app.store import Store;s=get_settings();Store(s.db_path,s.timezone);print('[OK]',s.db_path)"
& $vp -m compileall -q app
if($LASTEXITCODE -ne 0){throw 'Compilacion fallida'}
& $vp -m pytest -q
if($LASTEXITCODE -ne 0){throw 'Pruebas fallaron'}
Set-Content '.prepared_v5' ('Preparado '+(Get-Date -Format o))
