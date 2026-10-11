# Propuesta de demos prácticas Power BI y Fabric Data Agent · FraSoHome

Fecha: 5 de junio de 2026  
Curso: Business Intelligence y Gestión de Datos · MBA · 20 horas  
Caso transversal: FraSoHome

## 1. Objetivo

Convertir el caso FraSoHome en una experiencia práctica de aula con dos piezas demostrables:

1. Un conjunto de cuadros de mando Power BI que implementen los ejercicios C1-C8 de la guía docente.
2. Un Fabric Data Agent para la parte de IA generativa aplicada a BI, conectado a datos gobernados y preparado para preguntas en lenguaje natural.

La idea no es enseñar solo botones de Power BI, sino usar Power BI y Fabric como soporte visible de la lógica del curso: decisión, KPI, dato, calidad, modelo, visualización, IA, storytelling y adopción.

## 2. Encaje con las sesiones

| Bloque | Tema | Demostración propuesta | Resultado para el alumno |
| --- | --- | --- | --- |
| C1 | De la estrategia a la decisión | Brief de decisión sobre rentabilidad online | Entender que un dashboard empieza por una decisión recurrente |
| C2 | Preguntas y KPIs | KPI tree en Power BI: ventas netas, margen neto, stockout y devoluciones | Traducir estrategia en métricas accionables |
| C3 | Datos, calidad y gobierno | Página de calidad y confianza del dato | Ver por qué no todo dato disponible debe usarse directamente |
| C4 | Arquitectura y modelado | Modelo semántico en estrella sobre retail omnicanal | Entender hechos, dimensiones, granularidad y relaciones |
| C5 | Power BI aplicado | Dashboard ejecutivo de margen online | Construir una portada directiva con diagnóstico y acción |
| C6 | IA generativa aplicada a BI | Fabric Data Agent sobre modelo semántico y Lakehouse/Warehouse | Preguntar al dato con controles, grounding y validación |
| C7 | Storytelling y decisión | Rediseño narrativo del dashboard ejecutivo | Pasar de visualización a recomendación ejecutiva |
| C8 | Roadmap BI 90 días | Página final de adopción y backlog | Conectar el MVP con gobierno, adopción y mejora continua |

## 3. Activos existentes aprovechables

Activos ya disponibles en el repositorio:

- Datos retail omnicanal: `datos/retail_omnicanal/raw_csv`.
- Fact integrada para demos: `fact_transacciones.csv`.
- Datos de marketing precision: `datos/marketing_precision/raw_csv`.
- Notebooks Fabric de ingesta, perfilado, limpieza, integración, features y scoring: `escenarios/02-fabric-preparacion-datos/notebooks`.
- PBIX existente: `escenarios/03-sql-raw-core-analytics/powerbi/Pedidos-Online.pbix`.
- Guía docente y soluciones: `Guia_casos_y_soluciones_FrasoHome_BI_20h.docx`.
- Presentación del curso: `mba-bi-gestion-datos.pdf`.

Observación de alcance: el dataset retail cubre bien ventas, margen bruto, stock y devoluciones. Para cubrir exactamente OTIF y campañas como aparecen en la guía, conviene añadir una extensión ligera:

- `entregas.csv`: pedido, fecha prometida, fecha entrega, transportista, zona, coste envío, OTIF.
- enlace con marketing precision: campañas, contactos, cupones, eventos y costes operativos.

## 4. Propuesta de cuadros Power BI

### Dashboard 1 · Comité ecommerce: crecimiento rentable

Propósito: implementar el caso central de la guía: crecer online sin deteriorar margen, stock ni experiencia.

Páginas:

| Página | Contenido | Ejercicios que cubre |
| --- | --- | --- |
| Resumen ejecutivo | Ventas netas, margen neto, margen %, stockout %, tasa devolución, semáforos y tendencia | C1, C2, C5, C7 |
| Diagnóstico de margen | Matriz categoría/canal, waterfall de margen, ranking de erosión por descuento/devolución/coste | C2, C5 |
| Stock y disponibilidad | Stock mínimo, cobertura, stockout, SKUs críticos y ventas potencialmente perdidas | C2, C3, C5 |
| Devoluciones y CX | Tasa de devolución, motivos, coste, categorías afectadas y comentarios si se enlaza con feedback | C2, C5, C6 |
| Acción y seguimiento | Alertas, owner, acción recomendada, fecha de revisión y métrica de control | C7, C8 |

Medidas mínimas:

- Ventas netas.
- Margen bruto.
- Margen neto estimado.
- % margen neto.
- Ticket medio.
- Tasa devolución.
- Stockout %.
- Ventas perdidas estimadas por stockout.
- ROAS de margen, si se integra marketing precision.

### Dashboard 2 · Calidad, gobierno y confianza

