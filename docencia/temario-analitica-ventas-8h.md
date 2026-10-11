# Sesión de 8 horas: Analítica de Ventas aplicada al caso FraSoHome

## Enfoque general

Esta sesión se plantea como una continuación aplicada de la sesión de Inteligencia de Clientes que el alumnado ya ha visto. Por tanto, no conviene dedicar demasiado tiempo a definir qué es customer intelligence, qué es una regresión, qué es un árbol o qué significa AUC. El foco debe estar en algo que suelen conocer peor: cómo se convierte una necesidad comercial real en un proyecto analítico completo, desde la pregunta de negocio hasta una decisión medible.

El caso FraSoHome permite hacerlo muy bien porque combina ventas retail, ecommerce, CRM, campañas, stock, devoluciones, costes, feedback y señales digitales. La narrativa recomendada para la sesión es:

> FraSoHome no necesita "hacer un modelo". Necesita vender mejor, retener mejor, promocionar con más margen, reducir devoluciones y decidir con datos fiables en un entorno omnicanal.

La sesión debe alternar teoría breve, lectura crítica del caso, revisión de datos reales del repositorio y ejercicios de diseño analítico. La parte de modelización debe ser suficientemente concreta para que el alumnado entienda el pipeline completo, pero sin invadir la sesión posterior de interpretabilidad de modelos ML.

## Punto de partida del alumnado

Se asume que el alumnado ya ha trabajado o escuchado contenidos sobre:

- Inteligencia de clientes y analítica avanzada.
- Fuentes de datos internas y externas.
- Sistemas transaccionales, data warehouse y datamarts.
- Acceso a datos con SQL, Python/R, APIs y ficheros.
- Preparación básica de datos para modelización.
- Modelos supervisados y no supervisados: regresión, clasificación, clustering, redes neuronales, árboles, etc.
- Métricas como AUC, precisión, recall o errores de regresión.
- Explotación de resultados mediante reporting, dashboards o aplicaciones.
- Conceptos introductorios de explicabilidad como importancia de variables, SHAP y LIME.

Por eso, la sesión debe evitar repetir teoría general y debe insistir en:

- Definir bien el problema comercial.
- Elegir la granularidad correcta: cliente, pedido, línea, SKU, tienda, campaña, contacto.
- Diseñar targets observables y evitar leakage.
- Conectar ventas, marketing, margen, stock y experiencia de cliente.
- Traducir scores en acciones.
- Medir impacto incremental, no solo precisión del modelo.
- Preparar la transición hacia interpretabilidad: qué explicaciones necesitará negocio y qué dejaremos para la siguiente sesión.

## Materiales FraSoHome que se reutilizan

### Caso y narrativa

- `historia/caso-preparacion-datos.md`
- `historia/README.md`
- `escenarios/02-fabric-preparacion-datos/perfil-datos.md`
- `escenarios/05-marketing-precision/caso.md`

### Datos retail omnicanal

- `datos/retail_omnicanal/raw_csv/crm.csv`: clientes, fidelización, consentimiento y datos de contacto.
- `datos/retail_omnicanal/raw_csv/pedidos.csv`: cabecera de pedidos online.
- `datos/retail_omnicanal/raw_csv/lineas_pedido.csv`: líneas de venta online.
- `datos/retail_omnicanal/raw_csv/ventas_pos.csv`: ventas en tienda física.
- `datos/retail_omnicanal/raw_csv/devoluciones_online.csv`: devoluciones online.
- `datos/retail_omnicanal/raw_csv/devoluciones_tienda.csv`: devoluciones en tienda.
- `datos/retail_omnicanal/raw_csv/productos.csv`: maestro de producto, categoría, precio y coste.
- `datos/retail_omnicanal/raw_csv/stock_diario.csv`: stock por tienda/producto/fecha.
- `datos/retail_omnicanal/raw_csv/fact_transacciones.csv`: fact table integrada para demos.

### Datos de marketing precision

