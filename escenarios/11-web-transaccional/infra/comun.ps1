# FraSoHome Live · funciones comunes de los scripts de infraestructura (se cargan con dot-sourcing).
# Compatible con Windows PowerShell 5.1 y PowerShell 7.

$ErrorActionPreference = 'Stop'

$InfraDir = $PSScriptRoot
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$LocalDir = Join-Path $RepoRoot '.local\frasohome-live'     # .local/ está en .gitignore
$EstadoFile = Join-Path $LocalDir 'estado.json'             # nombres de recursos y correo de alertas
$Fase0EstadoFile = Join-Path $RepoRoot '.local\fase0\estado.json'
$GithubRepo = 'antoniosql/frasohome-demos'
$GithubEnvironment = 'frasohome-live'

function Hide-Secrets([string]$Text) {
    # Oculta contraseñas y claves antes de mostrar un comando o un error.
    return ($Text -replace '(?i)((password|pwd|key|token)[^=\s]*=)[^\s;"]+', '$1***')
}

function Invoke-Az {
    # Ejecuta az, devuelve su salida y falla con el mensaje de Azure (sin secretos) si az falla.
    # En Windows PowerShell 5.1, con ErrorActionPreference=Stop, una línea en stderr redirigido
    # (un simple WARNING de az) detiene el script: se relaja solo durante la llamada.
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

function Invoke-AzJson {
    $text = Invoke-Az @args -o json
    if ([string]::IsNullOrWhiteSpace($text)) { return $null }
    return ($text | ConvertFrom-Json)
}

function Invoke-AzLive {
    # Ejecuta az mostrando su salida en pantalla tal cual (what-if en color). Devuelve el código de salida.
    $prevPref = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { & az @args | Out-Host; $code = $LASTEXITCODE } finally { $ErrorActionPreference = $prevPref }
    return $code
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

function Assert-AzLogin {
    if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
        throw 'No encuentro la CLI de Azure (az). Instálala: https://learn.microsoft.com/cli/azure/install-azure-cli-windows'
    }
    $acc = Invoke-Quiet az account show -o json
    if ($LASTEXITCODE -ne 0) { throw 'No hay sesión en Azure. Ejecuta: az login' }
    return (($acc -join "`n") | ConvertFrom-Json)
}

function Read-JsonFile([string]$Path) {
    if (-not (Test-Path $Path)) { return $null }
    return (Get-Content $Path -Raw -Encoding UTF8 | ConvertFrom-Json)
}

function Read-Estado {
    $estado = Read-JsonFile $EstadoFile
    if (-not $estado) { throw "No existe $EstadoFile. Ejecuta antes desplegar_infra.ps1." }
    return $estado
}

function Save-Json($Object, $Path) {
    New-Item -ItemType Directory -Force -Path (Split-Path $Path) | Out-Null
    $Object | ConvertTo-Json -Depth 6 | Set-Content -Path $Path -Encoding UTF8
}

function Show-FailedOperations([string]$ResourceGroup, [string]$DeploymentName) {
    Write-Host ''
    Write-Host 'Recursos que fallaron en el despliegue:' -ForegroundColor Yellow
    $prevPref = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & az deployment operation group list -g $ResourceGroup -n $DeploymentName `
            --query "[?properties.provisioningState=='Failed'].{recurso:properties.targetResource.resourceName, codigo:properties.statusMessage.error.code, mensaje:properties.statusMessage.error.message}" `
            -o table | Out-String -Width 220 | Write-Host
    } finally { $ErrorActionPreference = $prevPref }
}

function Get-PythonCommand {
    # Devuelve el comando de Python 3.10+ como array (p. ej. @('py', '-3')).
    foreach ($cmd in @('py', 'python', 'python3')) {
        if (Get-Command $cmd -ErrorAction SilentlyContinue) {
            $extra = @()
            if ($cmd -eq 'py') { $extra = @('-3') }
            Invoke-Quiet $cmd @extra -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" | Out-Null
            if ($LASTEXITCODE -eq 0) { $found = @($cmd) + $extra; return , $found }
        }
    }
    throw 'Necesito Python 3.10 o superior en el PATH (py, python o python3).'
}

function Get-PublicIp {
    return (Invoke-RestMethod -Uri 'https://api.ipify.org' -TimeoutSec 20).ToString().Trim()
}
