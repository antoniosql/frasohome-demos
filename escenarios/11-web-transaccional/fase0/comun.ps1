# FraSoHome Live · fase 0 · funciones comunes de los scripts (se cargan con dot-sourcing).
# Compatible con Windows PowerShell 5.1 y PowerShell 7.

$ErrorActionPreference = 'Stop'

$Fase0Dir = $PSScriptRoot
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$LocalDir = Join-Path $RepoRoot '.local\fase0'          # .local/ está en .gitignore
$EstadoFile = Join-Path $LocalDir 'estado.json'          # nombres de recursos, sin secretos
$SecretosFile = Join-Path $LocalDir 'secretos.json'      # contraseña del administrador SQL

function Hide-Secrets([string]$Text) {
    # Oculta contraseñas y claves antes de mostrar un comando o un error.
    return ($Text -replace '(?i)((password|pwd|key|token)[^=\s]*=)[^\s;"]+', '$1***')
}

function Invoke-Az {
    # Ejecuta az y falla si az falla, con el mensaje de error de Azure y sin secretos.
    # En Windows PowerShell 5.1, con ErrorActionPreference=Stop, cualquier línea que un programa
    # escriba en stderr redirigido (un simple WARNING de az) detiene el script. Se relaja solo aquí.
    $errFile = [System.IO.Path]::GetTempFileName()
    $prevPref = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $out = & az @args 2> $errFile
        $code = $LASTEXITCODE
        $err = Get-Content $errFile -Raw -ErrorAction SilentlyContinue
    } finally {
        $ErrorActionPreference = $prevPref
        Remove-Item $errFile -ErrorAction SilentlyContinue
    }
    if ($code -ne 0) {
        $detail = 'sin detalle'
        if ($err) { $detail = $err.Trim() }
        throw (Hide-Secrets "Falló: az $($args -join ' ')`n$detail")
    }
    return ($out -join "`n")
}

function Invoke-Quiet {
    # Ejecuta un programa descartando stderr sin que PowerShell 5.1 lo convierta en error.
    # Devuelve la salida; el código de salida queda en $LASTEXITCODE.
    # Sin bloque param: así opciones como -c o -o llegan intactas al programa en $args.
    $exe = $args[0]
    $rest = @($args | Select-Object -Skip 1)
    $prevPref = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { $out = & $exe @rest 2>$null } finally { $ErrorActionPreference = $prevPref }
    return $out
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
    $acc = Invoke-Quiet az account show -o json
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
            Invoke-Quiet $cmd @args3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" | Out-Null
            if ($LASTEXITCODE -eq 0) { $found = @($cmd) + $args3; return , $found }
        }
    }
    throw 'Necesito Python 3.10 o superior en el PATH (py, python o python3).'
}
