param(
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $Root

$Embedded = Join-Path $Root 'runtime\python\python.exe'
$Venv = Join-Path $Root '.venv\Scripts\python.exe'

if (Test-Path $Embedded) {
    $Python = $Embedded
} elseif (Test-Path $Venv) {
    $Python = $Venv
} else {
    Write-Error 'No se encontró Python embebido ni .venv de Atas.'
    exit 1
}

$EnvFile = Join-Path $Root '.env'
$EnvExample = Join-Path $Root '.env.example'
if (-not (Test-Path $EnvFile) -and (Test-Path $EnvExample)) {
    Copy-Item $EnvExample $EnvFile
}

try {
    $PortRaw = & $Python -c "from app.config import get_settings; print(get_settings().app_port)"
    $Port = [int]($PortRaw | Select-Object -Last 1)
} catch {
    Write-Error "No se pudo resolver APP_PORT: $($_.Exception.Message)"
    exit 1
}

if ($Port -lt 1 -or $Port -gt 65535) {
    Write-Error "APP_PORT inválido: $Port"
    exit 1
}

$BaseUrl = "http://127.0.0.1:$Port"

function Test-AtasHealth {
    try {
        $r = Invoke-RestMethod -Uri "$BaseUrl/health" -TimeoutSec 1
        return ($r.status -eq 'ok' -and $r.service -eq 'Atas')
    } catch {
        return $false
    }
}

function Test-PortOpen {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $iar = $client.BeginConnect('127.0.0.1', $Port, $null, $null)
        if (-not $iar.AsyncWaitHandle.WaitOne(500)) {
            return $false
        }
        $client.EndConnect($iar)
        return $true
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

if (-not (Test-AtasHealth)) {
    if (Test-PortOpen) {
        Write-Error "El puerto $Port está ocupado por otra aplicación. Atas no se inició."
        exit 2
    }

    Start-Process -FilePath $Python -ArgumentList '-m','app.run_server' -WorkingDirectory $Root -WindowStyle Minimized | Out-Null

    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 1
        if (Test-AtasHealth) {
            $ready = $true
            break
        }
    }
    if (-not $ready) {
        Write-Error "Atas no respondió en $BaseUrl después de 30 segundos."
        exit 3
    }
}

if (-not $NoBrowser) {
    Start-Process "$BaseUrl/"
}

Write-Host "ATAS_READY=$BaseUrl"
exit 0
