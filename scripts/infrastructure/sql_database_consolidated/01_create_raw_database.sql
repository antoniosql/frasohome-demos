-- Auto-generado para FraSoHome: esquemas y tablas raw consolidadas.
-- Mantiene los valores como texto para preservar errores didacticos de calidad.

DROP VIEW IF EXISTS [raw_json].[document_properties];
GO
DROP VIEW IF EXISTS [raw_marketing].[vw_customer_touchpoints];
GO
DROP VIEW IF EXISTS [raw_people].[vw_employee_retail_context];
GO
DROP VIEW IF EXISTS [xref].[vw_store_aliases];
GO
DROP VIEW IF EXISTS [xref].[vw_product_aliases_rag_to_retail];
GO
DROP VIEW IF EXISTS [xref].[vw_employee_store_assignment];
GO
DROP VIEW IF EXISTS [xref].[vw_employee_operational_aliases];
GO
DROP VIEW IF EXISTS [xref].[vw_marketing_precision_operational_links];
GO
DROP VIEW IF EXISTS [xref].[vw_coherence_check_summary];
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = N'admin') EXEC(N'CREATE SCHEMA [admin]');
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = N'raw_json') EXEC(N'CREATE SCHEMA [raw_json]');
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = N'raw_marketing') EXEC(N'CREATE SCHEMA [raw_marketing]');
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = N'raw_people') EXEC(N'CREATE SCHEMA [raw_people]');
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = N'raw_rag') EXEC(N'CREATE SCHEMA [raw_rag]');
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = N'raw_retail') EXEC(N'CREATE SCHEMA [raw_retail]');
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = N'xref') EXEC(N'CREATE SCHEMA [xref]');
GO

IF OBJECT_ID(N'raw_marketing.afinidad_tienda_cliente', N'U') IS NOT NULL DROP TABLE [raw_marketing].[afinidad_tienda_cliente];
GO
CREATE TABLE [raw_marketing].[afinidad_tienda_cliente] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_marketing_afinidad_tienda_cliente_loaded_at] DEFAULT SYSUTCDATETIME(),
    [customer_id] NVARCHAR(4000) NULL,
    [store_id_preferida] NVARCHAR(4000) NULL,
    [store_id_mas_cercana] NVARCHAR(4000) NULL,
    [distancia_km_store_mas_cercana] NVARCHAR(4000) NULL,
    [frecuencia_visita_tienda_12m] NVARCHAR(4000) NULL,
    [gasto_tienda_12m_eur] NVARCHAR(4000) NULL,
    [gasto_online_12m_eur] NVARCHAR(4000) NULL,
    [click_collect_propension] NVARCHAR(4000) NULL,
    [probabilidad_visita_30d] NVARCHAR(4000) NULL,
    [cluster_local] NVARCHAR(4000) NULL,
    [es_capturable_localmente] NVARCHAR(4000) NULL,
    [ciudad_residencia] NVARCHAR(4000) NULL,
    [provincia_residencia] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_marketing_afinidad_tienda_cliente] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_marketing.campanas_marketing', N'U') IS NOT NULL DROP TABLE [raw_marketing].[campanas_marketing];
GO
CREATE TABLE [raw_marketing].[campanas_marketing] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_marketing_campanas_marketing_loaded_at] DEFAULT SYSUTCDATETIME(),
    [campaign_id] NVARCHAR(4000) NULL,
    [nombre_campana] NVARCHAR(4000) NULL,
    [objetivo] NVARCHAR(4000) NULL,
    [canal] NVARCHAR(4000) NULL,
    [fecha_inicio] NVARCHAR(4000) NULL,
    [fecha_fin] NVARCHAR(4000) NULL,
    [segmento_objetivo] NVARCHAR(4000) NULL,
    [categoria_objetivo] NVARCHAR(4000) NULL,
    [subcategoria_objetivo] NVARCHAR(4000) NULL,
    [store_id_objetivo] NVARCHAR(4000) NULL,
    [tipo_oferta] NVARCHAR(4000) NULL,
    [descuento_pct] NVARCHAR(4000) NULL,
    [presupuesto_plan_eur] NVARCHAR(4000) NULL,
    [grupo_control_pct] NVARCHAR(4000) NULL,
    [kpi_primario] NVARCHAR(4000) NULL,
    [estado] NVARCHAR(4000) NULL,
    [copy_eje] NVARCHAR(4000) NULL,
    [audiencia_estimada] NVARCHAR(4000) NULL,
    [contactos] NVARCHAR(4000) NULL,
    [audiencias] NVARCHAR(4000) NULL,
    [control] NVARCHAR(4000) NULL,
    [entregados] NVARCHAR(4000) NULL,
    [conversiones_30d] NVARCHAR(4000) NULL,
    [revenue_30d_total_eur] NVARCHAR(4000) NULL,
    [margen_30d_total_eur] NVARCHAR(4000) NULL,
    [coste_contacto_total_eur] NVARCHAR(4000) NULL,
    [cnt_add_to_cart] NVARCHAR(4000) NULL,
    [cnt_bounce] NVARCHAR(4000) NULL,
    [cnt_click] NVARCHAR(4000) NULL,
    [cnt_delivered] NVARCHAR(4000) NULL,
    [cnt_fallido] NVARCHAR(4000) NULL,
    [cnt_landing_visit] NVARCHAR(4000) NULL,
    [cnt_open] NVARCHAR(4000) NULL,
    [cnt_purchase] NVARCHAR(4000) NULL,
    [cnt_rechazado] NVARCHAR(4000) NULL,
    [cnt_redeem_coupon] NVARCHAR(4000) NULL,
    [cnt_store_visit_estimada] NVARCHAR(4000) NULL,
    [cnt_unsubscribe] NVARCHAR(4000) NULL,
    [cupones_emitidos] NVARCHAR(4000) NULL,
    [cupones_canjeados] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_marketing_campanas_marketing] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_marketing.catalogo_datasets_marketing_precision', N'U') IS NOT NULL DROP TABLE [raw_marketing].[catalogo_datasets_marketing_precision];
GO
CREATE TABLE [raw_marketing].[catalogo_datasets_marketing_precision] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_marketing_catalogo_datasets_marketing_precision_loaded_at] DEFAULT SYSUTCDATETIME(),
    [dataset] NVARCHAR(4000) NULL,
    [descripcion] NVARCHAR(4000) NULL,
    [granularidad] NVARCHAR(4000) NULL,
    [clave_principal] NVARCHAR(4000) NULL,
    [campos_clave] NVARCHAR(4000) NULL,
    [casos_relacionados] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_marketing_catalogo_datasets_marketing_precision] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_marketing.contactos_campana', N'U') IS NOT NULL DROP TABLE [raw_marketing].[contactos_campana];
GO
CREATE TABLE [raw_marketing].[contactos_campana] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_marketing_contactos_campana_loaded_at] DEFAULT SYSUTCDATETIME(),
    [contact_id] NVARCHAR(4000) NULL,
    [campaign_id] NVARCHAR(4000) NULL,
    [customer_id] NVARCHAR(4000) NULL,
    [fecha_contacto] NVARCHAR(4000) NULL,
    [canal_contacto] NVARCHAR(4000) NULL,
    [grupo_experimental] NVARCHAR(4000) NULL,
    [grupo_control_flag] NVARCHAR(4000) NULL,
    [segmento_asignado] NVARCHAR(4000) NULL,
    [offer_code] NVARCHAR(4000) NULL,
    [coupon_instance_id] NVARCHAR(4000) NULL,
    [estado_entrega] NVARCHAR(4000) NULL,
    [coste_contacto_eur] NVARCHAR(4000) NULL,
    [prioridad_contacto] NVARCHAR(4000) NULL,
    [store_id_personalizado] NVARCHAR(4000) NULL,
    [product_id_recomendado_1] NVARCHAR(4000) NULL,
    [product_id_recomendado_2] NVARCHAR(4000) NULL,
    [app_user_id] NVARCHAR(4000) NULL,
    [conversion_30d_flag] NVARCHAR(4000) NULL,
    [order_id_conversion_30d] NVARCHAR(4000) NULL,
    [ticket_id_conversion_30d] NVARCHAR(4000) NULL,
    [revenue_30d_eur] NVARCHAR(4000) NULL,
    [margen_30d_eur] NVARCHAR(4000) NULL,
    [fecha_conversion_30d] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_marketing_contactos_campana] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_marketing.costes_operativos_transaccion', N'U') IS NOT NULL DROP TABLE [raw_marketing].[costes_operativos_transaccion];
