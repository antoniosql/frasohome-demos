# FraSoHome_marketing_precision_analysis

# **Rediseño del caso FraSoHome**

### De preparación de datos a marketing de precisión

Análisis de los materiales adjuntos y propuesta de evolución hacia una formación centrada en analítica de clientes, toma de decisiones de marketing y casos de IA/IA generativa.

|Qué he encontrado en el material<br>• Una base muy sólida de retail omnicanal: CRM, pedidos online, líneas de pedido, devoluciones online y tienda, pagos POS, stock diario, maestro de producto, maestro de tiendas y fact table integrada.<br>• Una secuencia didáctica clara de notebooks: ingesta, calidad, limpieza, integración, features, preprocesamiento, baseline modeling, scoring y app en Streamlit.<br>• Un enfoque actual predominantemente técnico y de data preparation; todavía no está reencuadrado del todo hacia decisión, activación y ROI de marketing.|
|---|

Documento de trabajo para rediseñar la formación con foco en customer analytics y marketing de precisión.

## 1. Resumen ejecutivo

El caso actual funciona muy bien como laboratorio de integración y calidad de datos, pero necesita un cambio de narrativa para que la sesión gire en torno a una pregunta distinta: cómo usar esos datos para decidir mejor a quién impactar, con qué mensaje, en qué canal, con qué oferta y con qué criterio de rentabilidad.

|Lo que conviene mantener<br>• El contexto omnicanal retail hogar y decoración: es realista y muy útil para explicar customer analytics.<br>• Los notebooks 1-4 como base de preparación de datos.<br>• La fact table integrada y el maestro de cliente/producto/tienda.<br>• Los casos ya insinuados de RFM, churn, propensión y basket.|Lo que hay que cambiar<br>• Pasar de un objetivo pedagógico de 'limpieza y modelado baseline' a uno de 'decisión de marketing de precisión'.<br>• Añadir datasets de activación: campañas, contactos, aperturas/clicks, navegación web/app, cupones, promociones y service/VOC.<br>• Cerrar el ciclo score -> acción -> test -> KPI -> ROI.<br>• Añadir casos de IA generativa conectados a voz del cliente y personalización de contenido.|
|---|---|

|Indicadores que justifican el rediseño<br>• El CRM contiene 103 filas para 100 customer_id únicos: hay duplicados y necesidad de identidad/depuración.<br>• La fact table tiene 4.973 transacciones y un 41,3% no enlaza con CRM; eso limita cualquier activación basada en cliente identificado.<br>• En 2025, aproximadamente el 40,9% de las líneas de venta y el 41,3% del importe aparecen como anónimos/guest; capturar identidad y consentimiento pasa a ser un caso de negocio, no solo técnico.<br>• También se observan inconsistencias de consentimientos, tiers de fidelización, regiones y fechas fuera de rango, lo que abre la puerta a un bloque específico de contactabilidad y confianza del dato.|
|---|

Conclusión: el material no debe eliminarse; debe reencuadrarse. FraSoHome ya tiene la base transaccional adecuada. Lo que falta es la capa de marketing: señales de contacto, comportamiento, activación, atribución, medición y personalización.

## 2. Diagnóstico de los materiales actuales

### Vista por componente

**Narrativa del caso: **muy buena para explicar fragmentación de sistemas y problemas de calidad, pero todavía formula el reto en términos de integración de datos más que en términos de decisión comercial o de marketing.

**Datos disponibles: **correctos para omnicanal retail: cliente, compra, devolución, producto, tienda, pago y stock. Esto permite construir customer 360 transaccional, KPIs de valor, retorno, margen y comportamiento.

**Notebooks: **bien secuenciados y reutilizables. La lógica actual lleva al alumno desde el dato crudo hasta el score, pero el 'para qué' del score aún aparece poco conectado con acciones de negocio concretas.

**App Streamlit: **muy útil como capa de exploración. Hoy muestra overview, calidad, clientes RFM/churn, productos/stock y cesta; convendría evolucionarla hacia audiencias, journeys, next best action, riesgo de devolución y campañas activables.

### Principales huecos para marketing de precisión

**• **No hay historial de campañas o contactos (email, SMS, push, paid audiences), por lo que no puede enseñarse bien la orquestación de impactos ni la presión comercial.

