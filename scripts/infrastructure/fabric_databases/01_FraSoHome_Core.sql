IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'crm') EXEC('CREATE SCHEMA crm');
GO
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'catalog') EXEC('CREATE SCHEMA catalog');
GO
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'store') EXEC('CREATE SCHEMA store');
GO
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'sales') EXEC('CREATE SCHEMA sales');
GO
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'returns') EXEC('CREATE SCHEMA [returns]');
GO
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'inventory') EXEC('CREATE SCHEMA inventory');
GO
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'quality') EXEC('CREATE SCHEMA quality');
GO

CREATE TABLE crm.customer (
    customer_id                  NVARCHAR(50)    NOT NULL,
    customer_id_raw              NVARCHAR(50)    NULL,
    first_name                   NVARCHAR(100)   NULL,
    last_name                    NVARCHAR(150)   NULL,
    email                        NVARCHAR(255)   NULL,
    phone                        NVARCHAR(50)    NULL,
    loyalty_joined_at            DATETIME2(0)    NULL,
    loyalty_tier                 NVARCHAR(50)    NULL,
    loyalty_points               INT             NULL,
    birth_date                   DATE            NULL,
    gender                       NVARCHAR(30)    NULL,
    city                         NVARCHAR(100)   NULL,
    province                     NVARCHAR(100)   NULL,
    postal_code                  NVARCHAR(20)    NULL,
    country_code                 CHAR(2)         NULL,
    marketing_consent            BIT             NULL,
    customer_status              NVARCHAR(50)    NULL,
    churned_at                   DATE            NULL,
    acquisition_source           NVARCHAR(50)    NULL,
    preferred_channel            NVARCHAR(50)    NULL,
    source_updated_at            DATETIME2(0)    NULL,
    record_hash                  VARBINARY(32)   NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_customer_created_at DEFAULT SYSUTCDATETIME(),
    updated_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_customer_updated_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_customer PRIMARY KEY (customer_id)
);
GO

CREATE TABLE catalog.product (
    product_id                   NVARCHAR(50)    NOT NULL,
    product_id_raw               NVARCHAR(50)    NULL,
    product_name                 NVARCHAR(255)   NULL,
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
    product_status               NVARCHAR(50)    NULL,
    ean                          NVARCHAR(30)    NULL,
    record_hash                  VARBINARY(32)   NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_product_created_at DEFAULT SYSUTCDATETIME(),
    updated_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_product_updated_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_product PRIMARY KEY (product_id)
);
GO

CREATE TABLE store.store (
    store_id                     NVARCHAR(50)    NOT NULL,
    store_id_raw                 NVARCHAR(50)    NULL,
    store_name                   NVARCHAR(150)   NULL,
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
    store_status                 NVARCHAR(50)    NULL,
    region                       NVARCHAR(100)   NULL,
    manager_name                 NVARCHAR(150)   NULL,
    notes                        NVARCHAR(500)   NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_store_created_at DEFAULT SYSUTCDATETIME(),
    updated_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_store_updated_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_store PRIMARY KEY (store_id)
);
GO

CREATE TABLE sales.online_order (
    order_id                     NVARCHAR(50)    NOT NULL,
    ordered_at                   DATETIME2(0)    NULL,
    customer_id                  NVARCHAR(50)    NULL,
    online_user_id               NVARCHAR(50)    NULL,
    order_total                  DECIMAL(18,2)   NULL,
    currency_code                CHAR(3)         NULL,
    shipping_amount              DECIMAL(18,2)   NULL,
    shipping_address             NVARCHAR(255)   NULL,
    shipping_postal_code         NVARCHAR(20)    NULL,
    shipping_city                NVARCHAR(100)   NULL,
    shipping_province            NVARCHAR(100)   NULL,
    shipping_country_code        CHAR(2)         NULL,
    payment_method               NVARCHAR(50)    NULL,
    order_status                 NVARCHAR(50)    NULL,
    order_origin                 NVARCHAR(50)    NULL,
    source_updated_at            DATETIME2(0)    NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_online_order_created_at DEFAULT SYSUTCDATETIME(),
    updated_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_online_order_updated_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_online_order PRIMARY KEY (order_id),
    CONSTRAINT FK_online_order_customer FOREIGN KEY (customer_id) REFERENCES crm.customer(customer_id)
);
GO

CREATE TABLE sales.online_order_line (
    order_line_id                NVARCHAR(50)    NOT NULL,
    order_id                     NVARCHAR(50)    NOT NULL,
    product_id                   NVARCHAR(50)    NULL,
    product_description          NVARCHAR(255)   NULL,
    category                     NVARCHAR(100)   NULL,
    subcategory                  NVARCHAR(100)   NULL,
    quantity                     INT             NULL,
    unit_price                   DECIMAL(18,2)   NULL,
    discount_pct                 DECIMAL(9,4)    NULL,
    discount_amount              DECIMAL(18,2)   NULL,
    line_amount                  DECIMAL(18,2)   NULL,
    vat_pct                      DECIMAL(9,4)    NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_online_order_line_created_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_online_order_line PRIMARY KEY (order_line_id),
    CONSTRAINT FK_online_order_line_order FOREIGN KEY (order_id) REFERENCES sales.online_order(order_id),
    CONSTRAINT FK_online_order_line_product FOREIGN KEY (product_id) REFERENCES catalog.product(product_id)
);
GO

