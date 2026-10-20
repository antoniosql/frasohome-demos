<#
.SYNOPSIS
  FraSoHome Live · fase 1 · despliega la infraestructura como código desde tu equipo.

.DESCRIPTION
  1. Muestra el what-if de main.bicep sobre rg-frasohome-live y pide confirmación.
  2. Despliega main.bicep: adopta los recursos de la fase 0 (mismos nombres), crea los 9
     contenedores de Cosmos DB, el grupo de acciones por correo y las dos alertas de métrica.
  3. Crea el presupuesto mensual de 1 (presupuesto.bicep) si no existe todavía.
  4. Crea la identidad de GitHub Actions con credencial federada (github-oidc.bicep).
  5. Guarda los nombres y los identificadores en .local\frasohome-live\estado.json.

  No cambia la contraseña del administrador SQL ni las app settings de la Static Web App.
  Es idempotente: se puede volver a lanzar.

.EXAMPLE
  .\desplegar_infra.ps1 -AlertEmail tu@correo.com
  .\desplegar_infra.ps1 -SoloWhatIf          # muestra los cambios y no toca nada
#>
param(
    [string]$ResourceGroup = 'rg-frasohome-live',
    [string]$AlertEmail,
    [switch]$SoloWhatIf,
    [switch]$SinPresupuesto,
    [switch]$SinGithub,
    [switch]$Force
)

. (Join-Path $PSScriptRoot 'comun.ps1')

$acc = Assert-AzLogin
New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null
$previo = Read-JsonFile $EstadoFile
$fase0 = Read-JsonFile $Fase0EstadoFile

$rgExists = Invoke-Az group exists -n $ResourceGroup
if ($rgExists.Trim() -ne 'true') {
    throw "No existe el grupo de recursos $ResourceGroup. La fase 0 lo crea (fase0\desplegar.ps1) junto con el servidor SQL y su contraseña."
}

$me = Invoke-AzJson ad signed-in-user show --query '{id:id, upn:userPrincipalName, mail:mail}'
if (-not $AlertEmail -and $previo -and $previo.alertEmail) { $AlertEmail = $previo.alertEmail }
if (-not $AlertEmail -and $me.mail) { $AlertEmail = $me.mail }
if (-not $AlertEmail) { $AlertEmail = Read-Host 'Correo para las alertas' }
if ($AlertEmail -notmatch '^[^@\s]+@[^@\s]+\.[^@\s]+$') { throw "Correo no válido: $AlertEmail" }

Write-Host "Suscripción: $($acc.name) · grupo: $ResourceGroup · alertas a: $AlertEmail" -ForegroundColor Cyan

# main.bicepparam lee de aquí los datos personales, que no se guardan en el repositorio.
$env:FSH_ENTRA_ADMIN_OBJECT_ID = $me.id
$env:FSH_ENTRA_ADMIN_LOGIN = $me.upn
$env:FSH_ALERT_EMAIL = $AlertEmail
$paramFile = Join-Path $InfraDir 'main.bicepparam'
try {
    Write-Host '1/4 Cambios previstos (what-if)...' -ForegroundColor Cyan
    $code = Invoke-AzLive deployment group what-if -g $ResourceGroup -n frasohome-live-infra -p $paramFile
    if ($code -ne 0) { throw 'El what-if falló: revisa el mensaje de arriba.' }
    if ($SoloWhatIf) { Write-Host 'Solo what-if: no se ha cambiado nada.' -ForegroundColor Yellow; return }

    Write-Host ''
    Write-Host 'Revisa que no haya ningún "Delete" ni cambios en la base de datos o en las cuentas que no esperes.' -ForegroundColor Yellow
    if (-not $Force) {
        $answer = Read-Host 'Escribe "desplegar" para aplicar los cambios'
        if ($answer -ne 'desplegar') { throw 'Cancelado: no se ha cambiado nada.' }
    }

    Write-Host '2/4 Despliegue de main.bicep (tarda unos minutos)...' -ForegroundColor Cyan
    try {
        $outputs = Invoke-AzJson deployment group create -g $ResourceGroup -n frasohome-live-infra -p $paramFile --query properties.outputs
    } catch {
        Write-Host $_.Exception.Message -ForegroundColor Red
        Show-FailedOperations $ResourceGroup 'frasohome-live-infra'
        throw 'El despliegue de main.bicep falló: mira el código y el mensaje de arriba.'
    }
} finally {
    Remove-Item Env:\FSH_ENTRA_ADMIN_OBJECT_ID, Env:\FSH_ENTRA_ADMIN_LOGIN, Env:\FSH_ALERT_EMAIL -ErrorAction SilentlyContinue
}

