<#
.SYNOPSIS
  FraSoHome Live · fase 0 · consumo de la cuota gratuita de Azure SQL.

.DESCRIPTION
  Lee las métricas de la base gratuita (free_amount_consumed, free_amount_remaining y
  app_cpu_billed) y proyecta el consumo del mes. La cuota son 100.000 segundos de vCore
  al mes: unos 3.300 al día. Úsalo después de una sesión de trabajo normal y otra vez al
  día siguiente sin tocar nada, para comprobar que la base entra en pausa.

.EXAMPLE
  .\medir_cuota.ps1             # últimas 24 horas
  .\medir_cuota.ps1 -Horas 72
#>
param([int]$Horas = 24)

. (Join-Path $PSScriptRoot 'comun.ps1')
Assert-AzLogin | Out-Null
$estado = Read-Estado

$now = (Get-Date).ToUniversalTime()
$start = $now.AddHours(-$Horas).ToString('yyyy-MM-ddTHH:mm:ssZ')
$end = $now.ToString('yyyy-MM-ddTHH:mm:ssZ')

function Get-Series($metric, $aggregation, $interval) {
    $r = Invoke-AzJson monitor metrics list --resource $estado.sqlDatabaseId --metric $metric `
        --aggregation $aggregation --interval $interval --start-time $start --end-time $end
    $field = $aggregation.ToLower()
    return @($r.value[0].timeseries[0].data | Where-Object { $null -ne $_.$field } |
             ForEach-Object { [pscustomobject]@{ Hora = ([datetime]$_.timeStamp).ToLocalTime(); Valor = [double]$_.$field } })
}

$consumed = Get-Series 'free_amount_consumed' 'Maximum' 'PT1H'
$remaining = Get-Series 'free_amount_remaining' 'Minimum' 'PT1H'
$billed = Get-Series 'app_cpu_billed' 'Total' 'PT1H'

if ($consumed.Count -eq 0) { Write-Host 'Todavía no hay métricas (tardan unos minutos en aparecer).' -ForegroundColor Yellow; exit 0 }

$lastConsumed = $consumed[-1].Valor
$lastRemaining = if ($remaining.Count) { $remaining[-1].Valor } else { [double]::NaN }
$windowBilled = ($billed | Measure-Object Valor -Sum).Sum
$activeHours = @($billed | Where-Object { $_.Valor -gt 0 }).Count
$dayOfMonth = $now.Day - 1 + ($now.Hour / 24.0)
$daysInMonth = [datetime]::DaysInMonth($now.Year, $now.Month)
$projection = if ($dayOfMonth -gt 0.1) { $lastConsumed / $dayOfMonth * $daysInMonth } else { [double]::NaN }

Write-Host ''
Write-Host "Base gratuita · últimas $Horas h" -ForegroundColor Cyan
Write-Host ("  Consumido este mes:     {0:N0} s de vCore" -f $lastConsumed)
Write-Host ("  Restante este mes:      {0:N0} s de vCore" -f $lastRemaining)
Write-Host ("  Facturado en la ventana: {0:N0} s de vCore en {1} horas con actividad de {2}" -f $windowBilled, $activeHours, $billed.Count)
Write-Host ("  Proyección a fin de mes: {0:N0} s de 100.000" -f $projection)
Write-Host ''
Write-Host 'Horas con consumo (la base debería pausarse 60 minutos después de la última conexión):'
$billed | Where-Object { $_.Valor -gt 0 } | Format-Table Hora, @{ n = 's vCore'; e = { '{0:N0}' -f $_.Valor } } -AutoSize | Out-String -Width 200 | Write-Host
if ($projection -gt 100000) { Write-Host 'A este ritmo la cuota se agota antes de fin de mes: revisa conexiones abiertas (SSMS, VS Code) y el retardo de pausa.' -ForegroundColor Yellow }
else { Write-Host 'A este ritmo la cuota alcanza para el mes.' -ForegroundColor Green }
