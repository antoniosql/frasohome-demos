[CmdletBinding()]
param(
    [string]$ConfigPath = (Join-Path $PSScriptRoot "config.example.json"),
    [int]$Stage = 0,
    [string]$WorkspaceId = "",
    [string]$CapacityId = "",
    [switch]$SkipDataUpload,
    [switch]$SkipNotebookRun,
    [switch]$SkipGraphRefresh,
    [switch]$SkipAgent,
    [switch]$NoPublishAgent,
    [switch]$ValidateOnly
)

Set-StrictMode -Version 1.0
$ErrorActionPreference = "Stop"

$apiRoot = "https://api.fabric.microsoft.com/v1"
$modelPath = Join-Path $PSScriptRoot "fabric\ontology\ontology-model.json"
$sourceManifestPath = Join-Path $PSScriptRoot "fabric\data\source-manifest.json"
$agentInstructionsPath = Join-Path $PSScriptRoot "fabric\agent\instructions.md"
$prepareNotebookPath = Join-Path $PSScriptRoot "fabric\notebooks\FraSoHome_IQ_01_Prepare.py"
$validateNotebookPath = Join-Path $PSScriptRoot "fabric\notebooks\FraSoHome_IQ_02_Validate.py"
$stateDirectory = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\..\.local\fabric_iq_ontology"))
$statePath = Join-Path $stateDirectory "deployment-state.json"
$previousState = if (Test-Path -LiteralPath $statePath -PathType Leaf) {
    Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 100
}
else {
    $null
}

Import-Module (Join-Path $PSScriptRoot "scripts\FabricApi.psm1") -Force
Import-Module (Join-Path $PSScriptRoot "scripts\OntologyDefinition.psm1") -Force

function Read-JsonFile {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "No existe el archivo requerido: $Path"
    }
    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 100
}

function ConvertTo-InlineBase64 {
    param([Parameter(Mandatory)][string]$Text)
    return [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Text))
}

function Test-ResourceOwnership {
    param(
        [Parameter(Mandatory)][string]$Kind,
        [Parameter(Mandatory)][string]$Id,
        [Parameter(Mandatory)][bool]$CreatedThisRun
    )

    if ($CreatedThisRun) {
        return $true
    }
    if (-not $previousState -or -not $previousState.ownership) {
        return $false
    }

    $idProperties = @{
        workspace         = "workspaceId"
        lakehouse         = "lakehouseId"
        prepareNotebook   = "prepareNotebookId"
        validateNotebook  = "validateNotebookId"
        ontology          = "ontologyId"
        dataAgent         = "dataAgentId"
    }
    $idProperty = [string]$idProperties[$Kind]
    if (-not $idProperty) {
        return $false
    }

    $previousId = [string]$previousState.$idProperty
    $previousOwned = [bool]$previousState.ownership.$Kind
    return ($previousId -eq $Id -and $previousOwned)
}

function Test-LocalRepository {
    param(
        [Parameter(Mandatory)][psobject]$Model,
        [Parameter(Mandatory)][psobject]$SourceManifest,
        [Parameter(Mandatory)][string]$DataRoot
    )

    $modelResult = Test-FraSoHomeOntologyModel -Model $Model
    $warnings = [System.Collections.Generic.List[string]]::new()
    $sourceRows = [System.Collections.Generic.List[object]]::new()

    foreach ($source in $SourceManifest.sources) {
        $path = Join-Path $DataRoot ([string]$source.relativePath)
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Falta la fuente requerida: $path"
        }
        $header = Get-Content -LiteralPath $path -TotalCount 1 -Encoding UTF8
        $columns = @($header -split ",")
        $missingColumns = @($source.requiredColumns | Where-Object { $columns -notcontains [string]$_ })
        if ($missingColumns.Count -gt 0) {
            throw "La fuente $($source.file) no contiene: $($missingColumns -join ', ')."
        }
        $actualRows = (Get-Content -LiteralPath $path -Encoding UTF8 | Measure-Object -Line).Lines - 1
        if ($actualRows -ne [int]$source.expectedRows) {
            $warnings.Add("$($source.file): $actualRows filas; el manifiesto observó $($source.expectedRows).")
        }
        $sourceRows.Add([pscustomobject]@{ File = $source.file; Rows = $actualRows; Path = $path })
    }

    foreach ($path in @($prepareNotebookPath, $validateNotebookPath, $agentInstructionsPath)) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Falta el artefacto requerido: $path"
        }
    }

    [pscustomobject]@{
        Model    = $modelResult
        Sources  = @($sourceRows)
        Warnings = @($warnings)
    }
}

