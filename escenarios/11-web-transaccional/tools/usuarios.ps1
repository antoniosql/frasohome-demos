<#
.SYNOPSIS
  FraSoHome Live · gestiona los usuarios de la web en Azure (envoltorio de tools\users.py).

.DESCRIPTION
  Pasa los argumentos tal cual a users.py, con la conexión del usuario fsh_api que guardó
  configurar_api.ps1 y el firewall de SQL abierto a tu IP.

.EXAMPLE
  .\usuarios.ps1 list
  .\usuarios.ps1 add --login cajero.coruna --nombre "Caja A Coruña" --rol cajero --rol empleado --tienda S001 --empleado FSH0040
  .\usuarios.ps1 reset --login cajero.coruna
  .\usuarios.ps1 disable --login cajero.coruna
  .\usuarios.ps1 demo
#>
# Sin bloque param: así opciones como --login llegan intactas a users.py.

. (Join-Path $PSScriptRoot '..\infra\comun.ps1')

Assert-AzLogin | Out-Null
$estado = Read-Estado
$api = Read-JsonFile (Join-Path $LocalDir 'secretos_api.json')
if (-not $api) { throw 'Falta .local\frasohome-live\secretos_api.json: ejecuta antes .\configurar_api.ps1.' }
$venvPy = Initialize-Venv @()
Set-SqlFirewallForMe $estado $null | Out-Null

$env:SQL_CONNECTION_STRING = $api.connectionString
$env:PYTHONIOENCODING = 'utf-8'
try {
    $prevPref = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { & $venvPy (Join-Path $PSScriptRoot 'users.py') @args | Out-Host; $code = $LASTEXITCODE } finally { $ErrorActionPreference = $prevPref }
} finally { Remove-Item Env:\SQL_CONNECTION_STRING -ErrorAction SilentlyContinue }
exit $code
