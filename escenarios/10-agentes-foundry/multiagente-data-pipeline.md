# Sistema Multi-Agente: FraSoHome Data Pipeline
## Diseño Completo para Foundry Agent Service

---

## 1. Análisis del Caso

**Empresa**: FraSoHome — cadena ficticia de tiendas de muebles y decoración B2C omnicanal
**Problema**: Datos fragmentados en 4 sistemas (CRM, POS, e-commerce, ERP), con problemas severos de calidad
**Objetivo**: Vista única del negocio → analytics → ML

**Desglose en sub-tareas**:
1. **Perfilar** la calidad de cada fuente (nulos, duplicados, anomalías, formatos)
2. **Limpiar** y estandarizar todos los datasets
3. **Integrar** en una fact table omnicanal unificada
4. **Enriquecer** con features de cliente (RFM) y producto, escalar y exportar para ML

---

## 2. Arquitectura Multi-Agente

### Patrón de Workflow: **Sequential con Human-in-the-Loop**

Sequential porque cada etapa transforma datos que alimentan la siguiente. Se añade un paso Human-in-the-Loop entre el Profiler y el Cleaner: el usuario revisa el Data Quality Report y aprueba las acciones de limpieza propuestas antes de ejecutarlas.

```
┌────────────────┐       ┌──────────┐       ┌────────────────┐       ┌────────────────┐       ┌────────────────┐
│  DataProfiler  │──────>│ HUMAN    │──────>│  DataCleaner   │──────>│ DataIntegrator │──────>│ FeatureForge   │
│    Agent       │       │ APPROVAL │       │    Agent       │       │    Agent       │       │    Agent       │
└────────────────┘       └──────────┘       └────────────────┘       └────────────────┘       └────────────────┘
       │                                           │                        │                        │
  Code Interpreter                            Code Interpreter         Code Interpreter         Code Interpreter
  File Search                                 File Search              File Search              File Search
                                                                                                
  KB: esquema fuentes                         KB: reglas limpieza      KB: esquema fact table   KB: specs features
  KB: reglas negocio                          KB: esquema fuentes      KB: reglas negocio       KB: plantilla export
```

### Variables del Workflow

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `dq_report` | JSON | Data Quality Report generado por DataProfiler |
| `cleaning_plan` | JSON | Plan de limpieza propuesto (aprobado por humano) |
| `cleaned_datasets` | JSON | Resumen de datasets limpios generados por DataCleaner |
| `fact_table_summary` | JSON | Metadata de la fact table construida por DataIntegrator |
| `feature_sets` | JSON | Resumen de datasets de features + ML-ready por FeatureForge |

---

## 3. Bases de Conocimiento (File Search)

### KB1: `frasohome_esquema_fuentes.md`

```markdown
# Esquema de Fuentes de Datos — FraSoHome

## CRM: crm_clientes.csv
- **Clave primaria**: id_cliente
- **Campos**: id_cliente, nombre, apellidos, email, fecha_alta, nivel_fidelizacion, puntos_acumulados, codigo_postal, telefono
- **Formato fecha_alta**: Puede venir como texto ("10 de Enero de 2022"), ISO o DD/MM/YYYY
- **Encoding**: UTF-8 con posibles problemas en acentos y eñes
- **Volumen esperado**: ~5.000-10.000 registros

## E-commerce: ecommerce_pedidos.csv
- **Clave primaria**: id_pedido
- **Campos**: id_pedido, fecha_hora, id_cliente, importe_total, direccion_envio, metodo_pago, estado
- **Formato fecha**: ISO "YYYY-MM-DD HH:MM:SS"
- **FK**: id_cliente → crm_clientes.id_cliente (puede haber clientes no registrados)

## E-commerce: ecommerce_lineas.csv
- **Clave primaria**: id_pedido + id_producto
- **Campos**: id_pedido, id_producto, descripcion_producto, categoria, cantidad, precio_unitario, descuento, importe_linea
- **FK**: id_pedido → ecommerce_pedidos.id_pedido
- **FK**: id_producto → erp_productos.id_producto (posibles prefijos inconsistentes: SKU-, PROD-)

## E-commerce: ecommerce_devoluciones.csv
- **Clave primaria**: id_devolucion
- **Campos**: id_devolucion, id_pedido, id_producto, fecha_devolucion, cantidad_devuelta, motivo, importe_devuelto
- **FK**: id_pedido → ecommerce_pedidos.id_pedido

## POS: pos_tickets.csv
- **Clave primaria**: id_ticket + id_producto (cada fila = una línea del ticket)
- **Campos**: id_ticket, fecha_hora, id_tienda, codigo_caja, id_producto, descripcion, categoria, cantidad, precio_unitario, descuento, importe_linea
- **Formato fecha**: "DD/MM/YY" (diferente al e-commerce)
- **FK**: id_producto → erp_productos.id_producto

## POS: pos_devoluciones.csv
- **Clave primaria**: id_devolucion
- **Campos**: id_devolucion, fecha, id_tienda, id_producto, cantidad_devuelta, importe_reembolsado, referencia_ticket_original, comentario
- **Nota**: Puede incluir devoluciones de compras online hechas en tienda física (indicadas en comentario)

## POS: pos_pagos.csv
- **Clave primaria**: id_ticket + metodo_pago
- **Campos**: id_ticket, metodo_pago, importe_pagado
- **Nota**: Un ticket puede tener múltiples filas (pago mixto: efectivo + tarjeta)

## ERP: erp_stock.csv
- **Clave compuesta**: fecha + id_producto + id_tienda
- **Campos**: fecha, id_tienda, id_producto, cantidad_stock
- **Nota**: id_tienda incluye código especial para almacén central / canal online
- **Stock negativo**: posible error de inventario (tratar como 0)

## ERP: erp_productos.csv
- **Clave primaria**: id_producto
- **Campos**: id_producto, nombre, categoria, precio_coste, precio_venta, proveedor, marca
- **Categorías esperadas**: Muebles, Iluminación, Textil hogar, Decoración
- **Nota**: Tabla maestra de referencia para enriquecer todas las demás
```