function New-NotebookDefinition {
    param(
        [Parameter(Mandatory)][string]$SourcePath,
        [Parameter(Mandatory)][string]$DisplayName,
        [Parameter(Mandatory)][string]$Description
    )

    $platform = [ordered]@{
        '$schema' = "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json"
        metadata = [ordered]@{
            type        = "Notebook"
            displayName = $DisplayName
            description = $Description
        }
        config = [ordered]@{
            version   = "2.0"
            logicalId = Get-StableOntologyGuid -Seed "notebook:$DisplayName"
        }
    }

    return [ordered]@{
        format = "fabricGitSource"
        parts  = @(
            [ordered]@{
                path        = "notebook-content.py"
                payload     = ConvertTo-InlineBase64 -Text (Get-Content -LiteralPath $SourcePath -Raw -Encoding UTF8)
                payloadType = "InlineBase64"
            },
            [ordered]@{
                path        = ".platform"
                payload     = ConvertTo-InlineBase64 -Text ($platform | ConvertTo-Json -Depth 20 -Compress)
                payloadType = "InlineBase64"
            }
        )
    }
}

function Ensure-Notebook {
    param(
        [Parameter(Mandatory)][string]$WorkspaceId,
        [Parameter(Mandatory)][string]$DisplayName,
        [Parameter(Mandatory)][string]$Description,
        [Parameter(Mandatory)][string]$SourcePath,
        [Parameter(Mandatory)][string]$Token
    )

    $definition = New-NotebookDefinition -SourcePath $SourcePath -DisplayName $DisplayName -Description $Description
    $item = Get-FabricItemByName -WorkspaceId $WorkspaceId -Type "Notebook" -DisplayName $DisplayName -Token $Token
    if ($item) {
        Write-Host "Actualizando notebook $DisplayName..."
        $response = Invoke-FabricApi -Method POST -Uri "$apiRoot/workspaces/$WorkspaceId/notebooks/$($item.id)/updateDefinition?updateMetadata=true" -Token $Token -Body @{ definition = $definition }
        Wait-FabricOperation -InitialResponse $response -Token $Token | Out-Null
        $item | Add-Member -NotePropertyName createdThisRun -NotePropertyValue $false -Force
        return $item
    }

    Write-Host "Creando notebook $DisplayName..."
    $response = Invoke-FabricApi -Method POST -Uri "$apiRoot/workspaces/$WorkspaceId/notebooks" -Token $Token -Body @{
        displayName = $DisplayName
        description = $Description
        definition  = $definition
    }
    $created = Wait-FabricOperation -InitialResponse $response -Token $Token
    $item = if ($created.id) {
        $created
    }
    else {
        Get-FabricItemByName -WorkspaceId $WorkspaceId -Type "Notebook" -DisplayName $DisplayName -Token $Token
    }
    if (-not $item.id) {
        throw "No se pudo resolver el notebook $DisplayName."
    }
    $item | Add-Member -NotePropertyName createdThisRun -NotePropertyValue $true -Force
    return $item
}

function Start-NotebookAndWait {
    param(
        [Parameter(Mandatory)][string]$WorkspaceId,
        [Parameter(Mandatory)][string]$NotebookId,
        [Parameter(Mandatory)][string]$LakehouseId,
        [Parameter(Mandatory)][string]$Token
    )

    $body = [ordered]@{
        executionData = [ordered]@{
            compute              = "Spark"
            computeConfiguration = [ordered]@{
                defaultLakehouse = [ordered]@{
                    referenceType = "ById"
                    itemId        = $LakehouseId
                    workspaceId   = $WorkspaceId
                }
            }
        }
    }
    $response = Invoke-FabricApi -Method POST -Uri "$apiRoot/workspaces/$WorkspaceId/notebooks/$NotebookId/jobs/execute/instances?beta=false" -Token $Token -Body $body
    return Wait-FabricOperation -InitialResponse $response -Token $Token -TimeoutSeconds 3600
}