**• **No hay comportamiento digital previo a la compra (visitas, búsquedas, fichas de producto, carrito, wishlist, abandono de checkout), de modo que la propensión se apoya casi solo en histórico transaccional.

**• **No hay voz del cliente suficiente para IA generativa: faltan reviews, tickets, chat, NPS o encuestas. Los motivos de devolución sirven como semilla, pero no bastan para una capa rica de customer insight.

**• **No hay calendario promocional ni variable clara de precio de lista vs. precio final, lo que dificulta enseñar elasticidad, dependencia del descuento y optimización promocional.

**• **No se ve todavía un marco de medición causal: uplift, holdouts, tests, incrementalidad y ROI de la activación.

## 3. Cambios necesarios para reconvertir el caso

**Reescribir la pregunta docente: **Cambiar 'preparar datos para ML/BI' por 'usar datos e IA para decidir mejor a quién, cuándo, cómo y con qué ofrecer'. Cada notebook y cada dashboard debe empezar con una decisión de negocio.

**Crear un Customer 360 activable: **Añadir una tabla maestra de cliente con identidad consolidada, consentimiento normalizado, contactabilidad, afinidad de canal, valor esperado, riesgo de churn y sensibilidad a descuento.

**Añadir nuevas fuentes de marketing: **Incorporar tablas nuevas: historial de campañas/contactos, eventos web/app, cupones/promociones, tickets de atención/reviews y una tabla de costes de activación/logística.

**Cerrar el circuito de decisión: **Cada caso debe terminar en una acción concreta: exportar una audiencia, recomendar una oferta, disparar una secuencia o redefinir una política comercial.

**Introducir medición y test: **Añadir al menos un notebook o bloque de trabajo para definir grupos control, uplift, costes, margen incremental y criterios de éxito.

**Incluir IA generativa con guardrails: **Usar GenAI para sintetizar voz del cliente, generar hipótesis de copy por microsegmento y apoyar priorización creativa, nunca como sustituto de la medición.

|Nuevos datasets mínimos recomendados<br>• campanas_contactos.csv - customer_id, campaign_id, canal, fecha_envio, apertura, click, conversion, coste<br>• eventos_web_app.csv - customer_id / usuario_online_id, session_id, page_type, categoria, product_id, add_to_cart, checkout_start, timestamp<br>• promociones_cupones.csv - coupon_id, tipo_descuento, valor, campaña, categoría, fecha_inicio, fecha_fin, redimido<br>• service_voc.csv - customer_id, fecha, canal, tema, sentimiento, texto_ticket/review, resolución<br>• costes_operativos.csv - coste_envío, coste_devolución, coste_contacto, margen neto por línea o pedido|
|---|

## 4. Diez casos recomendados para la formación

La propuesta combina analítica avanzada, modelos predictivos y casos de IA generativa. Los he formulado para FraSoHome y para un enfoque de marketing de precisión: segmentar mejor, activar mejor y medir mejor.

### Caso 1. Resolución de identidad y customer 360 accionable

**Tipo: **Analítica avanzada + reglas/ML

**Aprovechamiento del material actual: **Alta reutilización del material actual

**Objetivo de negocio: **Unificar cliente online, tienda y fidelización para aumentar la base activable y reducir ventas anónimas.

**Datos y cambios necesarios: **CRM, pedidos, POS, devoluciones, pagos, usuario_online_id, emails/teléfonos; conviene añadir hashed email, tarjeta fidelización y reglas de matching.

**Enfoque analítico/IA: **Entity resolution, deduplicación probabilística, normalización de consentimiento y scoring de confianza del match.

**Decisión de marketing: **Qué clientes pasan a la base activable, qué ventas pueden atribuirse a cliente identificado y dónde conviene forzar captura de identidad en tienda.

**KPIs sugeridos: **% ventas identificadas, % base contactable, incremento de customer match rate, reducción de duplicados.

### Caso 2. Segmentación de valor omnicanal y CLV

**Tipo: **Analítica avanzada + ML predictivo

**Aprovechamiento del material actual: **Muy alta reutilización del material actual

**Objetivo de negocio: **Sustituir el RFM didáctico por una segmentación orientada a valor futuro y rentabilidad real.

**Datos y cambios necesarios: **Fact transaccional, devoluciones, costes de producto, descuentos, stock; idealmente añadir coste logístico y coste de activación.

**Enfoque analítico/IA: **RFM extendido, clustering, CLV esperado, share of channel, retorno neto post-devolución, sensibilidad a descuento.

