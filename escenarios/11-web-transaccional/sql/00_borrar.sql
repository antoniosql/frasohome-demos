/* =====================================================================
   FraSoHome Live · 00_borrar.sql
   Borra todos los objetos de datos de FraSoHome Live para volver a
   crearlos y recargarlos (seed/reset.py y seed/load_sql.py --recrear).

   Conserva los usuarios de la web (app.app_user, app.user_role,
   app.user_scope): se crean a mano y deben sobrevivir a un reinicio.
   Todo lo demás de app (contadores, outbox, sesiones, idempotencia,
   auditoría) se borra con los datos: un reinicio obliga a volver a entrar.
   ===================================================================== */

SET NOCOUNT ON;

DECLARE @schemas TABLE (name SYSNAME PRIMARY KEY);
INSERT INTO @schemas (name) VALUES
    (N'crm'), (N'catalog'), (N'store'), (N'sales'), (N'returns'), (N'inventory'), (N'quality'),
    (N'hr'), (N'mkt'), (N'fin'), (N'ref'), (N'xref'), (N'rag'), (N'meta'), (N'lab'), (N'exp'), (N'exp_rag'), (N'app');

DECLARE @keep TABLE (name SYSNAME PRIMARY KEY);
INSERT INTO @keep (name) VALUES (N'app.app_user'), (N'app.user_role'), (N'app.user_scope');

DECLARE @sql NVARCHAR(MAX);

/* 1. Claves foráneas que apuntan a tablas que se borran (también desde las que se conservan). */
SET @sql = N'';
SELECT @sql += N'ALTER TABLE ' + QUOTENAME(SCHEMA_NAME(fk.schema_id)) + N'.' + QUOTENAME(OBJECT_NAME(fk.parent_object_id))
             + N' DROP CONSTRAINT ' + QUOTENAME(fk.name) + N';' + NCHAR(10)
FROM sys.foreign_keys AS fk
JOIN sys.tables AS t ON t.object_id = fk.referenced_object_id
WHERE SCHEMA_NAME(t.schema_id) IN (SELECT name FROM @schemas)
  AND SCHEMA_NAME(t.schema_id) + N'.' + t.name NOT IN (SELECT name FROM @keep);
EXEC sys.sp_executesql @sql;

/* 2. Vistas, procedimientos y funciones. */
SET @sql = N'';
SELECT @sql += CASE o.type
                 WHEN 'V'  THEN N'DROP VIEW '
                 WHEN 'P'  THEN N'DROP PROCEDURE '
                 ELSE N'DROP FUNCTION '
               END + QUOTENAME(SCHEMA_NAME(o.schema_id)) + N'.' + QUOTENAME(o.name) + N';' + NCHAR(10)
FROM sys.objects AS o
WHERE o.type IN ('V', 'P', 'FN', 'IF', 'TF')
  AND SCHEMA_NAME(o.schema_id) IN (SELECT name FROM @schemas);
EXEC sys.sp_executesql @sql;

/* 3. Tablas (menos las de usuarios). */
SET @sql = N'';
SELECT @sql += N'DROP TABLE ' + QUOTENAME(SCHEMA_NAME(t.schema_id)) + N'.' + QUOTENAME(t.name) + N';' + NCHAR(10)
FROM sys.tables AS t
WHERE SCHEMA_NAME(t.schema_id) IN (SELECT name FROM @schemas)
  AND SCHEMA_NAME(t.schema_id) + N'.' + t.name NOT IN (SELECT name FROM @keep);
EXEC sys.sp_executesql @sql;