function Find-OntologyGraphModel {
    param(
        [Parameter(Mandatory)][string]$WorkspaceId,
        [Parameter(Mandatory)][string]$OntologyId,
        [Parameter(Mandatory)][string]$OntologyName,
        [Parameter(Mandatory)][string]$Token
    )

    foreach ($direction in @("downstream", "upstream")) {
        try {
            $response = Invoke-FabricApi -Method GET -Uri "$apiRoot/workspaces/$WorkspaceId/items/$OntologyId/relations/$direction`?beta=true" -Token $Token
            $graph = @($response.Body.items) | Where-Object { $_.type -eq "GraphModel" } | Select-Object -First 1
            if ($graph) {
                return $graph
            }
        }
        catch {
            Write-Verbose "No se pudo consultar la relación $direction de la ontología: $($_.Exception.Message)"
        }
    }

    $graphs = [System.Collections.Generic.List[object]]::new()
    $uri = "$apiRoot/workspaces/$WorkspaceId/items?type=GraphModel"
    while ($uri) {
        $response = Invoke-FabricApi -Method GET -Uri $uri -Token $Token
        foreach ($item in @($response.Body.value)) {
            $graphs.Add($item)
        }
        $uri = [string]$response.Body.continuationUri
    }
    $nameMatch = @($graphs) | Where-Object { $_.displayName -like "*$OntologyName*" } | Select-Object -First 1
    return $nameMatch
}

function Get-AgentDatasourceElements {
    param(
        [Parameter(Mandatory)][string]$WorkspaceId,
        [Parameter(Mandatory)][string]$AgentId,
        [Parameter(Mandatory)][string]$DatasourceId,
        [Parameter(Mandatory)][string]$Token,
        [string]$RootId = ""
    )

    $query = if ($RootId) { "?rootId=$([Uri]::EscapeDataString($RootId))" } else { "" }
    $uri = "$apiRoot/workspaces/$WorkspaceId/dataAgents/$AgentId/staging/datasources/$DatasourceId/elements$query"
    $all = [System.Collections.Generic.List[object]]::new()
    while ($uri) {
        $response = Invoke-FabricApi -Method GET -Uri $uri -Token $Token
        foreach ($element in @($response.Body.value)) {
            $all.Add($element)
        }
        $uri = [string]$response.Body.continuationUri
    }
    return @($all)
}

function Select-AgentOntologyEntities {
    param(
        [Parameter(Mandatory)][string]$WorkspaceId,
        [Parameter(Mandatory)][string]$AgentId,
        [Parameter(Mandatory)][string]$DatasourceId,
        [Parameter(Mandatory)][string]$Token,
        [Parameter(Mandatory)][hashtable]$Descriptions
    )

    $visited = [Collections.Generic.HashSet[string]]::new()
    $queue = [Collections.Generic.Queue[string]]::new()
    $queue.Enqueue("")
    $selected = 0

    while ($queue.Count -gt 0) {
        $rootId = $queue.Dequeue()
        $elements = Get-AgentDatasourceElements -WorkspaceId $WorkspaceId -AgentId $AgentId -DatasourceId $DatasourceId -Token $Token -RootId $rootId
        foreach ($element in $elements) {
            if (-not $visited.Add([string]$element.id)) {
                continue
            }
            if ([bool]$element.hasSubElements) {
                $queue.Enqueue([string]$element.id)
            }
            if ([string]$element.type -eq "Entity") {
                $body = [ordered]@{ isSelected = $true }
                if ($Descriptions.ContainsKey([string]$element.displayName)) {
                    $body.description = $Descriptions[[string]$element.displayName]
                }
                $elementId = [Uri]::EscapeDataString([string]$element.id)
                Invoke-FabricApi -Method PATCH -Uri "$apiRoot/workspaces/$WorkspaceId/dataAgents/$AgentId/staging/datasources/$DatasourceId/elements?id=$elementId" -Token $Token -Body $body | Out-Null
                $selected++
            }
        }
    }
    return $selected
}

