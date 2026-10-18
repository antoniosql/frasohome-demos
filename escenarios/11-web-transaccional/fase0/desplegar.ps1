<#
.SYNOPSIS
  FraSoHome Live · fase 0 · despliega los recursos gratuitos y la función de prueba, y los comprueba.

.DESCRIPTION
  1. Crea el grupo de recursos y despliega infra/fase0.bicep (SQL gratuita, Cosmos free tier, SWA Free).
  2. Abre el firewall de SQL a tu IP y crea el usuario de solo conexión fsh_fase0 (crear_usuario_sql.py).
  3. Configura las app settings de la Static Web App (SQL y Cosmos).
  4. Empaqueta la función con dependencias para Linux y Python 3.11 y la publica con la CLI de SWA.
  5. Ejecuta comprobar_despliegue.py contra la URL publicada.

  La región de la base gratuita no se puede cambiar después: el script pide confirmarla.
  Es idempotente: se puede volver a lanzar; reutiliza la contraseña guardada en .local\fase0\secretos.json.

.EXAMPLE
  .\desplegar.ps1 -Region westeurope
  .\desplegar.ps1 -Region westeurope -SoloCodigo      # vuelve a publicar solo app y api
#>
param(
    [Parameter(Mandatory = $true)][string]$Region,
    [string]$ResourceGroup = 'rg-frasohome-live',
    [ValidateSet('westeurope', 'westus2', 'centralus', 'eastus2', 'eastasia')][string]$WebRegion = 'westeurope',
    [switch]$SinCosmosFreeTier,
    [switch]$SoloCodigo,
    [switch]$Force
)

. (Join-Path $PSScriptRoot 'comun.ps1')
$SwaCli = '@azure/static-web-apps-cli@2.0.10'

$acc = Assert-AzLogin
foreach ($tool in @('node', 'npx')) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { throw 'Necesito Node.js (node y npx) para la CLI de Static Web Apps: https://nodejs.org' }
}
$python = Get-PythonCommand
$pyExe = $python[0]; $pyArgs = @(); if ($python.Count -gt 1) { $pyArgs = $python[1..($python.Count - 1)] }
New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null

# Entorno virtual local (.local\fase0\venv): instala mssql-python y descarga las dependencias de la función.
$venv = Join-Path $LocalDir 'venv'
if (-not (Test-Path $venv)) { & $pyExe @pyArgs -m venv $venv; if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno virtual.' } }
$venvPy = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path $venvPy)) { $venvPy = Join-Path $venv 'bin/python' }

Write-Host "Suscripción: $($acc.name) · grupo: $ResourceGroup · datos: $Region · web: $WebRegion" -ForegroundColor Cyan