- `datos/marketing_precision/raw_csv/campanas_marketing.csv`
- `datos/marketing_precision/raw_csv/contactos_campana.csv`
- `datos/marketing_precision/raw_csv/eventos_campana.csv`
- `datos/marketing_precision/raw_csv/eventos_web_app.csv`
- `datos/marketing_precision/raw_csv/cupones_clientes.csv`
- `datos/marketing_precision/raw_csv/costes_operativos_transaccion.csv`
- `datos/marketing_precision/raw_csv/feedback_clientes.csv`
- `datos/marketing_precision/raw_csv/tickets_atencion_cliente.csv`
- `datos/marketing_precision/raw_csv/identidades_cliente.csv`
- `datos/marketing_precision/raw_csv/guardrails_marca_genai.csv`

### Notebooks reutilizables

- Notebook 1: ingesta y tipado.
- Notebook 2: perfilado y reporte de calidad.
- Notebook 3: limpieza y estandarización.
- Notebook 4: integración y fact table.
- Notebook 5: features RFM, churn, basket y propensión.
- Notebook 6: preprocesamiento final ML/BI.
- Notebook 7: baseline modeling.
- Notebook 8: scoring y exportación a BI.

La sesión no tiene que ejecutar todos los notebooks de punta a punta. Es preferible usarlos como hilo conductor y profundizar en dos o tres decisiones críticas.

## Diagnóstico rápido del caso

Datos observados en el repositorio:

- CRM: 103 filas y 101 clientes distintos; hay duplicados y consentimientos heterogéneos.
- Pedidos online: 656 cabeceras, con clientes ausentes en una parte relevante de registros.
- Líneas online: 1.949 líneas, con duplicados y descuentos parcialmente nulos.
- Ventas POS: 2.521 líneas, con muchos clientes no identificados.
- Fact table integrada: 4.973 movimientos comerciales, con ventas y devoluciones.
- Eventos web/app: 9.030 eventos digitales.
- Contactos de campaña: 480 impactos con grupo experimental/control.
- Eventos de campaña: 935 eventos.
- Feedback de clientes: 850 registros.
- Tickets de atención: 560 casos.
- Costes operativos: 1.829 registros para aproximar margen neto.

Lectura docente: FraSoHome ya tiene materia prima suficiente para explicar analítica de ventas avanzada, pero también tiene los problemas reales que hacen que un proyecto de ML falle si se empieza por el algoritmo: identidad incompleta, granularidades mezcladas, datos anónimos, duplicados, claves inconsistentes, fechas e importes heterogéneos, devoluciones y costes que cambian la lectura de "ventas".

## Objetivos de aprendizaje

Al final de la sesión, el alumnado debería ser capaz de:

1. Formular problemas de analítica de ventas como decisiones de negocio, no como modelos aislados.
2. Identificar qué fuentes de FraSoHome alimentan cada caso de uso: reporting, segmentación, churn, propensión, cross-sell, promociones, devoluciones y stock.
3. Diseñar una fact table comercial con la granularidad adecuada.
4. Construir mentalmente un Customer 360 accionable: valor, recencia, frecuencia, canal, margen, devoluciones, contactabilidad y respuesta a campañas.
5. Diferenciar KPIs descriptivos, modelos predictivos y métricas de impacto comercial.
6. Diseñar targets y ventanas temporales evitando fugas de información.
7. Elegir métricas de evaluación conectadas con negocio: lift, top decile, margen incremental, ROI, tasa de conversión, retención y reducción de devolución.
8. Traducir un score en una acción: audiencia, canal, oferta, prioridad y mensaje.
9. Diseñar una medición con holdout/control para saber si la acción funciona.
10. Entender qué preguntas de interpretabilidad quedan abiertas para la sesión posterior.

## Estructura recomendada de 8 horas

### Hora 1. Del análisis de ventas al sistema de decisión comercial

**Objetivo:** cambiar el marco mental de "analizar ventas" a "tomar mejores decisiones comerciales con datos".

**Contenidos:**