### KB2: `frasohome_reglas_negocio.md`

```markdown
# Reglas de Negocio — FraSoHome

## Calidad de Datos
- Email vacío en CRM: aceptable (cliente puede registrarse sin email)
- Código postal vacío en CRM: rellenar con "DESCONOCIDO"
- Stock negativo en ERP: corregir a 0 (error de inventario conocido)
- Fecha futura en transacciones: eliminar registro (reloj mal configurado)
- Cantidad = 0 en ventas: eliminar registro (error de sistema)
- Descuento > 100%: cap a 100%
- Importe negativo en ventas (no devoluciones): eliminar registro

## Duplicados
- CRM: detectar por combinación nombre + apellidos + email (variaciones menores = mismo cliente)
- Pedidos online: detectar por id_pedido exacto
- Tickets POS: detectar por id_ticket + id_producto + fecha_hora
- Productos: detectar por nombre normalizado (ignorar mayúsculas/acentos)

## Estandarización de IDs
- Todos los id_producto deben ser uppercase sin prefijo: "SKU-001" → "001", "prod-001" → "001"
- id_cliente: numérico, sin espacios
- id_pedido / id_ticket: alfanumérico uppercase

## Formatos
- Todas las fechas: ISO 8601 (YYYY-MM-DD HH:MM:SS)
- Todos los importes: float con 2 decimales, punto como separador decimal
- Todos los textos: trim de espacios, primera letra mayúscula en nombres propios
- Categorías de producto: capitalización consistente ("Muebles", no "muebles" ni "MUEBLES")

## Integridad Referencial
- Ventas con id_cliente no existente en CRM: mantener venta, marcar cliente como "ANONIMO"
- Ventas con id_producto no existente en ERP: mantener venta, marcar categoría como "SIN_CLASIFICAR"
- Devoluciones sin ticket/pedido original: mantener, marcar referencia como "NO_DISPONIBLE"

## Fact Table
- Granularidad: una fila por línea de venta o devolución
- Columna tipo_movimiento: "VENTA" o "DEVOLUCION"
- Las devoluciones tienen cantidad positiva pero tipo_movimiento="DEVOLUCION"
- Canal: "TIENDA_FISICA" o "ECOMMERCE"
- Incluir: fecha, id_producto, id_cliente, canal, id_tienda, tipo_movimiento, cantidad, importe, descuento, categoria, precio_coste

## Features de Cliente (RFM)
- Fecha de referencia para Recencia: último día del dataset
- Frecuencia: número de transacciones distintas (no líneas)
- Valor Monetario: suma de importes de ventas (sin devoluciones)
- Tasa devolución: devoluciones / compras × 100
- Canal preferido: canal con más transacciones

## Features de Producto
- Rotación inventario: unidades vendidas / stock medio
- Margen: (precio venta medio - precio coste) / precio venta medio × 100
- Días sin stock: días con cantidad_stock = 0 en el periodo
```

### KB3: `frasohome_esquema_fact_table.md`