$config = Read-JsonFile -Path (Resolve-Path -LiteralPath $ConfigPath)
$model = Read-JsonFile -Path $modelPath
$sourceManifest = Read-JsonFile -Path $sourceManifestPath
$effectiveStage = if ($Stage -gt 0) { $Stage } else { [int]$config.deployment.stage }
if ($effectiveStage -lt 1 -or $effectiveStage -gt 6) {
    throw "Stage debe estar entre 1 y 6."
}

$configuredDataRoot = [string]$config.dataRoot
$dataRoot = if ([IO.Path]::IsPathRooted($configuredDataRoot)) {
    $configuredDataRoot
}
else {
    [IO.Path]::GetFullPath((Join-Path $PSScriptRoot $configuredDataRoot))
}

$validation = Test-LocalRepository -Model $model -SourceManifest $sourceManifest -DataRoot $dataRoot
Write-Host "Validación local: $($validation.Model.EntityCount) entidades, $($validation.Model.RelationshipCount) relaciones y $($validation.Model.PropertyCount) propiedades."
foreach ($warning in $validation.Warnings) {
    Write-Warning $warning
}

if ($ValidateOnly) {
    Write-Host "Repositorio válido. No se ha realizado ninguna llamada a Fabric."
    return
}

$fabricToken = Get-AzureCliAccessToken -Resource "https://api.fabric.microsoft.com"
$effectiveWorkspaceId = if ($WorkspaceId) { $WorkspaceId } else { [string]$config.workspace.id }
$effectiveCapacityId = if ($CapacityId) { $CapacityId } else { [string]$config.workspace.capacityId }
$workspaceName = [string]$config.workspace.displayName
$workspaceCreatedThisRun = $false

if (-not $effectiveWorkspaceId) {
    $workspace = Get-FabricWorkspaceByName -DisplayName $workspaceName -Token $fabricToken
    if (-not $workspace) {
        if (-not $effectiveCapacityId) {
            throw "Indica workspace.id o capacityId en config.local.json. La creación automática de un workspace requiere capacidad."
        }
        Write-Host "Creando workspace $workspaceName..."
        $workspaceResponse = Invoke-FabricApi -Method POST -Uri "$apiRoot/workspaces" -Token $fabricToken -Body @{
            displayName = $workspaceName
            description = "Demo FraSoHome de ontología, grafo y agente en Microsoft Fabric."
            capacityId  = $effectiveCapacityId
        }
        $workspace = $workspaceResponse.Body
        $workspaceCreatedThisRun = $true
    }
    $effectiveWorkspaceId = [string]$workspace.id
}

if (-not $effectiveWorkspaceId) {
    throw "No se pudo resolver el workspace de destino."
}

$workspaceInfo = (Invoke-FabricApi -Method GET -Uri "$apiRoot/workspaces/$effectiveWorkspaceId`?preferWorkspaceSpecificEndpoints=true" -Token $fabricToken).Body
Write-Host "Workspace: $($workspaceInfo.displayName) [$effectiveWorkspaceId]"

$lakehouseName = [string]$config.items.lakehouse
$lakehouse = Get-FabricItemByName -WorkspaceId $effectiveWorkspaceId -Type "Lakehouse" -DisplayName $lakehouseName -Token $fabricToken
$lakehouseCreatedThisRun = $false
if (-not $lakehouse) {
    Write-Host "Creando lakehouse con esquemas: $lakehouseName..."
    $response = Invoke-FabricApi -Method POST -Uri "$apiRoot/workspaces/$effectiveWorkspaceId/lakehouses" -Token $fabricToken -Body @{
        displayName     = $lakehouseName
        description     = "Lakehouse curado para la demo FraSoHome Fabric IQ."
        creationPayload = @{ enableSchemas = $true }
    }
    $lakehouse = Wait-FabricOperation -InitialResponse $response -Token $fabricToken
    if (-not $lakehouse.id) {
        $lakehouse = Get-FabricItemByName -WorkspaceId $effectiveWorkspaceId -Type "Lakehouse" -DisplayName $lakehouseName -Token $fabricToken
    }
    $lakehouseCreatedThisRun = $true
}
if (-not $lakehouse.id) {
    throw "No se pudo resolver el lakehouse $lakehouseName."
}

