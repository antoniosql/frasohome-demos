-- =========================================================
-- 1) Esquema
-- =========================================================
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'raw')
BEGIN
    EXEC('CREATE SCHEMA raw');
END
GO

-- =========================================================
-- 2) Tablas
-- =========================================================

IF OBJECT_ID('raw.crm', 'U') IS NOT NULL DROP TABLE raw.crm;
GO
CREATE TABLE raw.crm (
    customer_id                  NVARCHAR(50)    NOT NULL,
    nombre                       NVARCHAR(100)   NULL,
    apellidos                    NVARCHAR(150)   NULL,
    email                        NVARCHAR(255)   NULL,
    telefono                     NVARCHAR(50)    NULL,
    fecha_alta_programa          DATETIME2       NULL,
    tier_fidelizacion            NVARCHAR(50)    NULL,
    puntos_acumulados            DECIMAL(18,2)   NULL,
    fecha_nacimiento             DATE            NULL,
    genero                       NVARCHAR(20)    NULL,
    ciudad                       NVARCHAR(100)   NULL,
    provincia                    NVARCHAR(100)   NULL,
    codigo_postal                NVARCHAR(20)    NULL,
    pais                         NVARCHAR(10)    NULL,
    consentimiento_marketing     BIT             NULL,
    estado_cliente               NVARCHAR(50)    NULL,
    fecha_baja                   DATE            NULL,
    origen_alta                  NVARCHAR(50)    NULL,
    canal_preferido_declarado    NVARCHAR(50)    NULL,
    ultima_actualizacion         DATETIME2       NULL,
    CONSTRAINT PK_raw_crm PRIMARY KEY (customer_id)
);
GO


IF OBJECT_ID('raw.devoluciones_online', 'U') IS NOT NULL DROP TABLE raw.devoluciones_online;
GO
CREATE TABLE raw.devoluciones_online (
    return_id             NVARCHAR(50)   NOT NULL,
    order_id              NVARCHAR(50)   NULL,
    order_line_id         NVARCHAR(50)   NULL,
    product_id            NVARCHAR(50)   NULL,
    fecha_devolucion      DATETIME2      NULL,
    cantidad_devuelta     INT            NULL,
    motivo_devolucion     NVARCHAR(200)  NULL,
    metodo_devolucion     NVARCHAR(50)   NULL,
    estado_devolucion     NVARCHAR(50)   NULL,
    importe_reembolsado   DECIMAL(18,2)  NULL,
    moneda                NVARCHAR(10)   NULL,
    comentarios           NVARCHAR(500)  NULL,
    CONSTRAINT PK_raw_devoluciones_online PRIMARY KEY (return_id)
);
GO


IF OBJECT_ID('raw.devoluciones_tienda', 'U') IS NOT NULL DROP TABLE raw.devoluciones_tienda;
GO
CREATE TABLE raw.devoluciones_tienda (
    return_id                  NVARCHAR(50)   NOT NULL,
    fecha_devolucion           DATETIME2      NULL,
    store_id                   NVARCHAR(50)   NULL,
    ticket_id_original         NVARCHAR(50)   NULL,
    ticket_line_id_original    NVARCHAR(50)   NULL,
    order_id_original          NVARCHAR(50)   NULL,
    customer_id                NVARCHAR(50)   NULL,
    product_id                 NVARCHAR(50)   NULL,
    cantidad_devuelta          INT            NULL,
    estado_devolucion          NVARCHAR(50)   NULL,
    importe_reembolsado        DECIMAL(18,2)  NULL,
    moneda                     NVARCHAR(10)   NULL,
    metodo_reembolso           NVARCHAR(50)   NULL,
    motivo_devolucion          NVARCHAR(200)  NULL,
    canal_origen_venta         NVARCHAR(50)   NULL,
    comentarios                NVARCHAR(500)  NULL,
    CONSTRAINT PK_raw_devoluciones_tienda PRIMARY KEY (return_id)
);
GO