Propósito: hacer visible C3 y C4 antes de enseñar el dashboard final.

Páginas:

| Página | Contenido | Uso docente |
| --- | --- | --- |
| Perfilado de fuentes | Volumen por tabla, nulos, duplicados, fechas no parseadas, importes inválidos | Abrir debate sobre calidad |
| Reglas críticas | Cliente en CRM, producto en maestro, fecha válida, importe parseado, stock no negativo | Conectar reglas con KPIs |
| Linaje simplificado | CSV origen → limpieza → fact integrada → modelo semántico → informe | Explicar arquitectura |
| Diccionario KPI | Fórmula, owner, fuente autorizada, umbral, acción | Reforzar gobierno y catálogo |

Este dashboard puede apoyarse en las salidas de los notebooks Fabric, especialmente perfilado, limpieza e integración.

### Dashboard 3 · Marketing rentable y activación

Propósito: ampliar el caso si quieres una demo más cercana a CMO/eCommerce.

Páginas:

| Página | Contenido | Ejercicios que cubre |
| --- | --- | --- |
| Campañas | Coste, contactos, conversiones, ventas atribuidas, margen y cupones | C2, C5 |
| ROAS de margen | Diferencia entre ROAS de ventas y ROAS de contribución | C2, C7 |
| Segmentos | Segmento, canal preferido, conversión y devolución | C1, C2 |
| Decisión | Escalar, pausar o rediseñar campaña | C7, C8 |

Este dashboard usaría `datos/marketing_precision/raw_csv` y se conectaría con pedidos, clientes y productos del dominio retail.

### Dashboard 4 · Vista final de roadmap 90 días

Propósito: que el alumno vea cómo el prototipo se convierte en producto BI.

Contenido:

- MVP seleccionado.
- KPIs oficiales y owners.
- Fuentes autorizadas.
- Reglas de calidad.
- Riesgos y controles.
- Backlog 0-30, 31-60 y 61-90 días.
- Métricas de adopción: usuarios activos, decisiones registradas, incidencias de datos, acciones cerradas.

## 5. Propuesta de Fabric Data Agent

Nombre sugerido: `FrasoHome BI Agent`.

Objetivo: permitir preguntas de negocio sobre el caso FraSoHome usando lenguaje natural, pero con respuestas basadas en el modelo semántico y datos certificados.

Fuentes recomendadas:

| Fuente | Uso |
| --- | --- |
| Power BI semantic model | Métricas oficiales: ventas, margen, devoluciones, stockout, ROAS |
| Lakehouse o Warehouse | Exploración de tablas depuradas y datos de detalle |
| Tablas de calidad | Responder sobre confianza, frescura y reglas incumplidas |
| Datos marketing precision | Preguntas sobre campañas, contactos, cupones y conversión |

Configuración didáctica:

1. Preparar el semantic model para IA con nombres de negocio claros, medidas oficiales y un subconjunto de tablas relevante.
2. Configurar `Prep for AI` en Power BI para reducir ambigüedad y priorizar las medidas correctas.
3. Crear el Data Agent con un alcance claro: margen online, stock, devoluciones, campañas y calidad.
4. Añadir instrucciones de respuesta: separar hechos, hipótesis, datos faltantes y acciones.
5. Probar un set de preguntas de clase con respuesta esperada.
6. Enseñar limitaciones: si falta OTIF o coste logístico real, el agente debe decirlo.

Preguntas de demo:

| Pregunta | Qué enseña |
| --- | --- |
| ¿Por qué cae el margen online este mes? | Diagnóstico de causas y separación hechos/hipótesis |
| ¿Qué categorías venden más pero destruyen margen? | Diferencia entre crecimiento y rentabilidad |
| ¿Qué SKUs tienen riesgo de stockout y margen alto? | Priorización operativa |
| ¿Qué motivos de devolución erosionan más el margen? | Conexión postventa-finanzas |
| ¿Qué campañas debería pausar el CMO? | ROAS de margen frente a ROAS de ventas |
| ¿Qué datos faltan para confirmar la causa? | Buen uso de IA sin inventar |
| Dame un resumen ejecutivo de 5 líneas para el comité | Storytelling asistido |

Respuesta modelo esperada:

- Resumen ejecutivo breve.
- Tabla de evidencias.
- Hipótesis separadas de hechos.
- Datos faltantes o baja confianza.
- Acciones concretas con owner.
- Métrica de seguimiento.

## 6. Secuencia recomendada para 20 horas