if (-not $SkipDataUpload) {
    Write-Host "Subiendo las 15 fuentes seleccionadas a OneLake..."
    $storageToken = Get-AzureCliAccessToken -Resource "https://storage.azure.com/"
    $dfsEndpoint = if ($workspaceInfo.oneLakeEndpoints.dfsEndpoint) {
        [string]$workspaceInfo.oneLakeEndpoints.dfsEndpoint
    }
    else {
        "https://onelake.dfs.fabric.microsoft.com"
    }
    foreach ($source in $sourceManifest.sources) {
        $localPath = Join-Path $dataRoot ([string]$source.relativePath)
        $oneLakePath = "$($sourceManifest.oneLakeRoot)/$($source.domain)/$($source.file)"
        Write-Host "  $($source.file)"
        Set-OneLakeFile -DfsEndpoint $dfsEndpoint -WorkspaceId $effectiveWorkspaceId -LakehouseId $lakehouse.id -OneLakePath $oneLakePath -LocalPath $localPath -Token $storageToken
    }
}

$prepareNotebook = Ensure-Notebook -WorkspaceId $effectiveWorkspaceId -DisplayName ([string]$config.items.prepareNotebook) -Description "Prepara las tablas de entidades y relaciones de FraSoHome para Fabric IQ." -SourcePath $prepareNotebookPath -Token $fabricToken
$validationNotebook = Ensure-Notebook -WorkspaceId $effectiveWorkspaceId -DisplayName ([string]$config.items.validateNotebook) -Description "Valida claves, filas y relaciones antes de la demo FraSoHome." -SourcePath $validateNotebookPath -Token $fabricToken

if (-not $SkipNotebookRun) {
    Write-Host "Ejecutando preparación de tablas Delta..."
    Start-NotebookAndWait -WorkspaceId $effectiveWorkspaceId -NotebookId $prepareNotebook.id -LakehouseId $lakehouse.id -Token $fabricToken | Out-Null
    Write-Host "Ejecutando validación de la demo..."
    Start-NotebookAndWait -WorkspaceId $effectiveWorkspaceId -NotebookId $validationNotebook.id -LakehouseId $lakehouse.id -Token $fabricToken | Out-Null
}

$ontologyName = [string]$config.items.ontology
$ontologyDefinition = New-FraSoHomeOntologyDefinition -Model $model -Stage $effectiveStage -WorkspaceId $effectiveWorkspaceId -LakehouseId $lakehouse.id -DisplayName $ontologyName
$ontology = Get-FabricItemByName -WorkspaceId $effectiveWorkspaceId -Type "Ontology" -DisplayName $ontologyName -Token $fabricToken
$ontologyCreatedThisRun = $false
if ($ontology) {
    Write-Host "Actualizando ontología a la etapa $effectiveStage..."
    $response = Invoke-FabricApi -Method POST -Uri "$apiRoot/workspaces/$effectiveWorkspaceId/ontologies/$($ontology.id)/updateDefinition?updateMetadata=true" -Token $fabricToken -Body @{ definition = $ontologyDefinition }
    Wait-FabricOperation -InitialResponse $response -Token $fabricToken | Out-Null
}
else {
    Write-Host "Creando ontología $ontologyName en la etapa $effectiveStage..."
    $response = Invoke-FabricApi -Method POST -Uri "$apiRoot/workspaces/$effectiveWorkspaceId/ontologies" -Token $fabricToken -Body @{
        displayName = $ontologyName
        description = "Contexto empresarial FraSoHome. Etapa $effectiveStage de 6."
        definition  = $ontologyDefinition
    }
    $ontology = Wait-FabricOperation -InitialResponse $response -Token $fabricToken
    if (-not $ontology.id) {
        $ontology = Get-FabricItemByName -WorkspaceId $effectiveWorkspaceId -Type "Ontology" -DisplayName $ontologyName -Token $fabricToken
    }
    $ontologyCreatedThisRun = $true
}
if (-not $ontology.id) {
    throw "No se pudo resolver la ontología $ontologyName."
}