- Qué significa analítica de ventas en un retailer omnicanal.
- Diferencia entre reporting de ventas, diagnóstico, predicción, recomendación y optimización.
- FraSoHome como empresa con silos: POS, ecommerce, CRM, stock, devoluciones, campañas y atención al cliente.
- Decisiones típicas:
  - Qué categorías crecen o caen.
  - Qué clientes valen más.
  - Qué clientes están en riesgo.
  - Qué producto recomendar.
  - Qué promoción lanzar.
  - Qué devoluciones prevenir.
  - Qué tiendas necesitan acción local.
- Cadena de valor: dato -> insight -> score -> acción -> medición -> aprendizaje.

**Actividad:**

Dividir la clase en grupos y pedirles que formulen tres preguntas de negocio para FraSoHome. Después, convertir cada pregunta en:

- Unidad de decisión.
- Métrica objetivo.
- Datos necesarios.
- Acción posible.

**Ejemplo guía:**

"¿A qué clientes debemos enviar una promoción de decoración textil esta semana?" no es una pregunta de modelo; implica propensión, stock, margen, consentimiento, presión comercial, canal y medición.

### Hora 2. Mapa de datos FraSoHome y diseño de la fact table comercial

**Objetivo:** entender por qué la granularidad y la integración condicionan todo el proyecto analítico.

**Contenidos:**

- Sistemas transaccionales vs capa analítica, retomando lo visto en inteligencia de clientes.
- Granos disponibles:
  - Cliente.
  - Pedido.
  - Línea de pedido.
  - Ticket POS.
  - Línea de ticket.
  - Movimiento de devolución.
  - Contacto de campaña.
  - Evento digital.
  - SKU-tienda-día en stock.
- Diseño de una fact table de ventas:
  - Ventas brutas.
  - Descuentos.
  - Devoluciones.
  - Ventas netas.
  - Coste de producto.
  - Costes operativos.
  - Margen bruto y margen neto aproximado.
- Problemas reales detectados:
  - Clientes duplicados.
  - Clientes anónimos.
  - IDs con formatos distintos.
  - Fechas e importes heterogéneos.
  - Productos sin correspondencia completa.
  - Pagos y ventas no siempre conciliables.

**Demo sugerida:**

Abrir `perfil_datos_retail_omnicanal.md` y el Notebook 2 para enseñar nulos, duplicados, claves huérfanas y parseo de fechas/importes.

**Actividad:**

Pedir a cada grupo que diseñe una fact table mínima para responder:

"¿Cuál es la rentabilidad real por categoría y canal cuando tenemos en cuenta devoluciones y descuentos?"

**Cierre conceptual:**

Una venta no siempre es una venta buena: una categoría con mucho revenue puede destruir margen si necesita descuentos altos, genera devoluciones o consume stock crítico.

### Hora 3. KPIs de ventas, margen y cliente: de dashboard a diagnóstico

**Objetivo:** construir el cuadro mental de indicadores antes de pasar a ML.

**Contenidos:**

- KPIs comerciales:
  - Ventas brutas.
  - Ventas netas.
  - Unidades.
  - Ticket medio.
  - AOV online.
  - Frecuencia de compra.
  - Conversión de campaña.
  - Tasa de devolución.
  - Margen bruto/neto.
  - Sell-through y días sin stock.
- KPIs de cliente:
  - Clientes identificados vs anónimos.
  - Clientes activos.
  - Recompra.
  - Recencia.
  - Frecuencia.
  - Valor monetario.
  - Canal preferido.
  - Sensibilidad al descuento.
  - Contactabilidad y consentimiento.
- KPIs de marketing:
  - Entregas, aperturas, clicks, conversiones.
  - Revenue per send.
  - Coste por contacto.
  - Margen atribuido.
  - Presión comercial.
  - Grupo control y grupo expuesto.

**Teoría aplicada:**

- Qué es un buen KPI: accionable, comparable, gobernado y conectado con una decisión.
- Por qué revenue, conversión y AUC pueden empujar decisiones malas si se ignoran margen, stock y devoluciones.
- Diferencia entre atribución descriptiva e incrementalidad.

**Actividad:**

Construir una matriz KPI -> decisión -> fuente:

- "Reducir devoluciones" -> tasa de devolución, motivo, categoría, canal -> devoluciones + producto + fact.
- "Subir margen" -> margen post-descuento, coste operativo, elasticidad -> fact + costes + promociones.
- "Reactivar clientes" -> recencia, propensión, margen esperado -> CRM + fact + campañas.

