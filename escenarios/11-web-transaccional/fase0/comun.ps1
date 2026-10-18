# FraSoHome Live · fase 0 · funciones comunes de los scripts (se cargan con dot-sourcing).
# Compatible con Windows PowerShell 5.1 y PowerShell 7.

$ErrorActionPreference = 'Stop'

$Fase0Dir = $PSScriptRoot
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$LocalDir = Join-Path $RepoRoot '.local\fase0'          # .local/ está en .gitignore
$EstadoFile = Join-Path $LocalDir 'estado.json'          # nombres de recursos, sin secretos
$SecretosFile = Join-Path $LocalDir 'secretos.json'      # contraseña del administrador SQL

function Invoke-Az {
    # Ejecuta az y falla si az falla. Devuelve la salida como texto.
    $out = & az @args
    if ($LASTEXITCODE -ne 0) { throw "Falló: az $($args -join ' ')" }
    return ($out -join "`n")
}

function Invoke-AzJson {
    $text = Invoke-Az @args -o json
    if ([string]::IsNullOrWhiteSpace($text)) { return $null }
    return ($text | ConvertFrom-Json)
}

function Assert-AzLogin {
    if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
        throw 'No encuentro la CLI de Azure (az). Instálala: https://learn.microsoft.com/cli/azure/install-azure-cli-windows'
    }
    $acc = & az account show -o json 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'No hay sesión en Azure. Ejecuta: az login' }
    return ($acc | ConvertFrom-Json)
}

function Read-Estado {
    if (-not (Test-Path $EstadoFile)) { throw "No existe $EstadoFile. Ejecuta antes desplegar.ps1." }
    return (Get-Content $EstadoFile -Raw -Encoding UTF8 | ConvertFrom-Json)
}

function Save-Json($Object, $Path) {
    New-Item -ItemType Directory -Force -Path (Split-Path $Path) | Out-Null
    $Object | ConvertTo-Json -Depth 6 | Set-Content -Path $Path -Encoding UTF8
}

function New-Password([int]$Length = 24) {
    # Letras, dígitos, guion y guion bajo: sin comillas ni caracteres que haya que escapar en la línea de comandos.
    $alphabet = 'abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789-_'.ToCharArray()
    $rng = New-Object System.Security.Cryptography.RNGCryptoServiceProvider
    while ($true) {
        $bytes = New-Object byte[] $Length
        $rng.GetBytes($bytes)
        $secret = -join ($bytes | ForEach-Object { $alphabet[$_ % $alphabet.Length] })
        if ($secret -cmatch '[a-z]' -and $secret -cmatch '[A-Z]' -and $secret -match '[0-9]') { return $secret }
    }
}

function Get-PythonCommand {
    foreach ($cmd in @('py', 'python', 'python3')) {
        if (Get-Command $cmd -ErrorAction SilentlyContinue) {
            $args3 = @()
            if ($cmd -eq 'py') { $args3 = @('-3') }
            & $cmd @args3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) { $found = @($cmd) + $args3; return , $found }
        }
    }
    throw 'Necesito Python 3.10 o superior en el PATH (py, python o python3).'
}
