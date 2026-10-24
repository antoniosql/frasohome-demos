/* =====================================================================
   FraSoHome Live · 04_app.sql
   Infraestructura de la aplicación: usuarios y sesiones propios,
   identificadores legibles, outbox hacia Cosmos DB, idempotencia y
   auditoría. Sin proveedores externos de identidad.
   Las tablas de usuarios (app_user, user_role, user_scope) solo se crean
   si no existen: sobreviven a sql/00_borrar.sql y a los reinicios.
   ===================================================================== */

IF SCHEMA_ID('app') IS NULL EXEC('CREATE SCHEMA app');
GO

/* ---------- identificadores legibles ---------- */

/* Un contador por tipo de documento (y por año cuando la plantilla lleva {Y}).
   Ejemplos: O-{Y} -> O-202600001, T- -> T-501200, FSH -> FSH0821. */
CREATE TABLE app.id_counter (
    kind                         NVARCHAR(30)    NOT NULL,
    period_key                   SMALLINT        NOT NULL CONSTRAINT DF_id_counter_period DEFAULT 0,
    prefix_template              NVARCHAR(30)    NOT NULL,
    number_width                 TINYINT         NOT NULL,
    next_value                   BIGINT          NOT NULL CONSTRAINT DF_id_counter_next DEFAULT 1,
    CONSTRAINT PK_id_counter PRIMARY KEY (kind, period_key)
);
GO

CREATE TABLE app.id_kind (
    kind                         NVARCHAR(30)    NOT NULL,
    prefix_template              NVARCHAR(30)    NOT NULL,
    number_width                 TINYINT         NOT NULL,
    per_year                     BIT             NOT NULL,
    CONSTRAINT PK_id_kind PRIMARY KEY (kind)
);
GO

INSERT INTO app.id_kind (kind, prefix_template, number_width, per_year) VALUES
 (N'order', N'O-{Y}', 5, 1), (N'order_line', N'OL-', 7, 0),
 (N'ticket', N'T-', 6, 0), (N'ticket_line', N'TL-', 6, 0), (N'payment', N'PAY-', 7, 0),
 (N'return_online', N'RO-{Y}-', 5, 1), (N'return_store', N'RT-{Y}-', 5, 1),
 (N'customer', N'C', 4, 0), (N'product', N'P', 4, 0),
 (N'campaign', N'CAM-{Y}-', 3, 1), (N'contact', N'CT-', 6, 0),
 (N'coupon', N'CPN-', 6, 0), (N'coupon_code', N'FSH{Y}', 4, 1),
 (N'promo', N'PROMO-', 4, 0), (N'cost', N'CTC-', 6, 0),
 (N'employee', N'FSH', 4, 0), (N'movement', N'MOV', 6, 0), (N'absence', N'ABS', 6, 0),
 (N'overtime', N'HEX', 7, 0), (N'training', N'FOR', 6, 0), (N'review', N'EVA', 6, 0),
 (N'payroll', N'NOM', 6, 0),
 (N'web_event', N'WEB-', 7, 0), (N'web_session', N'SE-', 7, 0), (N'campaign_event', N'EV-', 7, 0),
 (N'identity', N'IDS-', 6, 0), (N'feedback', N'FB-', 6, 0), (N'service', N'SRV-', 6, 0),
 (N'creative', N'CR-', 5, 0), (N'survey', N'CLI', 7, 0), (N'exit', N'EXT', 6, 0);
GO

