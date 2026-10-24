/* =====================================================================
   FraSoHome Live · 01_core.sql
   Núcleo operacional de retail. Parte del core del escenario 03
   (fabric_databases/01_FraSoHome_Core.sql) con estos cambios:
   - quality.data_quality_issue guarda el fichero y la fila de origen
   - return_header admite método de devolución online
   - inventory.stock_level y stock_movement para el stock vivo
   - store.till_session para abrir y cerrar caja
   Reglas para el mirroring futuro a Fabric: sin tipos json/xml/text,
   sin columnas calculadas, sin datetime2(7), sin tablas temporales.
   Se ejecuta sobre una base vacía (sql/00_borrar.sql la deja así).
   Las fechas son DATETIME2(0): los datos de origen llegan al segundo.
   ===================================================================== */

IF SCHEMA_ID('crm') IS NULL EXEC('CREATE SCHEMA crm');
GO
IF SCHEMA_ID('catalog') IS NULL EXEC('CREATE SCHEMA catalog');
GO
IF SCHEMA_ID('store') IS NULL EXEC('CREATE SCHEMA store');
GO
IF SCHEMA_ID('sales') IS NULL EXEC('CREATE SCHEMA sales');
GO
IF SCHEMA_ID('returns') IS NULL EXEC('CREATE SCHEMA [returns]');
GO
IF SCHEMA_ID('inventory') IS NULL EXEC('CREATE SCHEMA inventory');
GO
IF SCHEMA_ID('quality') IS NULL EXEC('CREATE SCHEMA quality');
GO

CREATE TABLE crm.customer (
    customer_id                  NVARCHAR(50)    NOT NULL,
    first_name                   NVARCHAR(100)   NULL,
    last_name                    NVARCHAR(150)   NULL,
    email                        NVARCHAR(255)   NULL,
    email_is_valid               BIT             NULL,
    phone                        NVARCHAR(50)    NULL,
    loyalty_joined_at            DATE            NULL,
    loyalty_tier                 NVARCHAR(50)    NULL,
    loyalty_points               INT             NULL,
    birth_date                   DATE            NULL,
    gender                       NVARCHAR(30)    NULL,
    city                         NVARCHAR(100)   NULL,
    province                     NVARCHAR(100)   NULL,
    postal_code                  NVARCHAR(20)    NULL,
    country_code                 CHAR(2)         NULL,
    marketing_consent            BIT             NULL,
    customer_status              NVARCHAR(50)    NOT NULL CONSTRAINT DF_customer_status DEFAULT N'Activo',
    churned_at                   DATE            NULL,
    acquisition_source           NVARCHAR(50)    NULL,
    preferred_channel            NVARCHAR(50)    NULL,
    source_updated_at            DATETIME2(0)    NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_customer_created_at DEFAULT SYSUTCDATETIME(),
    updated_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_customer_updated_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_customer PRIMARY KEY (customer_id),
    CONSTRAINT CK_customer_status CHECK (customer_status IN (N'Activo', N'Inactivo', N'Bloqueado')),
    CONSTRAINT CK_customer_points CHECK (loyalty_points IS NULL OR loyalty_points >= 0)
);
GO

CREATE TABLE catalog.product (
    product_id                   NVARCHAR(50)    NOT NULL,
    product_name                 NVARCHAR(255)   NOT NULL,
    category                     NVARCHAR(100)   NULL,
    subcategory                  NVARCHAR(100)   NULL,
    brand                        NVARCHAR(100)   NULL,
    supplier                     NVARCHAR(100)   NULL,
    material                     NVARCHAR(100)   NULL,
    color                        NVARCHAR(100)   NULL,
    sale_price                   DECIMAL(18,2)   NULL,
    unit_cost                    DECIMAL(18,2)   NULL,
    vat_pct                      DECIMAL(9,4)    NULL,
    weight_kg                    DECIMAL(18,3)   NULL,
    length_cm                    DECIMAL(18,2)   NULL,
    width_cm                     DECIMAL(18,2)   NULL,
    height_cm                    DECIMAL(18,2)   NULL,
    catalog_start_date           DATE            NULL,
    product_status               NVARCHAR(50)    NOT NULL CONSTRAINT DF_product_status DEFAULT N'Activo',
    ean                          NVARCHAR(30)    NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_product_created_at DEFAULT SYSUTCDATETIME(),
    updated_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_product_updated_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_product PRIMARY KEY (product_id),
    CONSTRAINT CK_product_status CHECK (product_status IN (N'Activo', N'Descatalogado')),
    CONSTRAINT CK_product_price CHECK (sale_price IS NULL OR sale_price > 0),
    CONSTRAINT CK_product_cost CHECK (unit_cost IS NULL OR unit_cost >= 0)
);
GO

