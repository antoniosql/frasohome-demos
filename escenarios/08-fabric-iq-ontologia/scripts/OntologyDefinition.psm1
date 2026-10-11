Set-StrictMode -Version 1.0

function Get-StableOntologyId {
    param([Parameter(Mandatory)][string]$Seed)

    $bytes = [Text.Encoding]::UTF8.GetBytes($Seed)
    $hash = [Security.Cryptography.SHA256]::HashData($bytes)
    [uint64]$value = 0
    for ($i = 0; $i -lt 7; $i++) {
        $value = ($value * 256) + $hash[$i]
    }
    return ([uint64]100000000000000 + $value).ToString([Globalization.CultureInfo]::InvariantCulture)
}

function Get-StableOntologyGuid {
    param([Parameter(Mandatory)][string]$Seed)

    $bytes = [Text.Encoding]::UTF8.GetBytes($Seed)
    $hash = [Security.Cryptography.SHA256]::HashData($bytes)
    $guidBytes = [byte[]]::new(16)
    [Array]::Copy($hash, $guidBytes, 16)
    return ([Guid]::new($guidBytes)).ToString()
}

function ConvertTo-InlineBase64Json {
    param([Parameter(Mandatory)][AllowEmptyCollection()][object]$Value)

    $json = $Value | ConvertTo-Json -Depth 100 -Compress
    return [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($json))
}

function Test-FraSoHomeOntologyModel {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [psobject]$Model
    )

    $errors = [System.Collections.Generic.List[string]]::new()
    $allowedTypes = @("String", "Boolean", "DateTime", "Object", "BigInt", "Double")
    $entityNames = @($Model.entities.name)
    $relationshipNames = @($Model.relationships.name)

    if (($entityNames | Sort-Object -Unique).Count -ne $entityNames.Count) {
        $errors.Add("Hay nombres de entidad duplicados.")
    }
    if (($relationshipNames | Sort-Object -Unique).Count -ne $relationshipNames.Count) {
        $errors.Add("Hay nombres de relación duplicados.")
    }

    $allPropertyNames = [System.Collections.Generic.List[string]]::new()
    foreach ($entity in $Model.entities) {
        if ([int]$entity.stage -lt 1 -or [int]$entity.stage -gt 6) {
            $errors.Add("La entidad $($entity.name) tiene una etapa no válida.")
        }
        if ([string]$entity.name -notmatch "^[a-zA-Z][a-zA-Z0-9_-]{0,127}$") {
            $errors.Add("Nombre de entidad no válido: $($entity.name).")
        }

        $propertyNames = @($entity.properties.name)
        if (($propertyNames | Sort-Object -Unique).Count -ne $propertyNames.Count) {
            $errors.Add("La entidad $($entity.name) contiene propiedades duplicadas.")
        }
        if ($propertyNames -notcontains [string]$entity.keyProperty) {
            $errors.Add("La clave $($entity.keyProperty) no existe en $($entity.name).")
        }
        if ($propertyNames -notcontains [string]$entity.displayProperty) {
            $errors.Add("La propiedad de visualización $($entity.displayProperty) no existe en $($entity.name).")
        }

        foreach ($property in $entity.properties) {
            $allPropertyNames.Add([string]$property.name)
            if ([string]$property.name -notmatch "^[a-zA-Z][a-zA-Z0-9_-]{0,127}$") {
                $errors.Add("Nombre de propiedad no válido: $($property.name).")
            }
            if ($allowedTypes -notcontains [string]$property.type) {
                $errors.Add("Tipo no válido en $($entity.name).$($property.name): $($property.type).")
            }
            if ([string]::IsNullOrWhiteSpace([string]$property.column)) {
                $errors.Add("Falta la columna física de $($entity.name).$($property.name).")
            }
        }
    }

    if (($allPropertyNames | Sort-Object -Unique).Count -ne $allPropertyNames.Count) {
        $errors.Add("Los nombres de propiedad deben ser únicos en toda la ontología FraSoHome.")
    }

    $entityByName = @{}
    foreach ($entity in $Model.entities) {
        $entityByName[[string]$entity.name] = $entity
    }
    foreach ($relationship in $Model.relationships) {
        if ([int]$relationship.stage -lt 1 -or [int]$relationship.stage -gt 6) {
            $errors.Add("La relación $($relationship.name) tiene una etapa no válida.")
        }
        if ([string]$relationship.name -notmatch "^[a-zA-Z][a-zA-Z0-9_-]{0,127}$") {
            $errors.Add("Nombre de relación no válido: $($relationship.name).")
        }
        if (-not $entityByName.ContainsKey([string]$relationship.source)) {
            $errors.Add("Origen desconocido en $($relationship.name): $($relationship.source).")
        }
        if (-not $entityByName.ContainsKey([string]$relationship.target)) {
            $errors.Add("Destino desconocido en $($relationship.name): $($relationship.target).")
        }
        if ($entityByName.ContainsKey([string]$relationship.source) -and [int]$relationship.stage -lt [int]$entityByName[[string]$relationship.source].stage) {
            $errors.Add("La relación $($relationship.name) aparece antes que su entidad origen.")
        }
        if ($entityByName.ContainsKey([string]$relationship.target) -and [int]$relationship.stage -lt [int]$entityByName[[string]$relationship.target].stage) {
            $errors.Add("La relación $($relationship.name) aparece antes que su entidad destino.")
        }
    }

    if ($errors.Count -gt 0) {
        throw ($errors -join [Environment]::NewLine)
    }

    [pscustomobject]@{
        EntityCount       = $Model.entities.Count
        RelationshipCount = $Model.relationships.Count
        PropertyCount     = $allPropertyNames.Count
    }
}