**Decisión de marketing: **Qué segmentos merecen inversión, cuáles requieren protección de margen y cuáles deben activarse con menos presión promocional.

**KPIs sugeridos: **LTV/CAC, margen neto esperado, tasa de repetición, penetración de segmento en ventas.

### Caso 3. Churn y reactivación con next best action

**Tipo: **IA predictiva

**Aprovechamiento del material actual: **Evolución directa de notebook churn existente

**Objetivo de negocio: **Pasar del score de abandono a una recomendación de acción por cliente.

**Datos y cambios necesarios: **Histórico de compra, recencia, devoluciones, descuentos, canal; conviene añadir histórico de contactos y respuesta a campañas.

**Enfoque analítico/IA: **Modelo churn temporal, árboles o gradient boosting, segmentación por causa probable de abandono y motor de reglas para next best action.

**Decisión de marketing: **A quién reactivar, con qué incentivo, por qué canal y con qué prioridad económica.

**KPIs sugeridos: **Uplift de reactivación, margen incremental, coste por cliente recuperado, reducción de churn.

### Caso 4. Propensión de compra por categoría o colección

**Tipo: **IA predictiva

**Aprovechamiento del material actual: **Evolución del dataset de propensión ya previsto

**Objetivo de negocio: **Predecir qué familia de producto tiene más probabilidad de compra para cada cliente en el próximo periodo.

**Datos y cambios necesarios: **Compra histórica por categoría, ticket medio, afinidad de canal, estacionalidad; conviene añadir navegación, búsqueda y wishlist.

**Enfoque analítico/IA: **Clasificación multiclase o ranking por categoría, embeddings de afinidad producto-cliente y features temporales.

**Decisión de marketing: **Qué categoría mostrar primero en email, onsite o paid audiences; qué clientes deben entrar en campaña de colección concreta.

**KPIs sugeridos: **CTR por categoría recomendada, conversión, revenue per send, uplift frente a segmentación genérica.

### Caso 5. Cross-sell y recomendación basket-aware con stock

**Tipo: **Analítica avanzada + recomendador

**Aprovechamiento del material actual: **Alta, a partir del caso basket actual

**Objetivo de negocio: **Usar afinidades de cesta para recomendar productos complementarios sin empujar artículos con poco stock o mala rentabilidad.

**Datos y cambios necesarios: **Basket/lineas de pedido, fact table, producto, stock diario, margen; opcionalmente navegación de fichas y add-to-cart.

**Enfoque analítico/IA: **Reglas de asociación, item-based recommendation o ranking con restricción de stock y margen.

**Decisión de marketing: **Qué producto sugerir en checkout, post-compra o CRM; qué combinaciones merecen packs o bundles.

**KPIs sugeridos: **Attach rate, AOV, margen incremental, rotación de stock.

### Caso 6. Elasticidad promocional y dependencia del descuento

**Tipo: **Analítica avanzada / causal

**Aprovechamiento del material actual: **Media; requiere ampliar datos

**Objetivo de negocio: **Identificar qué clientes y categorías responden al descuento y dónde el descuento destruye valor.

**Datos y cambios necesarios: **Precio, descuento, importe, categoría, cliente, canal; conviene añadir calendario promocional, cupón, precio de lista, estacionalidad y campañas.

**Enfoque analítico/IA: **Modelos de elasticidad, árboles causal/heterogeneous treatment effects o experimentación por segmentos.

**Decisión de marketing: **Cuándo promocionar, a quién, con qué profundidad de descuento y en qué categorías no conviene rebajar.

**KPIs sugeridos: **Margen incremental, ratio promoción-venta, dependencia del descuento, elasticidad por segmento.

### Caso 7. Predicción de devolución y margen neto post-devolución

**Tipo: **IA predictiva

**Aprovechamiento del material actual: **Alta reutilización con devoluciones actuales

**Objetivo de negocio: **Predecir riesgo de devolución para reducir coste y mejorar experiencia sin frenar ventas de alto valor.

**Datos y cambios necesarios: **Devoluciones online/tienda, motivos, producto, canal, cliente, descuento; idealmente añadir logística, tiempos de entrega y estado del envío.

**Enfoque analítico/IA: **Modelo de riesgo de devolución a nivel pedido/línea, más segmentación por motivo probable.