GO
CREATE TABLE [raw_marketing].[costes_operativos_transaccion] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_marketing_costes_operativos_transaccion_loaded_at] DEFAULT SYSUTCDATETIME(),
    [transaction_cost_id] NVARCHAR(4000) NULL,
    [tipo_documento] NVARCHAR(4000) NULL,
    [order_id] NVARCHAR(4000) NULL,
    [ticket_id] NVARCHAR(4000) NULL,
    [customer_id] NVARCHAR(4000) NULL,
    [fecha_transaccion] NVARCHAR(4000) NULL,
    [canal] NVARCHAR(4000) NULL,
    [store_id] NVARCHAR(4000) NULL,
    [categoria_principal] NVARCHAR(4000) NULL,
    [ingreso_bruto_eur] NVARCHAR(4000) NULL,
    [descuento_total_eur] NVARCHAR(4000) NULL,
    [coste_producto_eur] NVARCHAR(4000) NULL,
    [coste_logistico_eur] NVARCHAR(4000) NULL,
    [coste_packaging_eur] NVARCHAR(4000) NULL,
    [coste_ultima_milla_eur] NVARCHAR(4000) NULL,
    [coste_pago_eur] NVARCHAR(4000) NULL,
    [coste_servicio_eur] NVARCHAR(4000) NULL,
    [coste_devolucion_esperado_eur] NVARCHAR(4000) NULL,
    [cac_asignado_eur] NVARCHAR(4000) NULL,
    [campaign_id_atribuida] NVARCHAR(4000) NULL,
    [margen_contribucion_neto_eur] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_marketing_costes_operativos_transaccion] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_marketing.creatividades_segmento', N'U') IS NOT NULL DROP TABLE [raw_marketing].[creatividades_segmento];
GO
CREATE TABLE [raw_marketing].[creatividades_segmento] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_marketing_creatividades_segmento_loaded_at] DEFAULT SYSUTCDATETIME(),
    [creative_id] NVARCHAR(4000) NULL,
    [campaign_id] NVARCHAR(4000) NULL,
    [microsegmento] NVARCHAR(4000) NULL,
    [canal] NVARCHAR(4000) NULL,
    [categoria_objetivo] NVARCHAR(4000) NULL,
    [tono] NVARCHAR(4000) NULL,
    [beneficio_principal] NVARCHAR(4000) NULL,
    [cta] NVARCHAR(4000) NULL,
    [asunto] NVARCHAR(4000) NULL,
    [copy_corto] NVARCHAR(4000) NULL,
    [copy_largo] NVARCHAR(4000) NULL,
    [prueba_social] NVARCHAR(4000) NULL,
    [prompt_base] NVARCHAR(4000) NULL,
    [guardrail_legal] NVARCHAR(4000) NULL,
    [open_rate] NVARCHAR(4000) NULL,
    [ctr] NVARCHAR(4000) NULL,
    [cvr] NVARCHAR(4000) NULL,
    [revenue_por_1000_envios_eur] NVARCHAR(4000) NULL,
    [winning_variant_flag] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_marketing_creatividades_segmento] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_marketing.cupones_clientes', N'U') IS NOT NULL DROP TABLE [raw_marketing].[cupones_clientes];
GO
CREATE TABLE [raw_marketing].[cupones_clientes] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_marketing_cupones_clientes_loaded_at] DEFAULT SYSUTCDATETIME(),
    [coupon_instance_id] NVARCHAR(4000) NULL,
    [coupon_code] NVARCHAR(4000) NULL,
    [campaign_id] NVARCHAR(4000) NULL,
    [customer_id] NVARCHAR(4000) NULL,
    [fecha_emision] NVARCHAR(4000) NULL,
    [fecha_inicio_validez] NVARCHAR(4000) NULL,
    [fecha_fin_validez] NVARCHAR(4000) NULL,
    [tipo_cupon] NVARCHAR(4000) NULL,
    [descuento_pct] NVARCHAR(4000) NULL,
    [descuento_importe_eur] NVARCHAR(4000) NULL,
    [gasto_minimo_eur] NVARCHAR(4000) NULL,
    [categoria_restringida] NVARCHAR(4000) NULL,
    [store_id_restringido] NVARCHAR(4000) NULL,
    [canal_emision] NVARCHAR(4000) NULL,
    [estado_cupon] NVARCHAR(4000) NULL,
    [fecha_canje] NVARCHAR(4000) NULL,
    [order_id] NVARCHAR(4000) NULL,
    [ticket_id] NVARCHAR(4000) NULL,
    [importe_cesta_eur] NVARCHAR(4000) NULL,
    [descuento_aplicado_eur] NVARCHAR(4000) NULL,
    [margen_post_descuento_eur] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_marketing_cupones_clientes] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_marketing.diccionario_columnas_marketing_precision', N'U') IS NOT NULL DROP TABLE [raw_marketing].[diccionario_columnas_marketing_precision];
GO
CREATE TABLE [raw_marketing].[diccionario_columnas_marketing_precision] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_marketing_diccionario_columnas_marketing_precision_loaded_at] DEFAULT SYSUTCDATETIME(),
    [dataset] NVARCHAR(4000) NULL,
    [columna] NVARCHAR(4000) NULL,
    [tipo_dato] NVARCHAR(4000) NULL,
    [ejemplo_valor] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_marketing_diccionario_columnas_marketing_precision] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_marketing.eventos_campana', N'U') IS NOT NULL DROP TABLE [raw_marketing].[eventos_campana];
GO
CREATE TABLE [raw_marketing].[eventos_campana] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_marketing_eventos_campana_loaded_at] DEFAULT SYSUTCDATETIME(),
    [event_id] NVARCHAR(4000) NULL,
    [contact_id] NVARCHAR(4000) NULL,
    [campaign_id] NVARCHAR(4000) NULL,
    [customer_id] NVARCHAR(4000) NULL,
    [fecha_evento] NVARCHAR(4000) NULL,
    [tipo_evento] NVARCHAR(4000) NULL,
    [order_id] NVARCHAR(4000) NULL,
    [ticket_id] NVARCHAR(4000) NULL,
    [store_id] NVARCHAR(4000) NULL,
    [revenue_atribuido_eur] NVARCHAR(4000) NULL,
    [margen_atribuido_eur] NVARCHAR(4000) NULL,
    [device_type] NVARCHAR(4000) NULL,
    [origen_evento] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_marketing_eventos_campana] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_marketing.eventos_web_app', N'U') IS NOT NULL DROP TABLE [raw_marketing].[eventos_web_app];
GO
CREATE TABLE [raw_marketing].[eventos_web_app] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_marketing_eventos_web_app_loaded_at] DEFAULT SYSUTCDATETIME(),
    [event_id] NVARCHAR(4000) NULL,
    [fecha_hora_evento] NVARCHAR(4000) NULL,
    [session_id] NVARCHAR(4000) NULL,
    [customer_id] NVARCHAR(4000) NULL,
    [cookie_id] NVARCHAR(4000) NULL,
    [device_id] NVARCHAR(4000) NULL,
    [usuario_online_id] NVARCHAR(4000) NULL,
    [canal_adquisicion] NVARCHAR(4000) NULL,
    [utm_source] NVARCHAR(4000) NULL,
    [utm_medium] NVARCHAR(4000) NULL,
    [utm_campaign] NVARCHAR(4000) NULL,
    [tipo_evento] NVARCHAR(4000) NULL,
    [page_type] NVARCHAR(4000) NULL,
    [product_id] NVARCHAR(4000) NULL,
    [categoria] NVARCHAR(4000) NULL,
    [subcategoria] NVARCHAR(4000) NULL,
    [search_term] NVARCHAR(4000) NULL,
    [store_id_interes] NVARCHAR(4000) NULL,
    [valor_evento_eur] NVARCHAR(4000) NULL,
    [order_id] NVARCHAR(4000) NULL,
    [consent_analytics] NVARCHAR(4000) NULL,
    [logged_in_flag] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_marketing_eventos_web_app] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_marketing.feedback_clientes', N'U') IS NOT NULL DROP TABLE [raw_marketing].[feedback_clientes];
GO
CREATE TABLE [raw_marketing].[feedback_clientes] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_marketing_feedback_clientes_loaded_at] DEFAULT SYSUTCDATETIME(),
    [feedback_id] NVARCHAR(4000) NULL,
    [fecha_feedback] NVARCHAR(4000) NULL,
    [customer_id] NVARCHAR(4000) NULL,
    [order_id] NVARCHAR(4000) NULL,
    [product_id] NVARCHAR(4000) NULL,
    [store_id] NVARCHAR(4000) NULL,
    [canal_feedback] NVARCHAR(4000) NULL,
    [tipo_feedback] NVARCHAR(4000) NULL,
    [rating_1_5] NVARCHAR(4000) NULL,
    [nps_0_10] NVARCHAR(4000) NULL,
    [sentimiento] NVARCHAR(4000) NULL,
    [tema_principal] NVARCHAR(4000) NULL,
    [texto_feedback] NVARCHAR(4000) NULL,
    [publicado_flag] NVARCHAR(4000) NULL,
    [respondido_flag] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_marketing_feedback_clientes] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_marketing.guardrails_marca_genai', N'U') IS NOT NULL DROP TABLE [raw_marketing].[guardrails_marca_genai];
GO
CREATE TABLE [raw_marketing].[guardrails_marca_genai] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_marketing_guardrails_marca_genai_loaded_at] DEFAULT SYSUTCDATETIME(),
    [regla_id] NVARCHAR(4000) NULL,
    [categoria_regla] NVARCHAR(4000) NULL,
    [descripcion_regla] NVARCHAR(4000) NULL,
    [aplica_a_canal] NVARCHAR(4000) NULL,
    [severidad] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_marketing_guardrails_marca_genai] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_marketing.identidades_cliente', N'U') IS NOT NULL DROP TABLE [raw_marketing].[identidades_cliente];
