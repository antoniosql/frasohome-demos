# Retail SQL Database

DDL base para crear tablas raw del dominio retail omnicanal.

## Archivos

- `ddl_raw_retail.sql`: tablas raw para CRM, productos, tiendas, ecommerce, POS, pagos, devoluciones, stock y fact integrada.
- `truncate_raw_retail_tables.sql`: limpieza de tablas raw.

Este DDL se usa desde [../fabric_databases/deploy_fabric_databases.ps1](../fabric_databases/deploy_fabric_databases.ps1) para preparar `FraSoHome_Raw`.
