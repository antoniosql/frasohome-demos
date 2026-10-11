IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'dw') EXEC('CREATE SCHEMA dw');
GO

CREATE TABLE dw.dim_date (
    date_key                     INT             NOT NULL,
    full_date                    DATE            NOT NULL,
    day_of_month                 TINYINT         NOT NULL,
    month_number                 TINYINT         NOT NULL,
    month_name                   NVARCHAR(20)    NOT NULL,
    quarter_number               TINYINT         NOT NULL,
    year_number                  SMALLINT        NOT NULL,
    week_of_year                 TINYINT         NOT NULL,
    is_weekend                   BIT             NOT NULL,
    CONSTRAINT PK_dim_date PRIMARY KEY (date_key)
);
GO

CREATE TABLE dw.dim_customer (
    customer_key                 BIGINT IDENTITY(1,1) NOT NULL,
    customer_id                  NVARCHAR(50)    NOT NULL,
    full_name                    NVARCHAR(255)   NULL,
    loyalty_tier                 NVARCHAR(50)    NULL,
    customer_status              NVARCHAR(50)    NULL,
    city                         NVARCHAR(100)   NULL,
    province                     NVARCHAR(100)   NULL,
    country_code                 CHAR(2)         NULL,
    marketing_consent            BIT             NULL,
    preferred_channel            NVARCHAR(50)    NULL,
    valid_from                   DATETIME2(0)    NOT NULL CONSTRAINT DF_dim_customer_valid_from DEFAULT SYSUTCDATETIME(),
    valid_to                     DATETIME2(0)    NULL,
    is_current                   BIT             NOT NULL CONSTRAINT DF_dim_customer_is_current DEFAULT 1,
    CONSTRAINT PK_dim_customer PRIMARY KEY (customer_key),
    CONSTRAINT UQ_dim_customer_current UNIQUE (customer_id, valid_from)
);
GO

CREATE TABLE dw.dim_product (
    product_key                  BIGINT IDENTITY(1,1) NOT NULL,
    product_id                   NVARCHAR(50)    NOT NULL,
    product_name                 NVARCHAR(255)   NULL,
    category                     NVARCHAR(100)   NULL,
    subcategory                  NVARCHAR(100)   NULL,
    brand                        NVARCHAR(100)   NULL,
    supplier                     NVARCHAR(100)   NULL,
    material                     NVARCHAR(100)   NULL,
    color                        NVARCHAR(100)   NULL,
    product_status               NVARCHAR(50)    NULL,
    sale_price                   DECIMAL(18,2)   NULL,
    unit_cost                    DECIMAL(18,2)   NULL,
    vat_pct                      DECIMAL(9,4)    NULL,
    valid_from                   DATETIME2(0)    NOT NULL CONSTRAINT DF_dim_product_valid_from DEFAULT SYSUTCDATETIME(),
    valid_to                     DATETIME2(0)    NULL,
    is_current                   BIT             NOT NULL CONSTRAINT DF_dim_product_is_current DEFAULT 1,
    CONSTRAINT PK_dim_product PRIMARY KEY (product_key),
    CONSTRAINT UQ_dim_product_current UNIQUE (product_id, valid_from)
);
GO

CREATE TABLE dw.dim_store (
    store_key                    BIGINT IDENTITY(1,1) NOT NULL,
    store_id                     NVARCHAR(50)    NOT NULL,
    store_name                   NVARCHAR(150)   NULL,
    channel                      NVARCHAR(50)    NULL,
    location_type                NVARCHAR(50)    NULL,
    city                         NVARCHAR(100)   NULL,
    province                     NVARCHAR(100)   NULL,
    region                       NVARCHAR(100)   NULL,
    country_code                 CHAR(2)         NULL,
    store_status                 NVARCHAR(50)    NULL,
    opened_at                    DATE            NULL,
    CONSTRAINT PK_dim_store PRIMARY KEY (store_key),
    CONSTRAINT UQ_dim_store_store_id UNIQUE (store_id)
);
GO

CREATE TABLE dw.dim_channel (
    channel_key                  SMALLINT IDENTITY(1,1) NOT NULL,
    channel_code                 NVARCHAR(50)    NOT NULL,
    channel_name                 NVARCHAR(100)   NOT NULL,
    CONSTRAINT PK_dim_channel PRIMARY KEY (channel_key),
    CONSTRAINT UQ_dim_channel_code UNIQUE (channel_code)
);
GO