### Hora 4. Customer 360, RFM extendido y segmentación de valor

**Objetivo:** reutilizar RFM del material anterior, pero elevarlo a segmentación comercial accionable.

**Contenidos:**

- RFM clásico:
  - Recency.
  - Frequency.
  - Monetary.
  - Quintiles y scoring.
- Limitaciones del RFM en FraSoHome:
  - No considera margen.
  - No considera devoluciones.
  - No considera canal.
  - No considera stock ni categoría.
  - No considera respuesta a campañas.
  - No distingue clientes identificados de anónimos.
- RFM extendido:
  - Valor neto post-devolución.
  - Margen neto estimado.
  - Preferencia de canal.
  - Tasa de devolución.
  - Sensibilidad al descuento.
  - Engagement digital.
  - Contactabilidad.
  - Afinidad a tienda local.
- Segmentación:
  - Segmentos por valor actual.
  - Segmentos por valor futuro.
  - Segmentos por comportamiento omnicanal.
  - Segmentos por elasticidad promocional.
  - Segmentos por riesgo de devolución.

**Demo sugerida:**

Usar Notebook 5 para enseñar cómo se calculan features de cliente, churn, basket y propensión.

**Actividad:**

Diseñar cuatro segmentos accionables de FraSoHome. Para cada segmento:

- Definición con variables.
- Hipótesis de negocio.
- Acción comercial.
- Métrica de éxito.

**Ejemplos:**

- "VIP con margen alto y bajo descuento": proteger experiencia, no sobrepromocionar.
- "Comprador reciente con alta afinidad textil": campaña de cross-sell sin descuento agresivo.
- "Alto gasto pero alta devolución": revisar promesa de producto, tallas/medidas, contenido y logística.
- "Dormido de alto valor": reactivación con categoría favorita y control de incentivo.

### Hora 5. Del caso de uso al dataset de entrenamiento

**Objetivo:** cubrir la parte más débil habitual: cómo se define el dataset de ML antes de entrenar nada.

**Contenidos:**

- Cómo formular un caso de ML comercial:
  - Churn/reactivación.
  - Propensión de compra por categoría.
  - Riesgo de devolución.
  - Recomendación/cross-sell.
  - Predicción de demanda/stock.
  - Optimización promocional.
- Para cada caso:
  - Unidad de predicción.
  - Momento de scoring.
  - Ventana de observación.
  - Ventana de predicción.
  - Target.
  - Features disponibles antes de la decisión.
  - Acción derivada.
  - Métrica de negocio.
- Riesgos:
  - Leakage temporal.
  - Targets mal definidos.
  - Mezclar clientes anónimos e identificados sin criterio.
  - Entrenar con ventas brutas y decidir con margen neto.
  - Evaluar conversión sin grupo control.
  - Optimizar para el cliente más fácil, no para el más rentable.

**Ejemplo principal: churn/reactivación FraSoHome**

- Unidad: cliente identificado y contactable.
- Observación: comportamiento hasta una fecha de corte.
- Target: no compra en los próximos N días o caída de actividad frente a patrón histórico.
- Features: RFM, canal preferido, categorías compradas, devoluciones, descuentos, engagement web/app, respuesta a campañas.
- Exclusiones: clientes sin consentimiento si la acción será CRM.
- Métrica ML: AUC, lift top decile, recall en top K.
- Métrica negocio: margen incremental de reactivación frente a holdout.

**Actividad:**

Cada grupo elige un caso de uso y completa una ficha:

- Pregunta de negocio.
- Dataset.
- Target.
- Features.
- Posibles fugas.
- Modelo baseline.
- Acción.
- KPI de impacto.

### Hora 6. Modelos baseline y evaluación orientada a ventas

**Objetivo:** repasar ML solo en lo necesario para conectar modelos con decisiones comerciales.

**Contenidos:**

- Por qué empezar con baseline:
  - Reglas RFM.
  - Regresión logística.
  - Árbol sencillo.
  - Random forest/gradient boosting como segunda iteración.
  - Reglas de asociación para cesta.
