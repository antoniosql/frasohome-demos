<#
.SYNOPSIS
  FraSoHome Live · fase 0 · comprobaciones de solo lectura sobre la suscripción.

.DESCRIPTION
  No crea ni cambia nada. Responde a las preguntas que hay que cerrar antes de desplegar:
    1. ¿Hay ya una base Azure SQL gratuita? Si la hay, su región es la única posible.
    2. ¿Hay ya una cuenta Cosmos DB con free tier? Solo se admite una por suscripción.
    3. ¿Dónde están las capacidades de Fabric? La región de datos debería coincidir.
    4. ¿Están registrados los proveedores Microsoft.Sql, Microsoft.DocumentDB y Microsoft.Web?
    5. ¿Cuántas Static Web Apps Free hay? (máximo 10 por suscripción)

.EXAMPLE
  .\comprobar_suscripcion.ps1
  .\comprobar_suscripcion.ps1 -Subscription "Plataformas MSDN"
#>
param([string]$Subscription)

. (Join-Path $PSScriptRoot 'comun.ps1')

$acc = Assert-AzLogin
if ($Subscription) {
    Invoke-Az account set --subscription $Subscription | Out-Null
    $acc = Invoke-AzJson account show
}
Write-Host ''
Write-Host "Suscripción: $($acc.name) ($($acc.id))" -ForegroundColor Cyan
Write-Host "Usuario:     $($acc.user.name)"

# 1. Bases SQL gratuitas
$freeDbs = @()
$dbIds = Invoke-AzJson resource list --resource-type Microsoft.Sql/servers/databases --query '[].id'
foreach ($id in @($dbIds)) {
    if (-not $id) { continue }
    $p = Invoke-AzJson resource show --ids $id --query '{name:name, location:location, free:properties.useFreeLimit, behavior:properties.freeLimitExhaustionBehavior}'
    if ($p.free) { $freeDbs += [pscustomobject]@{ Base = $id.Split('/')[-1]; Servidor = $id.Split('/')[-3]; Region = $p.location; AlAgotar = $p.behavior } }
}
Write-Host ''
Write-Host '1. Bases Azure SQL con la oferta gratuita' -ForegroundColor Cyan
if ($freeDbs.Count -eq 0) { Write-Host '   Ninguna. La región se elige al crear la primera y queda fija para todas.' }
else { $freeDbs | Format-Table -AutoSize | Out-String -Width 200 | Write-Host; Write-Host "   Región ya fijada: $($freeDbs[0].Region) (máximo 10 bases gratuitas por suscripción)." -ForegroundColor Yellow }

# 2. Cosmos DB free tier
$cosmos = @(Invoke-AzJson cosmosdb list --query '[?enableFreeTier].{Cuenta:name, Grupo:resourceGroup, Region:location}')
Write-Host ''
Write-Host '2. Cuentas Cosmos DB con free tier' -ForegroundColor Cyan
if ($cosmos.Count -eq 0 -or -not $cosmos[0]) { Write-Host '   Ninguna: se puede crear la de FraSoHome con free tier.' }
else { $cosmos | Format-Table -AutoSize | Out-String -Width 200 | Write-Host; Write-Host '   Ya existe una: despliega con -SinCosmosFreeTier o reutiliza esa cuenta.' -ForegroundColor Yellow }

# 3. Capacidades de Fabric
$fabric = @(Invoke-AzJson resource list --resource-type Microsoft.Fabric/capacities --query '[].{Capacidad:name, Region:location, Sku:sku.name}')
Write-Host ''
Write-Host '3. Capacidades de Microsoft Fabric en esta suscripción' -ForegroundColor Cyan
if ($fabric.Count -eq 0 -or -not $fabric[0]) { Write-Host '   Ninguna (puede estar en otra suscripción, o ser de prueba: mira la región en el portal de Fabric, Configuración > Acerca de).' }
else { $fabric | Format-Table -AutoSize | Out-String -Width 200 | Write-Host }

# 4. Proveedores
Write-Host ''
Write-Host '4. Proveedores de recursos' -ForegroundColor Cyan
foreach ($ns in @('Microsoft.Sql', 'Microsoft.DocumentDB', 'Microsoft.Web')) {
    $state = Invoke-Az provider show -n $ns --query registrationState -o tsv
    $color = 'Green'; if ($state -ne 'Registered') { $color = 'Yellow' }
    Write-Host ("   {0,-22} {1}" -f $ns, $state) -ForegroundColor $color
    if ($state -ne 'Registered') { Write-Host "   -> az provider register -n $ns" }
}

# 5. Static Web Apps Free
$swas = @(Invoke-AzJson staticwebapp list --query "[?sku.name=='Free'].{App:name, Grupo:resourceGroup, Region:location}")
Write-Host ''
Write-Host '5. Static Web Apps en plan Free' -ForegroundColor Cyan
$n = 0; if ($swas -and $swas[0]) { $n = $swas.Count }
Write-Host "   $n de 10 permitidas."

# Recomendación de región
Write-Host ''
Write-Host 'Región recomendada para SQL y Cosmos' -ForegroundColor Cyan
if ($freeDbs.Count -gt 0) {
    Write-Host "   $($freeDbs[0].Region): la oferta gratuita ya la fijó en esta suscripción." -ForegroundColor Green
} elseif ($fabric.Count -gt 0 -and $fabric[0]) {
    Write-Host "   $($fabric[0].Region): la de tu capacidad de Fabric, para que el mirroring futuro no cruce regiones." -ForegroundColor Green
} else {
    Write-Host '   westeurope: la misma región que la Static Web App, así la función y las bases están en el mismo centro de datos.' -ForegroundColor Green
    Write-Host '   Cámbiala solo si tu capacidad de Fabric (aunque sea de prueba) está en otra región.'
}
Write-Host ''