/* Reserva @count números consecutivos y devuelve el prefijo ya resuelto. */
CREATE PROCEDURE app.usp_reserve_ids
    @kind NVARCHAR(30),
    @count INT = 1,
    @first BIGINT OUTPUT,
    @prefix NVARCHAR(30) OUTPUT,
    @width TINYINT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @template NVARCHAR(30), @per_year BIT, @period SMALLINT;
    SELECT @template = prefix_template, @width = number_width, @per_year = per_year
    FROM app.id_kind WHERE kind = @kind;
    IF @template IS NULL THROW 50001, N'Tipo de identificador desconocido.', 1;
    SET @period = CASE WHEN @per_year = 1 THEN YEAR(SYSUTCDATETIME()) ELSE 0 END;

    UPDATE app.id_counter WITH (UPDLOCK, HOLDLOCK)
       SET @first = next_value, next_value = next_value + @count
     WHERE kind = @kind AND period_key = @period;
    IF @@ROWCOUNT = 0
    BEGIN
        INSERT INTO app.id_counter (kind, period_key, prefix_template, number_width, next_value)
        VALUES (@kind, @period, @template, @width, 1 + @count);
        SET @first = 1;
    END
    SET @prefix = REPLACE(@template, N'{Y}', CAST(YEAR(SYSUTCDATETIME()) AS NVARCHAR(4)));
END
GO

CREATE FUNCTION app.fn_format_id (@prefix NVARCHAR(30), @width TINYINT, @n BIGINT)
RETURNS NVARCHAR(50)
AS
BEGIN
    DECLARE @digits NVARCHAR(20) = CAST(@n AS NVARCHAR(20));
    RETURN @prefix + CASE WHEN LEN(@digits) >= @width THEN @digits
                          ELSE REPLICATE(N'0', @width - LEN(@digits)) + @digits END;
END
GO

/* Para la API: varios identificadores de una vez (documentos de Cosmos). */
CREATE PROCEDURE app.usp_next_ids
    @kind NVARCHAR(30),
    @count INT = 1
AS
BEGIN
    SET NOCOUNT ON;
    IF @count < 1 OR @count > 1000 THROW 50002, N'Número de identificadores fuera de rango.', 1;
    DECLARE @first BIGINT, @prefix NVARCHAR(30), @width TINYINT;
    BEGIN TRAN;
        EXEC app.usp_reserve_ids @kind, @count, @first OUTPUT, @prefix OUTPUT, @width OUTPUT;
    COMMIT;
    SELECT app.fn_format_id(@prefix, @width, @first + v.n) AS id
    FROM (SELECT TOP (@count) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS n
          FROM sys.all_objects) AS v
    ORDER BY v.n;
END
GO

/* ---------- usuarios y sesiones ---------- */

IF OBJECT_ID(N'app.app_user') IS NULL
CREATE TABLE app.app_user (
    user_id                      INT IDENTITY(1,1) NOT NULL,
    login                        NVARCHAR(100)   NOT NULL,
    display_name                 NVARCHAR(200)   NOT NULL,
    password_hash                VARBINARY(64)   NOT NULL,
    password_salt                VARBINARY(32)   NOT NULL,
    scrypt_n                     INT             NOT NULL,
    scrypt_r                     INT             NOT NULL,
    scrypt_p                     INT             NOT NULL,
    is_active                    BIT             NOT NULL CONSTRAINT DF_app_user_active DEFAULT 1,
    must_change_password         BIT             NOT NULL CONSTRAINT DF_app_user_must_change DEFAULT 1,
    failed_attempts              INT             NOT NULL CONSTRAINT DF_app_user_failed DEFAULT 0,
    locked_until                 DATETIME2(0)    NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_app_user_created DEFAULT SYSUTCDATETIME(),
    password_changed_at          DATETIME2(0)    NULL,
    last_login_at                DATETIME2(0)    NULL,
    CONSTRAINT PK_app_user PRIMARY KEY (user_id),
    CONSTRAINT UQ_app_user_login UNIQUE (login)
);
GO

IF OBJECT_ID(N'app.user_role') IS NULL
CREATE TABLE app.user_role (
    user_id                      INT             NOT NULL,
    role_name                    NVARCHAR(30)    NOT NULL,
    CONSTRAINT PK_user_role PRIMARY KEY (user_id, role_name),
    CONSTRAINT FK_user_role_user FOREIGN KEY (user_id) REFERENCES app.app_user(user_id),
    CONSTRAINT CK_user_role_name CHECK (role_name IN (N'cliente', N'cajero', N'tienda', N'atencion', N'marketing',
        N'rrhh', N'manager', N'empleado', N'direccion', N'profesor', N'admin'))
);
GO