GO
CREATE TABLE [raw_marketing].[identidades_cliente] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_marketing_identidades_cliente_loaded_at] DEFAULT SYSUTCDATETIME(),
    [identity_signal_id] NVARCHAR(4000) NULL,
    [fecha_evento] NVARCHAR(4000) NULL,
    [fuente_sistema] NVARCHAR(4000) NULL,
    [tipo_senal] NVARCHAR(4000) NULL,
    [customer_id_raw] NVARCHAR(4000) NULL,
    [email_hash] NVARCHAR(4000) NULL,
    [telefono_hash] NVARCHAR(4000) NULL,
    [tarjeta_fidelizacion_id] NVARCHAR(4000) NULL,
    [cookie_id] NVARCHAR(4000) NULL,
    [device_id] NVARCHAR(4000) NULL,
    [app_user_id] NVARCHAR(4000) NULL,
    [usuario_online_id] NVARCHAR(4000) NULL,
    [order_id] NVARCHAR(4000) NULL,
    [ticket_id] NVARCHAR(4000) NULL,
    [store_id] NVARCHAR(4000) NULL,
    [consentimiento_snapshot] NVARCHAR(4000) NULL,
    [confianza_origen] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_marketing_identidades_cliente] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_marketing.identidades_cliente_ground_truth', N'U') IS NOT NULL DROP TABLE [raw_marketing].[identidades_cliente_ground_truth];
GO
CREATE TABLE [raw_marketing].[identidades_cliente_ground_truth] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_marketing_identidades_cliente_ground_truth_loaded_at] DEFAULT SYSUTCDATETIME(),
    [identity_signal_id] NVARCHAR(4000) NULL,
    [customer_id_canonico] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_marketing_identidades_cliente_ground_truth] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_marketing.mapeo_casos_marketing_precision', N'U') IS NOT NULL DROP TABLE [raw_marketing].[mapeo_casos_marketing_precision];
GO
CREATE TABLE [raw_marketing].[mapeo_casos_marketing_precision] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_marketing_mapeo_casos_marketing_precision_loaded_at] DEFAULT SYSUTCDATETIME(),
    [caso_id] NVARCHAR(4000) NULL,
    [caso] NVARCHAR(4000) NULL,
    [datasets_principales] NVARCHAR(4000) NULL,
    [pregunta_negocio] NVARCHAR(4000) NULL,
    [output_esperado] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_marketing_mapeo_casos_marketing_precision] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_marketing.promociones_calendario', N'U') IS NOT NULL DROP TABLE [raw_marketing].[promociones_calendario];
GO
CREATE TABLE [raw_marketing].[promociones_calendario] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_marketing_promociones_calendario_loaded_at] DEFAULT SYSUTCDATETIME(),
    [promo_id] NVARCHAR(4000) NULL,
    [nombre_promocion] NVARCHAR(4000) NULL,
    [fecha_inicio] NVARCHAR(4000) NULL,
    [fecha_fin] NVARCHAR(4000) NULL,
    [ambito] NVARCHAR(4000) NULL,
    [scope_id] NVARCHAR(4000) NULL,
    [tipo_promocion] NVARCHAR(4000) NULL,
    [descuento_pct] NVARCHAR(4000) NULL,
    [descuento_importe_eur] NVARCHAR(4000) NULL,
    [canal] NVARCHAR(4000) NULL,
    [segmento_objetivo] NVARCHAR(4000) NULL,
    [store_id] NVARCHAR(4000) NULL,
    [combinable] NVARCHAR(4000) NULL,
    [umbral_cesta_eur] NVARCHAR(4000) NULL,
    [objetivo_margen_min_pct] NVARCHAR(4000) NULL,
    [campana_id_relacionada] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_marketing_promociones_calendario] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_marketing.tickets_atencion_cliente', N'U') IS NOT NULL DROP TABLE [raw_marketing].[tickets_atencion_cliente];
GO
CREATE TABLE [raw_marketing].[tickets_atencion_cliente] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_marketing_tickets_atencion_cliente_loaded_at] DEFAULT SYSUTCDATETIME(),
    [service_ticket_id] NVARCHAR(4000) NULL,
    [fecha_apertura] NVARCHAR(4000) NULL,
    [fecha_cierre] NVARCHAR(4000) NULL,
    [customer_id] NVARCHAR(4000) NULL,
    [order_id] NVARCHAR(4000) NULL,
    [ticket_id] NVARCHAR(4000) NULL,
    [store_id] NVARCHAR(4000) NULL,
    [canal_soporte] NVARCHAR(4000) NULL,
    [tipo_caso] NVARCHAR(4000) NULL,
    [subtipo_caso] NVARCHAR(4000) NULL,
    [motivo_contacto] NVARCHAR(4000) NULL,
    [prioridad] NVARCHAR(4000) NULL,
    [sentimiento_inicial] NVARCHAR(4000) NULL,
    [estado_resolucion] NVARCHAR(4000) NULL,
    [sla_horas] NVARCHAR(4000) NULL,
    [csat_1_5] NVARCHAR(4000) NULL,
    [agente_id] NVARCHAR(4000) NULL,
    [importe_compensacion_eur] NVARCHAR(4000) NULL,
    [texto_cliente] NVARCHAR(4000) NULL,
    [texto_resolucion] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_marketing_tickets_atencion_cliente] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_marketing.validacion_datasets_marketing_precision', N'U') IS NOT NULL DROP TABLE [raw_marketing].[validacion_datasets_marketing_precision];
GO
CREATE TABLE [raw_marketing].[validacion_datasets_marketing_precision] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_marketing_validacion_datasets_marketing_precision_loaded_at] DEFAULT SYSUTCDATETIME(),
    [dataset] NVARCHAR(4000) NULL,
    [filas] NVARCHAR(4000) NULL,
    [columnas] NVARCHAR(4000) NULL,
    [duplicados_clave] NVARCHAR(4000) NULL,
    [nulos_totales] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_marketing_validacion_datasets_marketing_precision] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_people.diccionario_fuentes_brutas', N'U') IS NOT NULL DROP TABLE [raw_people].[diccionario_fuentes_brutas];
GO
CREATE TABLE [raw_people].[diccionario_fuentes_brutas] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_people_diccionario_fuentes_brutas_loaded_at] DEFAULT SYSUTCDATETIME(),
    [archivo] NVARCHAR(4000) NULL,
    [campo_o_grupo] NVARCHAR(4000) NULL,
    [descripcion] NVARCHAR(4000) NULL,
    [uso_analitico] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_people_diccionario_fuentes_brutas] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_people.dim_calendario', N'U') IS NOT NULL DROP TABLE [raw_people].[dim_calendario];
GO
CREATE TABLE [raw_people].[dim_calendario] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_people_dim_calendario_loaded_at] DEFAULT SYSUTCDATETIME(),
    [fecha] NVARCHAR(4000) NULL,
    [anio] NVARCHAR(4000) NULL,
    [mes_num] NVARCHAR(4000) NULL,
    [mes_nombre] NVARCHAR(4000) NULL,
    [trimestre] NVARCHAR(4000) NULL,
    [periodo_mes] NVARCHAR(4000) NULL,
    [fin_mes] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_people_dim_calendario] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_people.dim_departamentos_mapeo', N'U') IS NOT NULL DROP TABLE [raw_people].[dim_departamentos_mapeo];
GO
CREATE TABLE [raw_people].[dim_departamentos_mapeo] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_people_dim_departamentos_mapeo_loaded_at] DEFAULT SYSUTCDATETIME(),
    [departamento_raw] NVARCHAR(4000) NULL,
    [departamento_estandar] NVARCHAR(4000) NULL,
    [area_rrhh] NVARCHAR(4000) NULL,
    [canal_negocio] NVARCHAR(4000) NULL,
    [area_critica_rotacion_default] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_people_dim_departamentos_mapeo] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_people.frasohome_comentarios_clima', N'U') IS NOT NULL DROP TABLE [raw_people].[frasohome_comentarios_clima];
GO
CREATE TABLE [raw_people].[frasohome_comentarios_clima] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_people_frasohome_comentarios_clima_loaded_at] DEFAULT SYSUTCDATETIME(),
    [employee_id] NVARCHAR(4000) NULL,
    [departamento] NVARCHAR(4000) NULL,
    [ubicacion] NVARCHAR(4000) NULL,
    [rol] NVARCHAR(4000) NULL,
    [nivel] NVARCHAR(4000) NULL,
    [estado_actual] NVARCHAR(4000) NULL,
    [satisfaccion_1_10] NVARCHAR(4000) NULL,
    [engagement_1_10] NVARCHAR(4000) NULL,
    [comentario_clima] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_people_frasohome_comentarios_clima] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_people.frasohome_comentarios_salida', N'U') IS NOT NULL DROP TABLE [raw_people].[frasohome_comentarios_salida];
