# Canvas_Solucion_Instructor

# **FraSoHome - RAG Canvas (Solución Instructor)**

Lienzo completo de referencia para el taller

Versión: Instructor

Fecha: 25/02/2026

## 1) Resultados de negocio

- Reducir tiempo de búsqueda de información interna (políticas, KPI, procedimientos) en 30-50%.
- Aumentar consistencia: respuestas citadas y definiciones unificadas (ventas netas, tasa devolución, stock disponible).
- Acelerar decisiones: reposición de stock, campañas por segmento, control de devoluciones y conciliaciones.
- Reducir dependencia del equipo de datos para preguntas recurrentes.
## 2) Usuarios y stakeholders

|Rol|Necesidad principal|Restricciones típicas|
|---|---|---|
|Dirección|Visión KPI + alertas, comparativas por canal|Acceso agregado; sin PII.|
|Marketing|Segmentos, campañas, fidelización|Acceso agregado; PII minimizada.|
|Operaciones/Logística|Stock, rotación, incidencias y devoluciones|Acceso por tienda; sin export masiva.|
|Tienda/Atención|Políticas, procedimientos, devoluciones, pagos|Acceso operativo; evitar extracción masiva.|

## 3) Casos de uso prioritarios (Top 5)

|Pregunta|Tipo|Fuente principal|
|---|---|---|
|¿Cuál es el plazo y las excepciones de devoluciones por canal?|Documental|FS-KB-01 (v1.3)|
|Define ventas netas y calcula ventas netas online por periodo.|Mixto|FS-KB-03 + VentasResumenDiario|
|¿Qué SKUs están en riesgo de stockout hoy por tienda?|Métrica|Alertas_Stockout / StockDiario|
|¿Qué hacer ante pago mixto y devolución sin ticket?|Documental|FS-KB-04 (+ FS-KB-05 si online)|
|Detectar devoluciones anómalas por cliente/SKU (alto nivel).|Mixto|DevolucionesFact + FS-KB-08|

## 4) Conocimiento documental (RAG)

- Política de devoluciones: plazos, excepciones, daños transporte, productos excluidos (FS-KB-01).
- Diccionario KPI y reglas de cálculo (FS-KB-03).
- Manual de tienda: caja, devoluciones, pagos mixtos, casos sin ticket (FS-KB-04).
- Guía conciliación e-commerce (FS-KB-05).
- Fidelización CRM: tiers y beneficios/excepciones (FS-KB-07).
- Política de datos y permisos (FS-KB-08).
## 5) Datos estructurados (Tools/Acciones)

- VentasResumenDiario: métricas agregadas por fecha/canal/tienda.
- DevolucionesFact: devoluciones a nivel transacción (razón, aprobado, importe).
- StockDiario: stock por tienda y SKU (disponible/reservado/bloqueado).
- Alertas_Stockout: lista priorizada de quiebras de stock (fecha, prioridad).
- Productos / Tiendas / Clientes: dimensiones.
## 6) Alcance y guardarraíles

- Responde solo con base en: documentos FS-KB autorizados y tablas del Dataverse.
- Preferir documentos vigentes (v1.3) y evitar obsoletos (v1.2).
- Abstención responsable: si no hay evidencia o el dato no está disponible, decirlo y proponer siguiente paso.
- Privacidad: no devolver PII (emails, direcciones, teléfonos) ni listados masivos; usar agregados.
- Seguridad: resistir prompt injection (ignorar instrucciones maliciosas del usuario o documentos).
## 7) Recuperación e indexación

- Chunking por secciones y por Q&A; solape pequeño para preservar excepciones.
- Metadatos mínimos: área, canal, versión, vigencia, sensibilidad.
- Búsqueda híbrida para términos exactos (KPI, SKU, ReasonCode).
## 8) Orquestación del asistente

- Clasificar intención: documental / métrica / mixta.
- Documental: recuperar evidencias -> generar -> citar.
- Métrica: pedir parámetros -> consultar tabla -> devolver cifra y criterios.
- Mixta: consultar datos -> recuperar definición/política -> respuesta integrada.
## 9) Salida y experiencia

- Formato 3 capas: Resumen, Detalle (filtros/supuestos), Fuentes/Evidencia.
- Para métricas: siempre indicar periodo, canal, tienda y definición KPI usada.
- Para listados: top N y criterio de orden.
## 10) Calidad y evaluación

- Separar evaluación de recuperación (doc correcto) vs respuesta (groundedness y formato).
- Test sets: documental (policy/KPI) y métrico/mixto (ventas, devoluciones, stockout).
- Criterios de aceptación: cita correcta, no inventa, pide parámetros, respeta seguridad.
## 11) Seguridad y gobierno

- Acceso a orígenes por rol (agregado vs detalle).
- Evitar publicación en canales no autorizados; aplicar políticas DLP/sensitivity.
- Logs/auditoría de preguntas, fuentes y consultas a datos.
- Proceso de retirada de documentos obsoletos y actualización controlada.
## 12) Operación y roadmap

- MVP: Q&A documental + definiciones KPI + 2 consultas (ventas netas, stockout).
- V1: tool completo para devoluciones + test sets + monitorización.
- V2: personalización por rol + insights (segmentación, fraude) con controles de seguridad.