if ($fase0 -and $fase0.sqlServerName -and $fase0.sqlServerName -ne $outputs.sqlServerName.value) {
    Write-Host "Aviso: el servidor SQL de la fase 0 es $($fase0.sqlServerName) y main.bicep usa $($outputs.sqlServerName.value)." -ForegroundColor Yellow
}

$presupuesto = 'no creado'
if ($SinPresupuesto) {
    $presupuesto = 'omitido'
} else {
    Write-Host '3/4 Presupuesto mensual...' -ForegroundColor Cyan
    $budgetUrl = "https://management.azure.com/subscriptions/$($acc.id)/resourceGroups/$ResourceGroup/providers/Microsoft.Consumption/budgets/presupuesto-frasohome-live?api-version=2023-11-01"
    Invoke-Quiet az rest --method get --url $budgetUrl -o none | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $presupuesto = 'ya existía'
        Write-Host '    Ya existe: no se toca (su fecha de inicio no se puede cambiar).'
    } else {
        try {
            Invoke-Az deployment group create -g $ResourceGroup -n frasohome-live-presupuesto `
                -f (Join-Path $InfraDir 'presupuesto.bicep') -p alertEmail=$AlertEmail -o none | Out-Null
            $presupuesto = 'creado'
        } catch {
            # Algunas ofertas (patrocinios, ciertas suscripciones de Visual Studio) no admiten presupuestos.
            Write-Host "    No se pudo crear el presupuesto: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host '    Las alertas de cuota de SQL y de RU de Cosmos siguen activas. Puedes crearlo en Cost Management a mano.' -ForegroundColor Yellow
        }
    }
}

$github = $null
if (-not $SinGithub) {
    Write-Host '4/4 Identidad de GitHub Actions (OIDC, sin secretos de Azure)...' -ForegroundColor Cyan
    try {
        $github = Invoke-AzJson deployment group create -g $ResourceGroup -n frasohome-live-github `
            -f (Join-Path $InfraDir 'github-oidc.bicep') -p githubRepo=$GithubRepo githubEnvironment=$GithubEnvironment `
            --query properties.outputs
    } catch {
        Write-Host $_.Exception.Message -ForegroundColor Red
        Show-FailedOperations $ResourceGroup 'frasohome-live-github'
        throw 'No se pudo crear la identidad de GitHub Actions (hace falta ser propietario del grupo de recursos para asignar el rol).'
    }
}

$estado = [ordered]@{
    subscriptionId    = $acc.id
    tenantId          = $acc.tenantId
    resourceGroup     = $ResourceGroup
    alertEmail        = $AlertEmail
    sqlServerName     = $outputs.sqlServerName.value
    sqlServerFqdn     = $outputs.sqlServerFqdn.value
    sqlDatabaseId     = $outputs.sqlDatabaseId.value
    cosmosAccountName = $outputs.cosmosAccountName.value
    cosmosEndpoint    = $outputs.cosmosEndpoint.value
    cosmosContainers  = $outputs.cosmosContainers.value
    swaName           = $outputs.swaName.value
    swaHostname       = $outputs.swaHostname.value
    presupuesto       = $presupuesto
    githubRepo        = $GithubRepo
    githubEnvironment = $GithubEnvironment
    githubClientId    = $null
    deployedAt        = (Get-Date).ToUniversalTime().ToString('s')
}
if ($github) { $estado.githubClientId = $github.clientId.value }
elseif ($previo -and $previo.githubClientId) { $estado.githubClientId = $previo.githubClientId }
Save-Json ([pscustomobject]$estado) $EstadoFile

Write-Host ''
Write-Host 'Infraestructura desplegada.' -ForegroundColor Green
Write-Host "  Contenedores Cosmos: $($estado.cosmosContainers -join ', ')"
Write-Host "  Presupuesto: $presupuesto"
Write-Host "  Estado guardado en $EstadoFile"
Write-Host ''
Write-Host 'Azure envía un correo informativo a esa dirección al añadirla al grupo de acciones.'
if ($estado.githubClientId) {
    Write-Host 'Siguiente paso: .\configurar_github.ps1 (crea el entorno frasohome-live y sus variables en GitHub).' -ForegroundColor Cyan
}