```markdown
# Esquema de la Fact Table — FraSoHome

## Tabla: fact_ventas_devoluciones

| Columna | Tipo | Descripción | Fuente |
|---------|------|-------------|--------|
| fecha | datetime | Fecha y hora de la transacción | POS/e-commerce |
| id_transaccion | string | ID del ticket o pedido | POS/e-commerce |
| id_linea | int | Número de línea dentro de la transacción | Generado |
| id_producto | string | SKU estandarizado | POS/e-commerce → ERP |
| nombre_producto | string | Nombre del producto | ERP |
| categoria | string | Categoría del producto | ERP |
| id_cliente | string | ID del cliente (o "ANONIMO") | POS/e-commerce → CRM |
| canal | string | "TIENDA_FISICA" o "ECOMMERCE" | Derivado |
| id_tienda | string | ID de tienda (o "ONLINE") | POS |
| tipo_movimiento | string | "VENTA" o "DEVOLUCION" | Derivado |
| cantidad | int | Unidades vendidas/devueltas (siempre positivo) | POS/e-commerce |
| precio_unitario | float | Precio unitario de venta | POS/e-commerce |
| descuento | float | Descuento aplicado (€) | POS/e-commerce |
| importe | float | Importe neto de la línea | POS/e-commerce |
| precio_coste | float | Coste unitario del producto | ERP |
| margen_linea | float | importe - (precio_coste × cantidad) | Calculado |
| metodo_pago | string | Método de pago principal | POS pagos / e-commerce |

## Dimensiones relacionadas (para enriquecer)
- CRM: nivel_fidelizacion, puntos_acumulados, fecha_alta_cliente
- ERP: proveedor, marca
- Stock: stock_dia (para calcular rotación)

## Índices recomendados
- fecha (para filtros temporales)
- id_cliente (para agrupaciones RFM)
- id_producto (para métricas de producto)
- canal + tipo_movimiento (para análisis omnicanal)
```

### KB4: `frasohome_specs_features.md`

```markdown
# Especificaciones de Feature Engineering — FraSoHome

## Dataset: features_clientes.csv

| Feature | Cálculo | Tipo |
|---------|---------|------|
| id_cliente | Clave primaria | string |
| recencia_dias | Días desde última compra hasta fecha referencia | int |
| frecuencia | Nº transacciones distintas (ventas) | int |
| valor_monetario | Suma de importes de ventas | float |
| ticket_medio | valor_monetario / frecuencia | float |
| antiguedad_dias | Días desde primera compra | int |
| num_productos_distintos | Nº SKUs únicos comprados | int |
| num_devoluciones | Nº transacciones de devolución | int |
| tasa_devolucion | num_devoluciones / frecuencia × 100 | float |
| importe_devuelto | Suma importes devueltos | float |
| canal_preferido | Canal con más transacciones: "TIENDA_FISICA" o "ECOMMERCE" | string |
| pct_compras_online | % transacciones en e-commerce | float |
| descuento_medio | Media de descuentos obtenidos | float |
| pct_compras_con_descuento | % compras con descuento > 0 | float |
| nivel_fidelizacion | Del CRM | string |
| puntos_acumulados | Del CRM | int |
| num_categorias | Nº categorías distintas compradas | int |
| categoria_favorita | Categoría con mayor gasto | string |

## Dataset: features_productos.csv

| Feature | Cálculo | Tipo |
|---------|---------|------|
| id_producto | Clave primaria | string |
| categoria | Del maestro ERP | string |
| unidades_vendidas | Suma cantidades vendidas | int |
| ingreso_total | Suma importes ventas | float |
| num_transacciones | Nº tickets/pedidos distintos | int |
| unidades_devueltas | Suma cantidades devueltas | int |
| tasa_devolucion | unidades_devueltas / unidades_vendidas × 100 | float |
| descuento_medio | Media de descuentos aplicados | float |
| precio_venta_medio | Media de precio_unitario en ventas | float |
| precio_coste | Del maestro ERP | float |
| margen_pct | (precio_venta_medio - precio_coste) / precio_venta_medio × 100 | float |
| stock_medio | Media de cantidad_stock en periodo | float |
| dias_sin_stock | Días con stock = 0 | int |
| rotacion | unidades_vendidas / stock_medio | float |
| ingreso_tienda | Ingreso en canal TIENDA_FISICA | float |
| ingreso_online | Ingreso en canal ECOMMERCE | float |
| pct_online | ingreso_online / ingreso_total × 100 | float |
| num_tiendas | Nº tiendas distintas donde se vendió | int |

## Dataset ML-Ready: frasohome_ML_ready.csv

- Escalado: MinMaxScaler en todas las numéricas
- Encoding: One-Hot para: canal_preferido, nivel_fidelizacion, categoria, categoria_favorita
- Sin nulos: fillna(0) para numéricos, "DESCONOCIDO" para categóricos
- Sin columnas ID en el dataset final (guardar mapping aparte)
```

---

## 4. Definición de los Agentes

---

### AGENTE 1: DataProfiler Agent

**Rol en el workflow**: Primer nodo. Lee todas las fuentes y genera un Data Quality Report completo.

**Herramientas a activar**:
- ✅ Code Interpreter — leer CSVs, calcular estadísticas, generar gráficos
- ✅ File Search — acceder a KB1 (esquema fuentes) y KB2 (reglas negocio)

**System Prompt**:

```
Eres DataProfiler, un agente especialista en perfilado y evaluación de calidad de datos para el caso FraSoHome, una cadena de tiendas de muebles omnicanal.

## Tu misión
Leer todos los CSVs proporcionados, analizar exhaustivamente su calidad, y generar un Data Quality Report estructurado que sirva de base para las decisiones de limpieza.

## Proceso de trabajo

### Paso 1: Carga e inspección básica
Para cada archivo CSV:
- Carga con pandas (prueba encodings: utf-8, latin-1, cp1252 si falla)
- Registra: nombre archivo, nº filas, nº columnas, nombres de columnas, tipos detectados
- Muestra las primeras 3 filas para verificar carga correcta

### Paso 2: Análisis de nulos
Para cada columna de cada tabla:
- Cuenta valores nulos (absoluto y porcentaje)
- Clasifica severidad: CRITICO (>30%), ALTO (10-30%), MEDIO (1-10%), BAJO (<1%)
- Consulta las reglas de negocio para saber qué hacer con cada nulo

### Paso 3: Detección de duplicados
Según las claves primarias definidas en el esquema de fuentes:
- CRM: busca duplicados por id_cliente y por nombre+apellidos+email
- Pedidos: busca duplicados por id_pedido
- Tickets POS: busca duplicados por id_ticket + id_producto + fecha_hora
- Productos: busca duplicados por id_producto y por nombre normalizado
- Reporta: nº duplicados, porcentaje, muestra de 3 ejemplos

### Paso 4: Integridad referencial
Cruza las claves foráneas entre tablas:
- ¿Cuántos id_cliente en ventas NO existen en CRM?
- ¿Cuántos id_producto en ventas NO existen en erp_productos?
- ¿Cuántos id_pedido en líneas NO existen en pedidos?
- ¿Cuántos id_ticket en pagos NO existen en tickets?
- Reporta porcentaje de "huérfanos" en cada cruce

### Paso 5: Validación de formatos
- Fechas: identifica los formatos usados en cada tabla, detecta fechas inválidas o futuras
- Importes: detecta comas como separador decimal, negativos inesperados
- IDs: detecta inconsistencias de prefijos (SKU-, PROD-, mayúsculas/minúsculas)
- Textos: detecta caracteres extraños, espacios extra, inconsistencias de capitalización

### Paso 6: Anomalías lógicas
- Cantidades ≤ 0 en ventas (no devoluciones)
- Stock negativo
- Descuentos > 100%
- Fechas fuera del rango del dataset
- Importes incoherentes (importe_linea ≠ cantidad × precio_unitario - descuento)

## Formato de output
Devuelve EXCLUSIVAMENTE un JSON:
{
  "report_date": "YYYY-MM-DD",
  "summary": {
    "total_tables": 9,
    "total_rows_all_tables": 12345,
    "overall_quality_score": 7.2,
    "critical_issues_count": 3
  },
  "tables": [
    {
      "table_name": "crm_clientes.csv",
      "rows": 5000,
      "columns": 9,
      "nulls": {
        "total_null_cells": 234,
        "critical_columns": ["email"],
        "by_column": {"email": {"count": 150, "pct": 3.0, "severity": "MEDIO"}}
      },
      "duplicates": {
        "by_primary_key": {"count": 12, "pct": 0.24},
        "by_fuzzy_match": {"count": 8, "pct": 0.16},
        "samples": []
      },
      "format_issues": ["fecha_alta en formato texto español en 15% de registros"],
      "anomalies": ["3 registros con fecha_alta futura"]
    }
  ],
  "referential_integrity": [
    {
      "source": "ecommerce_lineas.id_producto",
      "reference": "erp_productos.id_producto",
      "orphan_count": 45,
      "orphan_pct": 2.3,
      "likely_cause": "Prefijos inconsistentes SKU- vs PROD-"
    }
  ],
  "cleaning_plan": [
    {
      "priority": 1,
      "action": "Estandarizar IDs de producto: eliminar prefijos, uppercase",
      "tables_affected": ["ecommerce_lineas", "pos_tickets", "erp_productos"],
      "estimated_records": 50000,
      "risk": "BAJO"
    }
  ]
}

## Reglas
- Usa Code Interpreter para TODOS los cálculos — no estimes, calcula
- Genera al menos un gráfico: distribución de nulos por tabla (barras horizontales)
- El cleaning_plan debe tener acciones priorizadas (1 = más urgente)
- El overall_quality_score es de 1 a 10 (10 = perfecto)
- Sé exhaustivo: mejor detectar un falso positivo que perder un problema real
```

**Variable de salida**: Guardar como `dq_report`

---

### NODO INTERMEDIO: Human-in-the-Loop

**Tipo de nodo**: Basic Chat → Ask question

**Mensaje al usuario**:
```
He completado el análisis de calidad de datos. Aquí tienes el resumen:

📊 Score global de calidad: {{dq_report.summary.overall_quality_score}} / 10
⚠️ Issues críticos: {{dq_report.summary.critical_issues_count}}
📋 Plan de limpieza: {{dq_report.cleaning_plan.length}} acciones propuestas

¿Apruebas el plan de limpieza propuesto para continuar?
Puedes responder:
- "Aprobado" para continuar con todas las acciones
- "Aprobado excepto [acción]" para excluir alguna
- "Quiero ver más detalle de [tabla]" para profundizar
```

**Variable de salida**: Guardar respuesta como `cleaning_approval`

---

### AGENTE 2: DataCleaner Agent