/* Ámbito: a qué entidad se ata el usuario (su cliente, su empleado, su tienda). */
IF OBJECT_ID(N'app.user_scope') IS NULL
CREATE TABLE app.user_scope (
    user_id                      INT             NOT NULL,
    scope_type                   NVARCHAR(20)    NOT NULL,   -- customer | employee | store
    scope_value                  NVARCHAR(50)    NOT NULL,
    CONSTRAINT PK_user_scope PRIMARY KEY (user_id, scope_type, scope_value),
    CONSTRAINT FK_user_scope_user FOREIGN KEY (user_id) REFERENCES app.app_user(user_id),
    CONSTRAINT CK_user_scope_type CHECK (scope_type IN (N'customer', N'employee', N'store'))
);
GO

/* Solo se guarda el hash SHA-256 del token; el token viaja en la cookie. */
CREATE TABLE app.user_session (
    session_hash                 VARBINARY(32)   NOT NULL,
    user_id                      INT             NOT NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_session_created DEFAULT SYSUTCDATETIME(),
    expires_at                   DATETIME2(0)    NOT NULL,
    user_agent                   NVARCHAR(300)   NULL,
    CONSTRAINT PK_user_session PRIMARY KEY (session_hash),
    CONSTRAINT FK_user_session_user FOREIGN KEY (user_id) REFERENCES app.app_user(user_id)
);
GO
CREATE INDEX IX_user_session_user ON app.user_session(user_id, expires_at);
GO

CREATE PROCEDURE app.usp_user_create
    @login NVARCHAR(100), @display_name NVARCHAR(200),
    @password_hash VARBINARY(64), @password_salt VARBINARY(32),
    @scrypt_n INT, @scrypt_r INT, @scrypt_p INT,
    @must_change BIT = 1
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM app.app_user WHERE login = @login)
        THROW 50010, N'Ya existe un usuario con ese login.', 1;
    INSERT INTO app.app_user (login, display_name, password_hash, password_salt, scrypt_n, scrypt_r, scrypt_p, must_change_password)
    VALUES (@login, @display_name, @password_hash, @password_salt, @scrypt_n, @scrypt_r, @scrypt_p, @must_change);
    SELECT CAST(SCOPE_IDENTITY() AS INT) AS user_id;
END
GO

CREATE PROCEDURE app.usp_user_set_password
    @login NVARCHAR(100), @password_hash VARBINARY(64), @password_salt VARBINARY(32),
    @scrypt_n INT, @scrypt_r INT, @scrypt_p INT, @must_change BIT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE app.app_user
       SET password_hash = @password_hash, password_salt = @password_salt,
           scrypt_n = @scrypt_n, scrypt_r = @scrypt_r, scrypt_p = @scrypt_p,
           must_change_password = @must_change, failed_attempts = 0, locked_until = NULL,
           password_changed_at = SYSUTCDATETIME()
     WHERE login = @login;
    IF @@ROWCOUNT = 0 THROW 50011, N'Usuario no encontrado.', 1;
    -- Un cambio de contraseña cierra las demás sesiones.
    DELETE s FROM app.user_session s JOIN app.app_user u ON u.user_id = s.user_id WHERE u.login = @login;
END
GO

CREATE PROCEDURE app.usp_user_set_active @login NVARCHAR(100), @is_active BIT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE app.app_user SET is_active = @is_active WHERE login = @login;
    IF @@ROWCOUNT = 0 THROW 50011, N'Usuario no encontrado.', 1;
    IF @is_active = 0
        DELETE s FROM app.user_session s JOIN app.app_user u ON u.user_id = s.user_id WHERE u.login = @login;
END
GO