$graphModel = $null
if (-not $SkipGraphRefresh -and [bool]$config.deployment.refreshGraph) {
    Write-Host "Localizando el grafo hijo de la ontología..."
    for ($attempt = 1; $attempt -le 12 -and -not $graphModel; $attempt++) {
        $graphModel = Find-OntologyGraphModel -WorkspaceId $effectiveWorkspaceId -OntologyId $ontology.id -OntologyName $ontologyName -Token $fabricToken
        if (-not $graphModel) {
            Start-Sleep -Seconds 5
        }
    }
    if ($graphModel) {
        Write-Host "Actualizando el grafo asociado..."
        $response = Invoke-FabricApi -Method POST -Uri "$apiRoot/workspaces/$effectiveWorkspaceId/graphModels/$($graphModel.id)/jobs/refreshGraph/instances" -Token $fabricToken
        Wait-FabricOperation -InitialResponse $response -Token $fabricToken -TimeoutSeconds 3600 | Out-Null
    }
    else {
        Write-Warning "No se encontró el GraphModel hijo mediante la API beta. Abre su menú en Fabric y ejecuta Schedule > Refresh now."
    }
}

$agent = $null
$agentCreatedThisRun = $false
if ($effectiveStage -eq 6 -and -not $SkipAgent) {
    $agentName = [string]$config.items.dataAgent
    $agent = Get-FabricItemByName -WorkspaceId $effectiveWorkspaceId -Type "DataAgent" -DisplayName $agentName -Token $fabricToken
    if (-not $agent) {
        Write-Host "Creando agente de datos $agentName..."
        $response = Invoke-FabricApi -Method POST -Uri "$apiRoot/workspaces/$effectiveWorkspaceId/dataAgents" -Token $fabricToken -Body @{
            displayName = $agentName
            description = "Agente de demo conectado al contexto empresarial de FraSoHome."
        }
        $agent = Wait-FabricOperation -InitialResponse $response -Token $fabricToken
        if (-not $agent.id) {
            $agent = Get-FabricItemByName -WorkspaceId $effectiveWorkspaceId -Type "DataAgent" -DisplayName $agentName -Token $fabricToken
        }
        $agentCreatedThisRun = $true
    }
    if (-not $agent.id) {
        throw "No se pudo resolver el agente $agentName."
    }

    $datasourcesResponse = Invoke-FabricApi -Method GET -Uri "$apiRoot/workspaces/$effectiveWorkspaceId/dataAgents/$($agent.id)/staging/datasources" -Token $fabricToken
    $datasource = @($datasourcesResponse.Body.value) | Where-Object {
        $_.type -eq "FabricItem" -and $_.itemReference.itemId -eq $ontology.id
    } | Select-Object -First 1
    if (-not $datasource) {
        Write-Host "Conectando la ontología al agente..."
        $response = Invoke-FabricApi -Method POST -Uri "$apiRoot/workspaces/$effectiveWorkspaceId/dataAgents/$($agent.id)/staging/datasources" -Token $fabricToken -Body @{
            type          = "FabricItem"
            itemReference = @{
                referenceType = "ById"
                itemId        = $ontology.id
                workspaceId   = $effectiveWorkspaceId
            }
        }
        $datasource = Wait-FabricOperation -InitialResponse $response -Token $fabricToken
        if (-not $datasource.id) {
            $datasourcesResponse = Invoke-FabricApi -Method GET -Uri "$apiRoot/workspaces/$effectiveWorkspaceId/dataAgents/$($agent.id)/staging/datasources" -Token $fabricToken
            $datasource = @($datasourcesResponse.Body.value) | Where-Object {
                $_.type -eq "FabricItem" -and $_.itemReference.itemId -eq $ontology.id
            } | Select-Object -First 1
        }
    }
    if (-not $datasource.id) {
        throw "No se pudo conectar la ontología al agente."
    }

    $agentInstructions = Get-Content -LiteralPath $agentInstructionsPath -Raw -Encoding UTF8
    Invoke-FabricApi -Method PATCH -Uri "$apiRoot/workspaces/$effectiveWorkspaceId/dataAgents/$($agent.id)/staging/settings" -Token $fabricToken -Body @{ aiInstructions = $agentInstructions } | Out-Null
    Invoke-FabricApi -Method PATCH -Uri "$apiRoot/workspaces/$effectiveWorkspaceId/dataAgents/$($agent.id)/staging/datasources/$($datasource.id)" -Token $fabricToken -Body @{
        description  = "Ontología gobernada de FraSoHome con comercio, operación, demanda y marketing."
        instructions = "Usa los nombres de entidad y las relaciones de la ontología. Explica siempre el camino semántico."
    } | Out-Null

    $descriptions = @{}
    foreach ($entity in $model.entities) {
        $descriptions[[string]$entity.name] = [string]$entity.description
    }
    $selectedCount = 0
    for ($attempt = 1; $attempt -le 6 -and $selectedCount -eq 0; $attempt++) {
        $selectedCount = Select-AgentOntologyEntities -WorkspaceId $effectiveWorkspaceId -AgentId $agent.id -DatasourceId $datasource.id -Token $fabricToken -Descriptions $descriptions
        if ($selectedCount -eq 0) {
            Start-Sleep -Seconds 10
        }
    }
    Write-Host "Entidades seleccionadas en el agente: $selectedCount"
    $expectedAgentEntities = @($model.entities | Where-Object { [int]$_.stage -le $effectiveStage }).Count
    if ($selectedCount -lt $expectedAgentEntities) {
        throw "El agente solo expuso $selectedCount de $expectedAgentEntities entidades. Espera a que la ontología termine de sincronizarse y repite la etapa 6."
    }

    if (-not $NoPublishAgent -and [bool]$config.deployment.publishAgent) {
        Write-Host "Publicando el agente..."
        Invoke-FabricApi -Method POST -Uri "$apiRoot/workspaces/$effectiveWorkspaceId/dataAgents/$($agent.id)/staging/publish" -Token $fabricToken -Body @{
            publishedDescription = "Demo FraSoHome: contexto empresarial gobernado para respuestas omnicanal."
        } | Out-Null
    }
}

