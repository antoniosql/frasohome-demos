# SQL Database Consolidada

Scripts SQL para crear y cargar una base raw consolidada con todos los datos de `01_datos`.

## Objetivo

Esta capa no intenta limpiar ni tipar agresivamente. Carga todos los CSV como texto (`NVARCHAR`) para conservar errores de calidad, formatos mixtos y valores didacticos. Desde esta base raw se pueden construir modelos `core`, `analytics`, Power BI, Copilot Studio, Fabric notebooks o agentes.

## Archivos

- `01_create_raw_database.sql`: crea esquemas, tablas raw para todos los CSV, auditoria de carga y tabla de documentos JSON.
- `02_create_load_procedures.sql`: crea procedimientos para cargar CSV con `BULK INSERT` y documentos JSON con `OPENJSON`.
- `03_load_all_csv_template.sql`: plantilla `sqlcmd` con todas las llamadas de carga CSV.
- `04_create_semantic_views.sql`: vistas de ayuda para relaciones, touchpoints de marketing y contexto empleado-tienda.
- `05_load_json_template.sql`: ejemplo de carga de JSON.
- `table_file_manifest.csv`: manifiesto CSV -> esquema.tabla.

## Esquemas

- `raw_retail`: retail omnicanal.
- `raw_people`: People Analytics.
- `raw_rag`: CSV estructurados y test sets de Copilot Studio.
- `raw_marketing`: marketing precision.
- `xref`: tablas puente entre dominios.
- `raw_json`: documentos JSON genericos.
- `admin`: auditoria y procedimientos de carga.

## Orden de Ejecucion

```powershell
sqlcmd -S <server> -d <database> -G -i .\scripts\infrastructure\sql_database_consolidated\01_create_raw_database.sql
sqlcmd -S <server> -d <database> -G -i .\scripts\infrastructure\sql_database_consolidated\02_create_load_procedures.sql
sqlcmd -S <server> -d <database> -G -v DataRoot="C:\Users\anton\OneDrive\Materiales\FraSoHome\01_datos" -i .\scripts\infrastructure\sql_database_consolidated\03_load_all_csv_template.sql
sqlcmd -S <server> -d <database> -G -i .\scripts\infrastructure\sql_database_consolidated\04_create_semantic_views.sql
```

`BULK INSERT` requiere que la ruta indicada por `DataRoot` sea visible desde el motor SQL. En Azure SQL/Fabric, si el motor no puede leer rutas locales, usa un mecanismo de staging soportado por la plataforma o el loader Python del repositorio.

## JSON

La tabla `raw_json.documents` permite cargar payloads JSON completos y consultarlos con `raw_json.document_properties`.

Ejemplo:

```sql
EXEC [admin].[load_json_document]
    @source_path = N'mi_archivo.json',
    @document_type = N'configuracion_demo',
    @json_payload = N'{"caso":"FraSoHome","dominio":"marketing"}';
```

## Nota

Estos scripts son una base de aterrizaje. Los scripts de modelo operacional/analitico siguen viviendo en [../fabric_databases](../fabric_databases/README.md).
