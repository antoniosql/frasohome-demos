# LAB 5 — Arquitectura híbrida: Tools (Dataverse) + RAG (documentos)

Objetivo: habilitar al agente para responder preguntas métricas (datos estructurados) y, al mismo tiempo, citar definiciones oficiales de KPIs desde la base documental (RAG).

| Duración estimada | 90–120 min |
| --- | --- |
| Entregables | 1) 2–3 herramientas (Tools) de Dataverse configuradas. 2) Un topic 'Consultas métricas' que llama a herramientas, calcula y responde. 3) Pruebas con preguntas métricas + citación de KPI. |
| Prerrequisitos | LAB 2–4 completados: documentos en Knowledge + tablas en Dataverse creadas y con datos. |

## Material del lab

### Documentos de conocimiento (Knowledge) que DEBEN estar cargados:

- FS-KB-03_Diccionario_KPI_Reglas_Calculo_v1.0.docx (definiciones KPI)

- FS-KB-08_Politica_Datos_y_Permisos_Asistente_v1.0.docx (permisos/uso de datos)

### Tablas Dataverse que DEBEN existir:

- FS Ventas Resumen Diario

- FS Devoluciones

- FS Alertas Stockout

### Preguntas que vas a probar al final (ya te las damos aquí)

- “Dame las ventas netas online entre 2026-02-01 y 2026-02-15”

- “Calcula la tasa de devolución en importe para Online en febrero 2026 y explícame la fórmula”

- (Opcional) “Lista 5 devoluciones aprobadas con motivo R04 en enero 2026”

## Paso a paso

### 1) Añadir herramientas (Tools) desde el conector Microsoft Dataverse

Vas a crear herramientas de SOLO LECTURA (List rows) para consultar Dataverse.

- En Copilot Studio, abre tu agente FraSoHome.

- Ve a la pestaña Tools (Herramientas).

- Selecciona Add a tool (Agregar una herramienta).

- Selecciona Connector (Conector).

- Busca y selecciona Microsoft Dataverse.

- Selecciona la acción/herramienta: List rows from selected environment (Listar filas del entorno seleccionado).

- Si te lo pide, selecciona Create new connection (Crear nueva conexión) y autentica tu usuario.

- Pulsa Submit/Create y luego Add and configure (Agregar y configurar).

#### Crea estas 3 herramientas (repitiendo el proceso):

| Nombre sugerido del Tool | Tabla | Qué devuelve / para qué |
| --- | --- | --- |
| DV_ListSalesSummary | FS Ventas Resumen Diario | Filas con Date, Channel, StoreID, NetSalesEUR, Orders (para sumar ventas). |
| DV_ListReturns | FS Devoluciones | Filas con ReturnDate, Channel, StoreID, RefundAmountEUR, ReasonCode, Approved, ReturnID (para contar/sumar devoluciones). |
| DV_ListStockoutAlerts (opcional) | FS Alertas Stockout | AlertDate, StoreID, SKU, Severity, Priority, SuggestedAction (para alertas). |

### 2) Crear el topic 'Consultas métricas' (recoge parámetros y decide qué Tool usar)

- Ve a Topics (Temas).

- Selecciona New topic (Nuevo tema) > From blank (En blanco).

- Nombre: Consultas métricas.

- Añade triggers (frases) como: 'ventas netas', 'tasa de devolución', 'devoluciones online', 'stockout', 'alertas de stock'.

- En el lienzo del topic, añade un nodo Question para preguntar: “¿Qué métrica necesitas?” con opciones: (A) Ventas netas, (B) Tasa de devolución (importe), (C) Alertas stockout.

- Guarda la opción elegida en una variable: Topic.Metrica.

- Añade 4 nodos Question para capturar parámetros:

- Fecha inicio → Topic.FechaInicio (tipo fecha).

- Fecha fin → Topic.FechaFin (tipo fecha).

- Canal → Topic.Canal (opciones: Online, Tienda, Ambos).

- Tienda → Topic.Tienda (opciones: MAD01, BCN01, VLC01, ONLINE, Todas).

- Consejo: si el usuario elige Canal=Online, normalmente Tienda=ONLINE. Si elige Canal=Tienda, Tienda puede ser una tienda física o Todas.

### 3) Rama A — Ventas netas (Tool + cálculo con Power Fx)

- Debajo del bloque de preguntas, añade un nodo Condition (Condición): si Topic.Metrica = 'Ventas netas'.

- Dentro de la rama, añade un nodo para llamar al Tool DV_ListSalesSummary.

- Guarda la salida del Tool en una variable tipo tabla (por ejemplo Topic.SalesRows).

- Añade un nodo Set a variable value (Establecer variable) para filtrar filas con Power Fx (ejemplo abajo). Guarda el resultado en Topic.SalesFiltradas.

- Añade otro Set a variable value para calcular NetSalesTotal = Sum(Topic.SalesFiltradas, NetSalesEUR).