New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
$samePreviousWorkspace = $previousState -and ([string]$previousState.workspaceId -eq $effectiveWorkspaceId)
$stateGraphModelId = if ($graphModel) {
    [string]$graphModel.id
}
elseif ($samePreviousWorkspace -and [string]$previousState.ontologyId -eq [string]$ontology.id) {
    [string]$previousState.graphModelId
}
else {
    ""
}
$stateDataAgentId = if ($agent) {
    [string]$agent.id
}
elseif ($samePreviousWorkspace) {
    [string]$previousState.dataAgentId
}
else {
    ""
}
$state = [ordered]@{
    deployedAtUtc       = (Get-Date).ToUniversalTime().ToString("o")
    stage               = $effectiveStage
    workspaceId         = $effectiveWorkspaceId
    workspaceName       = [string]$workspaceInfo.displayName
    lakehouseId         = [string]$lakehouse.id
    lakehouseName       = $lakehouseName
    prepareNotebookId   = [string]$prepareNotebook.id
    validateNotebookId  = [string]$validationNotebook.id
    ontologyId          = [string]$ontology.id
    ontologyName        = $ontologyName
    graphModelId        = $stateGraphModelId
    dataAgentId         = $stateDataAgentId
    ownership           = [ordered]@{
        workspace        = Test-ResourceOwnership -Kind "workspace" -Id $effectiveWorkspaceId -CreatedThisRun $workspaceCreatedThisRun
        lakehouse        = Test-ResourceOwnership -Kind "lakehouse" -Id ([string]$lakehouse.id) -CreatedThisRun $lakehouseCreatedThisRun
        prepareNotebook  = Test-ResourceOwnership -Kind "prepareNotebook" -Id ([string]$prepareNotebook.id) -CreatedThisRun ([bool]$prepareNotebook.createdThisRun)
        validateNotebook = Test-ResourceOwnership -Kind "validateNotebook" -Id ([string]$validationNotebook.id) -CreatedThisRun ([bool]$validationNotebook.createdThisRun)
        ontology         = Test-ResourceOwnership -Kind "ontology" -Id ([string]$ontology.id) -CreatedThisRun $ontologyCreatedThisRun
        dataAgent        = if ($stateDataAgentId) {
            Test-ResourceOwnership -Kind "dataAgent" -Id $stateDataAgentId -CreatedThisRun $agentCreatedThisRun
        }
        else {
            $false
        }
    }
}
$state | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $statePath -Encoding UTF8

Write-Host ""
Write-Host "Despliegue completado."
Write-Host "Workspace: https://app.fabric.microsoft.com/groups/$effectiveWorkspaceId/list?experience=fabric-developer"
Write-Host "Estado local: $statePath"