CREATE TABLE dw.dim_payment_method (
    payment_method_key           SMALLINT IDENTITY(1,1) NOT NULL,
    payment_method_code          NVARCHAR(50)    NOT NULL,
    payment_method_name          NVARCHAR(100)   NOT NULL,
    payment_method_group         NVARCHAR(50)    NULL,
    CONSTRAINT PK_dim_payment_method PRIMARY KEY (payment_method_key),
    CONSTRAINT UQ_dim_payment_method_code UNIQUE (payment_method_code)
);
GO

CREATE TABLE dw.dim_return_reason (
    return_reason_key            SMALLINT IDENTITY(1,1) NOT NULL,
    return_reason_code           NVARCHAR(200)   NOT NULL,
    return_reason_group          NVARCHAR(100)   NULL,
    CONSTRAINT PK_dim_return_reason PRIMARY KEY (return_reason_key),
    CONSTRAINT UQ_dim_return_reason_code UNIQUE (return_reason_code)
);
GO

CREATE TABLE dw.fact_sales_transaction (
    sales_transaction_key        BIGINT IDENTITY(1,1) NOT NULL,
    source_transaction_id        NVARCHAR(80)    NOT NULL,
    source_system                NVARCHAR(50)    NOT NULL,
    movement_date_key            INT             NOT NULL,
    movement_at                  DATETIME2(0)    NULL,
    customer_key                 BIGINT          NULL,
    product_key                  BIGINT          NULL,
    store_key                    BIGINT          NULL,
    channel_key                  SMALLINT        NULL,
    payment_method_key           SMALLINT        NULL,
    document_type                NVARCHAR(50)    NULL,
    document_id                  NVARCHAR(50)    NULL,
    line_id                      NVARCHAR(50)    NULL,
    movement_type                NVARCHAR(50)    NOT NULL,
    is_return                    BIT             NOT NULL,
    quantity_signed              DECIMAL(18,2)   NULL,
    quantity_abs                 DECIMAL(18,2)   NULL,
    unit_price                   DECIMAL(18,2)   NULL,
    discount_pct                 DECIMAL(9,4)    NULL,
    discount_amount              DECIMAL(18,2)   NULL,
    net_amount_signed            DECIMAL(18,2)   NULL,
    net_amount_abs               DECIMAL(18,2)   NULL,
    unit_cost                    DECIMAL(18,2)   NULL,
    cost_amount                  DECIMAL(18,2)   NULL,
    gross_margin_amount          DECIMAL(18,2)   NULL,
    currency_code                CHAR(3)         NULL,
    vat_pct                      DECIMAL(9,4)    NULL,
    date_parse_ok                BIT             NULL,
    amount_parse_ok              BIT             NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_fact_sales_transaction_created_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_fact_sales_transaction PRIMARY KEY (sales_transaction_key),
    CONSTRAINT UQ_fact_sales_transaction_source UNIQUE (source_transaction_id),
    CONSTRAINT FK_fact_sales_date FOREIGN KEY (movement_date_key) REFERENCES dw.dim_date(date_key),
    CONSTRAINT FK_fact_sales_customer FOREIGN KEY (customer_key) REFERENCES dw.dim_customer(customer_key),
    CONSTRAINT FK_fact_sales_product FOREIGN KEY (product_key) REFERENCES dw.dim_product(product_key),
    CONSTRAINT FK_fact_sales_store FOREIGN KEY (store_key) REFERENCES dw.dim_store(store_key),
    CONSTRAINT FK_fact_sales_channel FOREIGN KEY (channel_key) REFERENCES dw.dim_channel(channel_key),
    CONSTRAINT FK_fact_sales_payment FOREIGN KEY (payment_method_key) REFERENCES dw.dim_payment_method(payment_method_key)
);
GO