CREATE PROCEDURE app.usp_user_set_role @login NVARCHAR(100), @role_name NVARCHAR(30), @grant BIT = 1
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @user_id INT = (SELECT user_id FROM app.app_user WHERE login = @login);
    IF @user_id IS NULL THROW 50011, N'Usuario no encontrado.', 1;
    IF @grant = 1 AND NOT EXISTS (SELECT 1 FROM app.user_role WHERE user_id = @user_id AND role_name = @role_name)
        INSERT INTO app.user_role (user_id, role_name) VALUES (@user_id, @role_name);
    IF @grant = 0
        DELETE FROM app.user_role WHERE user_id = @user_id AND role_name = @role_name;
END
GO

CREATE PROCEDURE app.usp_user_set_scope @login NVARCHAR(100), @scope_type NVARCHAR(20), @scope_value NVARCHAR(50), @grant BIT = 1
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @user_id INT = (SELECT user_id FROM app.app_user WHERE login = @login);
    IF @user_id IS NULL THROW 50011, N'Usuario no encontrado.', 1;
    IF @scope_type = N'customer' AND NOT EXISTS (SELECT 1 FROM crm.customer WHERE customer_id = @scope_value)
        THROW 50012, N'El cliente no existe.', 1;
    IF @scope_type = N'employee' AND NOT EXISTS (SELECT 1 FROM hr.employee WHERE employee_id = @scope_value)
        THROW 50013, N'El empleado no existe.', 1;
    IF @scope_type = N'store' AND NOT EXISTS (SELECT 1 FROM store.store WHERE store_id = @scope_value)
        THROW 50014, N'La tienda no existe.', 1;
    IF @grant = 1 AND NOT EXISTS (SELECT 1 FROM app.user_scope WHERE user_id = @user_id AND scope_type = @scope_type AND scope_value = @scope_value)
        INSERT INTO app.user_scope (user_id, scope_type, scope_value) VALUES (@user_id, @scope_type, @scope_value);
    IF @grant = 0
        DELETE FROM app.user_scope WHERE user_id = @user_id AND scope_type = @scope_type AND scope_value = @scope_value;
END
GO

/* Registra un intento fallido y bloquea 15 minutos al quinto. */
CREATE PROCEDURE app.usp_login_failed @login NVARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE app.app_user
       SET failed_attempts = failed_attempts + 1,
           locked_until = CASE WHEN failed_attempts + 1 >= 5 THEN DATEADD(MINUTE, 15, SYSUTCDATETIME()) ELSE locked_until END
     WHERE login = @login;
END
GO

CREATE PROCEDURE app.usp_login_succeeded
    @login NVARCHAR(100), @session_hash VARBINARY(32), @hours INT = 8, @user_agent NVARCHAR(300) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @user_id INT = (SELECT user_id FROM app.app_user WHERE login = @login AND is_active = 1);
    IF @user_id IS NULL THROW 50011, N'Usuario no encontrado.', 1;
    BEGIN TRAN;
        UPDATE app.app_user SET failed_attempts = 0, locked_until = NULL, last_login_at = SYSUTCDATETIME() WHERE user_id = @user_id;
        DELETE FROM app.user_session WHERE user_id = @user_id AND expires_at < SYSUTCDATETIME();
        INSERT INTO app.user_session (session_hash, user_id, expires_at, user_agent)
        VALUES (@session_hash, @user_id, DATEADD(HOUR, @hours, SYSUTCDATETIME()), LEFT(@user_agent, 300));
    COMMIT;
END
GO

CREATE PROCEDURE app.usp_logout @session_hash VARBINARY(32)
AS
BEGIN
    SET NOCOUNT ON;
    DELETE FROM app.user_session WHERE session_hash = @session_hash;
END
GO

/* ---------- outbox hacia Cosmos DB ---------- */

/* Los procedimientos que generan documentos para Cosmos los encolan aquí
   dentro de su propia transacción; la API los envía después y los marca.
   Si Cosmos falla, quedan pendientes y se reintentan. */