IF OBJECT_ID('raw.fact_transacciones', 'U') IS NOT NULL DROP TABLE raw.fact_transacciones;
GO
CREATE TABLE raw.fact_transacciones (
    fact_id                    NVARCHAR(50)    NOT NULL,
    source_system              NVARCHAR(50)    NULL,
    source_file                NVARCHAR(255)   NULL,
    canal_origen               NVARCHAR(50)    NULL,
    canal_movimiento           NVARCHAR(50)    NULL,
    tipo_movimiento            NVARCHAR(50)    NULL,
    es_devolucion              BIT             NULL,
    fecha_movimiento_raw       NVARCHAR(100)   NULL,
    fecha_movimiento           DATETIME2       NULL,
    store_id_raw               NVARCHAR(50)    NULL,
    store_id_std               NVARCHAR(50)    NULL,
    doc_tipo                   NVARCHAR(50)    NULL,
    doc_id_raw                 NVARCHAR(50)    NULL,
    doc_id_std                 NVARCHAR(50)    NULL,
    line_id_raw                NVARCHAR(50)    NULL,
    line_id_std                NVARCHAR(50)    NULL,
    return_id                  NVARCHAR(50)    NULL,
    customer_id_raw            NVARCHAR(50)    NULL,
    customer_id_std            NVARCHAR(50)    NULL,
    flag_customer_in_crm       BIT             NULL,
    product_id_raw             NVARCHAR(50)    NULL,
    product_id_std             NVARCHAR(50)    NULL,
    flag_product_in_master     BIT             NULL,
    descripcion_producto       NVARCHAR(255)   NULL,
    categoria                  NVARCHAR(100)   NULL,
    subcategoria               NVARCHAR(100)   NULL,
    cantidad_raw               INT             NULL,
    cantidad_signed            DECIMAL(18,2)   NULL,
    cantidad_abs               DECIMAL(18,2)   NULL,
    precio_unitario_raw        NVARCHAR(50)    NULL,
    precio_unitario_num        DECIMAL(18,2)   NULL,
    descuento_pct_raw          DECIMAL(18,4)   NULL,
    descuento_pct_num          DECIMAL(18,4)   NULL,
    descuento_importe_raw      DECIMAL(18,2)   NULL,
    descuento_importe_num      DECIMAL(18,2)   NULL,
    importe_linea_raw          NVARCHAR(50)    NULL,
    importe_signed_num         DECIMAL(18,2)   NULL,
    importe_abs_num            DECIMAL(18,2)   NULL,
    moneda                     NVARCHAR(10)    NULL,
    iva_pct                    DECIMAL(9,2)    NULL,
    coste_unitario_num         DECIMAL(18,2)   NULL,
    coste_total_num            DECIMAL(18,2)   NULL,
    margen_bruto_num           DECIMAL(18,2)   NULL,
    metodo_pago                NVARCHAR(50)    NULL,
    estado_pedido              NVARCHAR(50)    NULL,
    origen                     NVARCHAR(50)    NULL,
    ticket_id_original         NVARCHAR(50)    NULL,
    ticket_line_id_original    NVARCHAR(50)    NULL,
    order_id_original          NVARCHAR(50)    NULL,
    order_line_id_original     NVARCHAR(50)    NULL,
    motivo_devolucion          NVARCHAR(200)   NULL,
    metodo_devolucion          NVARCHAR(50)    NULL,
    caja_id                    NVARCHAR(50)    NULL,
    cajero_id                  NVARCHAR(50)    NULL,
    flag_fecha_parseada        BIT             NULL,
    flag_importe_parseado      BIT             NULL,
    nombre_producto            NVARCHAR(255)   NULL,
    precio_venta_num           DECIMAL(18,2)   NULL,
    estado_producto            NVARCHAR(50)    NULL,
    CONSTRAINT PK_raw_fact_transacciones PRIMARY KEY (fact_id)
);
GO


