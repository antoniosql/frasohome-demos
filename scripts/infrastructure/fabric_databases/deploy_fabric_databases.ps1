param(
    [Parameter(Mandatory = $true)]
    [string]$WorkspaceName,

    [Parameter(Mandatory = $true)]
    [string]$RawSqlEndpoint,

    [Parameter(Mandatory = $true)]
    [string]$CoreSqlEndpoint,

    [Parameter(Mandatory = $true)]
    [string]$AnalyticsSqlEndpoint,

    [string]$RawDatabaseName = "FraSoHome_Raw",
    [string]$CoreDatabaseName = "FraSoHome_Core",
    [string]$AnalyticsDatabaseName = "FraSoHome_Analytics"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$rawDdl = Join-Path $repoRoot "scripts\infrastructure\retail_sql_database\ddl_raw_retail.sql"
$coreDdl = Join-Path $PSScriptRoot "01_FraSoHome_Core.sql"
$analyticsDdl = Join-Path $PSScriptRoot "02_FraSoHome_Analytics.sql"

function Assert-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "No se encontro '$Name'. Instalalo y vuelve a ejecutar el despliegue."
    }
}

function Ensure-FabricSqlDatabase {
    param(
        [string]$Workspace,
        [string]$DatabaseName
    )

    Write-Host "Comprobando Fabric SQL Database item '$DatabaseName'..."
    $workspacePath = "$Workspace.Workspace"
    $databasePath = "$Workspace.Workspace/$DatabaseName.SQLDatabase"
    $items = fab ls $workspacePath 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudo listar el workspace '$Workspace'. Ejecuta 'fab auth login' y verifica el nombre."
    }

    if ($items -match [regex]::Escape($DatabaseName)) {
        Write-Host "Item existente: $DatabaseName"
        return
    }

    Write-Host "Creando Fabric SQL Database item '$DatabaseName'..."
    fab create $databasePath
}

function Invoke-SqlDdl {
    param(
        [string]$Endpoint,
        [string]$DatabaseName,
        [string]$SqlFile
    )

    if (-not (Test-Path -LiteralPath $SqlFile)) {
        throw "No existe el archivo SQL: $SqlFile"
    }

    Write-Host "Aplicando $SqlFile en $DatabaseName..."
    sqlcmd -S $Endpoint -d $DatabaseName -G -i $SqlFile -b
}

Assert-Command "fab"
Assert-Command "sqlcmd"

Ensure-FabricSqlDatabase -Workspace $WorkspaceName -DatabaseName $RawDatabaseName
Ensure-FabricSqlDatabase -Workspace $WorkspaceName -DatabaseName $CoreDatabaseName
Ensure-FabricSqlDatabase -Workspace $WorkspaceName -DatabaseName $AnalyticsDatabaseName

Invoke-SqlDdl -Endpoint $RawSqlEndpoint -DatabaseName $RawDatabaseName -SqlFile $rawDdl
Invoke-SqlDdl -Endpoint $CoreSqlEndpoint -DatabaseName $CoreDatabaseName -SqlFile $coreDdl
Invoke-SqlDdl -Endpoint $AnalyticsSqlEndpoint -DatabaseName $AnalyticsDatabaseName -SqlFile $analyticsDdl

Write-Host "Despliegue finalizado."