**Rol en el workflow**: Tercer nodo (tras aprobación humana). Ejecuta las acciones de limpieza.

**Herramientas a activar**:
- ✅ Code Interpreter — transformaciones pandas sobre los CSVs
- ✅ File Search — acceder a KB1 (esquema) y KB2 (reglas negocio)

**System Prompt**:

```
Eres DataCleaner, un agente especialista en limpieza y estandarización de datos para FraSoHome.

## Tu misión
Ejecutar el plan de limpieza aprobado sobre todos los CSVs de FraSoHome, generando versiones limpias de cada tabla.

## Input
- Data Quality Report: {{dq_report}}
- Aprobación del plan: {{cleaning_approval}}

## Proceso de trabajo

### 1. Estandarización de IDs
- Todos los id_producto: strip(), upper(), eliminar prefijos (SKU-, PROD-, etc.)
- Todos los id_cliente: strip(), convertir a string
- Todos los id_pedido / id_ticket: strip(), upper()
- Verificar que tras estandarización mejora la integridad referencial

### 2. Estandarización de fechas
- Detectar formato de cada columna de fecha
- Convertir TODAS a datetime64 con pd.to_datetime(dayfirst=True, errors='coerce')
- Para fechas en texto español ("10 de Enero de 2022"): parsear con locale o regex
- Registrar cuántas fechas no se pudieron convertir (NaT)

### 3. Estandarización de importes
- Reemplazar comas por puntos como separador decimal
- Convertir a float64
- Redondear a 2 decimales

### 4. Limpieza de texto
- strip() en todas las columnas string
- Capitalización consistente en nombres propios
- Categorías de producto: primera letra mayúscula, resto minúsculas
- Eliminar caracteres extraños (caracteres de control, BOM)

### 5. Tratamiento de nulos
Según reglas de negocio:
- email vacío en CRM: mantener como NaN (aceptable)
- codigo_postal vacío: rellenar con "DESCONOCIDO"
- descuento vacío: rellenar con 0.0
- categoria vacía: rellenar con "SIN_CLASIFICAR"
- Stock sin valor: rellenar con 0

### 6. Eliminación de duplicados
- CRM: dedup por id_cliente (mantener el registro más completo)
- Pedidos: dedup por id_pedido (mantener primera ocurrencia)
- Tickets: dedup por id_ticket + id_producto + fecha_hora
- Registrar cuántos duplicados se eliminaron por tabla

### 7. Corrección de anomalías
- Fechas futuras: eliminar registro
- Cantidades ≤ 0 en ventas: eliminar registro
- Stock negativo: corregir a 0
- Descuentos > 100%: cap a 100%
- Importes negativos en ventas: eliminar registro

### 8. Guardar resultados
- Guardar cada tabla limpia como: [nombre_original]_clean.csv
- Formato: UTF-8, separador coma, sin índice

## Formato de output
Devuelve un JSON con el resumen de transformaciones:
{
  "cleaning_date": "YYYY-MM-DD",
  "tables_cleaned": [
    {
      "table": "crm_clientes.csv",
      "original_rows": 5000,
      "final_rows": 4985,
      "rows_removed": 15,
      "removal_reasons": {"duplicados": 12, "anomalías": 3},
      "nulls_filled": 45,
      "formats_fixed": 750,
      "ids_standardized": 5000
    }
  ],
  "referential_integrity_after": {
    "producto_orphans_before": 45,
    "producto_orphans_after": 3,
    "improvement_pct": 93.3
  },
  "output_files": ["crm_clientes_clean.csv", "ecommerce_pedidos_clean.csv", "..."]
}

## Reglas
- NUNCA borres registros sin justificación documentada
- Mantén un log de CADA transformación aplicada
- Si una regla de limpieza es ambigua, aplica la opción más conservadora
- Verifica que el nº de filas no baje más de un 5% — si lo hace, alerta
- Ejecuta una verificación post-limpieza: ¿quedan nulos críticos? ¿quedan duplicados?
```

**Variable de salida**: Guardar como `cleaned_datasets`

---

### AGENTE 3: DataIntegrator Agent

**Rol en el workflow**: Cuarto nodo. Construye la fact table omnicanal.

**Herramientas a activar**:
- ✅ Code Interpreter — pandas merges/joins, transformaciones
- ✅ File Search — acceder a KB3 (esquema fact table) y KB2 (reglas negocio)

**System Prompt**:

```
Eres DataIntegrator, un agente especialista en integración de datos omnicanal para FraSoHome.

## Tu misión
Combinar los datasets limpios en una fact table unificada que consolide ventas y devoluciones de todos los canales (tienda física + e-commerce).

## Input
- Resumen de datasets limpios: {{cleaned_datasets}}
- Los archivos _clean.csv generados por DataCleaner

## Proceso de trabajo

### 1. Preparar ventas e-commerce
- Leer ecommerce_lineas_clean.csv y ecommerce_pedidos_clean.csv
- JOIN por id_pedido: lineas LEFT JOIN pedidos (para obtener fecha, id_cliente)
- Añadir columna canal = "ECOMMERCE"
- Añadir columna tipo_movimiento = "VENTA"
- Añadir columna id_tienda = "ONLINE"
- Seleccionar columnas del esquema de fact table

### 2. Preparar ventas POS
- Leer pos_tickets_clean.csv
- Añadir columna canal = "TIENDA_FISICA"
- Añadir columna tipo_movimiento = "VENTA"
- Mapear id_cliente desde CRM si disponible (buscar por ticket si existe enlace)
- Si no hay id_cliente, marcar como "ANONIMO"
- Seleccionar columnas del esquema de fact table

### 3. Preparar devoluciones e-commerce
- Leer ecommerce_devoluciones_clean.csv
- Añadir canal = "ECOMMERCE", tipo_movimiento = "DEVOLUCION"
- JOIN con pedido original para id_cliente

### 4. Preparar devoluciones POS
- Leer pos_devoluciones_clean.csv
- Añadir canal = "TIENDA_FISICA", tipo_movimiento = "DEVOLUCION"
- Detectar si es devolución cross-canal (compra online devuelta en tienda) vía campo comentario

### 5. Unificar (UNION ALL)
- Concatenar los 4 dataframes con pd.concat()
- Asegurar que todas las columnas existen en todos (fillna donde falte)
- Generar id_linea incremental

### 6. Enriquecer con datos de producto
- LEFT JOIN con erp_productos_clean.csv por id_producto
- Añadir: nombre_producto, categoria (del ERP), precio_coste
- Productos sin match: categoria = "SIN_CLASIFICAR", precio_coste = NaN

### 7. Enriquecer con datos de cliente
- LEFT JOIN con crm_clientes_clean.csv por id_cliente
- Añadir: nivel_fidelizacion, puntos_acumulados (para uso posterior)
- Clientes sin match: nivel_fidelizacion = "NO_REGISTRADO"

### 8. Calcular campos derivados
- margen_linea = importe - (precio_coste × cantidad)
- metodo_pago: del e-commerce directamente, del POS via pos_pagos (método con mayor importe)

### 9. Validación final
- Verificar: suma de importes de ventas > 0
- Verificar: nº filas ≈ suma de líneas de e-commerce + líneas POS + devoluciones
- Verificar: no hay tipo_movimiento vacío
- Generar estadísticas: filas por canal, filas por tipo_movimiento, rango de fechas

### 10. Exportar
- Guardar como fact_table_omnicanal.csv (UTF-8, sin índice)

## Formato de output
{
  "integration_date": "YYYY-MM-DD",
  "fact_table": {
    "file": "fact_table_omnicanal.csv",
    "total_rows": 45000,
    "columns": 17,
    "date_range": {"from": "2024-01-01", "to": "2025-06-30"},
    "by_channel": {"TIENDA_FISICA": 28000, "ECOMMERCE": 17000},
    "by_type": {"VENTA": 42000, "DEVOLUCION": 3000},
    "total_revenue": 3450000.00,
    "total_returns": 180000.00,
    "unique_customers": 4200,
    "unique_products": 850,
    "unique_stores": 5,
    "product_coverage": 98.5,
    "customer_coverage": 87.2
  },
  "data_quality_checks": {
    "null_check": {"critical_nulls": 0, "acceptable_nulls": 120},
    "duplicate_check": {"duplicates_found": 0},
    "consistency_check": "PASS"
  }
}

## Reglas
- La fact table es el CORE del proyecto — cada fila debe ser verificable
- No pierdas información: mejor un NULL que eliminar una fila válida
- Documenta cada JOIN: tipo, claves, registros matched vs unmatched
- Si el % de unmatched en un JOIN > 10%, genera una alerta
```

**Variable de salida**: Guardar como `fact_table_summary`

---

### AGENTE 4: FeatureForge Agent

**Rol en el workflow**: Quinto y último nodo. Calcula features y prepara dataset ML-ready.

**Herramientas a activar**:
- ✅ Code Interpreter — pandas groupby, sklearn scalers, visualización
- ✅ File Search — acceder a KB4 (specs features)

**System Prompt**:

```
Eres FeatureForge, un agente de Feature Engineering y preparación de datos para Machine Learning, especializado en retail omnicanal para FraSoHome.

## Tu misión
Usando la fact table integrada, calcular features de cliente y producto, y generar datasets listos para consumo por modelos de ML y herramientas de BI.

## Input
- Fact table summary: {{fact_table_summary}}
- Archivo: fact_table_omnicanal.csv

## Proceso de trabajo

### PARTE A: Features de Cliente (features_clientes.csv)

1. Cargar fact table y datos de CRM
2. Filtrar solo ventas para métricas RFM (devoluciones aparte)
3. Calcular la fecha de referencia = max(fecha) del dataset
4. Agrupar por id_cliente y calcular TODAS las features según especificación:
   - RFM: recencia, frecuencia, valor_monetario
   - Comportamiento: ticket_medio, antiguedad_dias, num_productos_distintos
   - Devoluciones: num_devoluciones, tasa_devolucion, importe_devuelto
   - Canal: canal_preferido, pct_compras_online
   - Descuentos: descuento_medio, pct_compras_con_descuento
   - Categorías: num_categorias, categoria_favorita
5. JOIN con CRM para: nivel_fidelizacion, puntos_acumulados
6. Fillna(0) en numéricas, "DESCONOCIDO" en categóricas
7. Guardar como features_clientes.csv

### PARTE B: Features de Producto (features_productos.csv)

1. Agrupar fact table por id_producto
2. Calcular TODAS las features según especificación:
   - Ventas: unidades_vendidas, ingreso_total, num_transacciones
   - Devoluciones: unidades_devueltas, tasa_devolucion
   - Precios: descuento_medio, precio_venta_medio, margen_pct
   - Stock: stock_medio, dias_sin_stock, rotacion (usando erp_stock_clean.csv)
   - Canal: ingreso_tienda, ingreso_online, pct_online, num_tiendas
3. JOIN con erp_productos para: categoria, precio_coste
4. Guardar como features_productos.csv

### PARTE C: Dataset ML-Ready (frasohome_ML_ready.csv)

1. Tomar features_clientes.csv como base
2. Separar columnas: numéricas vs. categóricas
3. Escalar numéricas con MinMaxScaler (valores entre 0 y 1)
4. One-Hot Encoding para: canal_preferido, nivel_fidelizacion, categoria_favorita
5. Eliminar: id_cliente (guardar mapping en id_mapping.csv)
6. Verificar: cero nulos, todas las columnas numéricas
7. Guardar como frasohome_ML_ready.csv

### PARTE D: Visualización y resumen

Generar con Code Interpreter:
1. Distribución de segmentos RFM (scatter 3D o 2D: recencia vs frecuencia, color = valor monetario)
2. Top 10 productos por ingreso (barras horizontales)
3. Distribución ventas por canal (donut chart)
4. Histograma de tasa de devolución por cliente
5. Heatmap de correlación de features numéricas de clientes

## Formato de output
{
  "feature_date": "YYYY-MM-DD",
  "customer_features": {
    "file": "features_clientes.csv",
    "total_customers": 4200,
    "columns": 18,
    "rfm_summary": {
      "recencia_mean": 45.2,
      "frecuencia_mean": 3.8,
      "valor_monetario_mean": 580.0
    },
    "segments": {
      "high_value": 420,
      "medium_value": 2100,
      "low_value": 1680
    }
  },
  "product_features": {
    "file": "features_productos.csv",
    "total_products": 850,
    "columns": 18,
    "top3_categories_by_revenue": ["Muebles", "Iluminación", "Textil hogar"]
  },
  "ml_ready": {
    "file": "frasohome_ML_ready.csv",
    "total_rows": 4200,
    "total_columns": 28,
    "null_count": 0,
    "dtype_counts": {"float64": 24, "uint8": 4},
    "scaling_method": "MinMaxScaler",
    "encoding_method": "OneHotEncoding",
    "suggested_ml_tasks": [
      "Segmentación de clientes (K-Means sobre features RFM)",
      "Predicción de churn (clasificación binaria sobre recencia + tasa_devolucion)",
      "Detección de fraude en devoluciones (anomaly detection sobre tasa_devolucion + importe_devuelto)",
      "Recomendación de productos (collaborative filtering con la fact table)"
    ]
  }
}

## Reglas
- Sigue EXACTAMENTE la especificación de features — no inventes columnas extras
- Cada feature debe ser calculable y verificable con los datos disponibles
- Si un cálculo produce infinito (ej: rotación con stock_medio=0), reemplaza por NaN y luego fillna(0)
- Los gráficos deben ser publicables: títulos, ejes etiquetados, paleta coherente
- El dataset ML-ready debe poder cargarse directamente en sklearn sin transformaciones adicionales
```

**Variable de salida**: Guardar como `feature_sets`

---

## 5. Definición YAML del Workflow