GO
CREATE TABLE [raw_people].[frasohome_comentarios_salida] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_people_frasohome_comentarios_salida_loaded_at] DEFAULT SYSUTCDATETIME(),
    [employee_id] NVARCHAR(4000) NULL,
    [departamento] NVARCHAR(4000) NULL,
    [ubicacion] NVARCHAR(4000) NULL,
    [rol] NVARCHAR(4000) NULL,
    [nivel] NVARCHAR(4000) NULL,
    [fecha_salida] NVARCHAR(4000) NULL,
    [tipo_salida] NVARCHAR(4000) NULL,
    [motivo_salida_sistema] NVARCHAR(4000) NULL,
    [comentario_salida] NVARCHAR(4000) NULL,
    [satisfaccion_1_10] NVARCHAR(4000) NULL,
    [probabilidad_abandono] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_people_frasohome_comentarios_salida] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_people.frasohome_diccionario_datos', N'U') IS NOT NULL DROP TABLE [raw_people].[frasohome_diccionario_datos];
GO
CREATE TABLE [raw_people].[frasohome_diccionario_datos] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_people_frasohome_diccionario_datos_loaded_at] DEFAULT SYSUTCDATETIME(),
    [dataset] NVARCHAR(4000) NULL,
    [columna] NVARCHAR(4000) NULL,
    [descripcion] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_people_frasohome_diccionario_datos] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_people.frasohome_muestra_prompt_chatgpt', N'U') IS NOT NULL DROP TABLE [raw_people].[frasohome_muestra_prompt_chatgpt];
GO
CREATE TABLE [raw_people].[frasohome_muestra_prompt_chatgpt] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_people_frasohome_muestra_prompt_chatgpt_loaded_at] DEFAULT SYSUTCDATETIME(),
    [employee_id] NVARCHAR(4000) NULL,
    [departamento] NVARCHAR(4000) NULL,
    [ubicacion] NVARCHAR(4000) NULL,
    [rol] NVARCHAR(4000) NULL,
    [nivel] NVARCHAR(4000) NULL,
    [fecha_salida] NVARCHAR(4000) NULL,
    [tipo_salida] NVARCHAR(4000) NULL,
    [motivo_salida_sistema] NVARCHAR(4000) NULL,
    [comentario_salida] NVARCHAR(4000) NULL,
    [satisfaccion_1_10] NVARCHAR(4000) NULL,
    [probabilidad_abandono] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_people_frasohome_muestra_prompt_chatgpt] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_people.frasohome_people_analytics', N'U') IS NOT NULL DROP TABLE [raw_people].[frasohome_people_analytics];
GO
CREATE TABLE [raw_people].[frasohome_people_analytics] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_people_frasohome_people_analytics_loaded_at] DEFAULT SYSUTCDATETIME(),
    [employee_id] NVARCHAR(4000) NULL,
    [nombre_anonimizado] NVARCHAR(4000) NULL,
    [genero] NVARCHAR(4000) NULL,
    [edad] NVARCHAR(4000) NULL,
    [departamento] NVARCHAR(4000) NULL,
    [ubicacion] NVARCHAR(4000) NULL,
    [rol] NVARCHAR(4000) NULL,
    [nivel] NVARCHAR(4000) NULL,
    [tipo_contrato] NVARCHAR(4000) NULL,
    [jornada] NVARCHAR(4000) NULL,
    [fecha_alta] NVARCHAR(4000) NULL,
    [fecha_salida] NVARCHAR(4000) NULL,
    [estado_actual] NVARCHAR(4000) NULL,
    [tipo_salida] NVARCHAR(4000) NULL,
    [motivo_salida] NVARCHAR(4000) NULL,
    [abandono_voluntario_24m] NVARCHAR(4000) NULL,
    [salida_24m] NVARCHAR(4000) NULL,
    [activo_actual] NVARCHAR(4000) NULL,
    [antiguedad_meses] NVARCHAR(4000) NULL,
    [evaluacion_desempeno_1_5] NVARCHAR(4000) NULL,
    [promociones_24m] NVARCHAR(4000) NULL,
    [incremento_salarial_12m_pct] NVARCHAR(4000) NULL,
    [salario_anual_eur] NVARCHAR(4000) NULL,
    [horas_formacion_12m] NVARCHAR(4000) NULL,
    [satisfaccion_1_10] NVARCHAR(4000) NULL,
    [engagement_1_10] NVARCHAR(4000) NULL,
    [enps] NVARCHAR(4000) NULL,
    [calidad_manager_1_5] NVARCHAR(4000) NULL,
    [desarrollo_carrera_1_5] NVARCHAR(4000) NULL,
    [reconocimiento_1_5] NVARCHAR(4000) NULL,
    [percepcion_salario_1_5] NVARCHAR(4000) NULL,
    [balance_vida_trabajo_1_5] NVARCHAR(4000) NULL,
    [carga_trabajo_1_5] NVARCHAR(4000) NULL,
    [absentismo_dias_12m] NVARCHAR(4000) NULL,
    [horas_extra_media_mes] NVARCHAR(4000) NULL,
    [teletrabajo_dias_semana] NVARCHAR(4000) NULL,
    [distancia_casa_trabajo_km] NVARCHAR(4000) NULL,
    [probabilidad_abandono] NVARCHAR(4000) NULL,
    [riesgo_abandono] NVARCHAR(4000) NULL,
    [alto_riesgo_flag] NVARCHAR(4000) NULL,
    [talento_clave_flag] NVARCHAR(4000) NULL,
    [prioridad_retencion] NVARCHAR(4000) NULL,
    [conteo_empleado] NVARCHAR(4000) NULL,
    [comentario_salida] NVARCHAR(4000) NULL,
    [comentario_clima] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_people_frasohome_people_analytics] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_people.frasohome_rotacion_mensual', N'U') IS NOT NULL DROP TABLE [raw_people].[frasohome_rotacion_mensual];
GO
CREATE TABLE [raw_people].[frasohome_rotacion_mensual] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_people_frasohome_rotacion_mensual_loaded_at] DEFAULT SYSUTCDATETIME(),
    [periodo_mes] NVARCHAR(4000) NULL,
    [departamento] NVARCHAR(4000) NULL,
    [headcount_inicio_mes] NVARCHAR(4000) NULL,
    [altas_mes] NVARCHAR(4000) NULL,
    [bajas_voluntarias_mes] NVARCHAR(4000) NULL,
    [bajas_no_voluntarias_mes] NVARCHAR(4000) NULL,
    [bajas_totales_mes] NVARCHAR(4000) NULL,
    [headcount_fin_mes] NVARCHAR(4000) NULL,
    [tasa_rotacion_voluntaria_pct] NVARCHAR(4000) NULL,
    [tasa_rotacion_total_pct] NVARCHAR(4000) NULL,
    [empleados_alto_riesgo_fin_mes] NVARCHAR(4000) NULL,
    [talento_clave_alto_riesgo_fin_mes] NVARCHAR(4000) NULL,
    [salario_medio_activos_mes_eur] NVARCHAR(4000) NULL,
    [satisfaccion_media_activos_mes] NVARCHAR(4000) NULL,
    [engagement_medio_activos_mes] NVARCHAR(4000) NULL,
    [area_critica_rotacion_flag] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_people_frasohome_rotacion_mensual] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_people.plantilla_backlog_indicadores', N'U') IS NOT NULL DROP TABLE [raw_people].[plantilla_backlog_indicadores];
GO
CREATE TABLE [raw_people].[plantilla_backlog_indicadores] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_people_plantilla_backlog_indicadores_loaded_at] DEFAULT SYSUTCDATETIME(),
    [pregunta_alumnos] NVARCHAR(4000) NULL,
    [indicador] NVARCHAR(4000) NULL,
    [datos_origen] NVARCHAR(4000) NULL,
    [formula_negocio] NVARCHAR(4000) NULL,
    [visual_sugerido] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_people_plantilla_backlog_indicadores] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_people.raw_absentismo', N'U') IS NOT NULL DROP TABLE [raw_people].[raw_absentismo];
GO
CREATE TABLE [raw_people].[raw_absentismo] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_people_raw_absentismo_loaded_at] DEFAULT SYSUTCDATETIME(),
    [ausencia_id] NVARCHAR(4000) NULL,
    [employee_code_raw] NVARCHAR(4000) NULL,
    [fecha_inicio_txt] NVARCHAR(4000) NULL,
    [fecha_fin_txt] NVARCHAR(4000) NULL,
    [tipo_ausencia_raw] NVARCHAR(4000) NULL,
    [dias_laborables_raw] NVARCHAR(4000) NULL,
    [justificada_raw] NVARCHAR(4000) NULL,
    [observaciones_raw] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_people_raw_absentismo] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_people.raw_encuesta_clima_respuestas', N'U') IS NOT NULL DROP TABLE [raw_people].[raw_encuesta_clima_respuestas];