if (-not $SoloCodigo) {
    if (-not $Force) {
        Write-Host ''
        Write-Host "La oferta gratuita de Azure SQL fija la región '$Region' para TODAS las bases gratuitas de esta suscripción y no se puede cambiar." -ForegroundColor Yellow
        $confirm = Read-Host "Escribe la región otra vez para continuar"
        if ($confirm -ne $Region) { throw 'Región no confirmada: no se ha creado nada.' }
    }

    # Secretos: se reutilizan en redespliegues.
    if (Test-Path $SecretosFile) { $secretos = Get-Content $SecretosFile -Raw -Encoding UTF8 | ConvertFrom-Json }
    else { $secretos = [pscustomobject]@{ sqlAdminLogin = 'fsh_admin'; sqlAdminPassword = (New-Password) }; Save-Json $secretos $SecretosFile }

    $me = Invoke-AzJson ad signed-in-user show --query '{id:id, upn:userPrincipalName}'

    Write-Host '1/5 Grupo de recursos y Bicep (tarda unos minutos)...' -ForegroundColor Cyan
    Invoke-Az group create -n $ResourceGroup -l $Region --tags proyecto=frasohome-live fase=0 -o none | Out-Null
    $freeTier = 'true'; if ($SinCosmosFreeTier) { $freeTier = 'false' }
    $outputs = Invoke-AzJson deployment group create -g $ResourceGroup -n fase0 -f (Join-Path $Fase0Dir 'infra\fase0.bicep') `
        --parameters dataLocation=$Region webLocation=$WebRegion sqlAdminLogin=$($secretos.sqlAdminLogin) `
                     sqlAdminPassword=$($secretos.sqlAdminPassword) entraAdminObjectId=$($me.id) entraAdminLogin=$($me.upn) `
                     cosmosFreeTier=$freeTier `
        --query properties.outputs

    $estado = [pscustomobject]@{
        subscriptionId = $acc.id; resourceGroup = $ResourceGroup; dataLocation = $Region; webLocation = $WebRegion
        sqlServerName = $outputs.sqlServerName.value; sqlServerFqdn = $outputs.sqlServerFqdn.value
        sqlDatabaseId = $outputs.sqlDatabaseId.value; cosmosAccountName = $outputs.cosmosAccountName.value
        swaName = $outputs.swaName.value; swaHostname = $outputs.swaHostname.value
        deployedAt = (Get-Date).ToUniversalTime().ToString('s')
    }
    Save-Json $estado $EstadoFile

    Write-Host '2/5 Firewall de SQL para tu IP y usuario fsh_fase0...' -ForegroundColor Cyan
    $ip = (Invoke-RestMethod -Uri 'https://api.ipify.org' -TimeoutSec 20).ToString().Trim()
    Invoke-Az sql server firewall-rule create -g $ResourceGroup -s $estado.sqlServerName -n equipo-antonio `
        --start-ip-address $ip --end-ip-address $ip -o none | Out-Null

    & $venvPy -m pip install --quiet --disable-pip-version-check mssql-python==1.15.0
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo instalar mssql-python en el entorno local.' }

    $env:FSH_SQL_ADMIN_PASSWORD = $secretos.sqlAdminPassword
    try {
        $userJson = & $venvPy (Join-Path $Fase0Dir 'crear_usuario_sql.py') --server $estado.sqlServerFqdn --admin-login $secretos.sqlAdminLogin
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el usuario fsh_fase0 (¿base en pausa? vuelve a intentarlo en un minuto).' }
    } finally { Remove-Item Env:\FSH_SQL_ADMIN_PASSWORD -ErrorAction SilentlyContinue }
    $sqlConn = ($userJson | ConvertFrom-Json).connection_string

    Write-Host '3/5 App settings de la Static Web App...' -ForegroundColor Cyan
    $cosmosEndpoint = Invoke-Az cosmosdb show -g $ResourceGroup -n $estado.cosmosAccountName --query documentEndpoint -o tsv
    $cosmosKey = Invoke-Az cosmosdb keys list -g $ResourceGroup -n $estado.cosmosAccountName --query primaryMasterKey -o tsv
    Invoke-Az staticwebapp appsettings set -n $estado.swaName -g $ResourceGroup --setting-names `
        "SQL_CONNECTION_STRING=$sqlConn" "COSMOS_ENDPOINT=$cosmosEndpoint" "COSMOS_KEY=$cosmosKey" "COSMOS_DATABASE=frasohome" -o none | Out-Null
} else {
    $estado = Read-Estado
}

Write-Host '4/5 Empaquetado de la función (dependencias Linux, Python 3.11) y publicación...' -ForegroundColor Cyan
$build = Join-Path $LocalDir 'build'
if (Test-Path $build) { Remove-Item $build -Recurse -Force }
New-Item -ItemType Directory -Force -Path $build | Out-Null
Copy-Item (Join-Path $Fase0Dir 'app') (Join-Path $build 'app') -Recurse
Copy-Item (Join-Path $Fase0Dir 'api') (Join-Path $build 'api') -Recurse
$site = Join-Path $build 'api\.python_packages\lib\site-packages'
& $venvPy -m pip install --quiet --disable-pip-version-check -r (Join-Path $build 'api\requirements.txt') --target $site `
    --platform manylinux_2_28_x86_64 --platform manylinux2014_x86_64 --platform manylinux_2_17_x86_64 `
    --only-binary=:all: --python-version 3.11 --implementation cp --upgrade
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron descargar las dependencias para Linux.' }

# El token va por variable de entorno, no en la línea de comandos.
$env:SWA_CLI_DEPLOYMENT_TOKEN = Invoke-Az staticwebapp secrets list -n $estado.swaName -g $estado.resourceGroup --query properties.apiKey -o tsv
try {
    & npx -y $SwaCli deploy (Join-Path $build 'app') --api-location (Join-Path $build 'api') --api-language python --api-version 3.11 --env production
    if ($LASTEXITCODE -ne 0) { throw 'La publicación con la CLI de Static Web Apps falló. Alternativa: github-actions-fase0.yml (ver README).' }
} finally { Remove-Item Env:\SWA_CLI_DEPLOYMENT_TOKEN -ErrorAction SilentlyContinue }

Write-Host '5/5 Comprobaciones contra la URL publicada...' -ForegroundColor Cyan
Start-Sleep -Seconds 20
$url = "https://$($estado.swaHostname)"
& $venvPy (Join-Path $Fase0Dir 'comprobar_despliegue.py') --url $url --json (Join-Path $LocalDir 'resultados.json')
$ok = ($LASTEXITCODE -eq 0)
Write-Host ''
Write-Host "Web de prueba: $url" -ForegroundColor Cyan
Write-Host 'Abre la página y pulsa los tres botones: confirma la cookie en un navegador real.'
if (-not $ok) { Write-Host 'Alguna comprobación falla: el detalle está en .local\fase0\resultados.json' -ForegroundColor Yellow; exit 1 }
