# FraSoHome_Fabric_IntroDeck

## Slide 1: FraSoHome

- Demo de Microsoft Fabric
- Analítica end-to-end en una única plataforma: OneLake, Lakehouse, SQL, Power BI, ML y tiempo real
- Data Factory
- OneLake
- Warehouse
- Power BI
- FraSoHome · Intro de la demo (≈40 min)

## Slide 2: Objetivo de la sesión

En 40 minutos, veremos cómo Fabric habilita una plataforma de datos moderna para FraSoHome (retail omnicanal).

- 1
- Resultado primero: KPIs y exploración en Power BI (Direct Lake)
- 2
- Arquitectura: OneLake + Lakehouse (Bronze/Silver/Gold) + SQL/WH
- 3
- Ciclo completo: ingesta, calidad, modelado, scoring y gobierno
- 4
- Tiempo real: eventstream + KQL + alertas (Activator)
- Qué te llevas
- Una referencia de arquitectura
- Un caso retail “end-to-end”
- Qué se puede operar y gobernar
- Cómo escalar a producción
- Duración
- ≈ 40 min
- Con Q&A al final
- FraSoHome · Demo Microsoft Fabric

## Slide 3: Microsoft Fabric, en 60 segundos

Plataforma SaaS de analítica end-to-end (ingesta → transformación → BI/ML → acción).

Un solo lago lógico: OneLake, compartido por todas las experiencias.

Múltiples motores (Spark, T-SQL, KQL, Analysis Services) sobre el mismo dato.

Gobierno y ciclo de vida: linaje, control de cambios, promoción entre entornos.

- Experiencias integradas sobre una base común (OneLake + gobierno)
- FraSoHome · Demo Microsoft Fabric

## Slide 4: Capacidades clave (qué cubre Fabric)

Una sola plataforma para equipos de datos y negocio: low-code, pro-code, SQL y BI.

- Data Factory (ingesta y orquestación)
Pipelines, Dataflows Gen2 y conectores. Programación, dependencias y observabilidad.

- ⧉
- Data Engineering (Lakehouse + Spark)
Notebooks, tablas Delta, calidad de datos y patrón Medallion (Bronze/Silver/Gold).

- Data Warehouse (T‑SQL)
Modelo estrella, vistas de negocio, alto rendimiento SQL y endpoints compartidos.

- Power BI (Direct Lake)
Modelo semántico + informes. Rendimiento interactivo sobre OneLake/Delta.

- ⚗
- Data Science (MLflow)
Experiment tracking, scoring y publicación de predicciones para BI.

- ⚡
- Real‑Time Intelligence (KQL)
Eventstreams, KQL DB, dashboards en tiempo real y alertas con Activator.

Todo se apoya en OneLake: un espacio de nombres común para datos y artefactos analíticos.

- FraSoHome · Demo Microsoft Fabric

## Slide 5: El caso FraSoHome (retail omnicanal)

Objetivo: unificar datos de CRM, eCommerce, POS y stock para decidir mejor (y más rápido).

- Situación actual
- Datos en silos por canal
- Calidad irregular (nulos/duplicados)
- Cierres de reporting lentos
- Difícil trazar “de dónde sale el KPI”
- Preguntas de negocio
- ¿Qué categorías tienen más devoluciones?
- ¿Qué tiendas y productos pierden margen?
- ¿Qué clientes tienen riesgo de churn?
- ¿Dónde habrá rotura de stock?
- Resultados esperados
- Cuadro de mando ejecutivo (Direct Lake)
- Vista 360º cliente y omnicanal
- Scoring churn/propensión integrado
- Alertas en tiempo real (devolución/stock)
- FraSoHome · Demo Microsoft Fabric

## Slide 6: Arquitectura demo (referencia)

Patrón Medallion en Lakehouse + consumo por SQL/Warehouse y Power BI (Direct Lake).

- Fuentes
- CRM
- eCommerce
- POS
- Stock/ERP
- Pagos
- Devoluciones
- Data Factory
- Pipelines
- Dataflows Gen2
- Scheduling
- Run history
- Lakehouse (OneLake)
- Bronze
- Raw (CSV) / landing
- Silver
- Delta limpio + estándares
- Gold
- Modelo curado + features
- Notebooks (Spark) + reglas de calidad
- → Tablas Delta consumibles por SQL/BI/ML
- Consumo
- Warehouse / SQL
- Power BI
- (Direct Lake)
- ⚗
- ML / Scoring
- ⚡
- Tiempo real
- (KQL + alertas)
→ Un KPI en BI puede trazarse hasta una tabla Delta “Gold”.

- FraSoHome · Demo Microsoft Fabric

## Slide 7: OneLake + Shortcuts: unificación sin mover ni duplicar datos

Idea clave: OneLake aporta un “namespace” común; Shortcuts conectan fuentes sin ETL de copia.

En la demo: usaremos OneLake para BI/SQL/ML y un stream para alertas (KQL + Activator).


## Slide 8: Lo que verás en la demo (≈40 min)

- Power BI
- (Direct Lake)
- 0–7
- Linaje
- + OneLake
- 7–12
- Data Factory
- (pipelines)
- 12–18
- Lakehouse
- (B/S/G)
- 18–28
- SQL/WH
- + Vistas
- 28–32
- ML + RTI
- (Activator)
- 32–40
- Qué demostramos (mensajes comerciales)
- Menos “pegamento” entre herramientas: todo en un mismo workspace
- Un solo dato (OneLake) para Spark, SQL y BI
- Rendimiento y agilidad: Direct Lake + SQL endpoint
- De insight a acción: streaming + alertas
- Operable: linaje y CI/CD
- Artefactos que veremos
- Lakehouse (Files + Tables)
- Notebooks (ingesta, calidad, features, scoring)
- Pipelines + run history
- SQL endpoint + Warehouse
- Modelo semántico + Report
- Eventstream + KQL DB + Activator
- FraSoHome · Demo Microsoft Fabric

## Slide 9: ¿Por qué Fabric para FraSoHome?

Los mismos datos habilitan reporting, ciencia de datos y operación (en tiempo real), con gobierno y ciclo de vida.

- Beneficios esperados
- Time-to-insight menor (menos integración entre herramientas)
- Una versión “confiable” del dato (calidad + linaje)
- Escalabilidad y rendimiento (Spark + SQL + Direct Lake)
- Casos avanzados sin mover datos (ML y tiempo real)
- Operación enterprise: CI/CD, seguridad y gobernanza
Siguiente paso sugerido: workshop de 2–3h con tus fuentes reales y KPIs prioritarios.

- Checklist de plataforma (lo que suele pedir IT)
- Seguridad y roles (workspace + datos)
- Linaje y auditoría
- Integración con Purview (catálogo/linaje)
- Git + deployment pipelines
- Cost management por capacidad
- Estrategia de modelos (Direct Lake / DirectQuery fallback)
- Gracias · Preguntas
