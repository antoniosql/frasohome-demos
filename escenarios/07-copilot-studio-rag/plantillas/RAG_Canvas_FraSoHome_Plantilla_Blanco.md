# RAG_Canvas_FraSoHome_Plantilla_Blanco

**RAG Canvas - FraSoHome**

*Plantilla en blanco (para completar en el taller)*

**Objetivo: **Definir qué asistente RAG/híbrido se construye, para quién, con qué fuentes y bajo qué controles.

**Flujo conceptual: **Pregunta -> Clasificación -> RAG (recupera-genera-cita) y/o Tool (consulta a datos) -> Respuesta con evidencia.

|1) Resultados de negocio<br>• KPI/impacto esperado (tiempo, coste, calidad)<br>• Decisiones a acelerar<br>• Dolor actual que se elimina<br>• Objetivos: ______________________________________|2) Usuarios y stakeholders<br>• Roles principales (dirección, marketing, tienda, datos...)<br>• Necesidades por rol<br>• Restricciones de acceso/permisos<br>• Notas: __________________________________________|3) Casos de uso prioritarios<br>• Top 5 preguntas (alto impacto)<br>• Qué es documental vs métrica vs mixto<br>• Frecuencia (alta/media/baja)<br>• Ejemplos: ________________________________________|
|---|---|---|
|4) Conocimiento documental (RAG)<br>• Fuentes: políticas, procedimientos, diccionario KPI<br>• Propietario y cadencia de actualización<br>• Versionado/vigencia<br>• Listado: _________________________________________|5) Datos estructurados (Tools/Acciones)<br>• Datasets: ventas, stock, devoluciones, CRM...<br>• Frecuencia de refresco<br>• Permisos por rol<br>• Listado: _________________________________________|6) Alcance y guardarraíles<br>• Qué responde / qué NO responde<br>• Abstención responsable<br>• Preferencia por fuentes vigentes<br>• PII/límites: ______________________________________|
|7) Recuperación e indexación<br>• Chunking (criterio + solape)<br>• Metadatos (área, canal, versión, sensibilidad)<br>• Búsqueda híbrida cuando aplique<br>• Decisiones: _______________________________________|8) Orquestación del asistente<br>• Enrutado por intención (documental/métrica/mixta)<br>• Orden de pasos (RAG, tool, respuesta)<br>• Citaciones y trazabilidad<br>• Reglas: __________________________________________|9) Salida y experiencia<br>• Formato (resumen + detalle + fuentes)<br>• Tablas/listados (top N) y desambiguación<br>• Gestión de contexto conversacional<br>• Ejemplo: __________________________________________|
|10) Calidad y evaluación<br>• Test sets por área<br>• Métricas (precision/recall, groundedness, abstención)<br>• Criterios de aceptación<br>• Plan: _____________________________________________|11) Seguridad y gobierno<br>• Control de acceso a orígenes<br>• DLP/sensitivity labels/canales<br>• Mitigación prompt injection<br>• Controles: _________________________________________|12) Operación y roadmap<br>• MVP (qué entra/qué no)<br>• Iteraciones (V1, V2) y responsables<br>• Monitorización y mantenimiento<br>• Roadmap: __________________________________________|