- Evaluación según caso:
  - Clasificación: AUC, precision/recall, lift, top decile, matriz de confusión a umbral de campaña.
  - Regresión: MAE/RMSE, error por segmento, sesgo en productos de alto valor.
  - Recomendación: precision@K, coverage, diversidad, disponibilidad de stock.
  - Campañas: conversión, uplift, margen incremental, ROI.
  - Stock/demanda: error ponderado por coste de stockout/sobrestock.
- Selección de umbral:
  - No elegir umbral por métrica técnica solamente.
  - Elegir por capacidad de contacto, coste, margen esperado y saturación comercial.
- Priorización:
  - Score de propensión.
  - Valor esperado.
  - Coste de incentivo.
  - Riesgo de devolución.
  - Stock disponible.

**Demo sugerida:**

Usar Notebook 7 y Notebook 8 para enseñar la lógica de baseline modeling, scoring y exportación a BI. No hace falta entrar en todos los hiperparámetros.

**Actividad:**

Dar un ranking hipotético de clientes con score de churn, margen esperado y coste de contacto. Pedir que seleccionen a quién impactarían si solo pueden contactar con el 20% de la base. Comparar una selección por score puro frente a una selección por valor esperado.

### Hora 7. Activación comercial: campañas, promociones, cross-sell y medición

**Objetivo:** cerrar el hueco entre "tengo un score" y "he mejorado ventas".

**Contenidos:**

- Cómo se activa un modelo en ventas/marketing:
  - Audiencias CRM.
  - Campañas email/SMS/push.
  - Personalización web/app.
  - Recomendaciones en checkout.
  - Argumentarios para tienda.
  - Acciones locales por tienda.
- FraSoHome marketing precision:
  - Campañas.
  - Contactos.
  - Cupones.
  - Eventos.
  - Creatividades.
  - Costes.
  - Feedback.
  - Guardrails de marca.
- Matriz score -> acción:
  - Churn alto + margen alto -> reactivación prioritaria.
  - Propensión textil + stock alto -> recomendación de categoría.
  - Alto riesgo de devolución -> contenido preventivo, no necesariamente descuento.
  - Alta sensibilidad a descuento + bajo margen -> limitar incentivo.
  - Alta afinidad local -> campaña de tienda con stock disponible.
- Diseño experimental:
  - Grupo tratamiento.
  - Grupo control/holdout.
  - Aleatorización.
  - Métricas primarias y secundarias.
  - Duración de la medición.
  - Incrementalidad frente a atribución.

**Actividad:**

Diseñar una campaña FraSoHome:

- Objetivo: reactivar clientes dormidos con afinidad a decoración.
- Audiencia.
- Exclusiones.
- Oferta.
- Canal.
- Mensaje.
- Grupo control.
- KPI principal.
- Criterio de éxito.
- Riesgo operativo.

**Cierre conceptual:**

Un modelo que mejora AUC pero no cambia la decisión o no se mide con control no ha demostrado valor comercial.

### Hora 8. Roadmap de proyecto ML completo y puente hacia interpretabilidad

**Objetivo:** consolidar el proceso completo y preparar la sesión posterior de interpretabilidad.

**Contenidos:**

- Blueprint de proyecto ML en FraSoHome:
  1. Problema de negocio.
  2. Decisión a mejorar.
  3. Unidad de decisión.
  4. Datos disponibles.
  5. Calidad y gobierno.
  6. Fact table / Customer 360.
  7. Target y ventanas temporales.
  8. Features.
  9. Baseline.
  10. Modelo candidato.
  11. Evaluación técnica.
  12. Evaluación económica.
  13. Activación.
  14. Experimento.
  15. Monitorización.
  16. Reentrenamiento.
- MLOps ligero para negocio:
  - Consistencia entrenamiento/scoring.
  - Versionado de features.
  - Drift de datos.
  - Seguimiento de performance.
  - Retraining.
  - Auditoría de decisiones.