GO
CREATE TABLE [raw_people].[raw_encuesta_clima_respuestas] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_people_raw_encuesta_clima_respuestas_loaded_at] DEFAULT SYSUTCDATETIME(),
    [respuesta_id] NVARCHAR(4000) NULL,
    [employee_code_raw] NVARCHAR(4000) NULL,
    [fecha_encuesta_txt] NVARCHAR(4000) NULL,
    [oleada_raw] NVARCHAR(4000) NULL,
    [dimension_raw] NVARCHAR(4000) NULL,
    [question_code] NVARCHAR(4000) NULL,
    [pregunta_texto] NVARCHAR(4000) NULL,
    [score_raw] NVARCHAR(4000) NULL,
    [comentario_abierto_raw] NVARCHAR(4000) NULL,
    [canal_respuesta] NVARCHAR(4000) NULL,
    [fuente] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_people_raw_encuesta_clima_respuestas] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_people.raw_evaluaciones_desempeno', N'U') IS NOT NULL DROP TABLE [raw_people].[raw_evaluaciones_desempeno];
GO
CREATE TABLE [raw_people].[raw_evaluaciones_desempeno] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_people_raw_evaluaciones_desempeno_loaded_at] DEFAULT SYSUTCDATETIME(),
    [evaluacion_id] NVARCHAR(4000) NULL,
    [employee_code_raw] NVARCHAR(4000) NULL,
    [ciclo_evaluacion] NVARCHAR(4000) NULL,
    [fecha_evaluacion_txt] NVARCHAR(4000) NULL,
    [evaluacion_global_raw] NVARCHAR(4000) NULL,
    [cumplimiento_objetivos_pct_raw] NVARCHAR(4000) NULL,
    [competencias_1_5_raw] NVARCHAR(4000) NULL,
    [potencial_raw] NVARCHAR(4000) NULL,
    [evaluador_code_raw] NVARCHAR(4000) NULL,
    [comentario_manager_raw] NVARCHAR(4000) NULL,
    [fuente] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_people_raw_evaluaciones_desempeno] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_people.raw_exit_interviews', N'U') IS NOT NULL DROP TABLE [raw_people].[raw_exit_interviews];
GO
CREATE TABLE [raw_people].[raw_exit_interviews] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_people_raw_exit_interviews_loaded_at] DEFAULT SYSUTCDATETIME(),
    [exit_interview_id] NVARCHAR(4000) NULL,
    [employee_code_raw] NVARCHAR(4000) NULL,
    [fecha_salida_txt] NVARCHAR(4000) NULL,
    [fecha_entrevista_txt] NVARCHAR(4000) NULL,
    [tipo_salida_raw] NVARCHAR(4000) NULL,
    [motivo_salida_rrhh_raw] NVARCHAR(4000) NULL,
    [comentario_salida_raw] NVARCHAR(4000) NULL,
    [recomendaria_empresa_1_10_raw] NVARCHAR(4000) NULL,
    [canal_entrevista_raw] NVARCHAR(4000) NULL,
    [entrevistador_raw] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_people_raw_exit_interviews] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_people.raw_formacion', N'U') IS NOT NULL DROP TABLE [raw_people].[raw_formacion];
GO
CREATE TABLE [raw_people].[raw_formacion] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_people_raw_formacion_loaded_at] DEFAULT SYSUTCDATETIME(),
    [formacion_id] NVARCHAR(4000) NULL,
    [employee_code_raw] NVARCHAR(4000) NULL,
    [curso_id] NVARCHAR(4000) NULL,
    [curso_nombre] NVARCHAR(4000) NULL,
    [categoria_formacion_raw] NVARCHAR(4000) NULL,
    [fecha_inicio_txt] NVARCHAR(4000) NULL,
    [fecha_fin_txt] NVARCHAR(4000) NULL,
    [horas_planificadas_raw] NVARCHAR(4000) NULL,
    [horas_realizadas_raw] NVARCHAR(4000) NULL,
    [estado_curso_raw] NVARCHAR(4000) NULL,
    [coste_eur_raw] NVARCHAR(4000) NULL,
    [proveedor_raw] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_people_raw_formacion] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_people.raw_horas_extra', N'U') IS NOT NULL DROP TABLE [raw_people].[raw_horas_extra];
GO
CREATE TABLE [raw_people].[raw_horas_extra] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_people_raw_horas_extra_loaded_at] DEFAULT SYSUTCDATETIME(),
    [horas_extra_id] NVARCHAR(4000) NULL,
    [employee_code_raw] NVARCHAR(4000) NULL,
    [periodo_mes_txt] NVARCHAR(4000) NULL,
    [departamento_reportado_raw] NVARCHAR(4000) NULL,
    [horas_extra_raw] NVARCHAR(4000) NULL,
    [motivo_raw] NVARCHAR(4000) NULL,
    [estado_aprobacion_raw] NVARCHAR(4000) NULL,
    [aprobador_raw] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_people_raw_horas_extra] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_people.raw_hris_empleados', N'U') IS NOT NULL DROP TABLE [raw_people].[raw_hris_empleados];
GO
CREATE TABLE [raw_people].[raw_hris_empleados] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_people_raw_hris_empleados_loaded_at] DEFAULT SYSUTCDATETIME(),
    [source_row_id] NVARCHAR(4000) NULL,
    [employee_code_raw] NVARCHAR(4000) NULL,
    [nombre_apellidos_raw] NVARCHAR(4000) NULL,
    [genero_raw] NVARCHAR(4000) NULL,
    [fecha_nacimiento_txt] NVARCHAR(4000) NULL,
    [fecha_alta_txt] NVARCHAR(4000) NULL,
    [fecha_salida_txt] NVARCHAR(4000) NULL,
    [estado_raw] NVARCHAR(4000) NULL,
    [tipo_salida_raw] NVARCHAR(4000) NULL,
    [departamento_raw] NVARCHAR(4000) NULL,
    [ubicacion_raw] NVARCHAR(4000) NULL,
    [rol_raw] NVARCHAR(4000) NULL,
    [nivel_raw] NVARCHAR(4000) NULL,
    [tipo_contrato_raw] NVARCHAR(4000) NULL,
    [jornada_raw] NVARCHAR(4000) NULL,
    [manager_code_raw] NVARCHAR(4000) NULL,
    [teletrabajo_dias_semana_raw] NVARCHAR(4000) NULL,
    [distancia_casa_trabajo_km_raw] NVARCHAR(4000) NULL,
    [source_system] NVARCHAR(4000) NULL,
    [fecha_carga_txt] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_people_raw_hris_empleados] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_people.raw_movimientos_personal', N'U') IS NOT NULL DROP TABLE [raw_people].[raw_movimientos_personal];
GO
CREATE TABLE [raw_people].[raw_movimientos_personal] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_people_raw_movimientos_personal_loaded_at] DEFAULT SYSUTCDATETIME(),
    [movimiento_id] NVARCHAR(4000) NULL,
    [employee_code_raw] NVARCHAR(4000) NULL,
    [fecha_movimiento_txt] NVARCHAR(4000) NULL,
    [tipo_movimiento_raw] NVARCHAR(4000) NULL,
    [departamento_origen_raw] NVARCHAR(4000) NULL,
    [departamento_destino_raw] NVARCHAR(4000) NULL,
    [nivel_origen_raw] NVARCHAR(4000) NULL,
    [nivel_destino_raw] NVARCHAR(4000) NULL,
    [motivo_movimiento_raw] NVARCHAR(4000) NULL,
    [comentario_rrhh] NVARCHAR(4000) NULL,
    [usuario_carga] NVARCHAR(4000) NULL,
    [fecha_carga_txt] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_people_raw_movimientos_personal] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_people.raw_salarios_beneficios', N'U') IS NOT NULL DROP TABLE [raw_people].[raw_salarios_beneficios];
GO
CREATE TABLE [raw_people].[raw_salarios_beneficios] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_people_raw_salarios_beneficios_loaded_at] DEFAULT SYSUTCDATETIME(),
    [nomina_id] NVARCHAR(4000) NULL,
    [employee_code_raw] NVARCHAR(4000) NULL,
    [periodo_nomina_txt] NVARCHAR(4000) NULL,
    [salario_base_anual_raw] NVARCHAR(4000) NULL,
    [salario_variable_anual_raw] NVARCHAR(4000) NULL,
    [incremento_aplicado_pct_raw] NVARCHAR(4000) NULL,
    [moneda_raw] NVARCHAR(4000) NULL,
    [fuente_nomina_raw] NVARCHAR(4000) NULL,
    [fecha_carga_txt] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_people_raw_salarios_beneficios] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_rag.fs_alertas_stockout', N'U') IS NOT NULL DROP TABLE [raw_rag].[fs_alertas_stockout];
GO
CREATE TABLE [raw_rag].[fs_alertas_stockout] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_rag_fs_alertas_stockout_loaded_at] DEFAULT SYSUTCDATETIME(),
    [alertdate] NVARCHAR(4000) NULL,
    [storeid] NVARCHAR(4000) NULL,
    [productid] NVARCHAR(4000) NULL,
    [availableunits] NVARCHAR(4000) NULL,
    [salesunitslast7d] NVARCHAR(4000) NULL,
    [priority] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_rag_fs_alertas_stockout] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_rag.fs_clientes', N'U') IS NOT NULL DROP TABLE [raw_rag].[fs_clientes];