CREATE TABLE dw.fact_return (
    return_fact_key              BIGINT IDENTITY(1,1) NOT NULL,
    return_id                    NVARCHAR(50)    NOT NULL,
    return_line_id               NVARCHAR(80)    NOT NULL,
    return_date_key              INT             NOT NULL,
    returned_at                  DATETIME2(0)    NULL,
    customer_key                 BIGINT          NULL,
    product_key                  BIGINT          NULL,
    store_key                    BIGINT          NULL,
    channel_key                  SMALLINT        NULL,
    return_reason_key            SMALLINT        NULL,
    original_document_id         NVARCHAR(50)    NULL,
    original_line_id             NVARCHAR(50)    NULL,
    returned_quantity            DECIMAL(18,2)   NULL,
    refund_amount                DECIMAL(18,2)   NULL,
    currency_code                CHAR(3)         NULL,
    return_status                NVARCHAR(50)    NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_fact_return_created_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_fact_return PRIMARY KEY (return_fact_key),
    CONSTRAINT UQ_fact_return_source UNIQUE (return_line_id),
    CONSTRAINT FK_fact_return_date FOREIGN KEY (return_date_key) REFERENCES dw.dim_date(date_key),
    CONSTRAINT FK_fact_return_customer FOREIGN KEY (customer_key) REFERENCES dw.dim_customer(customer_key),
    CONSTRAINT FK_fact_return_product FOREIGN KEY (product_key) REFERENCES dw.dim_product(product_key),
    CONSTRAINT FK_fact_return_store FOREIGN KEY (store_key) REFERENCES dw.dim_store(store_key),
    CONSTRAINT FK_fact_return_channel FOREIGN KEY (channel_key) REFERENCES dw.dim_channel(channel_key),
    CONSTRAINT FK_fact_return_reason FOREIGN KEY (return_reason_key) REFERENCES dw.dim_return_reason(return_reason_key)
);
GO

CREATE TABLE dw.fact_stock_snapshot (
    stock_snapshot_key           BIGINT IDENTITY(1,1) NOT NULL,
    snapshot_date_key            INT             NOT NULL,
    product_key                  BIGINT          NOT NULL,
    store_key                    BIGINT          NOT NULL,
    closing_stock_qty            DECIMAL(18,2)   NULL,
    reserved_stock_qty           DECIMAL(18,2)   NULL,
    in_transit_stock_qty         DECIMAL(18,2)   NULL,
    minimum_stock_qty            DECIMAL(18,2)   NULL,
    available_stock_qty          AS (closing_stock_qty - reserved_stock_qty) PERSISTED,
    is_below_minimum             BIT             NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_fact_stock_snapshot_created_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_fact_stock_snapshot PRIMARY KEY (stock_snapshot_key),
    CONSTRAINT UQ_fact_stock_snapshot_grain UNIQUE (snapshot_date_key, product_key, store_key),
    CONSTRAINT FK_fact_stock_date FOREIGN KEY (snapshot_date_key) REFERENCES dw.dim_date(date_key),
    CONSTRAINT FK_fact_stock_product FOREIGN KEY (product_key) REFERENCES dw.dim_product(product_key),
    CONSTRAINT FK_fact_stock_store FOREIGN KEY (store_key) REFERENCES dw.dim_store(store_key)
);
GO

CREATE TABLE dw.fact_payment (
    payment_fact_key             BIGINT IDENTITY(1,1) NOT NULL,
    payment_id                   NVARCHAR(50)    NOT NULL,
    payment_date_key             INT             NOT NULL,
    paid_at                      DATETIME2(0)    NULL,
    store_key                    BIGINT          NULL,
    payment_method_key           SMALLINT        NULL,
    ticket_id                    NVARCHAR(50)    NULL,
    paid_amount                  DECIMAL(18,2)   NULL,
    currency_code                CHAR(3)         NULL,
    payment_status               NVARCHAR(50)    NULL,
    created_at                   DATETIME2(0)    NOT NULL CONSTRAINT DF_fact_payment_created_at DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_fact_payment PRIMARY KEY (payment_fact_key),
    CONSTRAINT UQ_fact_payment_source UNIQUE (payment_id),
    CONSTRAINT FK_fact_payment_date FOREIGN KEY (payment_date_key) REFERENCES dw.dim_date(date_key),
    CONSTRAINT FK_fact_payment_store FOREIGN KEY (store_key) REFERENCES dw.dim_store(store_key),
    CONSTRAINT FK_fact_payment_method FOREIGN KEY (payment_method_key) REFERENCES dw.dim_payment_method(payment_method_key)
);
GO

CREATE INDEX IX_fact_sales_date_product ON dw.fact_sales_transaction(movement_date_key, product_key);
GO
CREATE INDEX IX_fact_sales_customer_date ON dw.fact_sales_transaction(customer_key, movement_date_key);
GO
CREATE INDEX IX_fact_return_date_product ON dw.fact_return(return_date_key, product_key);
GO
CREATE INDEX IX_fact_stock_product_date ON dw.fact_stock_snapshot(product_key, snapshot_date_key);
GO
CREATE INDEX IX_fact_payment_date_method ON dw.fact_payment(payment_date_key, payment_method_key);
GO