CREATE TABLE sales.pos_ticket (
    ticket_id                    NVARCHAR(50)    NOT NULL,
    ticket_at                    DATETIME2(0)    NULL,
    store_id                     NVARCHAR(50)    NULL,
    till_id                      NVARCHAR(50)    NULL,
    cashier_id                   NVARCHAR(50)    NULL,
    customer_id                  NVARCHAR(50)    NULL,
    currency_code                CHAR(3)         NULL,
    channel                      NVARCHAR(50)    NULL,
    ticket_gross_amount          DECIMAL(18,2)   NULL,
    ticket_discount_amount       DECIMAL(18,2)   NULL,
    ticket_net_amount            DECIMAL(18,2)   NULL,
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
    quantity                     INT             NULL,
    unit_price                   DECIMAL(18,2)   NULL,
    discount_pct                 DECIMAL(9,4)    NULL,
    discount_amount              DECIMAL(18,2)   NULL,
    line_amount                  DECIMAL(18,2)   NULL,
    notes                        NVARCHAR(500)   NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_pos_ticket_line_created_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_pos_ticket_line PRIMARY KEY (ticket_line_id),
    CONSTRAINT FK_pos_ticket_line_ticket FOREIGN KEY (ticket_id) REFERENCES sales.pos_ticket(ticket_id),
    CONSTRAINT FK_pos_ticket_line_product FOREIGN KEY (product_id) REFERENCES catalog.product(product_id)
);
GO

CREATE TABLE sales.store_payment (
    payment_id                   NVARCHAR(50)    NOT NULL,
    ticket_id                    NVARCHAR(50)    NULL,
    paid_at                      DATETIME2(0)    NULL,
    store_id                     NVARCHAR(50)    NULL,
    till_id                      NVARCHAR(50)    NULL,
    cashier_id                   NVARCHAR(50)    NULL,
    payment_method               NVARCHAR(50)    NULL,
    paid_amount                  DECIMAL(18,2)   NULL,
    currency_code                CHAR(3)         NULL,
    authorization_reference      NVARCHAR(100)   NULL,
    payment_status               NVARCHAR(50)    NULL,
    notes                        NVARCHAR(500)   NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_store_payment_created_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_store_payment PRIMARY KEY (payment_id),
    CONSTRAINT FK_store_payment_ticket FOREIGN KEY (ticket_id) REFERENCES sales.pos_ticket(ticket_id),
    CONSTRAINT FK_store_payment_store FOREIGN KEY (store_id) REFERENCES store.store(store_id)
);
GO

CREATE TABLE [returns].return_header (
    return_id                    NVARCHAR(50)    NOT NULL,
    returned_at                  DATETIME2(0)    NULL,
    return_channel               NVARCHAR(50)    NOT NULL,
    store_id                     NVARCHAR(50)    NULL,
    customer_id                  NVARCHAR(50)    NULL,
    original_ticket_id           NVARCHAR(50)    NULL,
    original_order_id            NVARCHAR(50)    NULL,
    return_status                NVARCHAR(50)    NULL,
    refund_method                NVARCHAR(50)    NULL,
    currency_code                CHAR(3)         NULL,
    notes                        NVARCHAR(500)   NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_return_header_created_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_return_header PRIMARY KEY (return_id),
    CONSTRAINT FK_return_header_store FOREIGN KEY (store_id) REFERENCES store.store(store_id),
    CONSTRAINT FK_return_header_customer FOREIGN KEY (customer_id) REFERENCES crm.customer(customer_id)
);
GO

CREATE TABLE [returns].return_line (
    return_line_id               NVARCHAR(80)    NOT NULL,
    return_id                    NVARCHAR(50)    NOT NULL,
    product_id                   NVARCHAR(50)    NULL,
    original_ticket_line_id      NVARCHAR(50)    NULL,
    original_order_line_id       NVARCHAR(50)    NULL,
    returned_quantity            INT             NULL,
    refund_amount                DECIMAL(18,2)   NULL,
    return_reason                NVARCHAR(200)   NULL,
    original_sales_channel       NVARCHAR(50)    NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_return_line_created_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_return_line PRIMARY KEY (return_line_id),
    CONSTRAINT FK_return_line_header FOREIGN KEY (return_id) REFERENCES [returns].return_header(return_id),
    CONSTRAINT FK_return_line_product FOREIGN KEY (product_id) REFERENCES catalog.product(product_id)
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

CREATE TABLE quality.data_quality_issue (
    issue_id                     BIGINT IDENTITY(1,1) NOT NULL,
    source_database              NVARCHAR(128)   NOT NULL,
    source_schema                NVARCHAR(128)   NOT NULL,
    source_table                 NVARCHAR(128)   NOT NULL,
    source_key                   NVARCHAR(255)   NULL,
    issue_type                   NVARCHAR(100)   NOT NULL,
    issue_severity               NVARCHAR(20)    NOT NULL,
    issue_description            NVARCHAR(1000)  NOT NULL,
    detected_at                  DATETIME2(0)    NOT NULL CONSTRAINT DF_dq_issue_detected_at DEFAULT SYSUTCDATETIME(),
    resolved_at                  DATETIME2(0)    NULL,
    CONSTRAINT PK_data_quality_issue PRIMARY KEY (issue_id)
);
GO

CREATE INDEX IX_customer_email ON crm.customer(email);
GO
CREATE INDEX IX_product_category ON catalog.product(category, subcategory);
GO
CREATE INDEX IX_online_order_customer_date ON sales.online_order(customer_id, ordered_at);
GO
CREATE INDEX IX_pos_ticket_store_date ON sales.pos_ticket(store_id, ticket_at);
GO
CREATE INDEX IX_return_header_customer_date ON [returns].return_header(customer_id, returned_at);
GO
CREATE INDEX IX_stock_snapshot_product_date ON inventory.stock_snapshot(product_id, snapshot_date);
GO