CREATE TABLE store.store (
    store_id                     NVARCHAR(50)    NOT NULL,
    store_name                   NVARCHAR(150)   NOT NULL,
    location_type                NVARCHAR(50)    NULL,
    channel                      NVARCHAR(50)    NULL,
    city                         NVARCHAR(100)   NULL,
    province                     NVARCHAR(100)   NULL,
    address_line                 NVARCHAR(255)   NULL,
    postal_code                  NVARCHAR(20)    NULL,
    country_code                 CHAR(2)         NULL,
    opened_at                    DATE            NULL,
    square_meters                INT             NULL,
    phone                        NVARCHAR(50)    NULL,
    opening_hours                NVARCHAR(100)   NULL,
    latitude                     DECIMAL(10,6)   NULL,
    longitude                    DECIMAL(10,6)   NULL,
    store_status                 NVARCHAR(50)    NOT NULL CONSTRAINT DF_store_status DEFAULT N'Activa',
    region                       NVARCHAR(100)   NULL,
    manager_name                 NVARCHAR(150)   NULL,
    notes                        NVARCHAR(500)   NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_store_created_at DEFAULT SYSUTCDATETIME(),
    updated_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_store_updated_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_store PRIMARY KEY (store_id),
    CONSTRAINT CK_store_status CHECK (store_status IN (N'Activa', N'Planificada', N'Cerrada')),
    CONSTRAINT CK_store_lat CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90)
);
GO

CREATE TABLE store.till_session (
    till_session_id              BIGINT IDENTITY(1,1) NOT NULL,
    store_id                     NVARCHAR(50)    NOT NULL,
    till_id                      NVARCHAR(50)    NOT NULL,
    cashier_id                   NVARCHAR(50)    NOT NULL,
    opened_at                    DATETIME2(0)    NOT NULL CONSTRAINT DF_till_session_opened DEFAULT SYSUTCDATETIME(),
    opening_cash                 DECIMAL(18,2)   NOT NULL CONSTRAINT DF_till_session_cash DEFAULT 0,
    closed_at                    DATETIME2(0)    NULL,
    expected_cash                DECIMAL(18,2)   NULL,
    counted_cash                 DECIMAL(18,2)   NULL,
    session_status               NVARCHAR(20)    NOT NULL CONSTRAINT DF_till_session_status DEFAULT N'Abierta',
    CONSTRAINT PK_till_session PRIMARY KEY (till_session_id),
    CONSTRAINT FK_till_session_store FOREIGN KEY (store_id) REFERENCES store.store(store_id),
    CONSTRAINT CK_till_session_status CHECK (session_status IN (N'Abierta', N'Cerrada'))
);
GO