CREATE TABLE app.outbox (
    outbox_id                    BIGINT IDENTITY(1,1) NOT NULL,
    container_name               NVARCHAR(50)    NOT NULL,
    operation                    NVARCHAR(10)    NOT NULL CONSTRAINT DF_outbox_operation DEFAULT N'upsert',
    document_json                NVARCHAR(MAX)   NOT NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_outbox_created DEFAULT SYSUTCDATETIME(),
    attempts                     INT             NOT NULL CONSTRAINT DF_outbox_attempts DEFAULT 0,
    last_error                   NVARCHAR(1000)  NULL,
    sent_at                      DATETIME2(0)    NULL,
    CONSTRAINT PK_outbox PRIMARY KEY (outbox_id),
    CONSTRAINT CK_outbox_operation CHECK (operation IN (N'upsert', N'delete'))
);
GO
CREATE INDEX IX_outbox_pending ON app.outbox(sent_at, outbox_id);
GO

CREATE PROCEDURE app.usp_outbox_enqueue @container_name NVARCHAR(50), @document_json NVARCHAR(MAX), @operation NVARCHAR(10) = N'upsert'
AS
BEGIN
    SET NOCOUNT ON;
    IF ISJSON(@document_json) = 0 THROW 50020, N'El documento no es JSON válido.', 1;
    INSERT INTO app.outbox (container_name, operation, document_json) VALUES (@container_name, @operation, @document_json);
    SELECT CAST(SCOPE_IDENTITY() AS BIGINT) AS outbox_id;
END
GO

CREATE PROCEDURE app.usp_outbox_mark @outbox_id BIGINT, @ok BIT, @error NVARCHAR(1000) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE app.outbox
       SET attempts = attempts + 1,
           sent_at = CASE WHEN @ok = 1 THEN SYSUTCDATETIME() ELSE NULL END,
           last_error = CASE WHEN @ok = 1 THEN NULL ELSE LEFT(@error, 1000) END
     WHERE outbox_id = @outbox_id;
END
GO

/* ---------- idempotencia y auditoría ---------- */

CREATE TABLE app.idempotency_key (
    idempotency_key              NVARCHAR(100)   NOT NULL,
    user_id                      INT             NOT NULL,
    request_path                 NVARCHAR(200)   NOT NULL,
    status_code                  INT             NOT NULL,
    response_body                NVARCHAR(MAX)   NOT NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_idempotency_created DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_idempotency_key PRIMARY KEY (user_id, idempotency_key)
);
GO

CREATE PROCEDURE app.usp_idempotency_save
    @idempotency_key NVARCHAR(100), @user_id INT, @request_path NVARCHAR(200), @status_code INT, @response_body NVARCHAR(MAX)
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM app.idempotency_key WHERE user_id = @user_id AND idempotency_key = @idempotency_key)
        INSERT INTO app.idempotency_key (idempotency_key, user_id, request_path, status_code, response_body)
        VALUES (@idempotency_key, @user_id, @request_path, @status_code, @response_body);
    DELETE FROM app.idempotency_key WHERE created_at < DATEADD(DAY, -2, SYSUTCDATETIME());
END
GO

CREATE TABLE app.audit_log (
    audit_id                     BIGINT IDENTITY(1,1) NOT NULL,
    logged_at                    DATETIME2(0)    NOT NULL CONSTRAINT DF_audit_logged DEFAULT SYSUTCDATETIME(),
    user_login                   NVARCHAR(100)   NULL,
    action_name                  NVARCHAR(100)   NOT NULL,
    entity_name                  NVARCHAR(100)   NULL,
    entity_id                    NVARCHAR(100)   NULL,
    detail                       NVARCHAR(2000)  NULL,
    CONSTRAINT PK_audit_log PRIMARY KEY (audit_id)
);
GO
CREATE INDEX IX_audit_log_entity ON app.audit_log(entity_name, entity_id);
GO

CREATE PROCEDURE app.usp_audit @user_login NVARCHAR(100), @action_name NVARCHAR(100), @entity_name NVARCHAR(100) = NULL,
    @entity_id NVARCHAR(100) = NULL, @detail NVARCHAR(2000) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO app.audit_log (user_login, action_name, entity_name, entity_id, detail)
    VALUES (@user_login, @action_name, @entity_name, @entity_id, @detail);
END
GO