IF OBJECT_ID('raw.lineas_pedido', 'U') IS NOT NULL DROP TABLE raw.lineas_pedido;
GO
CREATE TABLE raw.lineas_pedido (
    order_line_id           NVARCHAR(50)   NOT NULL,
    order_id                NVARCHAR(50)   NULL,
    product_id              NVARCHAR(50)   NULL,
    descripcion_producto    NVARCHAR(255)  NULL,
    categoria               NVARCHAR(100)  NULL,
    subcategoria            NVARCHAR(100)  NULL,
    cantidad                INT            NULL,
    precio_unitario         DECIMAL(18,2)  NULL,
    descuento_pct           DECIMAL(18,4)  NULL,
    descuento_importe       DECIMAL(18,2)  NULL,
    importe_linea           DECIMAL(18,2)  NULL,
    iva_pct                 DECIMAL(9,2)   NULL,
    CONSTRAINT PK_raw_lineas_pedido PRIMARY KEY (order_line_id)
);
GO


IF OBJECT_ID('raw.pagos_tienda', 'U') IS NOT NULL DROP TABLE raw.pagos_tienda;
GO
CREATE TABLE raw.pagos_tienda (
    payment_id                 NVARCHAR(50)   NOT NULL,
    ticket_id                  NVARCHAR(50)   NULL,
    fecha_pago                 DATETIME2      NULL,
    store_id                   NVARCHAR(50)   NULL,
    caja_id                    NVARCHAR(50)   NULL,
    cajero_id                  NVARCHAR(50)   NULL,
    metodo_pago                NVARCHAR(50)   NULL,
    importe_pagado             DECIMAL(18,2)  NULL,
    moneda                     NVARCHAR(10)   NULL,
    referencia_autorizacion    NVARCHAR(100)  NULL,
    estado_pago                NVARCHAR(50)   NULL,
    observaciones              NVARCHAR(500)  NULL,
    CONSTRAINT PK_raw_pagos_tienda PRIMARY KEY (payment_id)
);
GO


IF OBJECT_ID('raw.pedidos', 'U') IS NOT NULL DROP TABLE raw.pedidos;
GO
CREATE TABLE raw.pedidos (
    order_id                NVARCHAR(50)   NOT NULL,
    fecha_pedido            DATETIME2      NULL,
    customer_id             NVARCHAR(50)   NULL,
    usuario_online_id       NVARCHAR(50)   NULL,
    importe_total           DECIMAL(18,2)  NULL,
    moneda                  NVARCHAR(10)   NULL,
    gastos_envio            DECIMAL(18,2)  NULL,
    direccion_envio         NVARCHAR(255)  NULL,
    codigo_postal_envio     NVARCHAR(20)   NULL,
    ciudad_envio            NVARCHAR(100)  NULL,
    provincia_envio         NVARCHAR(100)  NULL,
    pais_envio              NVARCHAR(10)   NULL,
    metodo_pago             NVARCHAR(50)   NULL,
    estado_pedido           NVARCHAR(50)   NULL,
    origen                  NVARCHAR(50)   NULL,
    ultima_actualizacion    DATETIME2      NULL,
    CONSTRAINT PK_raw_pedidos PRIMARY KEY (order_id)
);
GO


IF OBJECT_ID('raw.productos', 'U') IS NOT NULL DROP TABLE raw.productos;
GO
CREATE TABLE raw.productos (
    product_id              NVARCHAR(50)   NOT NULL,
    nombre_producto         NVARCHAR(255)  NULL,
    categoria               NVARCHAR(100)  NULL,
    subcategoria            NVARCHAR(100)  NULL,
    marca                   NVARCHAR(100)  NULL,
    proveedor               NVARCHAR(100)  NULL,
    material                NVARCHAR(100)  NULL,
    color                   NVARCHAR(100)  NULL,
    precio_venta            DECIMAL(18,2)  NULL,
    coste_unitario          DECIMAL(18,2)  NULL,
    iva_pct                 DECIMAL(9,2)   NULL,
    peso_kg                 DECIMAL(18,3)  NULL,
    largo_cm                DECIMAL(18,2)  NULL,
    ancho_cm                DECIMAL(18,2)  NULL,
    alto_cm                 DECIMAL(18,2)  NULL,
    fecha_alta_catalogo     DATE           NULL,
    estado_producto         NVARCHAR(50)   NULL,
    ean                     NVARCHAR(30)   NULL,
    CONSTRAINT PK_raw_productos PRIMARY KEY (product_id)
);
GO


