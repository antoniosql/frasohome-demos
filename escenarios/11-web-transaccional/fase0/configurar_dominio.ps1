<#
.SYNOPSIS
  FraSoHome Live · fase 0 · dominio frasohome.dataging.com en la Static Web App.

.DESCRIPTION
  Los DNS de dataging.com están en Cloudflare. Antes de ejecutar este script, crea en Cloudflare:
    Tipo CNAME · Nombre frasohome · Destino <nombre>.azurestaticapps.net · Proxy DESACTIVADO (nube gris, "DNS only")
  Con el proxy activado, Azure no puede validar el dominio ni emitir el certificado.

  El script comprueba el CNAME con DNS sobre HTTPS, lo enlaza en la Static Web App, espera a que
  el certificado esté listo y repite las comprobaciones de la fase 0 contra el dominio propio.

.EXAMPLE
  .\configurar_dominio.ps1
#>
param([string]$Dominio = 'frasohome.dataging.com')

. (Join-Path $PSScriptRoot 'comun.ps1')
Assert-AzLogin | Out-Null
$estado = Read-Estado
$target = $estado.swaHostname.TrimEnd('.')

$dns = Invoke-RestMethod -Uri "https://dns.google/resolve?name=$Dominio&type=CNAME" -TimeoutSec 20
$cname = @($dns.Answer | Where-Object { $_.type -eq 5 } | ForEach-Object { $_.data.TrimEnd('.') })
if ($cname.Count -eq 0) {
    Write-Host "No existe el CNAME de $Dominio." -ForegroundColor Yellow
    Write-Host "Créalo en Cloudflare: CNAME  frasohome  ->  $target  (proxy desactivado, solo DNS)"
    exit 1
}
if ($cname[0] -ne $target) {
    Write-Host "El CNAME apunta a $($cname[0]) y debería apuntar a $target." -ForegroundColor Yellow
    exit 1
}
Write-Host "CNAME correcto: $Dominio -> $target" -ForegroundColor Green

Invoke-Quiet az staticwebapp hostname show -n $estado.swaName -g $estado.resourceGroup --hostname $Dominio -o none | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Enlazando el dominio en la Static Web App (validación por CNAME)...' -ForegroundColor Cyan
    Invoke-Az staticwebapp hostname set -n $estado.swaName -g $estado.resourceGroup --hostname $Dominio --no-wait -o none | Out-Null
}

for ($i = 0; $i -lt 40; $i++) {
    $h = Invoke-AzJson staticwebapp hostname show -n $estado.swaName -g $estado.resourceGroup --hostname $Dominio
    Write-Host "  estado: $($h.status)"
    if ($h.status -eq 'Ready') { break }
    if ($h.status -eq 'Failed') { throw "La validación falló: $($h.errorMessage)" }
    Start-Sleep -Seconds 30
}
if ($h.status -ne 'Ready') { throw 'El dominio sigue sin estar listo; vuelve a lanzar el script en unos minutos.' }

$python = Get-PythonCommand
$pyExe = $python[0]; $pyArgs = @(); if ($python.Count -gt 1) { $pyArgs = $python[1..($python.Count - 1)] }
& $pyExe @pyArgs (Join-Path $Fase0Dir 'comprobar_despliegue.py') --url "https://$Dominio" --json (Join-Path $LocalDir 'resultados-dominio.json')
exit $LASTEXITCODE