- Qué NO cerrar en esta sesión porque se verá en interpretabilidad:
  - SHAP en profundidad.
  - LIME.
  - Partial dependence / ICE.
  - Explicaciones locales vs globales.
  - Fairness y sesgos más allá de la formulación inicial.
  - Cómo convertir explicabilidad en narrativa ejecutiva.

**Actividad final:**

Cada grupo presenta en 5 minutos su diseño de caso de uso FraSoHome:

- Decisión de negocio.
- Dataset y target.
- Features principales.
- Modelo baseline.
- Métrica técnica.
- Métrica económica.
- Acción.
- Medición.
- Qué explicación necesitaría el negocio.

**Cierre:**

Presentar la pregunta puente para la siguiente sesión:

> Si el modelo recomienda no incentivar a un cliente, subirle prioridad de retención o empujarle una categoría concreta, ¿cómo justificamos esa decisión ante marketing, dirección comercial y el propio cliente?

## Casos de uso recomendados para trabajar durante la sesión

### Caso A. Segmentación de valor omnicanal

**Pregunta:** ¿qué clientes generan más valor neto y cómo debemos tratarlos?

**Datos:** CRM, fact transacciones, devoluciones, costes, campañas.

**Técnicas:** RFM extendido, clustering, scoring de valor, reglas de negocio.

**Acción:** segmentos comerciales con política de contacto e incentivo.

**KPIs:** margen neto, recompra, tasa de devolución, respuesta a campañas.

### Caso B. Churn y reactivación

**Pregunta:** ¿qué clientes están en riesgo de no volver a comprar y cuáles merece la pena reactivar?

**Datos:** CRM, ventas, campañas, eventos web/app, devoluciones.

**Técnicas:** clasificación, ranking, reglas de next best action.

**Acción:** audiencia de reactivación por canal y categoría favorita.

**KPIs:** uplift de recompra, margen incremental, coste por cliente recuperado.

### Caso C. Propensión de compra por categoría

**Pregunta:** ¿qué categoría es más probable que compre cada cliente en el próximo periodo?

**Datos:** fact transacciones, productos, eventos web/app, campañas, stock.

**Técnicas:** clasificación multiclase, ranking, recomendador simple.

**Acción:** personalización de email, web/app o paid audiences.

**KPIs:** conversión, revenue per send, margen por contacto, stock sell-through.

### Caso D. Cross-sell con restricciones de stock y margen

**Pregunta:** ¿qué producto complementario conviene recomendar tras una compra?

**Datos:** líneas de pedido, tickets POS, productos, stock, margen.

**Técnicas:** reglas de asociación, recomendador item-based, ranking con reglas.

**Acción:** recomendación en checkout, post-compra o tienda.

**KPIs:** attach rate, AOV, margen incremental, rotación de stock.

### Caso E. Riesgo de devolución

**Pregunta:** ¿qué ventas tienen más probabilidad de acabar en devolución y qué podemos hacer antes?

**Datos:** ventas, devoluciones, producto, canal, cliente, feedback, tickets.

**Técnicas:** clasificación, análisis de motivos, segmentación de producto/cliente.

**Acción:** mejorar contenido de ficha, guía de medidas, mensajes preventivos, revisión de promociones.

**KPIs:** return rate, coste de devolución, margen neto, satisfacción.

### Caso F. Promociones y ROI

**Pregunta:** ¿qué promoción genera ventas incrementales sin destruir margen?

**Datos:** campañas, contactos, cupones, promociones, costes, fact transacciones.

**Técnicas:** análisis de campaña, holdout, uplift básico, elasticidad promocional.

**Acción:** calendario promocional y reglas de incentivo por segmento.

**KPIs:** conversión incremental, margen incremental, ROI, dependencia del descuento.

## Dinámicas docentes sugeridas

### Dinámica 1. "No me digas el modelo, dime la decisión"

Plantear varias frases y pedir que las reformulen:

- "Hacer un modelo de churn."
- "Hacer un recomendador."
- "Predecir ventas."
- "Segmentar clientes."

Reformulaciones esperadas:

