-- Procedimientos de carga para CSV y JSON.
-- BULK INSERT requiere que la ruta sea accesible desde el motor SQL.

CREATE OR ALTER PROCEDURE [admin].[bulk_load_csv]
    @schema_name SYSNAME,
    @table_name SYSNAME,
    @source_path NVARCHAR(1000),
    @truncate_first BIT = 1,
    @field_terminator NVARCHAR(10) = N',',
    @row_terminator NVARCHAR(20) = N'0x0a',
    @codepage NVARCHAR(20) = N'65001'
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @audit_id BIGINT;
    INSERT INTO [admin].[load_audit] ([schema_name], [table_name], [source_path], [source_format])
    VALUES (@schema_name, @table_name, @source_path, N'CSV');
    SET @audit_id = SCOPE_IDENTITY();
    BEGIN TRY
        DECLARE @full_table NVARCHAR(300) = QUOTENAME(@schema_name) + N'.' + QUOTENAME(@table_name);
        DECLARE @sql NVARCHAR(MAX);
        IF @truncate_first = 1
        BEGIN
            SET @sql = N'TRUNCATE TABLE ' + @full_table + N';';
            EXEC sys.sp_executesql @sql;
        END;
        SET @sql = N'BULK INSERT ' + @full_table + N'
FROM ' + QUOTENAME(@source_path, '''') + N'
WITH (
    FIRSTROW = 2,
    FORMAT = ''CSV'',
    FIELDTERMINATOR = ' + QUOTENAME(@field_terminator, '''') + N',
    ROWTERMINATOR = ' + QUOTENAME(@row_terminator, '''') + N',
    FIELDQUOTE = ''"'',
    CODEPAGE = ' + QUOTENAME(@codepage, '''') + N',
    TABLOCK,
    KEEPNULLS
);';
        EXEC sys.sp_executesql @sql;
        SET @sql = N'UPDATE ' + @full_table + N' SET [_source_file] = @p WHERE [_source_file] IS NULL;';
        EXEC sys.sp_executesql @sql, N'@p NVARCHAR(1000)', @p = @source_path;
        DECLARE @rows BIGINT;
        SET @sql = N'SELECT @rows_out = COUNT_BIG(*) FROM ' + @full_table + N';';
        EXEC sys.sp_executesql @sql, N'@rows_out BIGINT OUTPUT', @rows_out = @rows OUTPUT;
        UPDATE [admin].[load_audit]
        SET [finished_at_utc] = SYSUTCDATETIME(), [status] = N'OK', [rows_loaded] = @rows
        WHERE [load_audit_id] = @audit_id;
    END TRY
    BEGIN CATCH
        UPDATE [admin].[load_audit]
        SET [finished_at_utc] = SYSUTCDATETIME(), [status] = N'ERROR', [error_message] = ERROR_MESSAGE()
        WHERE [load_audit_id] = @audit_id;
        THROW;
    END CATCH
END;
GO

CREATE OR ALTER PROCEDURE [admin].[load_json_document]
    @source_path NVARCHAR(1000),
    @document_type NVARCHAR(100),
    @json_payload NVARCHAR(MAX)
AS
BEGIN
    SET NOCOUNT ON;
    IF ISJSON(@json_payload) <> 1
        THROW 51000, 'El payload no es JSON valido.', 1;
    INSERT INTO [raw_json].[documents] ([source_path], [document_type], [json_payload])
    VALUES (@source_path, @document_type, @json_payload);
END;
GO

CREATE OR ALTER VIEW [raw_json].[document_properties]
AS
SELECT d.[json_document_id], d.[source_path], d.[document_type], j.[key] AS [json_key], j.[value] AS [json_value], j.[type] AS [json_type], d.[loaded_at_utc]
FROM [raw_json].[documents] AS d
CROSS APPLY OPENJSON(d.[json_payload]) AS j;
GO
