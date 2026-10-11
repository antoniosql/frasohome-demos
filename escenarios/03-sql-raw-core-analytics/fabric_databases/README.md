# Fabric Databases

Scripts de infraestructura para crear y preparar las Fabric SQL Databases del caso FraSoHome.

## Bases

1. `FraSoHome_Raw`: aterrizaje fiel de los CSV de ejemplo. Usa [../retail_sql_database/ddl_raw_retail.sql](../retail_sql_database/ddl_raw_retail.sql).
2. `FraSoHome_Core`: modelo operacional limpio y relacional.
3. `FraSoHome_Analytics`: modelo dimensional para BI, ML y reporting.

## Artefactos

- `01_FraSoHome_Core.sql`: DDL del modelo operacional.
- `02_FraSoHome_Analytics.sql`: DDL del modelo estrella.
- `deploy_fabric_databases.ps1`: crea los items `SQLDatabase` en Fabric y aplica los DDL.

## Despliegue

Requisitos:

- Microsoft Fabric CLI instalado y autenticado (`fab auth login`).
- `sqlcmd` instalado con soporte de autenticacion Microsoft Entra.
- Permisos para crear items en el workspace de Fabric.
- Endpoints SQL de cada Fabric SQL Database despues de crearlos.

Ejemplo desde la raiz del repositorio:

```powershell
.\escenarios\03-sql-raw-core-analytics\fabric_databases\deploy_fabric_databases.ps1 `
  -WorkspaceName "Mi Workspace" `
  -RawSqlEndpoint "xxxxx.database.fabric.microsoft.com" `
  -CoreSqlEndpoint "yyyyy.database.fabric.microsoft.com" `
  -AnalyticsSqlEndpoint "zzzzz.database.fabric.microsoft.com"
```

El script ejecuta:

- `escenarios/03-sql-raw-core-analytics/retail_sql_database/ddl_raw_retail.sql` sobre `FraSoHome_Raw`
- `escenarios/03-sql-raw-core-analytics/fabric_databases/01_FraSoHome_Core.sql` sobre `FraSoHome_Core`
- `escenarios/03-sql-raw-core-analytics/fabric_databases/02_FraSoHome_Analytics.sql` sobre `FraSoHome_Analytics`

La creacion de Fabric SQL Database se hace por Fabric CLI/API, no mediante `CREATE DATABASE` dentro de T-SQL.