GO
CREATE TABLE [raw_rag].[fs_clientes] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_rag_fs_clientes_loaded_at] DEFAULT SYSUTCDATETIME(),
    [customerid] NVARCHAR(4000) NULL,
    [tier] NVARCHAR(4000) NULL,
    [joindate] NVARCHAR(4000) NULL,
    [city] NVARCHAR(4000) NULL,
    [consentmarketing] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_rag_fs_clientes] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_rag.fs_devolucionesfact', N'U') IS NOT NULL DROP TABLE [raw_rag].[fs_devolucionesfact];
GO
CREATE TABLE [raw_rag].[fs_devolucionesfact] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_rag_fs_devolucionesfact_loaded_at] DEFAULT SYSUTCDATETIME(),
    [returnid] NVARCHAR(4000) NULL,
    [returndate] NVARCHAR(4000) NULL,
    [channel] NVARCHAR(4000) NULL,
    [storeid] NVARCHAR(4000) NULL,
    [customerid] NVARCHAR(4000) NULL,
    [productid] NVARCHAR(4000) NULL,
    [units] NVARCHAR(4000) NULL,
    [refundamounteur] NVARCHAR(4000) NULL,
    [reasoncode] NVARCHAR(4000) NULL,
    [reasondesc] NVARCHAR(4000) NULL,
    [condition] NVARCHAR(4000) NULL,
    [approved] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_rag_fs_devolucionesfact] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_rag.fs_productos', N'U') IS NOT NULL DROP TABLE [raw_rag].[fs_productos];
GO
CREATE TABLE [raw_rag].[fs_productos] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_rag_fs_productos_loaded_at] DEFAULT SYSUTCDATETIME(),
    [productid] NVARCHAR(4000) NULL,
    [productname] NVARCHAR(4000) NULL,
    [categoryfamily] NVARCHAR(4000) NULL,
    [categorycode] NVARCHAR(4000) NULL,
    [categoryname] NVARCHAR(4000) NULL,
    [material] NVARCHAR(4000) NULL,
    [color] NVARCHAR(4000) NULL,
    [bulkyflag] NVARCHAR(4000) NULL,
    [standardcosteur] NVARCHAR(4000) NULL,
    [listpriceeur] NVARCHAR(4000) NULL,
    [status] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_rag_fs_productos] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_rag.fs_stockdiario', N'U') IS NOT NULL DROP TABLE [raw_rag].[fs_stockdiario];
GO
CREATE TABLE [raw_rag].[fs_stockdiario] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_rag_fs_stockdiario_loaded_at] DEFAULT SYSUTCDATETIME(),
    [date] NVARCHAR(4000) NULL,
    [storeid] NVARCHAR(4000) NULL,
    [productid] NVARCHAR(4000) NULL,
    [onhandunits] NVARCHAR(4000) NULL,
    [reservedunits] NVARCHAR(4000) NULL,
    [blockedunits] NVARCHAR(4000) NULL,
    [availableunits] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_rag_fs_stockdiario] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_rag.fs_tiendas', N'U') IS NOT NULL DROP TABLE [raw_rag].[fs_tiendas];
GO
CREATE TABLE [raw_rag].[fs_tiendas] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_rag_fs_tiendas_loaded_at] DEFAULT SYSUTCDATETIME(),
    [storeid] NVARCHAR(4000) NULL,
    [storename] NVARCHAR(4000) NULL,
    [city] NVARCHAR(4000) NULL,
    [region] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_rag_fs_tiendas] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_rag.fs_ventasresumendiario', N'U') IS NOT NULL DROP TABLE [raw_rag].[fs_ventasresumendiario];
GO
CREATE TABLE [raw_rag].[fs_ventasresumendiario] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_rag_fs_ventasresumendiario_loaded_at] DEFAULT SYSUTCDATETIME(),
    [date] NVARCHAR(4000) NULL,
    [channel] NVARCHAR(4000) NULL,
    [storeid] NVARCHAR(4000) NULL,
    [grosssaleseur] NVARCHAR(4000) NULL,
    [discountseur] NVARCHAR(4000) NULL,
    [pointsdiscounteur] NVARCHAR(4000) NULL,
    [returnseur] NVARCHAR(4000) NULL,
    [netsaleseur] NVARCHAR(4000) NULL,
    [orders] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_rag_fs_ventasresumendiario] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_rag.fs_testset_documental', N'U') IS NOT NULL DROP TABLE [raw_rag].[fs_testset_documental];
GO
CREATE TABLE [raw_rag].[fs_testset_documental] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_rag_fs_testset_documental_loaded_at] DEFAULT SYSUTCDATETIME(),
    [question] NVARCHAR(4000) NULL,
    [expected_response] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_rag_fs_testset_documental] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_rag.fs_testset_metrico_mixto', N'U') IS NOT NULL DROP TABLE [raw_rag].[fs_testset_metrico_mixto];
GO
CREATE TABLE [raw_rag].[fs_testset_metrico_mixto] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_rag_fs_testset_metrico_mixto_loaded_at] DEFAULT SYSUTCDATETIME(),
    [question] NVARCHAR(4000) NULL,
    [expected_response] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_rag_fs_testset_metrico_mixto] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'xref.coherence_check_summary', N'U') IS NOT NULL DROP TABLE [xref].[coherence_check_summary];
GO
CREATE TABLE [xref].[coherence_check_summary] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_xref_coherence_check_summary_loaded_at] DEFAULT SYSUTCDATETIME(),
    [scope] NVARCHAR(4000) NULL,
    [dataset] NVARCHAR(4000) NULL,
    [column] NVARCHAR(4000) NULL,
    [refs] NVARCHAR(4000) NULL,
    [hits_after_mapping] NVARCHAR(4000) NULL,
    [misses_after_mapping] NVARCHAR(4000) NULL,
    [hit_pct_after_mapping] NVARCHAR(4000) NULL,
    [sample_misses] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_xref_coherence_check_summary] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'xref.employee_operational_aliases', N'U') IS NOT NULL DROP TABLE [xref].[employee_operational_aliases];
GO
CREATE TABLE [xref].[employee_operational_aliases] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_xref_employee_operational_aliases_loaded_at] DEFAULT SYSUTCDATETIME(),
    [source_system] NVARCHAR(4000) NULL,
    [operational_employee_id] NVARCHAR(4000) NULL,
    [canonical_employee_id] NVARCHAR(4000) NULL,
    [canonical_employee_location] NVARCHAR(4000) NULL,
    [canonical_employee_department] NVARCHAR(4000) NULL,
    [match_method] NVARCHAR(4000) NULL,
    [confidence] NVARCHAR(4000) NULL,
    [note] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_xref_employee_operational_aliases] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'xref.employee_store_assignment', N'U') IS NOT NULL DROP TABLE [xref].[employee_store_assignment];
GO
CREATE TABLE [xref].[employee_store_assignment] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_xref_employee_store_assignment_loaded_at] DEFAULT SYSUTCDATETIME(),
    [employee_id] NVARCHAR(4000) NULL,
    [department] NVARCHAR(4000) NULL,
    [location] NVARCHAR(4000) NULL,
    [canonical_store_id] NVARCHAR(4000) NULL,
    [assignment_type] NVARCHAR(4000) NULL,
    [confidence] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_xref_employee_store_assignment] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'xref.marketing_precision_operational_links', N'U') IS NOT NULL DROP TABLE [xref].[marketing_precision_operational_links];
GO
CREATE TABLE [xref].[marketing_precision_operational_links] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_xref_marketing_precision_operational_links_loaded_at] DEFAULT SYSUTCDATETIME(),
    [dataset] NVARCHAR(4000) NULL,
    [column] NVARCHAR(4000) NULL,
    [business_entity] NVARCHAR(4000) NULL,
    [canonical_reference] NVARCHAR(4000) NULL,
    [notes] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_xref_marketing_precision_operational_links] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'xref.product_aliases_rag_to_retail', N'U') IS NOT NULL DROP TABLE [xref].[product_aliases_rag_to_retail];
GO
CREATE TABLE [xref].[product_aliases_rag_to_retail] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_xref_product_aliases_rag_to_retail_loaded_at] DEFAULT SYSUTCDATETIME(),
    [source_system] NVARCHAR(4000) NULL,
    [source_product_id] NVARCHAR(4000) NULL,
    [source_product_name] NVARCHAR(4000) NULL,
    [source_category_code] NVARCHAR(4000) NULL,
    [source_category_name] NVARCHAR(4000) NULL,
    [canonical_product_id] NVARCHAR(4000) NULL,
    [canonical_product_name] NVARCHAR(4000) NULL,
    [canonical_category] NVARCHAR(4000) NULL,
    [canonical_subcategory] NVARCHAR(4000) NULL,
    [match_method] NVARCHAR(4000) NULL,
    [confidence] NVARCHAR(4000) NULL,
    [note] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_xref_product_aliases_rag_to_retail] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'xref.store_aliases', N'U') IS NOT NULL DROP TABLE [xref].[store_aliases];