IF OBJECT_ID('raw.stock_diario', 'U') IS NOT NULL DROP TABLE raw.stock_diario;
GO
CREATE TABLE raw.stock_diario (
    fecha               DATETIME2      NOT NULL,
    store_id            NVARCHAR(50)   NOT NULL,
    product_id          NVARCHAR(50)   NOT NULL,
    stock_cierre        DECIMAL(18,2)  NULL,
    stock_reservado     DECIMAL(18,2)  NULL,
    stock_en_transito   DECIMAL(18,2)  NULL,
    stock_minimo        INT            NULL,
    fuente              NVARCHAR(50)   NULL,
    comentarios         NVARCHAR(500)  NULL,
    CONSTRAINT PK_raw_stock_diario PRIMARY KEY (fecha, store_id, product_id)
);
GO


IF OBJECT_ID('raw.tiendas', 'U') IS NOT NULL DROP TABLE raw.tiendas;
GO
CREATE TABLE raw.tiendas (
    store_id            NVARCHAR(50)   NOT NULL,
    nombre_tienda       NVARCHAR(150)  NULL,
    tipo_ubicacion      NVARCHAR(50)   NULL,
    canal               NVARCHAR(50)   NULL,
    ciudad              NVARCHAR(100)  NULL,
    provincia           NVARCHAR(100)  NULL,
    direccion           NVARCHAR(255)  NULL,
    codigo_postal       NVARCHAR(20)   NULL,
    pais                NVARCHAR(10)   NULL,
    fecha_apertura      DATE           NULL,
    metros_cuadrados    INT            NULL,
    telefono            NVARCHAR(50)   NULL,
    horario             NVARCHAR(100)  NULL,
    lat                 DECIMAL(10,6)  NULL,
    lon                 DECIMAL(10,6)  NULL,
    estado              NVARCHAR(50)   NULL,
    region              NVARCHAR(100)  NULL,
    gerente             NVARCHAR(150)  NULL,
    observaciones       NVARCHAR(500)  NULL,
    CONSTRAINT PK_raw_tiendas PRIMARY KEY (store_id)
);
GO


IF OBJECT_ID('raw.ventas_pos', 'U') IS NOT NULL DROP TABLE raw.ventas_pos;
GO
CREATE TABLE raw.ventas_pos (
    ticket_line_id          NVARCHAR(50)   NOT NULL,
    ticket_id               NVARCHAR(50)   NULL,
    fecha_hora              DATETIME2      NULL,
    store_id                NVARCHAR(50)   NULL,
    caja_id                 NVARCHAR(50)   NULL,
    cajero_id               NVARCHAR(50)   NULL,
    customer_id             NVARCHAR(50)   NULL,
    product_id              NVARCHAR(50)   NULL,
    descripcion_producto    NVARCHAR(255)  NULL,
    categoria               NVARCHAR(100)  NULL,
    subcategoria            NVARCHAR(100)  NULL,
    cantidad                INT            NULL,
    precio_unitario         DECIMAL(18,2)  NULL,
    descuento_pct           DECIMAL(18,4)  NULL,
    descuento_importe       DECIMAL(18,2)  NULL,
    importe_linea           DECIMAL(18,2)  NULL,
    moneda                  NVARCHAR(10)   NULL,
    canal                   NVARCHAR(50)   NULL,
    observaciones           NVARCHAR(500)  NULL,
    CONSTRAINT PK_raw_ventas_pos PRIMARY KEY (ticket_line_id)
);
GO