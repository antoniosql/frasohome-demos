# La historia de FraSoHome

FraSoHome nació en 2015 como tienda online con un almacén en Madrid. En 2016 abrió su primera tienda física en la Gran Vía y, en cinco años, llegó a Barcelona, Valencia, Sevilla y Bilbao. Hoy vende muebles, iluminación, textil y decoración a un público generalista, tiene un programa de fidelización con niveles y puntos, lanza campañas por email, app y tienda, y prepara su apertura en Málaga.

Creció deprisa, y cada área compró o construyó el sistema que necesitaba en cada momento. El resultado es conocido: **la empresa tiene datos de todo, pero no consigue contestar con seguridad preguntas sencillas**. ¿Cuánto vendimos realmente el mes pasado, descontando devoluciones? ¿Quiénes son nuestros mejores clientes si compran en tienda y online? ¿Por qué se nos va la gente de logística? ¿Qué dice la política de devoluciones vigente, y no la del año pasado?

Esta es la historia de cómo FraSoHome pasa de los silos a una empresa que decide con datos y usa IA con criterio. Cada capítulo se apoya en uno o varios [escenarios de demo](../escenarios/README.md).

## Capítulo 1 · Una empresa con datos pero sin visión única

Marketing dice que la campaña de primavera fue un éxito; finanzas no ve el impacto en el margen. Tienda y ecommerce cuentan las devoluciones de forma distinta. El CRM tiene clientes duplicados, el TPV registra la mitad de las ventas sin cliente y el maestro de productos no coincide con lo que se vende. La dirección pide **una vista única del negocio**.

→ [Escenario 01 · La empresa con silos](../escenarios/01-empresa-con-silos/README.md)

## Capítulo 2 · Poner orden en los datos

El equipo de datos aterriza las fuentes tal y como llegan, perfila su calidad, limpia y estandariza identificadores, fechas e importes, e integra ventas y devoluciones de todos los canales en una única *fact table*. Después separa tres capas: Raw para auditar, Core para operar y Analytics para analizar.

→ [Escenario 02 · Fabric: del CSV a la fact table](../escenarios/02-fabric-preparacion-datos/README.md)
→ [Escenario 03 · SQL Raw → Core → Analytics](../escenarios/03-sql-raw-core-analytics/README.md)

## Capítulo 3 · Vender mejor, no solo vender más

Con datos fiables, comercial y marketing dejan de mirar solo la facturación. Construyen un Customer 360, segmentan por valor, predicen inactividad y propensión, recomiendan con stock y margen, miden la elasticidad de las promociones y empiezan a usar IA generativa con *guardrails* de marca.

→ [Escenario 04 · Analítica de ventas y ML](../escenarios/04-analitica-ventas-ml/README.md)
→ [Escenario 05 · Marketing de precisión](../escenarios/05-marketing-precision/README.md)

## Capítulo 4 · Las personas detrás de la tienda

El crecimiento online, los horarios ampliados y la presión de Black Friday y Navidad pasan factura: rotación en tienda y atención al cliente, salida de perfiles senior en ecommerce, tensión en logística. La Dirección de Personas aplica el mismo enfoque basado en datos para entender la rotación y priorizar acciones de retención, sin convertir un *score* en una decisión automática.

→ [Escenario 06 · People Analytics con Power BI](../escenarios/06-power-bi-people-analytics/README.md)

## Capítulo 5 · Preguntar a la empresa

Las mismas preguntas llegan una y otra vez al equipo de datos y a operaciones. FraSoHome construye un asistente que responde sobre políticas, procedimientos y KPI citando el documento vigente, que consulta métricas en datos estructurados y que resiste documentos obsoletos e intentos de *prompt injection*.

→ [Escenario 07 · Asistente RAG con Copilot Studio](../escenarios/07-copilot-studio-rag/README.md)

## Capítulo 6 · Del dato al contexto

Integrar tablas no basta: cada área sigue hablando su propio idioma. Un pedido no es una venta en tienda, una visita a la web no es una previsión de demanda y una campaña solo se atribuye cuando hay evidencia. FraSoHome formaliza ese significado en una ontología, la materializa en un grafo y la pone al servicio de un agente.

→ [Escenario 08 · Fabric IQ: ontología, grafo y agente](../escenarios/08-fabric-iq-ontologia/README.md)

## Capítulo 7 · IA que se explica y agentes

Los modelos, los RAG y los agentes ya toman parte en decisiones comerciales. Ahora hay que explicarlos, trazarlos y evaluarlos por capas. Y, con esa base, diseñar sistemas multiagente que preparen datos o detecten tendencias con supervisión humana.

→ [Escenario 09 · Interpretabilidad GenAI](../escenarios/09-genai-interpretabilidad/README.md)
→ [Escenario 10 · Agentes con Foundry](../escenarios/10-agentes-foundry/README.md)

## Para saber más

- [La empresa en cifras](empresa.md)
- [Los problemas de datos (intencionados)](problemas-de-datos.md)
- [El universo de datos y cómo se conecta](universo-de-datos.md)
- [Caso original: preparación de datos en retail omnicanal](caso-preparacion-datos.md)