function New-FraSoHomeOntologyDefinition {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [psobject]$Model,

        [Parameter(Mandatory)]
        [ValidateRange(1, 6)]
        [int]$Stage,

        [Parameter(Mandatory)]
        [string]$WorkspaceId,

        [Parameter(Mandatory)]
        [string]$LakehouseId,

        [Parameter(Mandatory)]
        [string]$DisplayName
    )

    Test-FraSoHomeOntologyModel -Model $Model | Out-Null

    $entities = @($Model.entities | Where-Object { [int]$_.stage -le $Stage })
    $relationships = @($Model.relationships | Where-Object { [int]$_.stage -le $Stage })
    $entityByName = @{}
    $entityIdByName = @{}
    $propertyIdByName = @{}

    foreach ($entity in $entities) {
        $entityByName[[string]$entity.name] = $entity
        $entityIdByName[[string]$entity.name] = Get-StableOntologyId -Seed "entity:$($entity.name)"
        foreach ($property in $entity.properties) {
            $propertyIdByName["$($entity.name)|$($property.name)"] = Get-StableOntologyId -Seed "property:$($entity.name):$($property.name)"
        }
    }

    $parts = [System.Collections.Generic.List[object]]::new()
    $platform = [ordered]@{
        metadata = [ordered]@{
            type        = "Ontology"
            displayName = $DisplayName
            description = "$($Model.description) Etapa $Stage de 6."
        }
        config = [ordered]@{
            version   = "2.0"
            logicalId = Get-StableOntologyGuid -Seed "platform:$($Model.name)"
        }
    }
    $parts.Add([ordered]@{ path = ".platform"; payload = ConvertTo-InlineBase64Json -Value $platform; payloadType = "InlineBase64" })
    $parts.Add([ordered]@{ path = "definition.json"; payload = ConvertTo-InlineBase64Json -Value ([ordered]@{}); payloadType = "InlineBase64" })

    foreach ($entity in $entities) {
        $entityId = $entityIdByName[[string]$entity.name]
        $propertyDefinitions = [System.Collections.Generic.List[object]]::new()
        $propertyBindings = [System.Collections.Generic.List[object]]::new()

        foreach ($property in $entity.properties) {
            $propertyId = $propertyIdByName["$($entity.name)|$($property.name)"]
            $propertyDefinitions.Add([ordered]@{
                id                    = $propertyId
                name                  = [string]$property.name
                redefines             = $null
                baseTypeNamespaceType = $null
                valueType             = [string]$property.type
            })
            $propertyBindings.Add([ordered]@{
                sourceColumnName = [string]$property.column
                targetPropertyId = $propertyId
            })
        }

        $entityDefinition = [ordered]@{
            id                    = $entityId
            namespace             = "usertypes"
            baseEntityTypeId      = $null
            name                  = [string]$entity.name
            entityIdParts         = @($propertyIdByName["$($entity.name)|$($entity.keyProperty)"])
            displayNamePropertyId = $propertyIdByName["$($entity.name)|$($entity.displayProperty)"]
            namespaceType         = "Custom"
            visibility            = "Visible"
            properties            = @($propertyDefinitions)
            timeseriesProperties  = @()
        }
        $parts.Add([ordered]@{
            path        = "EntityTypes/$entityId/definition.json"
            payload     = ConvertTo-InlineBase64Json -Value $entityDefinition
            payloadType = "InlineBase64"
        })

        $bindingId = Get-StableOntologyGuid -Seed "binding:$($entity.name)"
        $binding = [ordered]@{
            id                       = $bindingId
            dataBindingConfiguration = [ordered]@{
                dataBindingType      = "NonTimeSeries"
                propertyBindings     = @($propertyBindings)
                sourceTableProperties = [ordered]@{
                    sourceType     = "LakehouseTable"
                    workspaceId    = $WorkspaceId
                    itemId         = $LakehouseId
                    sourceTableName = [string]$entity.table
                    sourceSchema   = "dbo"
                }
            }
        }
        $parts.Add([ordered]@{
            path        = "EntityTypes/$entityId/DataBindings/$bindingId.json"
            payload     = ConvertTo-InlineBase64Json -Value $binding
            payloadType = "InlineBase64"
        })
    }

    foreach ($relationship in $relationships) {
        $relationshipId = Get-StableOntologyId -Seed "relationship:$($relationship.name)"
        $sourceEntity = $entityByName[[string]$relationship.source]
        $targetEntity = $entityByName[[string]$relationship.target]
        $sourceKeyPropertyId = $propertyIdByName["$($sourceEntity.name)|$($sourceEntity.keyProperty)"]
        $targetKeyPropertyId = $propertyIdByName["$($targetEntity.name)|$($targetEntity.keyProperty)"]

        $relationshipDefinition = [ordered]@{
            namespace     = "usertypes"
            id            = $relationshipId
            name          = [string]$relationship.name
            namespaceType = "Custom"
            source        = [ordered]@{ entityTypeId = $entityIdByName[[string]$relationship.source] }
            target        = [ordered]@{ entityTypeId = $entityIdByName[[string]$relationship.target] }
        }
        $parts.Add([ordered]@{
            path        = "RelationshipTypes/$relationshipId/definition.json"
            payload     = ConvertTo-InlineBase64Json -Value $relationshipDefinition
            payloadType = "InlineBase64"
        })

        $contextId = Get-StableOntologyGuid -Seed "contextualization:$($relationship.name)"
        $contextualization = [ordered]@{
            id                     = $contextId
            dataBindingTable       = [ordered]@{
                workspaceId     = $WorkspaceId
                itemId          = $LakehouseId
                sourceTableName = [string]$relationship.table
                sourceSchema    = "dbo"
                sourceType      = "LakehouseTable"
            }
            sourceKeyRefBindings = @(
                [ordered]@{
                    sourceColumnName = "source_id"
                    targetPropertyId = $sourceKeyPropertyId
                }
            )
            targetKeyRefBindings = @(
                [ordered]@{
                    sourceColumnName = "target_id"
                    targetPropertyId = $targetKeyPropertyId
                }
            )
        }
        $parts.Add([ordered]@{
            path        = "RelationshipTypes/$relationshipId/Contextualizations/$contextId.json"
            payload     = ConvertTo-InlineBase64Json -Value $contextualization
            payloadType = "InlineBase64"
        })
    }

    return [ordered]@{ parts = @($parts) }
}

Export-ModuleMember -Function @(
    "Get-StableOntologyId",
    "Get-StableOntologyGuid",
    "Test-FraSoHomeOntologyModel",
    "New-FraSoHomeOntologyDefinition"
)
