<#
.SYNOPSIS
  FraSoHome Live · fase 3 · prepara Azure para la API: usuario de base de datos, app settings y usuarios de demo.

.DESCRIPTION
  0. Aplica sql\03_procedimientos.sql (CREATE OR ALTER) sin tocar los datos.
  1. Crea (o renueva la contraseña de) el usuario contenido fsh_api con permisos mínimos:
     SELECT y EXECUTE sobre los esquemas de FraSoHome Live (las escrituras van por procedimientos).
  2. Guarda su cadena de conexión en .local\frasohome-live\secretos_api.json (Git lo ignora),
     para usuarios.ps1.
  3. Configura las app settings de la Static Web App: SQL_CONNECTION_STRING (fsh_api),
     COSMOS_ENDPOINT, COSMOS_KEY y COSMOS_DATABASE.
  4. Crea los usuarios de demostración (uno por rol y doce clientes) si no existen, salvo con
     -SinUsuariosDemo. Las contraseñas temporales se muestran una sola vez; con -GuardarDemo se
     escriben además en .local\frasohome-live\usuarios_demo.txt.

  Se puede repetir: renueva la contraseña de fsh_api y vuelve a escribir las app settings.
  Después, publica con .\desplegar_api.ps1.

.EXAMPLE
  .\configurar_api.ps1
  .\configurar_api.ps1 -SinUsuariosDemo
#>
param(
    [switch]$SinUsuariosDemo,
    [switch]$GuardarDemo,
    [string]$IpPublica
)

. (Join-Path $PSScriptRoot '..\infra\comun.ps1')
$ToolsDir = $PSScriptRoot
$ScenarioDir = Split-Path $ToolsDir

$acc = Assert-AzLogin
$estado = Read-Estado
$secretos = Read-JsonFile (Join-Path $RepoRoot '.local\fase0\secretos.json')
if (-not $secretos) { throw 'No encuentro .local\fase0\secretos.json con la contraseña del administrador SQL (lo crea la fase 0).' }
Write-Host "Suscripción: $($acc.name) · SQL: $($estado.sqlServerName) · web: $($estado.swaName)" -ForegroundColor Cyan

Write-Host '1/5 Entorno de Python y firewall...' -ForegroundColor Cyan
$venvPy = Initialize-Venv @((Join-Path $ScenarioDir 'seed\requirements.txt'))
$ip = Set-SqlFirewallForMe $estado $IpPublica
Write-Host "    Regla equipo-carga: $ip"

Write-Host '2/5 Procedimientos almacenados (sin tocar los datos)...' -ForegroundColor Cyan
$env:FSH_SQL_CONNECTION_STRING = "Server=tcp:$($estado.sqlServerFqdn),1433;Database=frasohome-oltp;UID=$($secretos.sqlAdminLogin);PWD=$($secretos.sqlAdminPassword);Encrypt=yes;TrustServerCertificate=no;ConnectRetryCount=3;ConnectRetryInterval=10"
$env:PYTHONIOENCODING = 'utf-8'
try {
    $prevPref = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { & $venvPy (Join-Path $ScenarioDir 'seed\load_sql.py') --solo-procedimientos | Out-Host; $code = $LASTEXITCODE }
    finally { $ErrorActionPreference = $prevPref }
    if ($code -ne 0) { throw 'No se pudieron aplicar los procedimientos.' }
} finally { Remove-Item Env:\FSH_SQL_CONNECTION_STRING -ErrorAction SilentlyContinue }

Write-Host '3/5 Usuario de base de datos fsh_api...' -ForegroundColor Cyan
$env:FSH_SQL_ADMIN_PASSWORD = $secretos.sqlAdminPassword
try {
    $prevPref = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { $json = & $venvPy (Join-Path $ToolsDir 'crear_usuario_api.py') --server $estado.sqlServerFqdn --admin-login $secretos.sqlAdminLogin }
    finally { $ErrorActionPreference = $prevPref }
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el usuario fsh_api (¿base en pausa? vuelve a intentarlo en un minuto).' }
} finally { Remove-Item Env:\FSH_SQL_ADMIN_PASSWORD -ErrorAction SilentlyContinue }
$api = ($json -join "`n") | ConvertFrom-Json
Save-Json ([pscustomobject]@{ sqlUser = $api.user; connectionString = $api.connection_string }) (Join-Path $LocalDir 'secretos_api.json')
Write-Host "    fsh_api ve $($api.clientes_visibles) clientes. Cadena guardada en .local\frasohome-live\secretos_api.json"

Write-Host '4/5 App settings de la Static Web App...' -ForegroundColor Cyan
$cosmosKey = Invoke-Az cosmosdb keys list -g $estado.resourceGroup -n $estado.cosmosAccountName --type keys --query primaryMasterKey -o tsv
Invoke-Az staticwebapp appsettings set -n $estado.swaName -g $estado.resourceGroup --setting-names `
    "SQL_CONNECTION_STRING=$($api.connection_string)" "COSMOS_ENDPOINT=$($estado.cosmosEndpoint)" `
    "COSMOS_KEY=$($cosmosKey.Trim())" "COSMOS_DATABASE=frasohome" -o none | Out-Null
Write-Host '    SQL_CONNECTION_STRING, COSMOS_ENDPOINT, COSMOS_KEY, COSMOS_DATABASE'

if ($SinUsuariosDemo) {
    Write-Host '5/5 Usuarios de demo: omitido.' -ForegroundColor Cyan
} else {
    Write-Host '5/5 Usuarios de demostración...' -ForegroundColor Cyan
    $demoArgs = @('demo'); if ($GuardarDemo) { $demoArgs += '--guardar' }
    $env:SQL_CONNECTION_STRING = $api.connection_string
    try {
        $prevPref = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
        try { & $venvPy (Join-Path $ToolsDir 'users.py') @demoArgs | Out-Host; $code = $LASTEXITCODE } finally { $ErrorActionPreference = $prevPref }
        if ($code -ne 0) { throw 'No se pudieron crear los usuarios de demo.' }
    } finally { Remove-Item Env:\SQL_CONNECTION_STRING -ErrorAction SilentlyContinue }
}

Write-Host ''
Write-Host 'Azure listo para la API. Siguiente paso: .\desplegar_api.ps1' -ForegroundColor Green
