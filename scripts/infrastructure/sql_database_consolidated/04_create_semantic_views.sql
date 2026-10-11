-- Vistas de ayuda para consumir dominios y relaciones consolidadas.

CREATE OR ALTER VIEW [xref].[vw_store_aliases] AS SELECT * FROM [xref].[store_aliases];
GO
CREATE OR ALTER VIEW [xref].[vw_product_aliases_rag_to_retail] AS SELECT * FROM [xref].[product_aliases_rag_to_retail];
GO
CREATE OR ALTER VIEW [xref].[vw_employee_store_assignment] AS SELECT * FROM [xref].[employee_store_assignment];
GO
CREATE OR ALTER VIEW [xref].[vw_employee_operational_aliases] AS SELECT * FROM [xref].[employee_operational_aliases];
GO
CREATE OR ALTER VIEW [xref].[vw_marketing_precision_operational_links] AS SELECT * FROM [xref].[marketing_precision_operational_links];
GO
CREATE OR ALTER VIEW [xref].[vw_coherence_check_summary] AS SELECT * FROM [xref].[coherence_check_summary];
GO

CREATE OR ALTER VIEW [raw_marketing].[vw_customer_touchpoints] AS
SELECT N'contacto_campana' AS touchpoint_type, [customer_id], [campaign_id], [fecha_contacto] AS event_at, [canal_contacto] AS channel, [offer_code], [coupon_instance_id], [product_id_recomendado_1] AS product_id, [store_id_personalizado] AS store_id FROM [raw_marketing].[contactos_campana]
UNION ALL
SELECT N'evento_campana', [customer_id], [campaign_id], [fecha_evento], [tipo_evento], NULL, NULL, NULL, [store_id] FROM [raw_marketing].[eventos_campana]
UNION ALL
SELECT N'web_app', [customer_id], [utm_campaign], [fecha_hora_evento], [tipo_evento], NULL, NULL, [product_id], [store_id_interes] FROM [raw_marketing].[eventos_web_app];
GO

CREATE OR ALTER VIEW [raw_people].[vw_employee_retail_context] AS
SELECT e.[employee_id], e.[department], e.[location], e.[canonical_store_id], s.[nombre_tienda] AS canonical_store_name, s.[ciudad] AS canonical_store_city, e.[assignment_type], e.[confidence]
FROM [xref].[employee_store_assignment] AS e
LEFT JOIN [raw_retail].[tiendas] AS s ON UPPER(LTRIM(RTRIM(e.[canonical_store_id]))) = UPPER(LTRIM(RTRIM(s.[store_id])));
GO