- "Decidir qué clientes contactables de alto margen priorizamos para reactivación esta semana."
- "Elegir qué producto complementario mostrar en checkout sin recomendar productos sin stock."
- "Planificar stock y campañas por categoría/tienda minimizando roturas."
- "Definir tratamientos comerciales diferenciados por valor, canal y sensibilidad a descuento."

### Dinámica 2. "Caza de leakage"

Mostrar posibles variables y preguntar cuáles no deberían usarse si el scoring se hace antes de la campaña:

- Fecha de conversión de campaña.
- Revenue atribuido a campaña.
- Número de clicks antes del envío.
- Segmento CRM previo.
- Compras de los últimos 90 días antes de fecha de corte.
- Devolución posterior a la compra.
- Cupón redimido en los 30 días posteriores.

### Dinámica 3. "AUC no paga facturas"

Comparar dos modelos ficticios:

- Modelo A: AUC mayor, selecciona muchos clientes de bajo margen.
- Modelo B: AUC menor, mejor margen incremental en top 20%.

Preguntar cuál se desplegaría y qué evidencia falta.

### Dinámica 4. "Del score al playbook"

Dar cinco perfiles de cliente y pedir una acción:

- Alto churn, alto margen, contactable.
- Alto churn, bajo margen, alta sensibilidad a descuento.
- Alta propensión a textil, tienda cercana con stock alto.
- Alto valor, alta devolución.
- Cliente anónimo con señales web recurrentes.

## Entregables que deberían salir de la sesión

Aunque la sesión no tenga por qué ser evaluable, conviene terminar con artefactos claros:

- Mapa de fuentes FraSoHome para analítica de ventas.
- Matriz de casos de uso: pregunta, datos, target, features, acción y KPI.
- Diseño de fact table comercial.
- Propuesta de Customer 360.
- Ficha de un caso ML completo.
- Diseño de campaña o acción comercial con holdout.
- Lista de preguntas de interpretabilidad para la siguiente sesión.

## Propuesta de evaluación rápida

Si se quiere evaluar la sesión, propongo una entrega breve por grupos:

**Título:** Diseño de un caso de analítica de ventas FraSoHome.

**Extensión:** 2-3 páginas o 6-8 diapositivas.

**Contenido mínimo:**

1. Pregunta de negocio.
2. Decisión a mejorar.
3. Fuentes de datos.
4. Unidad de análisis.
5. Target y ventana temporal.
6. Features principales.
7. Modelo baseline.
8. Métricas técnicas.
9. Métricas de negocio.
10. Acción comercial.
11. Diseño de medición.
12. Riesgos y controles.
13. Preguntas de interpretabilidad.

**Criterios de corrección:**

- Claridad de la decisión de negocio: 20%.
- Calidad del diseño de datos y target: 25%.
- Coherencia entre modelo, acción y KPI: 25%.
- Medición de impacto y control: 20%.
- Identificación de riesgos e interpretabilidad: 10%.

## Relación con la sesión posterior de interpretabilidad

Esta sesión debe dejar preparadas las preguntas, no resolverlas todas.

Preguntas puente:

- ¿Por qué un cliente aparece en alto riesgo de churn?
- ¿Qué variables hacen que una recomendación sea adecuada?
- ¿El modelo está capturando valor real o solo comportamiento promocional?
- ¿Hay segmentos perjudicados por una regla de decisión?
- ¿Cómo explicamos a marketing que no todos los clientes de alto score deben recibir descuento?
- ¿Qué explicación necesita dirección: global, local, por segmento o por campaña?
- ¿Qué explicación necesita operaciones si el modelo recomienda reducir stock o empujar una categoría?

Recomendación: cerrar la sesión con un modelo o ranking ya diseñado conceptualmente y usarlo como punto de partida en interpretabilidad.

## Mensaje final para el alumnado

La analítica de ventas no consiste en aplicar modelos conocidos sobre una tabla cualquiera. Consiste en diseñar un sistema de decisión que conecte negocio, datos, modelos, activación y medición. En FraSoHome, el reto no es solo predecir quién compra: es decidir a quién impactar, con qué oferta, por qué canal, con qué coste, con qué margen esperado y cómo demostrar que la decisión ha generado valor incremental.