GO
CREATE TABLE [xref].[store_aliases] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_xref_store_aliases_loaded_at] DEFAULT SYSUTCDATETIME(),
    [alias_store_id_or_location] NVARCHAR(4000) NULL,
    [canonical_store_id] NVARCHAR(4000) NULL,
    [source_context] NVARCHAR(4000) NULL,
    [confidence] NVARCHAR(4000) NULL,
    [note] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_xref_store_aliases] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_retail.crm', N'U') IS NOT NULL DROP TABLE [raw_retail].[crm];
GO
CREATE TABLE [raw_retail].[crm] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_retail_crm_loaded_at] DEFAULT SYSUTCDATETIME(),
    [customer_id] NVARCHAR(4000) NULL,
    [nombre] NVARCHAR(4000) NULL,
    [apellidos] NVARCHAR(4000) NULL,
    [email] NVARCHAR(4000) NULL,
    [telefono] NVARCHAR(4000) NULL,
    [fecha_alta_programa] NVARCHAR(4000) NULL,
    [tier_fidelizacion] NVARCHAR(4000) NULL,
    [puntos_acumulados] NVARCHAR(4000) NULL,
    [fecha_nacimiento] NVARCHAR(4000) NULL,
    [genero] NVARCHAR(4000) NULL,
    [ciudad] NVARCHAR(4000) NULL,
    [provincia] NVARCHAR(4000) NULL,
    [codigo_postal] NVARCHAR(4000) NULL,
    [pais] NVARCHAR(4000) NULL,
    [consentimiento_marketing] NVARCHAR(4000) NULL,
    [estado_cliente] NVARCHAR(4000) NULL,
    [fecha_baja] NVARCHAR(4000) NULL,
    [origen_alta] NVARCHAR(4000) NULL,
    [canal_preferido_declarado] NVARCHAR(4000) NULL,
    [ultima_actualizacion] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_retail_crm] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_retail.devoluciones_online', N'U') IS NOT NULL DROP TABLE [raw_retail].[devoluciones_online];
GO
CREATE TABLE [raw_retail].[devoluciones_online] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_retail_devoluciones_online_loaded_at] DEFAULT SYSUTCDATETIME(),
    [return_id] NVARCHAR(4000) NULL,
    [order_id] NVARCHAR(4000) NULL,
    [order_line_id] NVARCHAR(4000) NULL,
    [product_id] NVARCHAR(4000) NULL,
    [fecha_devolucion] NVARCHAR(4000) NULL,
    [cantidad_devuelta] NVARCHAR(4000) NULL,
    [motivo_devolucion] NVARCHAR(4000) NULL,
    [metodo_devolucion] NVARCHAR(4000) NULL,
    [estado_devolucion] NVARCHAR(4000) NULL,
    [importe_reembolsado] NVARCHAR(4000) NULL,
    [moneda] NVARCHAR(4000) NULL,
    [comentarios] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_retail_devoluciones_online] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_retail.devoluciones_tienda', N'U') IS NOT NULL DROP TABLE [raw_retail].[devoluciones_tienda];
GO
CREATE TABLE [raw_retail].[devoluciones_tienda] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_retail_devoluciones_tienda_loaded_at] DEFAULT SYSUTCDATETIME(),
    [return_id] NVARCHAR(4000) NULL,
    [fecha_devolucion] NVARCHAR(4000) NULL,
    [store_id] NVARCHAR(4000) NULL,
    [ticket_id_original] NVARCHAR(4000) NULL,
    [ticket_line_id_original] NVARCHAR(4000) NULL,
    [order_id_original] NVARCHAR(4000) NULL,
    [customer_id] NVARCHAR(4000) NULL,
    [product_id] NVARCHAR(4000) NULL,
    [cantidad_devuelta] NVARCHAR(4000) NULL,
    [estado_devolucion] NVARCHAR(4000) NULL,
    [importe_reembolsado] NVARCHAR(4000) NULL,
    [moneda] NVARCHAR(4000) NULL,
    [metodo_reembolso] NVARCHAR(4000) NULL,
    [motivo_devolucion] NVARCHAR(4000) NULL,
    [canal_origen_venta] NVARCHAR(4000) NULL,
    [comentarios] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_retail_devoluciones_tienda] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_retail.fact_transacciones', N'U') IS NOT NULL DROP TABLE [raw_retail].[fact_transacciones];
GO
CREATE TABLE [raw_retail].[fact_transacciones] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_retail_fact_transacciones_loaded_at] DEFAULT SYSUTCDATETIME(),
    [fact_id] NVARCHAR(4000) NULL,
    [source_system] NVARCHAR(4000) NULL,
    [source_file] NVARCHAR(4000) NULL,
    [canal_origen] NVARCHAR(4000) NULL,
    [canal_movimiento] NVARCHAR(4000) NULL,
    [tipo_movimiento] NVARCHAR(4000) NULL,
    [es_devolucion] NVARCHAR(4000) NULL,
    [fecha_movimiento_raw] NVARCHAR(4000) NULL,
    [fecha_movimiento] NVARCHAR(4000) NULL,
    [store_id_raw] NVARCHAR(4000) NULL,
    [store_id_std] NVARCHAR(4000) NULL,
    [doc_tipo] NVARCHAR(4000) NULL,
    [doc_id_raw] NVARCHAR(4000) NULL,
    [doc_id_std] NVARCHAR(4000) NULL,
    [line_id_raw] NVARCHAR(4000) NULL,
    [line_id_std] NVARCHAR(4000) NULL,
    [return_id] NVARCHAR(4000) NULL,
    [customer_id_raw] NVARCHAR(4000) NULL,
    [customer_id_std] NVARCHAR(4000) NULL,
    [flag_customer_in_crm] NVARCHAR(4000) NULL,
    [product_id_raw] NVARCHAR(4000) NULL,
    [product_id_std] NVARCHAR(4000) NULL,
    [flag_product_in_master] NVARCHAR(4000) NULL,
    [descripcion_producto] NVARCHAR(4000) NULL,
    [categoria] NVARCHAR(4000) NULL,
    [subcategoria] NVARCHAR(4000) NULL,
    [cantidad_raw] NVARCHAR(4000) NULL,
    [cantidad_signed] NVARCHAR(4000) NULL,
    [cantidad_abs] NVARCHAR(4000) NULL,
    [precio_unitario_raw] NVARCHAR(4000) NULL,
    [precio_unitario_num] NVARCHAR(4000) NULL,
    [descuento_pct_raw] NVARCHAR(4000) NULL,
    [descuento_pct_num] NVARCHAR(4000) NULL,
    [descuento_importe_raw] NVARCHAR(4000) NULL,
    [descuento_importe_num] NVARCHAR(4000) NULL,
    [importe_linea_raw] NVARCHAR(4000) NULL,
    [importe_signed_num] NVARCHAR(4000) NULL,
    [importe_abs_num] NVARCHAR(4000) NULL,
    [moneda] NVARCHAR(4000) NULL,
    [iva_pct] NVARCHAR(4000) NULL,
    [coste_unitario_num] NVARCHAR(4000) NULL,
    [coste_total_num] NVARCHAR(4000) NULL,
    [margen_bruto_num] NVARCHAR(4000) NULL,
    [metodo_pago] NVARCHAR(4000) NULL,
    [estado_pedido] NVARCHAR(4000) NULL,
    [origen] NVARCHAR(4000) NULL,
    [ticket_id_original] NVARCHAR(4000) NULL,
    [ticket_line_id_original] NVARCHAR(4000) NULL,
    [order_id_original] NVARCHAR(4000) NULL,
    [order_line_id_original] NVARCHAR(4000) NULL,
    [motivo_devolucion] NVARCHAR(4000) NULL,
    [metodo_devolucion] NVARCHAR(4000) NULL,
    [caja_id] NVARCHAR(4000) NULL,
    [cajero_id] NVARCHAR(4000) NULL,
    [flag_fecha_parseada] NVARCHAR(4000) NULL,
    [flag_importe_parseado] NVARCHAR(4000) NULL,
    [nombre_producto] NVARCHAR(4000) NULL,
    [precio_venta_num] NVARCHAR(4000) NULL,
    [estado_producto] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_retail_fact_transacciones] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_retail.lineas_pedido', N'U') IS NOT NULL DROP TABLE [raw_retail].[lineas_pedido];
GO
CREATE TABLE [raw_retail].[lineas_pedido] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_retail_lineas_pedido_loaded_at] DEFAULT SYSUTCDATETIME(),
    [order_line_id] NVARCHAR(4000) NULL,
    [order_id] NVARCHAR(4000) NULL,
    [product_id] NVARCHAR(4000) NULL,
    [descripcion_producto] NVARCHAR(4000) NULL,
    [categoria] NVARCHAR(4000) NULL,
    [subcategoria] NVARCHAR(4000) NULL,
    [cantidad] NVARCHAR(4000) NULL,
    [precio_unitario] NVARCHAR(4000) NULL,
    [descuento_pct] NVARCHAR(4000) NULL,
    [descuento_importe] NVARCHAR(4000) NULL,
    [importe_linea] NVARCHAR(4000) NULL,
    [iva_pct] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_retail_lineas_pedido] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_retail.pagos_tienda', N'U') IS NOT NULL DROP TABLE [raw_retail].[pagos_tienda];
