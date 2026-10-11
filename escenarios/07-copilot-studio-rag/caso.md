# Caso FraSoHome - RAG - Completo

# Caso FraSoHome — Descripción del problema de negocio para el taller (RAG + Copilot Studio)

## 1) Contexto empresarial

FraSoHome es una cadena ficticia B2C de muebles y decoración con operación omnicanal: tiendas físicas, e-commerce y un programa de fidelización gestionado en CRM. En su catálogo conviven artículos pequeños (decoración) y productos voluminosos (muebles), lo que incrementa la complejidad operativa en logística, stock, devoluciones y atención al cliente.

En los últimos meses, la dirección ha detectado una pérdida progresiva de capacidad para tomar decisiones basadas en datos y para dar respuestas consistentes a preguntas internas (marketing, tienda, operaciones, finanzas) debido a dos causas principales:

Fragmentación de la información: clientes, compras en tienda, pedidos online, devoluciones y stock viven en sistemas distintos (CRM, POS, e-commerce, ERP).

Problemas de calidad y consistencia: duplicados, claves que no encajan entre sistemas, formatos heterogéneos (fechas, importes, IDs), nulos y anomalías lógicas (fechas fuera de rango, cantidades negativas, etc.).

El resultado es visible: informes de marketing inconsistentes, dificultad para medir lealtad y valor del cliente, fricción al analizar devoluciones y pérdidas de inventario, y una alta dependencia del equipo de datos para responder preguntas recurrentes.

## 2) Necesidad de negocio: “una única forma de preguntar y obtener respuestas fiables”

FraSoHome necesita habilitar un punto único de consulta que permita:

Responder preguntas operativas con trazabilidad (qué fuente respalda la respuesta).

Unificar definiciones (qué es “ventas netas”, cómo se calcula la “tasa de devolución”, qué incluye “stock disponible”, etc.).

Reducir el tiempo que managers y analistas dedican a buscar documentos, KPI definitions y procedimientos en múltiples ubicaciones.

Acelerar decisiones: reposición de stock, campañas por segmento, control de devoluciones y conciliaciones de pagos, etc.

Sentar bases para analítica avanzada y ML (segmentación, predicción de demanda, fraude en devoluciones), una vez que la información esté consolidada.

Para ello, se plantea implementar un asistente en Copilot Studio basado en RAG (Retrieval-Augmented Generation) complementado con un enfoque híbrido (documentación + herramientas/datos estructurados) para cubrir tanto conocimiento “estático” como información transaccional.

## 3) Qué tipo de preguntas debe resolver el asistente (y por qué el enfoque debe ser híbrido)

El caso FraSoHome combina dos familias de necesidades:

### A. Conocimiento no estructurado (ideal para RAG)

Preguntas cuyo origen “verdadero” es documental (políticas, procedimientos, definiciones, guías, acuerdos):

Políticas de devoluciones (online vs tienda; excepciones; plazos; motivos).

Manuales internos (cierre de caja, conciliación de pagos mixtos, tratamiento de incidencias).

Definiciones oficiales de KPIs y reglas de negocio (cómo se computan descuentos, devoluciones, márgenes).

Catálogo y taxonomía (categorías, reglas de naming, criterios de segmentación del CRM).

Este bloque encaja con un flujo RAG: recuperación → generación → citación, separando el modelo del conocimiento empresarial y exigiendo trazabilidad.

### B. Información estructurada/dinámica (RAG no es suficiente por sí solo)

Preguntas que requieren cálculos o consulta directa a datos:

Ventas y devoluciones por canal/tienda/periodo.

Top SKUs por margen, stock disponible, quiebras de stock.

Clientes con mayor tasa de devolución o con patrones anómalos.

Conciliaciones (tickets con pagos múltiples) o incidencias por tienda.

Aquí el taller fuerza la decisión arquitectónica: cuándo RAG no basta (datos transaccionales, altamente estructurados, potencialmente personalizados o cambiantes) y cuándo conviene integrar herramientas/acciones o un agente de datos (p. ej., Dataverse como fuente estructurada).

## 4) Problema específico que el taller propone resolver

FraSoHome define como iniciativa prioritaria construir un “FraSoHome Copilot” para empleados (marketing, operaciones, tienda, atención al cliente y analítica) con estas capacidades:

Responder de forma consistente y citada a preguntas sobre políticas, procesos y definiciones internas.

Consultar datos consolidados (ventas, devoluciones, stock, fidelización) para devolver métricas y listados con criterios claros.

Reducir riesgo operativo: evitar decisiones basadas en documentos obsoletos, datos duplicados o respuestas “inventadas” sin respaldo.

Operar con seguridad corporativa: respetar permisos, controlar el alcance del conocimiento y minimizar exposición indebida de información.

