<#
.SYNOPSIS
  FraSoHome Live · fase 2 · carga los CSV de datos/ en Azure SQL y Cosmos DB y comprueba los recuentos.

.DESCRIPTION
  1. Prepara un entorno de Python en .local\frasohome-live\venv con mssql-python y azure-cosmos.
  2. Abre el firewall de SQL a tu IP actual (regla «equipo-carga»).
  3. Obtiene la clave de Cosmos DB con tu sesión de az y lee la contraseña del administrador
     SQL de .local\fase0\secretos.json. Las pasa a Python por variables de entorno que se
     borran al terminar.
  4. Según el modo:
       (por defecto)   crea el esquema si no existe y carga SQL y Cosmos DB sobre bases vacías
       -Reiniciar      borra todos los datos y vuelve a cargar (pide escribir «reiniciar»);
                       los usuarios de la web se conservan
       -SoloVerificar  solo compara recuentos

  La base gratuita se despierta de la autopausa en la primera conexión (hasta un minuto).
  La carga de Cosmos DB tarda unos minutos: se limita a -RU unidades por segundo para no
  pasar de las 1.000 gratuitas.

.EXAMPLE
  .\cargar_datos.ps1
  .\cargar_datos.ps1 -Reiniciar
  .\cargar_datos.ps1 -IpPublica 203.0.113.7
  .\cargar_datos.ps1 -SoloVerificar
#>
param(
    [switch]$Reiniciar,
    [switch]$SoloVerificar,
    [ValidateRange(100, 950)][int]$RU = 700,
    [string]$IpPublica    # si tu red no deja consultar api.ipify.org
)

. (Join-Path $PSScriptRoot '..\infra\comun.ps1')
$SeedDir = $PSScriptRoot

$acc = Assert-AzLogin
$estado = Read-Estado
$secretosFile = Join-Path $RepoRoot '.local\fase0\secretos.json'
$secretos = Read-JsonFile $secretosFile
if (-not $secretos) { throw "No encuentro $secretosFile (lo crea fase0\desplegar.ps1 con la contraseña del administrador SQL)." }

Write-Host "Suscripción: $($acc.name) · SQL: $($estado.sqlServerName) · Cosmos: $($estado.cosmosAccountName)" -ForegroundColor Cyan

Write-Host '1/4 Entorno de Python...' -ForegroundColor Cyan
$python = Get-PythonCommand
$pyExe = $python[0]; $pyArgs = @(); if ($python.Count -gt 1) { $pyArgs = $python[1..($python.Count - 1)] }
$venv = Join-Path $LocalDir 'venv'
if (-not (Test-Path $venv)) {
    & $pyExe @pyArgs -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno virtual.' }
}
$venvPy = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path $venvPy)) { $venvPy = Join-Path $venv 'bin/python' }
Invoke-Quiet $venvPy -m pip install --quiet --disable-pip-version-check -r (Join-Path $SeedDir 'requirements.txt') | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar mssql-python y azure-cosmos en el entorno virtual.' }

Write-Host '2/4 Firewall de SQL para tu IP...' -ForegroundColor Cyan
$ip = $IpPublica
if (-not $ip) { $ip = Get-PublicIp }
Invoke-Quiet az sql server firewall-rule show -g $estado.resourceGroup -s $estado.sqlServerName -n equipo-carga -o none | Out-Null
if ($LASTEXITCODE -eq 0) {
    Invoke-Az sql server firewall-rule update -g $estado.resourceGroup -s $estado.sqlServerName -n equipo-carga `
        --start-ip-address $ip --end-ip-address $ip -o none | Out-Null
} else {
    Invoke-Az sql server firewall-rule create -g $estado.resourceGroup -s $estado.sqlServerName -n equipo-carga `
        --start-ip-address $ip --end-ip-address $ip -o none | Out-Null
}
Write-Host "    Regla equipo-carga: $ip"

Write-Host '3/4 Credenciales...' -ForegroundColor Cyan
$cosmosKey = Invoke-Az cosmosdb keys list -g $estado.resourceGroup -n $estado.cosmosAccountName --type keys --query primaryMasterKey -o tsv
$env:FSH_SQL_CONNECTION_STRING = "Server=tcp:$($estado.sqlServerFqdn),1433;Database=frasohome-oltp;UID=$($secretos.sqlAdminLogin);PWD=$($secretos.sqlAdminPassword);Encrypt=yes;TrustServerCertificate=no;ConnectRetryCount=3;ConnectRetryInterval=10"
$env:FSH_COSMOS_ENDPOINT = $estado.cosmosEndpoint
$env:FSH_COSMOS_KEY = $cosmosKey.Trim()
$env:FSH_COSMOS_DATABASE = 'frasohome'
$env:PYTHONIOENCODING = 'utf-8'
$prevEncoding = [Console]::OutputEncoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Invoke-Seed([string]$Script, [string[]]$Arguments = @()) {
    Write-Host ''
    Write-Host "=== $Script $($Arguments -join ' ')" -ForegroundColor Cyan
    $prevPref = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    # Out-Host: la salida de Python va a la pantalla y la función solo devuelve el código.
    try { & $venvPy (Join-Path $SeedDir $Script) @Arguments | Out-Host; $code = $LASTEXITCODE } finally { $ErrorActionPreference = $prevPref }
    return $code
}

try {
    Write-Host '4/4 Carga...' -ForegroundColor Cyan
    if ($SoloVerificar) {
        $code = Invoke-Seed 'verify.py'
    } elseif ($Reiniciar) {
        Write-Host ''
        Write-Host 'Se borrarán TODOS los datos de SQL y de Cosmos DB y se volverán a cargar los CSV.' -ForegroundColor Yellow
        Write-Host 'Los usuarios de la web se conservan; sus sesiones se cierran.' -ForegroundColor Yellow
        if ((Read-Host 'Escribe "reiniciar" para continuar') -ne 'reiniciar') { throw 'Cancelado: no se ha tocado nada.' }
        $code = Invoke-Seed 'reset.py' @('--si', '--ru', "$RU")
    } else {
        $code = Invoke-Seed 'load_sql.py'
        if ($code -eq 0) { $code = Invoke-Seed 'load_cosmos.py' @('--ru', "$RU") }
        if ($code -eq 0) { $code = Invoke-Seed 'verify.py' }
        if ($code -eq 2) {
            Write-Host 'Las bases ya tienen datos: para empezar de cero usa .\cargar_datos.ps1 -Reiniciar' -ForegroundColor Yellow
        }
    }
} finally {
    Remove-Item Env:\FSH_SQL_CONNECTION_STRING, Env:\FSH_COSMOS_KEY, Env:\FSH_COSMOS_ENDPOINT, Env:\FSH_COSMOS_DATABASE -ErrorAction SilentlyContinue
    [Console]::OutputEncoding = $prevEncoding
}

Write-Host ''
if ($code -eq 0) {
    Write-Host 'Listo. Resúmenes en .local\frasohome-live\ (carga_sql.json, carga_cosmos.json, verificacion.json).' -ForegroundColor Green
    Write-Host 'Cierra las herramientas que se conecten a SQL para que la base vuelva a pausarse en una hora.'
} else {
    Write-Host "La carga terminó con código $($code): revisa el mensaje de arriba." -ForegroundColor Red
    exit $code
}