| Tiempo | Sesión | Demo |
| --- | --- | --- |
| 2 h | Conceptos y caso FraSoHome | Presentación del caso + decisión prioritaria |
| 2 h | Estrategia, preguntas y KPIs | KPI tree + fichas KPI |
| 3 h | Datos, calidad y gobierno | Dashboard de calidad + revisión de fuentes |
| 3 h | Arquitectura y modelado | Lakehouse/Warehouse + modelo semántico |
| 4 h | Power BI aplicado | Construcción guiada del dashboard ejecutivo |
| 2 h | IA generativa aplicada a BI | Fabric Data Agent + prompts seguros |
| 2 h | Storytelling | Rediseño narrativo y guion de 90 segundos |
| 2 h | Roadmap y pitch final | Roadmap 90 días + defensa por grupos |

## 7. Entregables propuestos

Entregables para preparar antes de impartir:

| Entregable | Prioridad | Comentario |
| --- | --- | --- |
| PBIX v1 `FraSoHome_Comite_Ecommerce.pbix` | Alta | Dashboard principal del curso |
| PBIX v1 `FraSoHome_Calidad_Gobierno.pbix` | Alta | Muy útil para C3-C4 |
| Modelo semántico certificado | Alta | Base común para Power BI y Data Agent |
| Lakehouse/Warehouse con tablas limpias | Alta | Preparado desde notebooks Fabric |
| Diccionario KPI en tabla | Alta | Necesario para gobierno y Data Agent |
| Set de preguntas y respuestas esperadas | Alta | Permite evaluar el agente |
| Extensión `entregas.csv` | Media | Necesaria si se quiere OTIF completo |
| Integración marketing precision | Media | Recomendada para ROAS de margen |
| Guion de demo por sesión | Alta | Evita improvisar transiciones |

## 8. Trabajo de preparación

Fase 1 · Consolidación de datos:

- Ejecutar o adaptar notebooks Fabric 1-4 para producir tablas limpias.
- Definir tablas Gold: `FactSales`, `FactReturns`, `FactStockDaily`, `DimDate`, `DimProduct`, `DimCustomer`, `DimStore`.
- Añadir `FactCampaigns` si se integra marketing precision.
- Añadir `FactDeliveries` si se quiere cubrir OTIF.

Fase 2 · Modelo semántico:

- Crear relaciones uno-a-muchos desde dimensiones hacia hechos.
- Centralizar medidas DAX oficiales.
- Ocultar claves técnicas y columnas de control no docentes.
- Renombrar campos con vocabulario de negocio.
- Documentar medidas y owners.

Fase 3 · Informes Power BI:

- Crear dashboard ejecutivo.
- Crear dashboard de calidad y gobierno.
- Preparar versión "alumno" incompleta y versión "instructor" resuelta.
- Añadir bookmarks o páginas ocultas para enseñar errores frecuentes.

Fase 4 · Data Agent:

- Publicar semantic model en Fabric/Power BI.
- Configurar `Prep for AI`.
- Crear `FrasoHome BI Agent`.
- Conectar semantic model y, si procede, Lakehouse/Warehouse.
- Validar preguntas de aula con answer key.
- Documentar limitaciones conocidas.

## 9. Decisiones pendientes

| Decisión | Recomendación |
| --- | --- |
| ¿Usar solo retail o integrar marketing? | Empezar con retail para el MVP y añadir marketing como demo avanzada |
| ¿Cubrir OTIF desde el primer día? | Añadir una tabla sintética pequeña de entregas, porque es central en la guía |
| ¿Un PBIX o varios? | Dos PBIX: ejecutivo y calidad/gobierno. Marketing como tercero opcional |
| ¿Alumno construye o instructor demuestra? | Modelo mixto: demo guiada + ejercicios por grupos |
| ¿Data Agent sobre semantic model o tablas? | Semantic model para KPIs oficiales; Lakehouse/Warehouse para detalle y calidad |

## 10. Referencias Microsoft revisadas

- Microsoft Learn indica que Fabric Data Agent permite construir sistemas conversacionales de Q&A con IA generativa sobre datos en OneLake y fuentes como lakehouse, warehouse, semantic model, KQL database, mirrored database u ontology.
- La documentación oficial señala como prerrequisito una capacidad Fabric de pago F2 o superior, o Power BI Premium por capacidad P1 o superior con Fabric habilitado.
- Para semantic models, Microsoft recomienda preparar el modelo para IA con `Prep for AI`, nombres de negocio, subconjuntos de tablas y medidas claras.
- El consumo desde Copilot en Power BI está documentado como característica en preview, con selección de data agents desde OneLake catalog y respeto de permisos como RLS/CLS.

Enlaces:

- Fabric Data Agent concepts: https://learn.microsoft.com/en-us/fabric/data-science/concept-data-agent
- Add a data source to Data Agent: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-add-datasources
- Semantic model best practices for Data Agent: https://learn.microsoft.com/en-us/fabric/data-science/semantic-model-best-practices
- Consume a data agent from Copilot in Power BI: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-copilot-powerbi