- Añade otro Set a variable value para calcular OrdersTotal = Sum(Topic.SalesFiltradas, Orders).

- Añade un nodo Message para responder con el total y con el contexto (periodo/canal/tienda).

#### Power Fx (copiar y pegar) — Filtrado y suma

Nota: si tus columnas tienen prefijos (por el schema de Dataverse), usa los nombres exactos que te aparecen en el output del Tool.

```text
// Filtrar ventas por fechas, canal y tienda
Filter(
    Topic.SalesRows,
    Date >= Topic.FechaInicio &&
    Date <= Topic.FechaFin &&
    (Topic.Canal = "Ambos" || Channel = Topic.Canal) &&
    (Topic.Tienda = "Todas" || StoreID = Topic.Tienda)
)
```

```text
// Sumar ventas netas y pedidos
Sum(Topic.SalesFiltradas, NetSalesEUR)
```

### 4) Rama B — Tasa de devolución (Tool + cálculo + definición citada)

- Añade una segunda condición: si Topic.Metrica = 'Tasa de devolución (importe)'.

- Llama a DV_ListSalesSummary y calcula NetSalesTotal igual que en la rama A (mismo filtro).

- Llama a DV_ListReturns y guarda la salida en Topic.ReturnRows.

- Filtra devoluciones aprobadas con Power Fx y suma el importe devuelto.

- Calcula la tasa = RefundTotal / NetSalesTotal (si NetSalesTotal = 0, devuelve 'No aplicable').

- Después, añade un nodo Create generative answers (respuestas generativas) para recuperar la DEFINICIÓN oficial del KPI desde FS-KB-03 (ejemplo de prompt abajo).

- Responde con: cifra + explicación + citación del diccionario KPI.

#### Power Fx (copiar y pegar) — Devoluciones aprobadas y ratio

```text
// Filtrar devoluciones aprobadas por fechas/canal/tienda
Filter(
    Topic.ReturnRows,
    ReturnDate >= Topic.FechaInicio &&
    ReturnDate <= Topic.FechaFin &&
    (Topic.Canal = "Ambos" || Channel = Topic.Canal) &&
    (Topic.Tienda = "Todas" || StoreID = Topic.Tienda) &&
    Approved = "Sí"
)
```

```text
// Importe total devuelto
Sum(Topic.ReturnsFiltradas, RefundAmountEUR)
```

```text
// Tasa de devolución (importe)
If(
    Topic.NetSalesTotal <= 0,
    Blank(),
    Topic.RefundTotal / Topic.NetSalesTotal
)
```

#### Prompt sugerido para el nodo Create generative answers (definición KPI)

En el nodo Create generative answers, pega como 'User question' o entrada:

¿Cuál es la definición oficial de “tasa de devolución en importe” y su fórmula? Responde en 2–3 líneas y con citaciones.

### (Opcional) Rama C — Alertas stockout

- Si implementas la opción C, llama al Tool DV_ListStockoutAlerts y filtra por tienda (si el usuario la indicó).

- Responde con una lista corta (top 5) mostrando SKU + Severidad + Acción sugerida.

- Nota: esta rama es útil para probar listados y priorización.

### 5) Pruebas guiadas (con resultados esperados)

Abre el panel Test y ejecuta estas pruebas (copia y pega). Si tus tablas se importaron bien, deberías obtener números similares:

| Pregunta | Resultado esperado | Fuentes esperadas |
| --- | --- | --- |
| Dame las ventas netas online entre 2026-02-01 y 2026-02-15 | Esperado (dataset del pack): NetSalesEUR ≈ 21429.39 y Orders ≈ 272. Además, debe indicar periodo/canal y NO inventar. | Dataverse (FS Ventas Resumen Diario) + definición de 'ventas netas' citada en FS-KB-03 (si la incluyes). |
| Calcula la tasa de devolución en importe para Online en febrero 2026 y explícame la fórmula | Esperado: RefundTotal ≈ 22849.89; NetSales ≈ 26971.17; ratio ≈ 0.8472 (84.72%). Debe citar la fórmula desde FS-KB-03. | Dataverse (Ventas + Devoluciones) + FS-KB-03. |
| Lista 5 devoluciones aprobadas con motivo R04 en enero 2026 | Ejemplo esperado (primeros IDs): R000005, R000016, R000018, R000022, R000043 (puede variar si ordenas distinto). | Dataverse (FS Devoluciones). |

## Checklist de entrega

- ✅ Tools Dataverse creados (mínimo DV_ListSalesSummary y DV_ListReturns).

- ✅ Topic 'Consultas métricas' creado, con preguntas de parámetros y ramas.

- ✅ Cálculos hechos con Power Fx (Filter + Sum).

- ✅ Pruebas ejecutadas y resultados coherentes.

- ✅ Definiciones KPI citadas desde FS-KB-03 (si incluiste nodo generativo).