Este objetivo se apoya directamente en los retos del caso (fragmentación de sistemas y calidad de datos) y en sus metas (vista única del negocio y base para analítica/ML).

## 5) Implicaciones RAG que el caso obliga a abordar (alineado al temario)

### 5.1 Arquitectura RAG en entorno empresarial

El asistente debe implementar explícitamente:

Separación modelo–conocimiento: el modelo no “sabe” FraSoHome; se apoya en fuentes controladas.

Flujo operativo recupera–genera–cita: el valor del sistema no es solo responder, sino responder con evidencia.

Elección de tipología según uso: RAG básico para FAQs internas, RAG híbrido (lexical+vectorial) para precisión en términos/IDs, y RAG conversacional para continuidad y contexto en conversaciones largas (por ejemplo, un análisis guiado de devoluciones por canal).

Factores críticos corporativos: versionado documental, permisos y delimitación del alcance (evitar que el asistente “mezcle” temas o conteste con documentos no vigentes).

### 5.2 Proceso de indexación documental (para que “recupere bien”)

La calidad del asistente dependerá de cómo se transformen los documentos en conocimiento recuperable:

Ingesta: selección de fuentes autorizadas (p. ej., procedimientos operativos, políticas, diccionario de datos, definiciones de KPI).

Chunking: criterios de fragmentación (por secciones, tablas, FAQs), solape y preservación de contexto para evitar respuestas incompletas (p. ej., política de devoluciones sin excepciones).

Metadatos: etiquetar por versión, vigencia, área (Marketing/Operaciones/Finanzas), canal (online/tienda), sensibilidad, etc., habilitando filtrado y control.

### **5.3 ****Embeddings**** y recuperación semántica (y sus límites)**

El caso fuerza a tratar:

Representación vectorial para preguntas abiertas (“¿por qué tenemos discrepancias en devoluciones?”).

Limitación del enfoque exclusivamente vectorial cuando hay términos exactos (SKUs, IDs, nombres de KPIs), donde la búsqueda híbrida (semántica + keyword) mejora el recall/precision.

### 5.4 Orígenes de conocimiento en Copilot Studio y sus implicaciones operativas

FraSoHome no tiene “una carpeta” única: el taller contempla un escenario realista con múltiples orígenes:

SharePoint/OneDrive, web corporativa, Dataverse y una visión de integración con Azure AI Search.

Diferenciar operativamente entre:

Knowledge source persistente

Documento incorporado al agente

Archivo subido por el usuario en conversación
y sus implicaciones de seguridad/exposición de contenido.

### 5.5 Arquitectura híbrida: documentación + herramientas + datos estructurados

El caso está diseñado para que aparezcan situaciones donde:

RAG no basta (información dinámica, transaccional, altamente estructurada o personalizada).

Se necesita integrar herramientas/acciones (por ejemplo, consulta a un dataset consolidado de ventas/stock/devoluciones) y después generar una respuesta final contextualizada con normas y definiciones recuperadas del conocimiento documental.

Se introduce el concepto de datos estructurados (tablas/registros) y el rol de Dataverse como repositorio estructurado, separando responsabilidades entre agente conversacional y agente de datos.

## 6) Riesgos de negocio que el asistente debe controlar (evaluación, seguridad y gobierno)

### 6.1 Evaluación de calidad (no solo “que suene bien”)

FraSoHome exige evidencia de que el sistema funciona con calidad empresarial:

Diferenciar evaluación de recuperación vs evaluación de respuesta.

Medir y mejorar métricas como precision, recall, relevancia, groundedness y abstención adecuada (mejor decir “no tengo base suficiente” que inventar).

Construir datasets de prueba y aplicar mejora iterativa desde Copilot Studio.

### 6.2 Seguridad y control empresarial (condición de despliegue)

Dado que el asistente tocará información sensible (clientes, ventas, márgenes, incidencias), el caso incorpora:

Permisos por usuario y control de acceso a orígenes.

Sensitivity labels, DLP y políticas de datos, además del control de canales de publicación.

Mitigación básica frente a prompt injection (p. ej., evitar que instrucciones del usuario anulen reglas del sistema o expongan información fuera de alcance).

### 6.3 Citaciones y trazabilidad como requisito operativo

Para que negocio confíe:

La respuesta debe incluir citaciones (cuando aplica) y reconocer limitaciones (cuando no hay soporte documental suficiente o cuando faltan datos).

## 7) Resultado esperado del caso en el taller

Al finalizar, FraSoHome espera disponer (al menos como prototipo funcional) de un asistente capaz de:

Responder preguntas internas con evidencia y control de versiones.

Combinar recuperación documental con consultas estructuradas para métricas operativas.

Demostrar calidad mediante un conjunto básico de pruebas y métricas, y operar con controles de seguridad razonables para entorno corporativo.
