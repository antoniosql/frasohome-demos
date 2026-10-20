<#
.SYNOPSIS
  FraSoHome Live · fase 1 · prepara el entorno de GitHub Actions del repositorio.

.DESCRIPTION
  Con la CLI de GitHub (gh) y los datos que dejó desplegar_infra.ps1:
    - crea el entorno "frasohome-live" (la credencial federada de Azure solo acepta ese entorno);
    - guarda como variables del entorno AZURE_CLIENT_ID, AZURE_TENANT_ID y AZURE_SUBSCRIPTION_ID
      (identifican, no autentican: sin el token OIDC de este repositorio no sirven de nada);
    - guarda como secretos los datos personales que necesita main.bicepparam: el correo de las
      alertas y el administrador Entra del servidor SQL. El repositorio es público y los secretos
      se enmascaran en los registros de Actions; las variables no.

  Los valores secretos se pasan a gh por la entrada estándar, no en la línea de comandos.

.EXAMPLE
  gh auth login
  .\configurar_github.ps1
#>
param(
    [string]$Repo
)

. (Join-Path $PSScriptRoot 'comun.ps1')

if (-not $Repo) { $Repo = $GithubRepo }
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw 'No encuentro la CLI de GitHub (gh). Instálala: winget install GitHub.cli'
}
Invoke-Quiet gh auth status | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'No hay sesión en GitHub. Ejecuta: gh auth login' }

$estado = Read-Estado
if (-not $estado.githubClientId) { throw 'Falta la identidad de GitHub Actions: ejecuta .\desplegar_infra.ps1 sin -SinGithub.' }
Assert-AzLogin | Out-Null
$me = Invoke-AzJson ad signed-in-user show --query '{id:id, upn:userPrincipalName}'

function Invoke-Gh {
    $prevPref = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { $out = & gh @args 2>&1; $code = $LASTEXITCODE } finally { $ErrorActionPreference = $prevPref }
    if ($code -ne 0) { throw "Falló: gh $($args[0..2] -join ' ')`n$($out -join "`n")" }
}

function Set-GhSecret([string]$Name, [string]$Value) {
    $prevPref = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { $out = $Value | & gh secret set $Name --env $GithubEnvironment -R $Repo 2>&1; $code = $LASTEXITCODE }
    finally { $ErrorActionPreference = $prevPref }
    if ($code -ne 0) { throw "No se pudo guardar el secreto $Name`n$($out -join "`n")" }
}

Write-Host "Repositorio: $Repo · entorno: $GithubEnvironment" -ForegroundColor Cyan

Write-Host '1/3 Entorno...' -ForegroundColor Cyan
Invoke-Gh api -X PUT "repos/$Repo/environments/$GithubEnvironment" --silent

Write-Host '2/3 Variables (identificadores de Azure)...' -ForegroundColor Cyan
$variables = [ordered]@{
    AZURE_CLIENT_ID       = $estado.githubClientId
    AZURE_TENANT_ID       = $estado.tenantId
    AZURE_SUBSCRIPTION_ID = $estado.subscriptionId
    FSH_RESOURCE_GROUP    = $estado.resourceGroup
    FSH_SWA_NAME          = $estado.swaName
}
foreach ($name in $variables.Keys) {
    Invoke-Gh variable set $name --env $GithubEnvironment -R $Repo --body $variables[$name]
    Write-Host "    $name"
}

Write-Host '3/3 Secretos (datos personales para main.bicepparam)...' -ForegroundColor Cyan
Set-GhSecret 'FSH_ALERT_EMAIL' $estado.alertEmail
Set-GhSecret 'FSH_ENTRA_ADMIN_OBJECT_ID' $me.id
Set-GhSecret 'FSH_ENTRA_ADMIN_LOGIN' $me.upn
Write-Host '    FSH_ALERT_EMAIL, FSH_ENTRA_ADMIN_OBJECT_ID, FSH_ENTRA_ADMIN_LOGIN'

Write-Host ''
Write-Host 'GitHub listo.' -ForegroundColor Green
Write-Host "Recomendado: en https://github.com/$Repo/settings/environments añade tu usuario como"
Write-Host 'revisor obligatorio del entorno, para aprobar cada despliegue antes de que toque Azure.'
Write-Host 'Los workflows aparecen en la pestaña Actions cuando están en la rama main.'
