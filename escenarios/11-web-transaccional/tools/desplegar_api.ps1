<#
.SYNOPSIS
  FraSoHome Live · fase 3 · publica la API y la consola en la Static Web App y la comprueba.

.DESCRIPTION
  1. Copia app\ y api\ (sin pruebas) a .local\frasohome-live\build.
  2. Descarga las dependencias de la API para Linux y Python 3.11 (el máximo de las managed
     Functions de SWA) en api\.python_packages.
  3. Publica con la CLI de Static Web Apps; el token se obtiene con tu sesión de az y viaja en
     una variable de entorno.
  4. Lanza tools\comprobar_api.py contra la URL publicada.

  Requisitos: Node.js (npx) y haber ejecutado antes .\configurar_api.ps1.
  Para probar también la sesión completa, define FSH_CHECK_LOGIN y FSH_CHECK_PASSWORD con un
  usuario que ya haya cambiado su contraseña.

.EXAMPLE
  .\desplegar_api.ps1
#>
param(
    [switch]$SinComprobar
)

. (Join-Path $PSScriptRoot '..\infra\comun.ps1')
$ToolsDir = $PSScriptRoot
$ScenarioDir = Split-Path $ToolsDir
$SwaCli = '@azure/static-web-apps-cli@2.0.10'

Assert-AzLogin | Out-Null
$estado = Read-Estado
foreach ($tool in @('node', 'npx')) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { throw 'Necesito Node.js (node y npx) para la CLI de Static Web Apps: https://nodejs.org' }
}

Write-Host '1/4 Copia de app y api...' -ForegroundColor Cyan
$venvPy = Initialize-Venv @()
$build = Join-Path $LocalDir 'build'
if (Test-Path $build) { Remove-Item $build -Recurse -Force }
New-Item -ItemType Directory -Force -Path $build | Out-Null
Copy-Item (Join-Path $ScenarioDir 'app') (Join-Path $build 'app') -Recurse
Copy-Item (Join-Path $ScenarioDir 'api') (Join-Path $build 'api') -Recurse
foreach ($junk in @('tests', '.pytest_cache', '.python_packages')) {
    $p = Join-Path $build "api\$junk"
    if (Test-Path $p) { Remove-Item $p -Recurse -Force }
}
Get-ChildItem (Join-Path $build 'api') -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force

Write-Host '2/4 Dependencias para Linux y Python 3.11...' -ForegroundColor Cyan
$site = Join-Path $build 'api\.python_packages\lib\site-packages'
Invoke-Quiet $venvPy -m pip install --quiet --disable-pip-version-check -r (Join-Path $build 'api\requirements.txt') --target $site `
    --platform manylinux_2_28_x86_64 --platform manylinux2014_x86_64 --platform manylinux_2_17_x86_64 `
    --only-binary=:all: --python-version 3.11 --implementation cp --upgrade | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron descargar las dependencias para Linux.' }

Write-Host '3/4 Publicación...' -ForegroundColor Cyan
$env:SWA_CLI_DEPLOYMENT_TOKEN = Invoke-Az staticwebapp secrets list -n $estado.swaName -g $estado.resourceGroup --query properties.apiKey -o tsv
try {
    $prevPref = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try {
        & npx -y $SwaCli deploy (Join-Path $build 'app') --api-location (Join-Path $build 'api') --api-language python `
            --api-version 3.11 --env production | Out-Host
        $code = $LASTEXITCODE
    } finally { $ErrorActionPreference = $prevPref }
    if ($code -ne 0) { throw 'La publicación con la CLI de Static Web Apps falló.' }
} finally { Remove-Item Env:\SWA_CLI_DEPLOYMENT_TOKEN -ErrorAction SilentlyContinue }

if ($SinComprobar) { Write-Host 'Publicada. Comprobaciones omitidas.' -ForegroundColor Green; return }

Write-Host '4/4 Comprobaciones contra la URL publicada...' -ForegroundColor Cyan
Start-Sleep -Seconds 20
$url = "https://$($estado.swaHostname)"
$prevPref = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
try {
    & $venvPy (Join-Path $ToolsDir 'comprobar_api.py') --url $url --json (Join-Path $LocalDir 'comprobar_api.json') | Out-Host
    $ok = ($LASTEXITCODE -eq 0)
} finally { $ErrorActionPreference = $prevPref }
Write-Host ''
Write-Host "Consola de la API: $url" -ForegroundColor Cyan
if (-not $ok) { Write-Host 'Alguna comprobación falla: detalle en .local\frasohome-live\comprobar_api.json' -ForegroundColor Yellow; exit 1 }