**Decisión de marketing: **A qué pedidos aplicar mensajes preventivos, qué productos requieren mejor contenido/medidas y dónde conviene ajustar política de incentivo.

**KPIs sugeridos: **Return rate, coste de devolución, margen neto, reducción de incidencias por motivo.

### Caso 8. Activación local y store marketing con stock disponible

**Tipo: **Analítica avanzada geoespacial

**Aprovechamiento del material actual: **Media-alta gracias a tiendas y stock

**Objetivo de negocio: **Hacer marketing hiperlocal por tienda y no solo por canal general.

**Datos y cambios necesarios: **Tiendas con lat/lon, CRM por ciudad/código postal, stock diario por tienda, histórico de compra; conviene añadir drive time, tráfico tienda y radio de influencia.

**Enfoque analítico/IA: **Geosegmentación, propensión por proximidad, cluster de catchment y reglas de campaña local stock-aware.

**Decisión de marketing: **Qué tienda empuja qué categoría, qué clientes reciben campañas de tienda cercana y qué aperturas o eventos locales merecen apoyo.

**KPIs sugeridos: **Store visits, ventas locales, sell-through por tienda, reducción de stock inmovilizado.

### Caso 9. GenAI para voz del cliente: devoluciones, tickets y reviews

**Tipo: **IA generativa + NLP

**Aprovechamiento del material actual: **Media; hoy existe una semilla con motivos/comentarios de devolución

**Objetivo de negocio: **Convertir texto disperso en insight accionable para marketing, CRO y producto.

**Datos y cambios necesarios: **Motivos y comentarios de devolución; conviene añadir reviews, tickets de soporte, chat, encuestas/NPS y reseñas de producto.

**Enfoque analítico/IA: **Clasificación temática, clustering semántico, resumen con LLM, extracción de objeciones, drivers de compra y propuestas de mejora.

**Decisión de marketing: **Qué objeciones resolver en la ficha, qué mensajes revisar, qué productos necesitan mejor contenido o promesa comercial distinta.

**KPIs sugeridos: **Mejora de CVR, reducción de devoluciones por motivo, share de objeciones resueltas, satisfacción.

### Caso 10. GenAI para personalización de copy y creatividad por microsegmento

**Tipo: **IA generativa aplicada a activación

**Aprovechamiento del material actual: **Media-baja; requiere capa de campañas y brand rules

**Objetivo de negocio: **Generar variantes de mensajes, asuntos, landings o fichas de producto alineadas con segmento, categoría e intención.

**Datos y cambios necesarios: **Segmentos, propensión, afinidades de categoría, brand guidelines, catálogo, históricos de campañas y performance creativa.

**Enfoque analítico/IA: **LLM con plantillas y guardrails, generación de hipótesis creativas, scoring humano/automático y experimentación A/B.

**Decisión de marketing: **Qué mensaje usar por microsegmento, en qué tono, con qué prueba social, beneficio y CTA.

**KPIs sugeridos: **Open rate, CTR, CVR, revenue per send, mejora frente a control creativo.

## 5. Cómo lo llevaría a la formación

Para una formación de marketing de precisión, no conviene dedicar el mismo tiempo a todos los materiales. Mi recomendación sería reorganizar el caso en tres capas:

**• **Capa 1 - Fundamentos de dato: resumir notebooks 1-4 y dejar parte del trabajo de limpieza prehecho para no gastar demasiada sesión en plumbing técnico.

**• **Capa 2 - Customer analytics: centrar el núcleo de la sesión en customer 360, segmentación de valor, churn/reactivación, propensión, retorno y recomendación.

**• **Capa 3 - Activación y medición: terminar siempre en una audiencia, una regla de negocio, una acción de CRM/media y un diseño de test.

|Entregables docentes recomendados<br>• Dashboard de customer 360 y marketing performance, no solo dashboard de calidad de datos.<br>• Ficheros de audiencias: high value, churn risk, category propensity, return risk, local store audience.<br>• Matriz score -> acción -> canal -> KPI.<br>• Mini playbook de IA generativa con prompts, guardrails y evaluación humana.<br>• Plantilla de experimento con grupo control, hipótesis y medida de incrementalidad.|
|---|

En una frase: FraSoHome ya es un muy buen caso de datos. Para convertirlo en un excelente caso de marketing de precisión hay que añadir la capa que va del insight a la activación y de la activación al impacto medible.