CREATE TABLE sales.online_order (
    order_id                     NVARCHAR(50)    NOT NULL,
    ordered_at                   DATETIME2(0)    NULL,
    customer_id                  NVARCHAR(50)    NULL,
    online_user_id               NVARCHAR(50)    NULL,
    order_total                  DECIMAL(18,2)   NULL,
    currency_code                CHAR(3)         NOT NULL CONSTRAINT DF_online_order_currency DEFAULT 'EUR',
    shipping_amount              DECIMAL(18,2)   NULL,
    shipping_address             NVARCHAR(255)   NULL,
    shipping_postal_code         NVARCHAR(20)    NULL,
    shipping_city                NVARCHAR(100)   NULL,
    shipping_province            NVARCHAR(100)   NULL,
    shipping_country_code        CHAR(2)         NULL,
    payment_method               NVARCHAR(50)    NULL,
    order_status                 NVARCHAR(50)    NOT NULL CONSTRAINT DF_online_order_status DEFAULT N'Pendiente',
    order_origin                 NVARCHAR(50)    NULL,
    coupon_instance_id           NVARCHAR(50)    NULL,
    source_updated_at            DATETIME2(0)    NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_online_order_created_at DEFAULT SYSUTCDATETIME(),
    updated_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_online_order_updated_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_online_order PRIMARY KEY (order_id),
    CONSTRAINT FK_online_order_customer FOREIGN KEY (customer_id) REFERENCES crm.customer(customer_id),
    CONSTRAINT CK_online_order_status CHECK (order_status IN (N'Pendiente', N'En preparación', N'Entregado', N'Cancelado', N'Devuelto Parcial', N'Devuelto Total'))
);
GO

CREATE TABLE sales.online_order_line (
    order_line_id                NVARCHAR(50)    NOT NULL,
    order_id                     NVARCHAR(50)    NOT NULL,
    product_id                   NVARCHAR(50)    NULL,
    product_description          NVARCHAR(255)   NULL,
    category                     NVARCHAR(100)   NULL,
    subcategory                  NVARCHAR(100)   NULL,
    quantity                     INT             NOT NULL,
    unit_price                   DECIMAL(18,2)   NULL,
    discount_pct                 DECIMAL(9,4)    NULL,
    discount_amount              DECIMAL(18,2)   NULL,
    line_amount                  DECIMAL(18,2)   NULL,
    vat_pct                      DECIMAL(9,4)    NULL,
    promo_id                     NVARCHAR(50)    NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_online_order_line_created_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_online_order_line PRIMARY KEY (order_line_id),
    CONSTRAINT FK_online_order_line_order FOREIGN KEY (order_id) REFERENCES sales.online_order(order_id),
    CONSTRAINT FK_online_order_line_product FOREIGN KEY (product_id) REFERENCES catalog.product(product_id),
    CONSTRAINT CK_online_order_line_qty CHECK (quantity > 0)
);
GO

