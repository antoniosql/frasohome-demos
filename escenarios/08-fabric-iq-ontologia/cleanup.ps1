[CmdletBinding(SupportsShouldProcess, ConfirmImpact = "High")]
param(
    [string]$StatePath = ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\..\.local\fabric_iq_ontology\deployment-state.json"))),
    [switch]$DeleteReusedItems,
    [switch]$DeleteWorkspace
)

Set-StrictMode -Version 1.0
$ErrorActionPreference = "Stop"

Import-Module (Join-Path $PSScriptRoot "scripts\FabricApi.psm1") -Force

if (-not (Test-Path -LiteralPath $StatePath -PathType Leaf)) {
    throw "No existe el estado de despliegue: $StatePath"
}

$state = Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8 | ConvertFrom-Json
$workspaceId = [string]$state.workspaceId
if (-not $workspaceId) {
    throw "El estado no contiene workspaceId."
}

$token = Get-AzureCliAccessToken -Resource "https://api.fabric.microsoft.com"
$apiRoot = "https://api.fabric.microsoft.com/v1"

$items = @(
    [pscustomobject]@{ Name = "Data Agent"; Id = [string]$state.dataAgentId; Owned = [bool]$state.ownership.dataAgent },
    [pscustomobject]@{ Name = "Ontology"; Id = [string]$state.ontologyId; Owned = [bool]$state.ownership.ontology },
    [pscustomobject]@{ Name = "Validation notebook"; Id = [string]$state.validateNotebookId; Owned = [bool]$state.ownership.validateNotebook },
    [pscustomobject]@{ Name = "Preparation notebook"; Id = [string]$state.prepareNotebookId; Owned = [bool]$state.ownership.prepareNotebook },
    [pscustomobject]@{ Name = "Lakehouse"; Id = [string]$state.lakehouseId; Owned = [bool]$state.ownership.lakehouse }
)

foreach ($item in $items) {
    if (-not $item.Id) {
        continue
    }
    if (-not $item.Owned -and -not $DeleteReusedItems) {
        Write-Host "Conservado por haber sido reutilizado: $($item.Name) [$($item.Id)]"
        continue
    }
    if ($PSCmdlet.ShouldProcess("$($item.Name) [$($item.Id)]", "Eliminar del workspace $workspaceId")) {
        try {
            Invoke-FabricApi -Method DELETE -Uri "$apiRoot/workspaces/$workspaceId/items/$($item.Id)" -Token $token | Out-Null
            Write-Host "Eliminado: $($item.Name)"
        }
        catch {
            Write-Warning "No se pudo eliminar $($item.Name): $($_.Exception.Message)"
        }
    }
}

if ($DeleteWorkspace) {
    $workspaceOwned = [bool]$state.ownership.workspace
    if (-not $workspaceOwned -and -not $DeleteReusedItems) {
        Write-Warning "El workspace fue reutilizado y se conserva. Usa -DeleteReusedItems junto con -DeleteWorkspace solo si deseas eliminarlo expresamente."
    }
    elseif ($PSCmdlet.ShouldProcess("Workspace [$workspaceId]", "Eliminar workspace completo")) {
        Invoke-FabricApi -Method DELETE -Uri "$apiRoot/workspaces/$workspaceId" -Token $token | Out-Null
        Write-Host "Workspace eliminado."
    }
}

if ($PSCmdlet.ShouldProcess($StatePath, "Eliminar estado local")) {
    Remove-Item -LiteralPath $StatePath -Force
}