GO
CREATE TABLE [raw_retail].[pagos_tienda] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_retail_pagos_tienda_loaded_at] DEFAULT SYSUTCDATETIME(),
    [payment_id] NVARCHAR(4000) NULL,
    [ticket_id] NVARCHAR(4000) NULL,
    [fecha_pago] NVARCHAR(4000) NULL,
    [store_id] NVARCHAR(4000) NULL,
    [caja_id] NVARCHAR(4000) NULL,
    [cajero_id] NVARCHAR(4000) NULL,
    [metodo_pago] NVARCHAR(4000) NULL,
    [importe_pagado] NVARCHAR(4000) NULL,
    [moneda] NVARCHAR(4000) NULL,
    [referencia_autorizacion] NVARCHAR(4000) NULL,
    [estado_pago] NVARCHAR(4000) NULL,
    [observaciones] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_retail_pagos_tienda] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_retail.pedidos', N'U') IS NOT NULL DROP TABLE [raw_retail].[pedidos];
GO
CREATE TABLE [raw_retail].[pedidos] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_retail_pedidos_loaded_at] DEFAULT SYSUTCDATETIME(),
    [order_id] NVARCHAR(4000) NULL,
    [fecha_pedido] NVARCHAR(4000) NULL,
    [customer_id] NVARCHAR(4000) NULL,
    [usuario_online_id] NVARCHAR(4000) NULL,
    [importe_total] NVARCHAR(4000) NULL,
    [moneda] NVARCHAR(4000) NULL,
    [gastos_envio] NVARCHAR(4000) NULL,
    [direccion_envio] NVARCHAR(4000) NULL,
    [codigo_postal_envio] NVARCHAR(4000) NULL,
    [ciudad_envio] NVARCHAR(4000) NULL,
    [provincia_envio] NVARCHAR(4000) NULL,
    [pais_envio] NVARCHAR(4000) NULL,
    [metodo_pago] NVARCHAR(4000) NULL,
    [estado_pedido] NVARCHAR(4000) NULL,
    [origen] NVARCHAR(4000) NULL,
    [ultima_actualizacion] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_retail_pedidos] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_retail.productos', N'U') IS NOT NULL DROP TABLE [raw_retail].[productos];
GO
CREATE TABLE [raw_retail].[productos] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_retail_productos_loaded_at] DEFAULT SYSUTCDATETIME(),
    [product_id] NVARCHAR(4000) NULL,
    [nombre_producto] NVARCHAR(4000) NULL,
    [categoria] NVARCHAR(4000) NULL,
    [subcategoria] NVARCHAR(4000) NULL,
    [marca] NVARCHAR(4000) NULL,
    [proveedor] NVARCHAR(4000) NULL,
    [material] NVARCHAR(4000) NULL,
    [color] NVARCHAR(4000) NULL,
    [precio_venta] NVARCHAR(4000) NULL,
    [coste_unitario] NVARCHAR(4000) NULL,
    [iva_pct] NVARCHAR(4000) NULL,
    [peso_kg] NVARCHAR(4000) NULL,
    [largo_cm] NVARCHAR(4000) NULL,
    [ancho_cm] NVARCHAR(4000) NULL,
    [alto_cm] NVARCHAR(4000) NULL,
    [fecha_alta_catalogo] NVARCHAR(4000) NULL,
    [estado_producto] NVARCHAR(4000) NULL,
    [ean] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_retail_productos] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_retail.stock_diario', N'U') IS NOT NULL DROP TABLE [raw_retail].[stock_diario];
GO
CREATE TABLE [raw_retail].[stock_diario] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_retail_stock_diario_loaded_at] DEFAULT SYSUTCDATETIME(),
    [fecha] NVARCHAR(4000) NULL,
    [store_id] NVARCHAR(4000) NULL,
    [product_id] NVARCHAR(4000) NULL,
    [stock_cierre] NVARCHAR(4000) NULL,
    [stock_reservado] NVARCHAR(4000) NULL,
    [stock_en_transito] NVARCHAR(4000) NULL,
    [stock_minimo] NVARCHAR(4000) NULL,
    [fuente] NVARCHAR(4000) NULL,
    [comentarios] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_retail_stock_diario] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_retail.tiendas', N'U') IS NOT NULL DROP TABLE [raw_retail].[tiendas];
GO
CREATE TABLE [raw_retail].[tiendas] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_retail_tiendas_loaded_at] DEFAULT SYSUTCDATETIME(),
    [store_id] NVARCHAR(4000) NULL,
    [nombre_tienda] NVARCHAR(4000) NULL,
    [tipo_ubicacion] NVARCHAR(4000) NULL,
    [canal] NVARCHAR(4000) NULL,
    [ciudad] NVARCHAR(4000) NULL,
    [provincia] NVARCHAR(4000) NULL,
    [direccion] NVARCHAR(4000) NULL,
    [codigo_postal] NVARCHAR(4000) NULL,
    [pais] NVARCHAR(4000) NULL,
    [fecha_apertura] NVARCHAR(4000) NULL,
    [metros_cuadrados] NVARCHAR(4000) NULL,
    [telefono] NVARCHAR(4000) NULL,
    [horario] NVARCHAR(4000) NULL,
    [lat] NVARCHAR(4000) NULL,
    [lon] NVARCHAR(4000) NULL,
    [estado] NVARCHAR(4000) NULL,
    [region] NVARCHAR(4000) NULL,
    [gerente] NVARCHAR(4000) NULL,
    [observaciones] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_retail_tiendas] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'raw_retail.ventas_pos', N'U') IS NOT NULL DROP TABLE [raw_retail].[ventas_pos];
GO
CREATE TABLE [raw_retail].[ventas_pos] (
    [_load_id] BIGINT IDENTITY(1,1) NOT NULL,
    [_source_file] NVARCHAR(500) NULL,
    [_loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_raw_retail_ventas_pos_loaded_at] DEFAULT SYSUTCDATETIME(),
    [ticket_line_id] NVARCHAR(4000) NULL,
    [ticket_id] NVARCHAR(4000) NULL,
    [fecha_hora] NVARCHAR(4000) NULL,
    [store_id] NVARCHAR(4000) NULL,
    [caja_id] NVARCHAR(4000) NULL,
    [cajero_id] NVARCHAR(4000) NULL,
    [customer_id] NVARCHAR(4000) NULL,
    [product_id] NVARCHAR(4000) NULL,
    [descripcion_producto] NVARCHAR(4000) NULL,
    [categoria] NVARCHAR(4000) NULL,
    [subcategoria] NVARCHAR(4000) NULL,
    [cantidad] NVARCHAR(4000) NULL,
    [precio_unitario] NVARCHAR(4000) NULL,
    [descuento_pct] NVARCHAR(4000) NULL,
    [descuento_importe] NVARCHAR(4000) NULL,
    [importe_linea] NVARCHAR(4000) NULL,
    [moneda] NVARCHAR(4000) NULL,
    [canal] NVARCHAR(4000) NULL,
    [observaciones] NVARCHAR(4000) NULL,
    CONSTRAINT [PK_raw_retail_ventas_pos] PRIMARY KEY CLUSTERED ([_load_id])
);
GO

IF OBJECT_ID(N'admin.load_audit', N'U') IS NOT NULL DROP TABLE [admin].[load_audit];
GO
CREATE TABLE [admin].[load_audit] (
    [load_audit_id] BIGINT IDENTITY(1,1) NOT NULL,
    [schema_name] SYSNAME NOT NULL,
    [table_name] SYSNAME NOT NULL,
    [source_path] NVARCHAR(1000) NULL,
    [source_format] NVARCHAR(20) NOT NULL,
    [started_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_load_audit_started] DEFAULT SYSUTCDATETIME(),
    [finished_at_utc] DATETIME2(0) NULL,
    [status] NVARCHAR(30) NOT NULL CONSTRAINT [DF_load_audit_status] DEFAULT N'STARTED',
    [rows_loaded] BIGINT NULL,
    [error_message] NVARCHAR(MAX) NULL,
    CONSTRAINT [PK_load_audit] PRIMARY KEY CLUSTERED ([load_audit_id])
);
GO

IF OBJECT_ID(N'raw_json.documents', N'U') IS NOT NULL DROP TABLE [raw_json].[documents];
GO
CREATE TABLE [raw_json].[documents] (
    [json_document_id] BIGINT IDENTITY(1,1) NOT NULL,
    [source_path] NVARCHAR(1000) NULL,
    [document_type] NVARCHAR(100) NULL,
    [json_payload] NVARCHAR(MAX) NOT NULL,
    [loaded_at_utc] DATETIME2(0) NOT NULL CONSTRAINT [DF_json_documents_loaded] DEFAULT SYSUTCDATETIME(),
    CONSTRAINT [PK_json_documents] PRIMARY KEY CLUSTERED ([json_document_id]),
    CONSTRAINT [CK_json_documents_isjson] CHECK (ISJSON([json_payload]) = 1)
);
GO
