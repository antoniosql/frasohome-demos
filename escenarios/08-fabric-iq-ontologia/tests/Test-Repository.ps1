[CmdletBinding()]
param(
    [string]$DataRoot = ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\..\..\datos")))
)

Set-StrictMode -Version 1.0
$ErrorActionPreference = "Stop"

$demoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$modelPath = Join-Path $demoRoot "fabric\ontology\ontology-model.json"
$manifestPath = Join-Path $demoRoot "fabric\data\source-manifest.json"
$prepareNotebookPath = Join-Path $demoRoot "fabric\notebooks\FraSoHome_IQ_01_Prepare.py"

Import-Module (Join-Path $demoRoot "scripts\OntologyDefinition.psm1") -Force

$model = Get-Content -LiteralPath $modelPath -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 100
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 100
$validation = Test-FraSoHomeOntologyModel -Model $model

$dummyWorkspace = "11111111-1111-1111-1111-111111111111"
$dummyLakehouse = "22222222-2222-2222-2222-222222222222"
$seenIds = [Collections.Generic.HashSet[string]]::new()

foreach ($stage in 1..6) {
    $definition = New-FraSoHomeOntologyDefinition -Model $model -Stage $stage -WorkspaceId $dummyWorkspace -LakehouseId $dummyLakehouse -DisplayName "FraSoHome_Context"
    $expectedEntities = @($model.entities | Where-Object { [int]$_.stage -le $stage }).Count
    $expectedRelationships = @($model.relationships | Where-Object { [int]$_.stage -le $stage }).Count
    $expectedParts = 2 + (2 * $expectedEntities) + (2 * $expectedRelationships)
    if ($definition.parts.Count -ne $expectedParts) {
        throw "Etapa ${stage}: $($definition.parts.Count) partes; se esperaban $expectedParts."
    }

    $paths = @($definition.parts.path)
    if (($paths | Sort-Object -Unique).Count -ne $paths.Count) {
        throw "Etapa ${stage}: hay rutas de definición duplicadas."
    }

    foreach ($part in $definition.parts) {
        $decoded = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String([string]$part.payload))
        $json = $decoded | ConvertFrom-Json -Depth 100
        if ($part.path -match "/definition.json$" -and $json.id) {
            if (-not $seenIds.Add([string]$json.id) -and $stage -eq 1) {
                throw "ID duplicado en la definición: $($json.id)."
            }
        }
    }
}

$notebookText = Get-Content -LiteralPath $prepareNotebookPath -Raw -Encoding UTF8
foreach ($entity in $model.entities) {
    if ($notebookText -notmatch [Regex]::Escape([string]$entity.table)) {
        throw "La tabla de entidad $($entity.table) no aparece en el notebook."
    }
}
foreach ($relationship in $model.relationships) {
    if ($notebookText -notmatch [Regex]::Escape([string]$relationship.table)) {
        throw "La tabla de relación $($relationship.table) no aparece en el notebook."
    }
}

$sourceAudit = [System.Collections.Generic.List[object]]::new()
foreach ($source in $manifest.sources) {
    $path = Join-Path $DataRoot ([string]$source.relativePath)
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Falta la fuente $path."
    }
    $rows = @(Import-Csv -LiteralPath $path -Encoding UTF8)
    $key = @($source.primaryKey)
    $duplicateCount = 0
    if ($key.Count -gt 0) {
        $duplicateCount = @(
            $rows | Group-Object -Property $key | Where-Object { $_.Count -gt 1 }
        ).Count
    }
    $sourceAudit.Add([pscustomobject]@{
        Source          = [string]$source.file
        Rows            = $rows.Count
        DuplicateGroups = $duplicateCount
    })
}

[pscustomobject]@{
    Status            = "OK"
    Entities          = $validation.EntityCount
    Relationships     = $validation.RelationshipCount
    Properties        = $validation.PropertyCount
    ProgressiveStages = 6
    Sources           = @($sourceAudit)
}
