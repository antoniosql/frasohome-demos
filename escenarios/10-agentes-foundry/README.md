# 10 · Agentes con Foundry

| Capítulo | Audiencia | Duración | Tecnología |
| --- | --- | --- | --- |
| 7 · IA que se explica y agentes | IA aplicada, arquitectura, estrategia | 45–90 min (diseño y construcción guiada) | Microsoft Foundry Agent Service · Code Interpreter · File Search · Web Search |

## La historia en este punto

FraSoHome ya ha visto un asistente que responde ([escenario 07](../07-copilot-studio-rag/README.md)) y un agente que razona sobre una ontología ([escenario 08](../08-fabric-iq-ontologia/README.md)). El siguiente paso es dejar que **varios agentes especializados colaboren en un proceso completo**, con una persona aprobando los puntos críticos. Dos procesos candidatos:

- **Preparar los datos** que hoy cuestan una semana a un analista: perfilar, limpiar, integrar y generar *features*.
- **Detectar tendencias** de interiorismo y convertirlas en propuestas de colección y un *brief* de compras, cruzándolas con lo que FraSoHome vende, devuelve y tiene en stock.

## Qué se demuestra

- Cómo se descompone un problema en sub-tareas y agentes con responsabilidad única.
- Patrones de orquestación: secuencial y secuencial con humano en el bucle.
- Herramientas por agente (Code Interpreter, File Search, Web Search) y bases de conocimiento por agente.
- Variables de *workflow* que pasan el resultado de un agente al siguiente.
- La evolución de un diseño: el TrendScout original frente a la estrategia dual cuantitativa (Google Trends) + cualitativa (web).

## Los tres diseños

| Diseño | Agentes | Patrón | Documento |
| --- | --- | --- | --- |
| **Data Pipeline** | DataProfiler → *aprobación humana* → DataCleaner → DataIntegrator → FeatureForge | Secuencial con *human-in-the-loop* | [multiagente-data-pipeline.md](multiagente-data-pipeline.md) |
| **TrendHunter** | TrendScout → CatalogMatch → CollectionArchitect → BuyingBrief | Secuencial | [trendhunter.md](trendhunter.md) |
| **TrendScout v2** | TrendRadar (Google Trends) + TrendContext (web) → TrendFusion → CatalogMatch… | Paralelo + fusión | [trendscout-v2.md](trendscout-v2.md) |

## Recursos necesarios

### Entorno

| Recurso | Para qué |
| --- | --- |
| Un proyecto de Microsoft Foundry con Agent Service | Crear agentes y *workflows* |
| Un modelo desplegado compatible con agentes | Razonamiento de cada agente |
| Herramientas Code Interpreter y File Search habilitadas | Todos los diseños |
| Grounding con búsqueda web | TrendHunter y TrendScout v2 |

### Datos

**Data Pipeline**: los documentos de diseño usan nombres de fichero genéricos. Su equivalencia en este repositorio es:

| Nombre en el diseño | Fichero en el repositorio |
| --- | --- |
| `crm_clientes.csv` | [`crm.csv`](../../datos/retail_omnicanal/raw_csv/crm.csv) |
| `ecommerce_pedidos.csv` | [`pedidos.csv`](../../datos/retail_omnicanal/raw_csv/pedidos.csv) |
| `ecommerce_lineas.csv` | [`lineas_pedido.csv`](../../datos/retail_omnicanal/raw_csv/lineas_pedido.csv) |
| `ecommerce_devoluciones.csv` | [`devoluciones_online.csv`](../../datos/retail_omnicanal/raw_csv/devoluciones_online.csv) |
| `pos_tickets.csv` | [`ventas_pos.csv`](../../datos/retail_omnicanal/raw_csv/ventas_pos.csv) |
| `pos_devoluciones.csv` | [`devoluciones_tienda.csv`](../../datos/retail_omnicanal/raw_csv/devoluciones_tienda.csv) |
| `pos_pagos.csv` | [`pagos_tienda.csv`](../../datos/retail_omnicanal/raw_csv/pagos_tienda.csv) |
| `erp_stock.csv` | [`stock_diario.csv`](../../datos/retail_omnicanal/raw_csv/stock_diario.csv) |
| `erp_productos.csv` | [`productos.csv`](../../datos/retail_omnicanal/raw_csv/productos.csv) |

Las columnas reales pueden diferir de las del diseño: revisa el [perfil de datos](../02-fabric-preparacion-datos/perfil-datos.md) y adapta las bases de conocimiento (KB) antes de subirlas.

**TrendHunter**: el agente CatalogMatch cruza tendencias con [`productos.csv`](../../datos/retail_omnicanal/raw_csv/productos.csv), [`fact_transacciones.csv`](../../datos/retail_omnicanal/raw_csv/fact_transacciones.csv) y [`stock_diario.csv`](../../datos/retail_omnicanal/raw_csv/stock_diario.csv). Las KB de mercado, competidores, catálogo, proveedores, plantilla de *brief* y calendario retail están redactadas dentro de [trendhunter.md](trendhunter.md).

### Material de la demo

Los tres documentos de diseño incluyen, para cada agente: misión, instrucciones (*system prompt*), herramientas, bases de conocimiento, formato de salida y reglas. Las KB están escritas en Markdown dentro de cada documento, listas para copiarlas a ficheros y subirlas a File Search.

## Cómo ejecutarla

1. Elige un diseño y léelo de principio a fin con la audiencia: problema, sub-tareas, patrón.
2. Extrae las KB del documento a ficheros `.md` y súbelas a File Search.
3. Crea cada agente en Foundry con sus instrucciones y herramientas.
4. Encadénalos en un *workflow* con las variables indicadas.
5. **Data Pipeline**: sube los CSV a Code Interpreter, ejecuta DataProfiler y revisa el *Data Quality Report* antes de aprobar el plan de limpieza.
6. **TrendHunter**: lanza TrendScout con una temporada objetivo y sigue la cadena hasta el *brief* de compras.

Para comparar, el mismo pipeline de datos está implementado de forma determinista en los notebooks del [escenario 02](../02-fabric-preparacion-datos/README.md).

## Guion sugerido (45 min)

| Minuto | Bloque | Mensaje |
| --- | --- | --- |
| 0–10 | Del copiloto al sistema | Un agente que hace todo es difícil de evaluar; varios especializados, no |
| 10–20 | Data Pipeline | Dónde va el humano: entre el diagnóstico y la acción |
| 20–35 | TrendHunter | El valor está en cruzar señales externas con datos internos |
| 35–45 | TrendScout v2 | Rediseñar cuando las señales son de segunda mano |

## Mensajes clave

- Un agente por responsabilidad, con sus herramientas y su conocimiento.
- El humano en el bucle se coloca donde una decisión es difícil de deshacer.
- Los agentes heredan la calidad de los datos y las definiciones: sin los capítulos anteriores, esto no funciona.
