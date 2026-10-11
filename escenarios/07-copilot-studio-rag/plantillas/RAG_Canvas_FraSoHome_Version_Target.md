# RAG_Canvas_FraSoHome_Version_Target

**RAG Canvas - FraSoHome**

*Versión target (definición ejecutiva / estratégica)*

**Objetivo: **Definir qué asistente RAG/híbrido se construye, para quién, con qué fuentes y bajo qué controles.

**Flujo conceptual: **Pregunta -> Clasificación -> RAG (recupera-genera-cita) y/o Tool (consulta a datos) -> Respuesta con evidencia.

|1) Resultados de negocio<br>• Definiciones unificadas (KPI/políticas)<br>• Decisiones más rápidas (stock/campañas/devoluciones)<br>• Menos dependencia del equipo de datos<br>• Base para analítica/ML (demanda, fraude)|2) Usuarios y stakeholders<br>• Dirección: KPI y alertas<br>• Marketing: segmentación y campañas<br>• Operaciones: stock, rotación, incidencias<br>• Tiendas/Atención: políticas y procedimientos|3) Casos de uso prioritarios<br>• Políticas: excepciones de devolución por canal<br>• KPI: ventas netas y tasa de devolución (definición)<br>• Métricas: ventas netas por canal/tienda/periodo<br>• Operación: top SKUs sin stock<br>• Riesgo: devoluciones anómalas (cliente/SKU)|
|---|---|---|
|4) Conocimiento documental (RAG)<br>• Política devoluciones (plazos, excepciones)<br>• Manual tienda (cierres, pagos, incidencias)<br>• Diccionario KPI y reglas de cálculo<br>• Taxonomía catálogo y descuentos<br>• Versionado + vigencia (owner)|5) Datos estructurados (Tools/Acciones)<br>• CRM: clientes, tier, puntos<br>• E-commerce: pedidos, líneas, devoluciones<br>• POS: tickets, devoluciones, pagos<br>• ERP: stock diario, costes, productos<br>• Vista consolidada para consulta|6) Alcance y guardarraíles<br>• Fuentes autorizadas + permisos por rol<br>• Preferir versiones vigentes<br>• Abstención si falta evidencia/datos<br>• No exponer PII innecesaria|
|7) Recuperación e indexación<br>• Chunking por secciones + solape<br>• Metadatos: área, canal, versión, sensibilidad<br>• Búsqueda híbrida para KPI/SKU/IDs<br>• Filtros por canal/área|8) Orquestación del asistente<br>• Enrutado: documental / métrica / mixta<br>• Documental: RAG con citaciones<br>• Métrica: Tool + supuestos explícitos<br>• Mixta: Tool + RAG -> respuesta integrada|9) Salida y experiencia<br>• 3 capas: resumen, detalle, fuentes<br>• Supuestos: periodo/canal/definición KPI<br>• Tablas top N y comparativas<br>• Sugerir próximos pasos (filtros/desglose)|
|10) Calidad y evaluación<br>• Test sets por área (preguntas reales)<br>• Métricas: precision/recall, groundedness<br>• Mejora iterativa (chunks, metadatos, prompts)|11) Seguridad y gobierno<br>• Acceso a orígenes por rol<br>• DLP + sensitivity labels + canales<br>• Logs y mitigación de prompt injection|12) Operación y roadmap<br>• MVP: Q&A + definiciones KPI + 2 consultas<br>• V1: híbrido completo + evaluación + monitorización<br>• V2: personalización por rol + insights/ML<br>• Owners: negocio + datos + IT|