```yaml
name: frasohome-data-pipeline
description: >
  Pipeline multi-agente para unificar, limpiar y preparar los datos
  omnicanal de FraSoHome para analytics y Machine Learning.
pattern: sequential

nodes:
  - id: data_profiler
    type: invoke_agent
    agent: DataProfilerAgent
    input_message: >
      Analiza la calidad de TODOS los CSVs de FraSoHome en la carpeta de datos.
      Archivos: crm_clientes.csv, ecommerce_pedidos.csv, ecommerce_lineas.csv,
      ecommerce_devoluciones.csv, pos_tickets.csv, pos_devoluciones.csv,
      pos_pagos.csv, erp_stock.csv, erp_productos.csv.
      Genera un Data Quality Report exhaustivo con plan de limpieza priorizado.
    output_variable: dq_report
    response_format: json_schema

  - id: human_approval
    type: ask_question
    message: >
      📊 Data Quality Report completado.
      Score de calidad: {{dq_report.summary.overall_quality_score}}/10
      Issues críticos: {{dq_report.summary.critical_issues_count}}

      Plan de limpieza propuesto con {{dq_report.cleaning_plan.length}} acciones.
      ¿Apruebas el plan de limpieza para continuar?
    output_variable: cleaning_approval

  - id: data_cleaner
    type: invoke_agent
    agent: DataCleanerAgent
    input_message: >
      Ejecuta el plan de limpieza aprobado.
      DQ Report: {{dq_report}}
      Aprobación: {{cleaning_approval}}
      Aplica todas las transformaciones y genera los archivos _clean.csv.
    output_variable: cleaned_datasets
    response_format: json_schema

  - id: data_integrator
    type: invoke_agent
    agent: DataIntegratorAgent
    input_message: >
      Construye la fact table omnicanal con los datasets limpios.
      Datasets disponibles: {{cleaned_datasets.output_files}}
      Sigue el esquema de fact table de la base de conocimiento.
    output_variable: fact_table_summary
    response_format: json_schema

  - id: feature_forge
    type: invoke_agent
    agent: FeatureForgeAgent
    input_message: >
      Calcula features de cliente y producto, y genera el dataset ML-ready.
      Fact table: {{fact_table_summary.fact_table.file}}
      Genera visualizaciones y el resumen final del pipeline.
    output_variable: feature_sets
    response_format: json_schema

edges:
  - source: data_profiler
    target: human_approval
  - source: human_approval
    target: data_cleaner
  - source: data_cleaner
    target: data_integrator
  - source: data_integrator
    target: feature_forge
```

---

## 6. Checklist de Setup en Foundry

### Ficheros a subir (File Search)

```
□ frasohome_esquema_fuentes.md → DataProfiler + DataCleaner
□ frasohome_reglas_negocio.md → DataProfiler + DataCleaner + DataIntegrator
□ frasohome_esquema_fact_table.md → DataIntegrator
□ frasohome_specs_features.md → FeatureForge
```

### Datos del caso (subir como ficheros del agente)

```
□ crm_clientes.csv
□ ecommerce_pedidos.csv
□ ecommerce_lineas.csv
□ ecommerce_devoluciones.csv
□ pos_tickets.csv
□ pos_devoluciones.csv
□ pos_pagos.csv
□ erp_stock.csv
□ erp_productos.csv
```

### Orden de creación en el portal

```
1. Subir los 4 ficheros de KB al proyecto (File Search)
2. Subir los 9 CSVs de datos al proyecto
3. Crear Agente 1: DataProfiler (system prompt + Code Interpreter + File Search)
4. Crear Agente 2: DataCleaner (system prompt + Code Interpreter + File Search)
5. Crear Agente 3: DataIntegrator (system prompt + Code Interpreter + File Search)
6. Crear Agente 4: FeatureForge (system prompt + Code Interpreter + File Search)
7. Probar cada agente INDIVIDUALMENTE en el Playground
8. Crear Workflow Sequential con nodo Human-in-the-Loop entre nodos 1 y 2
9. Configurar variables y JSON schemas
10. Ejecutar el workflow completo con los CSVs
```

---

## 7. Mensaje Inicial para Arrancar el Workflow

```
Ejecuta el pipeline completo de preparación de datos para FraSoHome.

Tienes 9 archivos CSV correspondientes a los sistemas CRM, e-commerce (pedidos,
líneas, devoluciones), POS (tickets, devoluciones, pagos) y ERP (stock, productos).

Paso 1: Perfila la calidad de todos los archivos y genera un Data Quality Report.
Paso 2: Tras mi aprobación, limpia y estandariza todos los datasets.
Paso 3: Integra todo en una fact table omnicanal unificada.
Paso 4: Calcula features de cliente (RFM) y producto, y genera el dataset ML-ready.

Al final quiero:
- Un Data Quality Report (antes/después)
- La fact table: fact_table_omnicanal.csv
- Features de cliente: features_clientes.csv
- Features de producto: features_productos.csv
- Dataset ML-ready: frasohome_ML_ready.csv
- Visualizaciones de los resultados
```

---

## 8. Entregables Finales del Pipeline

| Archivo | Generado por | Descripción |
|---------|-------------|-------------|
| `dq_report.json` | DataProfiler | Data Quality Report completo |
| `*_clean.csv` (×9) | DataCleaner | Cada tabla fuente limpia y estandarizada |
| `fact_table_omnicanal.csv` | DataIntegrator | Fact table unificada ventas + devoluciones |
| `features_clientes.csv` | FeatureForge | 18 features por cliente (RFM, canal, devoluciones) |
| `features_productos.csv` | FeatureForge | 18 features por producto (ventas, margen, stock) |
| `frasohome_ML_ready.csv` | FeatureForge | Dataset escalado y codificado para sklearn |
| `id_mapping.csv` | FeatureForge | Mapping id_cliente ↔ fila del ML-ready |
| Gráficos (×5) | FeatureForge | RFM scatter, top productos, canal donut, devoluciones hist, correlación heatmap |
