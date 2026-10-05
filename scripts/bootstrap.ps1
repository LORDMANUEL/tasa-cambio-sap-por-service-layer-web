$ErrorActionPreference='Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)

function Resolve-AtasPython {
    $launcher=Get-Command py -ErrorAction SilentlyContinue
    if($launcher){ return @{ Command='py'; Args=@('-3.13') } }

    $python=Get-Command python -ErrorAction SilentlyContinue
    if($python){ return @{ Command=$python.Source; Args=@() } }

    $candidates=@(
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:ProgramFiles\Python313\python.exe",
        "$env:ProgramFiles\Python\Python313\python.exe"
    )
    foreach($candidate in $candidates){
        if($candidate -and (Test-Path $candidate)){ return @{ Command=$candidate; Args=@() } }
    }
    return $null
}

$resolved=Resolve-AtasPython
if(-not $resolved){
    $winget=Get-Command winget -ErrorAction SilentlyContinue
    if(-not $winget){
        throw 'Python 3.13 no está instalado y winget no está disponible. Use el instalador EXE de Atas o instale Python 3.13.'
    }
    winget install -e --id Python.Python.3.13 --accept-package-agreements --accept-source-agreements
    if($LASTEXITCODE -ne 0){ throw "winget no pudo instalar Python 3.13 (código $LASTEXITCODE)" }
    $resolved=Resolve-AtasPython
}
if(-not $resolved){ throw 'Python 3.13 fue instalado pero no se pudo localizar python.exe en esta sesión.' }

$pythonCommand=$resolved.Command
$pythonArgs=$resolved.Args
if(-not(Test-Path '.venv\Scripts\python.exe')){
    & $pythonCommand @pythonArgs -m venv .venv
    if($LASTEXITCODE -ne 0){ throw 'No se pudo crear el entorno virtual.' }
}
$vp='.\.venv\Scripts\python.exe'
& $vp -m pip install --upgrade pip
if($LASTEXITCODE -ne 0){ throw 'No se pudo actualizar pip.' }
& $vp -m pip install -r requirements.txt
if($LASTEXITCODE -ne 0){ throw 'No se pudieron instalar las dependencias.' }
if(-not(Test-Path '.env')){Copy-Item '.env.example' '.env'}
& $vp -c "from app.config import get_settings;from app.store import Store;s=get_settings();Store(s.db_path,s.timezone);print('[OK]',s.db_path)"
if($LASTEXITCODE -ne 0){ throw 'No se pudo inicializar SQLite/configuración.' }
& $vp -m compileall -q app
if($LASTEXITCODE -ne 0){throw 'Compilación fallida'}
& $vp -m pytest -q
if($LASTEXITCODE -ne 0){throw 'Pruebas fallaron'}
Set-Content '.prepared_v5' ('Preparado '+(Get-Date -Format o))