CREATE TABLE sales.pos_ticket (
    ticket_id                    NVARCHAR(50)    NOT NULL,
    ticket_at                    DATETIME2(0)    NULL,
    store_id                     NVARCHAR(50)    NULL,
    till_id                      NVARCHAR(50)    NULL,
    cashier_id                   NVARCHAR(50)    NULL,   -- código del TPV (EMP###), tal como lo registra la caja
    cashier_employee_id          NVARCHAR(20)    NULL,   -- empleado FSH#### resuelto con xref.employee_alias
    customer_id                  NVARCHAR(50)    NULL,
    currency_code                CHAR(3)         NOT NULL CONSTRAINT DF_pos_ticket_currency DEFAULT 'EUR',
    channel                      NVARCHAR(50)    NOT NULL CONSTRAINT DF_pos_ticket_channel DEFAULT N'POS',
    ticket_gross_amount          DECIMAL(18,2)   NULL,
    ticket_discount_amount       DECIMAL(18,2)   NULL,
    ticket_net_amount            DECIMAL(18,2)   NULL,
    coupon_instance_id           NVARCHAR(50)    NULL,
    till_session_id              BIGINT          NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_pos_ticket_created_at DEFAULT SYSUTCDATETIME(),
    updated_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_pos_ticket_updated_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_pos_ticket PRIMARY KEY (ticket_id),
    CONSTRAINT FK_pos_ticket_store FOREIGN KEY (store_id) REFERENCES store.store(store_id),
    CONSTRAINT FK_pos_ticket_customer FOREIGN KEY (customer_id) REFERENCES crm.customer(customer_id)
);
GO

CREATE TABLE sales.pos_ticket_line (
    ticket_line_id               NVARCHAR(50)    NOT NULL,
    ticket_id                    NVARCHAR(50)    NOT NULL,
    product_id                   NVARCHAR(50)    NULL,
    product_description          NVARCHAR(255)   NULL,
    category                     NVARCHAR(100)   NULL,
    subcategory                  NVARCHAR(100)   NULL,
    quantity                     INT             NOT NULL,
    unit_price                   DECIMAL(18,2)   NULL,
    discount_pct                 DECIMAL(9,4)    NULL,
    discount_amount              DECIMAL(18,2)   NULL,
    line_amount                  DECIMAL(18,2)   NULL,
    promo_id                     NVARCHAR(50)    NULL,
    notes                        NVARCHAR(500)   NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_pos_ticket_line_created_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_pos_ticket_line PRIMARY KEY (ticket_line_id),
    CONSTRAINT FK_pos_ticket_line_ticket FOREIGN KEY (ticket_id) REFERENCES sales.pos_ticket(ticket_id),
    CONSTRAINT FK_pos_ticket_line_product FOREIGN KEY (product_id) REFERENCES catalog.product(product_id),
    CONSTRAINT CK_pos_ticket_line_qty CHECK (quantity > 0)
);
GO

CREATE TABLE sales.store_payment (
    payment_id                   NVARCHAR(50)    NOT NULL,
    ticket_id                    NVARCHAR(50)    NOT NULL,
    paid_at                      DATETIME2(0)    NULL,
    store_id                     NVARCHAR(50)    NULL,
    till_id                      NVARCHAR(50)    NULL,
    cashier_id                   NVARCHAR(50)    NULL,   -- código del TPV (EMP###)
    cashier_employee_id          NVARCHAR(20)    NULL,   -- empleado FSH#### resuelto con xref.employee_alias
    payment_method               NVARCHAR(50)    NULL,
    paid_amount                  DECIMAL(18,2)   NULL,
    currency_code                CHAR(3)         NOT NULL CONSTRAINT DF_store_payment_currency DEFAULT 'EUR',
    authorization_reference      NVARCHAR(100)   NULL,
    payment_status               NVARCHAR(50)    NOT NULL CONSTRAINT DF_store_payment_status DEFAULT N'OK',
    notes                        NVARCHAR(500)   NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_store_payment_created_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_store_payment PRIMARY KEY (payment_id),
    CONSTRAINT FK_store_payment_ticket FOREIGN KEY (ticket_id) REFERENCES sales.pos_ticket(ticket_id),
    CONSTRAINT FK_store_payment_store FOREIGN KEY (store_id) REFERENCES store.store(store_id),
    CONSTRAINT CK_store_payment_status CHECK (payment_status IN (N'OK', N'ANULADO', N'PENDIENTE'))
);
GO

CREATE TABLE [returns].return_header (
    return_id                    NVARCHAR(50)    NOT NULL,
    returned_at                  DATETIME2(0)    NULL,
    return_channel               NVARCHAR(50)    NOT NULL,   -- ONLINE | TIENDA
    store_id                     NVARCHAR(50)    NULL,
    customer_id                  NVARCHAR(50)    NULL,
    original_ticket_id           NVARCHAR(50)    NULL,
    original_order_id            NVARCHAR(50)    NULL,
    return_status                NVARCHAR(50)    NOT NULL CONSTRAINT DF_return_status DEFAULT N'Pendiente',
    return_method                NVARCHAR(50)    NULL,       -- online: Envío, Tienda, Punto Pack
    refund_method                NVARCHAR(50)    NULL,       -- tienda: Tarjeta, Efectivo, Vale...
    currency_code                CHAR(3)         NOT NULL CONSTRAINT DF_return_currency DEFAULT 'EUR',
    notes                        NVARCHAR(500)   NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_return_header_created_at DEFAULT SYSUTCDATETIME(),
    updated_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_return_header_updated_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_return_header PRIMARY KEY (return_id),
    CONSTRAINT FK_return_header_store FOREIGN KEY (store_id) REFERENCES store.store(store_id),
    CONSTRAINT FK_return_header_customer FOREIGN KEY (customer_id) REFERENCES crm.customer(customer_id),
    CONSTRAINT CK_return_channel CHECK (return_channel IN (N'ONLINE', N'TIENDA')),
    CONSTRAINT CK_return_status CHECK (return_status IN (N'Pendiente', N'Aceptada', N'Rechazada', N'Reembolsada'))
);
GO

CREATE TABLE [returns].return_line (
    return_line_id               NVARCHAR(80)    NOT NULL,
    return_id                    NVARCHAR(50)    NOT NULL,
    product_id                   NVARCHAR(50)    NULL,
    original_ticket_line_id      NVARCHAR(50)    NULL,
    original_order_line_id       NVARCHAR(50)    NULL,
    returned_quantity            INT             NOT NULL,
    refund_amount                DECIMAL(18,2)   NULL,
    return_reason                NVARCHAR(200)   NULL,
    original_sales_channel       NVARCHAR(50)    NULL,       -- POS | ONLINE | OMNI
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_return_line_created_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_return_line PRIMARY KEY (return_line_id),
    CONSTRAINT FK_return_line_header FOREIGN KEY (return_id) REFERENCES [returns].return_header(return_id),
    CONSTRAINT FK_return_line_product FOREIGN KEY (product_id) REFERENCES catalog.product(product_id),
    CONSTRAINT CK_return_line_qty CHECK (returned_quantity > 0)
);
GO

CREATE TABLE inventory.stock_snapshot (
    snapshot_date                DATE            NOT NULL,
    store_id                     NVARCHAR(50)    NOT NULL,
    product_id                   NVARCHAR(50)    NOT NULL,
    closing_stock_qty            DECIMAL(18,2)   NULL,
    reserved_stock_qty           DECIMAL(18,2)   NULL,
    in_transit_stock_qty         DECIMAL(18,2)   NULL,
    minimum_stock_qty            DECIMAL(18,2)   NULL,
    source_system                NVARCHAR(50)    NULL,
    notes                        NVARCHAR(500)   NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_stock_snapshot_created_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_stock_snapshot PRIMARY KEY (snapshot_date, store_id, product_id),
    CONSTRAINT FK_stock_snapshot_store FOREIGN KEY (store_id) REFERENCES store.store(store_id),
    CONSTRAINT FK_stock_snapshot_product FOREIGN KEY (product_id) REFERENCES catalog.product(product_id)
);
GO

/* Stock vivo: una fila por tienda y producto. Lo mueven las ventas,
   devoluciones, ajustes y recepciones; el cierre diario lo fotografía
   en stock_snapshot. */
CREATE TABLE inventory.stock_level (
    store_id                     NVARCHAR(50)    NOT NULL,
    product_id                   NVARCHAR(50)    NOT NULL,
    on_hand_qty                  INT             NOT NULL CONSTRAINT DF_stock_level_on_hand DEFAULT 0,
    reserved_qty                 INT             NOT NULL CONSTRAINT DF_stock_level_reserved DEFAULT 0,
    in_transit_qty               INT             NOT NULL CONSTRAINT DF_stock_level_transit DEFAULT 0,
    minimum_qty                  INT             NOT NULL CONSTRAINT DF_stock_level_minimum DEFAULT 0,
    updated_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_stock_level_updated DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_stock_level PRIMARY KEY (store_id, product_id),
    CONSTRAINT FK_stock_level_store FOREIGN KEY (store_id) REFERENCES store.store(store_id),
    CONSTRAINT FK_stock_level_product FOREIGN KEY (product_id) REFERENCES catalog.product(product_id),
    CONSTRAINT CK_stock_level_qty CHECK (on_hand_qty >= 0 AND reserved_qty >= 0 AND in_transit_qty >= 0 AND minimum_qty >= 0)
);
GO

CREATE TABLE inventory.stock_movement (
    movement_id                  BIGINT IDENTITY(1,1) NOT NULL,
    moved_at                     DATETIME2(0)    NOT NULL CONSTRAINT DF_stock_movement_moved DEFAULT SYSUTCDATETIME(),
    store_id                     NVARCHAR(50)    NOT NULL,
    product_id                   NVARCHAR(50)    NOT NULL,
    movement_type                NVARCHAR(30)    NOT NULL,
    on_hand_delta                INT             NOT NULL CONSTRAINT DF_stock_movement_on_hand DEFAULT 0,
    reserved_delta               INT             NOT NULL CONSTRAINT DF_stock_movement_reserved DEFAULT 0,
    in_transit_delta             INT             NOT NULL CONSTRAINT DF_stock_movement_transit DEFAULT 0,
    document_type                NVARCHAR(30)    NULL,
    document_id                  NVARCHAR(50)    NULL,
    user_login                   NVARCHAR(100)   NULL,
    notes                        NVARCHAR(500)   NULL,
    CONSTRAINT PK_stock_movement PRIMARY KEY (movement_id),
    CONSTRAINT CK_stock_movement_type CHECK (movement_type IN (N'VENTA', N'DEVOLUCION', N'AJUSTE', N'RECEPCION', N'ENVIO', N'CANCELACION'))
);
GO

CREATE TABLE quality.data_quality_issue (
    issue_id                     BIGINT IDENTITY(1,1) NOT NULL,
    source_database              NVARCHAR(128)   NOT NULL CONSTRAINT DF_dq_issue_db DEFAULT N'frasohome-oltp',
    source_schema                NVARCHAR(128)   NOT NULL,
    source_table                 NVARCHAR(128)   NOT NULL,
    source_file                  NVARCHAR(260)   NULL,
    source_key                   NVARCHAR(255)   NULL,
    issue_type                   NVARCHAR(100)   NOT NULL,
    issue_severity               NVARCHAR(20)    NOT NULL,   -- rechazo | corregido | aviso
    issue_description            NVARCHAR(1000)  NOT NULL,
    source_row                   NVARCHAR(MAX)   NULL,       -- fila original en JSON
    detected_at                  DATETIME2(0)    NOT NULL CONSTRAINT DF_dq_issue_detected_at DEFAULT SYSUTCDATETIME(),
    resolved_at                  DATETIME2(0)    NULL,
    CONSTRAINT PK_data_quality_issue PRIMARY KEY (issue_id),
    CONSTRAINT CK_dq_issue_severity CHECK (issue_severity IN (N'rechazo', N'corregido', N'aviso'))
);
GO

CREATE INDEX IX_customer_email ON crm.customer(email);
CREATE INDEX IX_product_category ON catalog.product(category, subcategory);
CREATE INDEX IX_online_order_customer_date ON sales.online_order(customer_id, ordered_at);
CREATE INDEX IX_online_order_line_order ON sales.online_order_line(order_id);
CREATE INDEX IX_pos_ticket_store_date ON sales.pos_ticket(store_id, ticket_at);
CREATE INDEX IX_pos_ticket_customer ON sales.pos_ticket(customer_id, ticket_at);
CREATE INDEX IX_pos_ticket_line_ticket ON sales.pos_ticket_line(ticket_id);
CREATE INDEX IX_store_payment_ticket ON sales.store_payment(ticket_id);
CREATE INDEX IX_return_header_customer_date ON [returns].return_header(customer_id, returned_at);
CREATE INDEX IX_return_line_return ON [returns].return_line(return_id);
CREATE INDEX IX_stock_snapshot_product_date ON inventory.stock_snapshot(product_id, snapshot_date);
CREATE INDEX IX_stock_movement_store_product ON inventory.stock_movement(store_id, product_id, moved_at);
CREATE INDEX IX_dq_issue_table ON quality.data_quality_issue(source_schema, source_table, issue_type);
GO
