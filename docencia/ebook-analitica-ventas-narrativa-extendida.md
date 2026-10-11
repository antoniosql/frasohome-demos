# Analítica de Ventas aplicada al caso FraSoHome

## Versión narrativa extendida para una sesión de 8 horas

### Propósito del documento

Este ebook está pensado como material de apoyo para una sesión de Analítica de Ventas dirigida a alumnado de un máster de Big Data. No es un guion de diapositivas ni una lista de conceptos aislados. La intención es construir una narrativa completa: partir de una empresa con problemas comerciales reales, FraSoHome, y recorrer el camino que va desde los datos brutos hasta la decisión comercial medible.

El alumnado ya ha visto teoría de inteligencia de clientes, fuentes de datos, modelización, métricas e introducción a la explotación de resultados. Por eso, este documento no se limita a repetir qué es un modelo de clasificación o qué es un dashboard. Su objetivo es explicar cómo se conectan esas piezas en un proyecto completo.

La idea central es sencilla, pero poderosa:

> La analítica de ventas no consiste en aplicar modelos sobre una tabla. Consiste en mejorar decisiones comerciales usando datos, modelos, criterio de negocio y medición rigurosa.

FraSoHome nos permite trabajar esta idea con un caso suficientemente rico: una cadena de muebles y decoración con tiendas físicas, ecommerce, CRM, campañas de marketing, devoluciones, stock, costes, feedback de clientes y problemas de calidad de datos.

---

## Índice

1. [Vender más no siempre significa vender mejor](#1-vender-más-no-siempre-significa-vender-mejor)
2. [FraSoHome como caso de negocio: una empresa con datos, pero sin una visión única](#2-frasohome-como-caso-de-negocio-una-empresa-con-datos-pero-sin-una-visión-única)
3. [El mapa de datos: de los sistemas operacionales al modelo analítico](#3-el-mapa-de-datos-de-los-sistemas-operacionales-al-modelo-analítico)
4. [La fact table comercial: el corazón de la analítica de ventas](#4-la-fact-table-comercial-el-corazón-de-la-analítica-de-ventas)
5. [KPIs comerciales: aprender a mirar las ventas con criterio](#5-kpis-comerciales-aprender-a-mirar-las-ventas-con-criterio)
6. [Customer 360: entender al cliente antes de modelarlo](#6-customer-360-entender-al-cliente-antes-de-modelarlo)
7. [RFM, segmentación y valor de cliente](#7-rfm-segmentación-y-valor-de-cliente)
8. [Churn y reactivación: cuando el silencio del cliente también es una señal](#8-churn-y-reactivación-cuando-el-silencio-del-cliente-también-es-una-señal)
9. [Propensión de compra: anticipar intención sin confundir deseo con valor](#9-propensión-de-compra-anticipar-intención-sin-confundir-deseo-con-valor)
10. [Cross-sell, up-sell y recomendación: vender lo siguiente correcto](#10-cross-sell-up-sell-y-recomendación-vender-lo-siguiente-correcto)
11. [Promociones y campañas: pasar del score a la intervención](#11-promociones-y-campañas-pasar-del-score-a-la-intervención)
12. [Incrementalidad: demostrar que la acción causó el resultado](#12-incrementalidad-demostrar-que-la-acción-causó-el-resultado)
13. [Devoluciones, stock y margen: las ventas que el revenue no explica](#13-devoluciones-stock-y-margen-las-ventas-que-el-revenue-no-explica)
14. [Diseñar un dataset de entrenamiento: la parte menos vistosa y más decisiva](#14-diseñar-un-dataset-de-entrenamiento-la-parte-menos-vistosa-y-más-decisiva)
15. [Modelos baseline y evaluación: empezar simple para aprender rápido](#15-modelos-baseline-y-evaluación-empezar-simple-para-aprender-rápido)
16. [Del modelo al playbook comercial](#16-del-modelo-al-playbook-comercial)
17. [El ciclo completo de un proyecto ML en ventas](#17-el-ciclo-completo-de-un-proyecto-ml-en-ventas)
18. [Métricas técnicas y métricas de negocio: dos idiomas que deben entenderse](#18-métricas-técnicas-y-métricas-de-negocio-dos-idiomas-que-deben-entenderse)
19. [Gobierno, privacidad y operación del modelo](#19-gobierno-privacidad-y-operación-del-modelo)
20. [Puente hacia interpretabilidad: explicar para poder decidir](#20-puente-hacia-interpretabilidad-explicar-para-poder-decidir)
21. [Glosario narrativo de conceptos comerciales y analíticos](#21-glosario-narrativo-de-conceptos-comerciales-y-analíticos)
22. [Cierre](#22-cierre)

---

## 1. Vender más no siempre significa vender mejor

En muchas organizaciones, la primera conversación sobre analítica de ventas empieza con una frase aparentemente clara: "queremos vender más". Es una frase comprensible. Las empresas viven de vender, y cualquier área comercial tiene presión por crecer. Sin embargo, cuando miramos esa petición con ojos analíticos, enseguida aparece una pregunta incómoda:

> ¿Vender más de qué, a quién, por qué canal, con qué descuento, con qué coste y con qué probabilidad de devolución?

Esta pregunta cambia completamente el enfoque. Una venta no es solo un ingreso. Una venta consume stock, puede requerir descuentos, puede activar costes logísticos, puede generar una devolución, puede afectar a la experiencia de cliente y puede condicionar futuras compras.

Imaginemos dos campañas en FraSoHome.

La primera campaña vende muchos sofás con un descuento agresivo. El dashboard de revenue muestra un resultado espectacular: las ventas brutas suben un 25% durante la semana de campaña. Marketing celebra el resultado y dirección comercial ve una gráfica ascendente. Pero, al cerrar el mes, aparecen matices: el margen ha caído, algunas tiendas se han quedado sin stock de referencias clave, una parte de los pedidos se ha devuelto porque las medidas no estaban bien explicadas en la web y, además, muchos compradores eran clientes que probablemente iban a comprar igualmente.

La segunda campaña vende menos en importe bruto. Está dirigida a clientes con afinidad a decoración textil, usando productos con buen margen y stock suficiente en tiendas concretas. La conversión no es tan espectacular, pero el margen incremental es positivo, las devoluciones son bajas, el stock inmovilizado se reduce y el grupo control demuestra que las compras no se habrían producido al mismo nivel sin la campaña.

¿Cuál de las dos campañas es mejor? Si solo miramos ventas brutas, gana la primera. Si miramos valor comercial, probablemente gana la segunda.

Esta es la primera gran lección de la sesión:

> La analítica de ventas no debe limitarse a medir cuánto se vende. Debe ayudar a decidir qué ventas interesa provocar.

### 1.1 La diferencia entre reporting y sistema de decisión

Un dashboard de ventas puede responder preguntas como:

- ¿Cuánto vendimos ayer?
- ¿Qué tienda vendió más?
- ¿Qué categoría creció respecto al mes pasado?
- ¿Cuál fue el ticket medio?

Estas preguntas son útiles, pero describen lo ocurrido. La analítica avanzada aparece cuando queremos ir un paso más allá:

- ¿Qué clientes tienen más probabilidad de comprar una categoría concreta?
- ¿Qué clientes dejarán de comprar si no actuamos?
- ¿Qué promoción generará margen incremental?
- ¿Qué productos conviene recomendar juntos?
- ¿Qué ventas tienen riesgo de devolución?
- ¿Dónde debemos activar una campaña local porque hay stock disponible?

El reporting mira el pasado. La analítica avanzada ayuda a tomar decisiones sobre el futuro. Pero ambas capas deben convivir. No hay buen modelo predictivo sin una base descriptiva fiable.

En FraSoHome, por ejemplo, antes de crear un modelo de propensión hay que saber si las ventas online y POS están integradas, si los clientes se identifican correctamente, si las devoluciones se restan de forma consistente y si el maestro de productos permite entender categorías y costes.

### 1.2 La pregunta comercial bien formulada

Una mala formulación sería:

> Queremos hacer un modelo de machine learning para ventas.

La frase parece moderna, pero no dice qué decisión se quiere mejorar. Una formulación más útil sería:

> Queremos priorizar clientes contactables con alta probabilidad de comprar decoración en los próximos 30 días, siempre que exista stock disponible, el margen esperado sea positivo y podamos medir el incremento frente a un grupo control.

Esta segunda formulación incluye:

- Unidad de decisión: cliente.
- Acción: contacto comercial.
- Horizonte temporal: próximos 30 días.
- Restricción legal/operativa: contactabilidad.
- Restricción comercial: margen.
- Restricción de operaciones: stock.
- Medición: grupo control.

Eso ya no es "hacer un modelo". Eso es diseñar un sistema de decisión.

### 1.3 La cadena de valor analítica

Podemos resumir la cadena de valor de la analítica de ventas así:

1. Dato.
2. Información.
3. Insight.
4. Predicción.
5. Decisión.
6. Acción.
7. Medición.
8. Aprendizaje.

El dato es el registro bruto: una línea de venta, un evento web, una devolución. La información aparece cuando ese dato se organiza: ventas por categoría, clientes activos, tasa de devolución. El insight surge cuando interpretamos la información: una categoría vende mucho, pero devuelve demasiado. La predicción anticipa lo que puede ocurrir: este cliente tiene alta probabilidad de comprar textil. La decisión define qué hacer: incluirlo o no en una campaña. La acción ejecuta: enviar un email, mostrar una recomendación o activar una tienda. La medición verifica si ha funcionado. El aprendizaje permite mejorar la siguiente acción.

En clase, es importante insistir en que muchos proyectos se quedan a medio camino. Hay dashboards que nunca llegan a decisión. Hay modelos que nunca llegan a acción. Hay campañas que nunca llegan a medición. FraSoHome debe usarse para enseñar el recorrido completo.

---

## 2. FraSoHome como caso de negocio: una empresa con datos, pero sin una visión única

FraSoHome es una cadena ficticia de muebles y decoración para el hogar. Opera en un entorno B2C omnicanal. Tiene tiendas físicas, ecommerce, programa de fidelización, campañas de marketing, stock distribuido y procesos de devolución. Es una empresa suficientemente reconocible para cualquier alumno: vende productos tangibles, combina canales digitales y físicos, y necesita equilibrar crecimiento, margen y experiencia.

Lo interesante de FraSoHome no es que tenga datos. Muchas empresas tienen datos. Lo interesante es que esos datos no nacen integrados. Cada sistema registra una parte de la realidad.

El CRM sabe quién es el cliente, pero puede no tener todas sus compras si en tienda no se identificó. El POS sabe qué se vendió en caja, pero puede no conocer el comportamiento digital previo. El ecommerce sabe qué productos se añadieron al carrito, pero puede no saber si ese cliente terminó comprando en tienda. El sistema de stock sabe disponibilidad, pero no necesariamente conoce qué campañas están empujando la demanda. Atención al cliente sabe qué problemas aparecen después de la venta, pero muchas veces esa información no vuelve al modelo comercial.

### 2.1 El problema de los silos

Un silo de datos es una fuente o sistema que contiene información útil pero aislada del resto. En FraSoHome, los silos no son un problema abstracto. Tienen consecuencias concretas.

Si marketing trabaja solo con CRM, puede ignorar compras anónimas o ventas POS no identificadas. Si ecommerce analiza navegación sin enlazar con compras posteriores en tienda, puede infravalorar el efecto digital. Si operaciones mira stock sin campañas, puede no anticipar roturas. Si dirección mira ventas sin devoluciones, puede sobreestimar categorías.

El silo más peligroso no es técnico, sino conceptual: cada área cree que su dato representa la realidad completa. La analítica de ventas debe construir una realidad compartida.

### 2.2 Fuentes principales de FraSoHome

El caso contiene fuentes de retail omnicanal:

- `crm.csv`, con clientes, fidelización y consentimiento.
- `pedidos.csv`, con cabeceras de pedidos online.
- `lineas_pedido.csv`, con detalle de productos comprados online.
- `ventas_pos.csv`, con líneas de venta en tienda.
- `devoluciones_online.csv`, con devoluciones de ecommerce.
- `devoluciones_tienda.csv`, con devoluciones en tienda física.
- `productos.csv`, con catálogo, categoría, precio y coste.
- `tiendas.csv`, con información de tiendas y ubicaciones.
- `stock_diario.csv`, con snapshots de inventario.
- `fact_transacciones.csv`, con una fact table integrada para demos.

Además, contiene fuentes de marketing precision:

- Campañas.
- Contactos de campaña.
- Eventos de campaña.
- Eventos web/app.
- Cupones.
- Costes operativos.
- Feedback.
- Tickets de atención.
- Identidades de cliente.
- Guardrails de marca para GenAI.

Este conjunto permite explicar algo muy importante: los modelos comerciales modernos no viven solo de transacciones. También necesitan señales de intención, exposición, respuesta, coste y experiencia.

### 2.3 Problemas de calidad como problema comercial

En los datos de FraSoHome aparecen duplicados, nulos, fechas heterogéneas, importes con formatos distintos, claves inconsistentes y clientes no identificados. En una clase técnica, podríamos ver esto como un ejercicio de limpieza. Pero en una clase de analítica de ventas conviene elevarlo:

> Cada problema de calidad de datos es una posible mala decisión comercial.

Un cliente duplicado puede recibir dos comunicaciones o quedar mal segmentado. Un importe mal parseado puede distorsionar margen. Una devolución no enlazada puede hacer que un producto parezca rentable. Un consentimiento mal normalizado puede provocar una activación incorrecta. Un product_id con casing inconsistente puede romper análisis por categoría.

Por eso, la calidad de datos no se debe presentar como una fase aburrida previa al "verdadero" machine learning. Es parte del valor del proyecto.

### 2.4 El reto narrativo de FraSoHome

La narrativa del caso puede formularse así:

FraSoHome quiere mejorar sus ventas, pero descubre que sus decisiones comerciales están limitadas por la fragmentación de datos. Tiene clientes fieles, pero no siempre identificados. Tiene campañas, pero no siempre sabe si generan ventas incrementales. Tiene productos que venden mucho, pero algunos devuelven demasiado. Tiene stock en tiendas, pero no siempre lo conecta con acciones locales. Tiene modelos posibles, pero antes necesita definir bien sus problemas.

Esta narrativa permite llevar al alumnado por el camino completo:

- Primero entender el negocio.
- Después mapear datos.
- Luego definir KPIs.
- Construir Customer 360.
- Diseñar casos de uso.
- Preparar datasets de entrenamiento.
- Evaluar modelos.
- Activar acciones.
- Medir impacto.
- Preparar interpretabilidad.

---

## 3. El mapa de datos: de los sistemas operacionales al modelo analítico

Una de las dificultades habituales de los alumnos que ya conocen algoritmos es que tienden a imaginar el proyecto de ML empezando en una tabla limpia, con una columna objetivo y varias features listas. En la vida real, esa tabla rara vez existe. Hay que construirla.

FraSoHome es útil porque muestra esa distancia entre los sistemas origen y el dataset analítico.

### 3.1 Sistemas operacionales

Los sistemas operacionales están diseñados para ejecutar el negocio. Su prioridad no es que un científico de datos entrene un modelo cómodamente, sino que la operación diaria funcione.

El POS debe registrar ventas. El ecommerce debe aceptar pedidos. El sistema de devoluciones debe tramitar reembolsos. El CRM debe guardar clientes. La herramienta de campañas debe enviar mensajes. El sistema de stock debe registrar existencias.

Cada sistema tiene su propia lógica, sus claves, sus formatos y sus urgencias. Por eso, una misma realidad puede aparecer repartida.

Ejemplo: una clienta ve una lámpara en la web, recibe un email, la compra en tienda, la paga parcialmente con un cupón y después devuelve otro artículo comprado online. Para entender su comportamiento comercial hay que unir navegación, campaña, POS, cupón, CRM y devoluciones.

### 3.2 Sistemas analíticos

Un sistema analítico reorganiza los datos para responder preguntas. Aquí aparecen conceptos como data warehouse, datamart, modelo dimensional y semantic layer.

Un data warehouse busca integrar datos de toda la organización. Un datamart reduce el alcance a un área. Un modelo dimensional organiza hechos y dimensiones para que las consultas sean consistentes. Una capa semántica define métricas de negocio de forma común.

La idea importante para clase es esta:

> Un modelo analítico no es una copia de los sistemas origen. Es una interpretación organizada del negocio.

Cuando decidimos que una fila representa una línea de venta, estamos eligiendo una granularidad. Cuando decidimos que las devoluciones se registran como movimientos negativos o como hechos separados, estamos eligiendo una forma de interpretar el negocio. Cuando decidimos calcular ventas netas restando devoluciones, estamos definiendo una métrica.

### 3.3 Granularidad: la decisión silenciosa

La granularidad es el nivel de detalle de una tabla. Es una de las decisiones más silenciosas y más importantes de cualquier proyecto.

Si analizamos a nivel cliente, una fila representa un cliente. Esto es útil para churn, segmentación o propensión. Pero perdemos detalle de producto y transacción.

Si analizamos a nivel pedido, una fila representa una compra. Esto es útil para ticket medio, conversión o devolución de pedido. Pero un pedido puede contener productos de varias categorías.

Si analizamos a nivel línea de pedido, una fila representa un producto dentro de una compra. Esto es útil para margen, recomendación, devolución por SKU y análisis de cesta.

Si analizamos a nivel producto-tienda-día, una fila representa stock o rendimiento local. Esto es útil para operaciones y campañas locales.

No existe una granularidad universal. La granularidad correcta depende de la decisión.

### 3.4 Dimensiones

Las dimensiones son las entidades que dan contexto a los hechos. En FraSoHome, las dimensiones principales son:

- Cliente.
- Producto.
- Tienda.
- Fecha.
- Canal.
- Campaña.
- Cupón.
- Método de pago.

Las dimensiones permiten segmentar, filtrar y explicar. Una venta sin dimensión producto es solo un importe. Una venta con producto, categoría, coste y proveedor se convierte en una señal de rentabilidad. Una venta con cliente, canal y campaña permite medir comportamiento y activación.

### 3.5 Hechos

Los hechos son eventos medibles:

- Una venta.
- Una devolución.
- Un pago.
- Un contacto de campaña.
- Un click.
- Una visita web.
- Una redención de cupón.
- Un snapshot de stock.

Cada hecho tiene medidas: importe, cantidad, coste, margen, unidades, clicks, conversiones, stock disponible.

La analítica de ventas consiste en conectar hechos y dimensiones para generar indicadores y modelos.

---

## 4. La fact table comercial: el corazón de la analítica de ventas

Si tuviéramos que elegir una pieza central para la sesión, sería la fact table comercial. No porque sea el elemento más vistoso, sino porque de ella depende casi todo lo demás.

Una fact table comercial integra movimientos de negocio con una granularidad clara. En FraSoHome, debe permitir analizar ventas y devoluciones en todos los canales.

### 4.1 Qué debería representar

Una fila de la fact table podría representar una línea de venta o devolución. Eso permite saber:

- Qué producto se movió.
- En qué fecha.
- En qué canal.
- En qué tienda o ubicación.
- Qué cliente estuvo asociado, si existe.
- Qué importe se vendió o devolvió.
- Qué descuento se aplicó.
- Qué coste tenía el producto.
- Qué margen generó.

Este diseño permite construir indicadores desde abajo hacia arriba. Podemos agregar por cliente, producto, categoría, tienda, canal, campaña o periodo.

### 4.2 Ventas y devoluciones en la misma lógica

Una decisión importante es cómo tratar las devoluciones. Podemos representarlas como hechos separados o como movimientos negativos. Lo importante es que el criterio sea explícito y consistente.

Si las devoluciones no se incorporan a la fact table, la empresa verá una versión optimista de las ventas. En FraSoHome eso sería especialmente peligroso porque las devoluciones son parte natural del negocio.

Una categoría puede parecer excelente por revenue bruto y mediocre por revenue neto. Un cliente puede parecer valioso por compras acumuladas y menos valioso por devoluciones recurrentes. Una campaña puede parecer rentable antes de devoluciones y fallar después de ellas.

### 4.3 Margen dentro de la fact table

Siempre que sea posible, la fact table debe incorporar coste de producto y margen. Sin margen, la analítica de ventas tiende a optimizar revenue, no valor.

Ejemplo:

Un producto A vende 100.000 euros con margen del 10%. Un producto B vende 60.000 euros con margen del 40%. Si solo miramos revenue, A parece mejor. Si miramos margen bruto, B puede ser más interesante.

En FraSoHome, además, el margen debe matizarse con descuentos, devoluciones y costes operativos. Esto lleva al concepto de margen neto aproximado.

### 4.4 El cliente identificado y el cliente anónimo

Uno de los retos del retail físico es que no todas las ventas tienen cliente identificado. En ecommerce suele haber más identificación, pero también puede haber usuarios invitados. En tienda, si el cliente no usa tarjeta de fidelización o no proporciona datos, la venta queda anónima.

Para reporting financiero, una venta anónima sigue siendo una venta. Para customer analytics, es una oportunidad perdida.

Si una parte relevante de ventas no enlaza con CRM, FraSoHome no puede:

- Calcular bien CLV.
- Segmentar comportamiento real.
- Activar reactivación.
- Medir frecuencia completa.
- Conectar campañas con ventas.

La identificación del cliente es, por tanto, una palanca comercial. No es un capricho del equipo de datos.

### 4.5 Una buena fact table responde muchas preguntas

Con una fact table bien diseñada, FraSoHome puede responder:

- ¿Qué categorías generan más margen neto por canal?
- ¿Qué productos tienen alta devolución?
- ¿Qué clientes compran con descuento?
- ¿Qué tiendas tienen buen sell-through?
- ¿Qué campañas generan ventas netas y no solo clicks?
- ¿Qué segmentos compran online pero devuelven en tienda?
- ¿Qué categorías conviene recomendar según cesta?

La fact table no resuelve todos los problemas, pero crea la base para que el resto del proyecto sea posible.

---

## 5. KPIs comerciales: aprender a mirar las ventas con criterio

Los KPIs son el idioma común entre datos y negocio. Pero un KPI mal definido puede ser peor que no tener KPI, porque crea una ilusión de objetividad.

En FraSoHome, los KPIs deben ayudar a responder no solo cuánto se vende, sino qué calidad tiene esa venta.

### 5.1 Ventas brutas

Ventas brutas es el importe total vendido antes de ajustes. Es el indicador más intuitivo y muchas veces el primero que mira dirección. Sirve para medir volumen de actividad comercial.

Pero tiene un riesgo: puede celebrar ventas que no aportan valor. Si una campaña genera mucho revenue porque aplica descuentos profundos, las ventas brutas suben. Si luego hay devoluciones, costes logísticos o bajo margen, el resultado real puede ser flojo.

En clase conviene usar ventas brutas como punto de partida, no como verdad final.

### 5.2 Ventas netas

Ventas netas descuenta devoluciones y ajustes. En retail es un KPI mucho más cercano a la realidad comercial.

En FraSoHome, donde existen devoluciones online y en tienda, mirar ventas netas es obligatorio. Si no lo hacemos, productos problemáticos pueden parecer exitosos. También podemos sobrevalorar campañas que generan compras impulsivas y devoluciones posteriores.

La narrativa docente puede ser:

> Las ventas brutas cuentan la historia de la caja. Las ventas netas empiezan a contar la historia del negocio.

### 5.3 Ticket medio y AOV

Ticket medio y AOV muestran cuánto se gasta en una transacción o pedido.

Si FraSoHome lanza una estrategia de cross-sell, esperamos que el ticket medio suba. Si recomienda productos complementarios en checkout, el AOV online puede aumentar. Si una tienda hace bundles de decoración, el ticket puede crecer.

Pero, de nuevo, hay que matizar. Subir ticket medio a base de descuentos puede reducir margen. Subir AOV empujando productos de alta devolución puede crear problemas posteriores.

### 5.4 Frecuencia y recencia

Frecuencia y recencia son dos variables esenciales para entender relación con cliente.

La frecuencia indica cuántas veces compra. La recencia indica cuánto tiempo ha pasado desde la última compra.

En FraSoHome, estas variables deben interpretarse según el tipo de producto. Un cliente que compra un sofá cada cinco años no es necesariamente poco fiel. Pero si compra decoración de forma recurrente y deja de hacerlo, eso sí puede ser una señal de abandono.

Esto permite introducir una idea importante: los KPIs no son universales; se interpretan con conocimiento de negocio.

### 5.5 Margen bruto y margen neto

El margen bruto resta el coste del producto al ingreso neto. El margen neto incorpora además costes operativos relevantes.

En analítica de ventas, el margen es el antídoto contra el optimismo del revenue. Una empresa no vive del importe vendido, sino del valor que queda después de costes.

En FraSoHome, el margen puede verse afectado por:

- Coste de producto.
- Descuento aplicado.
- Coste de campaña.
- Coste de envío.
- Coste de devolución.
- Coste de atención al cliente.

Por eso, al diseñar campañas, conviene pasar de "clientes con mayor probabilidad de compra" a "clientes con mayor margen esperado incremental".

### 5.6 Tasa de devolución

La tasa de devolución es especialmente interesante porque conecta ventas, producto, operaciones y experiencia.

Una alta tasa de devolución puede indicar:

- Producto de mala calidad.
- Descripción insuficiente.
- Fotos poco representativas.
- Medidas confusas.
- Expectativas mal gestionadas.
- Promoción que empuja a comprar sin intención clara.
- Problemas logísticos.

En FraSoHome, si una categoría tiene alta venta y alta devolución, no basta con pedir al modelo que venda más. Quizá hay que mejorar contenido, segmentar mejor, ajustar promesas o revisar proveedores.

### 5.7 Conversión

Conversión mide el paso desde una oportunidad hasta una acción deseada. Puede ser compra, click, redención de cupón o registro.

La conversión es atractiva porque parece clara, pero exige definir el denominador. No es lo mismo convertir sobre visitantes web, sobre emails entregados, sobre clicks, sobre clientes contactables o sobre clientes seleccionados.

Una campaña puede tener alta conversión entre quienes hacen click, pero baja conversión sobre el total enviado. Por eso hay que especificar siempre el contexto.

### 5.8 ROI

ROI mide retorno sobre inversión. En marketing, se usa mucho, pero a menudo se calcula de forma demasiado optimista.

Un ROI serio debería considerar margen incremental y costes reales. Si FraSoHome invierte 1.000 euros en una campaña y atribuye 5.000 euros de ventas, no significa automáticamente que el ROI sea excelente. Hay que preguntar:

- ¿Cuánto margen dejaron esas ventas?
- ¿Cuántas se habrían producido sin campaña?
- ¿Qué descuentos se aplicaron?
- ¿Hubo devoluciones?
- ¿Qué coste tuvo el contacto?

### 5.9 Sell-through, stockout y sobrestock

Ventas y stock son inseparables. Una campaña puede fracasar no porque el modelo sea malo, sino porque no había producto disponible. Otra puede ser útil no por generar demanda nueva, sino por liberar stock inmovilizado.

Sell-through mide cuánto stock se vende. Stockout indica rotura de stock. Sobrestock indica exceso.

En FraSoHome, estas métricas permiten conectar analítica de ventas con operaciones. Por ejemplo, una audiencia local con afinidad a una categoría y una tienda con sobrestock pueden convertirse en una campaña hiperlocal.

---

## 6. Customer 360: entender al cliente antes de modelarlo

Customer 360 es una expresión muy utilizada, pero a veces se convierte en un contenedor difuso. En este curso debe explicarse de forma pragmática:

> Customer 360 es la vista mínima y suficiente para decidir qué hacer con un cliente.

No se trata de acumular cientos de variables. Se trata de reunir las señales que permiten entender valor, necesidad, canal, riesgo y acción.

### 6.1 Identidad

La identidad responde a la pregunta: ¿sabemos quién es este cliente?

En ecommerce, la identidad puede venir de un usuario, email o customer_id. En tienda, puede depender de una tarjeta de fidelización o de que el cliente se identifique. En navegación web, puede aparecer como cookie o device_id.

El reto de FraSoHome es unir estas señales. Si un cliente navega online, compra en tienda y devuelve por otro canal, necesitamos reconocer que forma parte de una misma relación.

La resolución de identidad no es solo una técnica de matching. Comercialmente, permite:

- Aumentar ventas identificadas.
- Mejorar segmentación.
- Reducir duplicados.
- Evitar impactos repetidos.
- Medir campañas.
- Construir CLV.

### 6.2 Contactabilidad y consentimiento

Saber quién es el cliente no significa poder contactarle. La contactabilidad exige tener un canal válido. El consentimiento exige tener permiso para usarlo con una finalidad.

En marketing moderno, esta distinción es crítica. Un cliente puede tener email registrado, pero no aceptar comunicaciones comerciales. O puede aceptar email, pero no SMS. O puede haber dado consentimiento para fidelización, pero no para campañas de terceros.

En FraSoHome, normalizar consentimientos heterogéneos es parte del proyecto. Si no se hace bien, el modelo puede seleccionar clientes que legal o éticamente no deben activarse.

### 6.3 Comportamiento transaccional

El comportamiento transaccional responde a:

- Qué compra.
- Cuándo compra.
- Cuánto compra.
- Con qué frecuencia.
- En qué canal.
- Con qué descuento.
- Qué devuelve.

Estas señales son la base de muchas features. Pero deben leerse con cuidado. Un cliente que no compra muebles en seis meses puede ser normal. Un cliente que compraba decoración mensual y deja de hacerlo puede estar en riesgo.

### 6.4 Comportamiento digital

Las señales digitales permiten detectar intención antes de la compra:

- Vistas de producto.
- Búsquedas.
- Añadidos al carrito.
- Abandono de checkout.
- Clicks.
- Sesiones recientes.

Estas señales enriquecen los modelos de propensión. Si un cliente visita repetidamente lámparas de pie, FraSoHome puede inferir interés. Pero debe combinarlo con stock, margen, preferencias y presión comercial.

### 6.5 Relación con campañas

No todos los clientes responden igual a marketing. Algunos abren emails pero no compran. Otros compran sin abrir comunicaciones. Otros solo responden a descuento.

El historial de campañas permite medir:

- Entregas.
- Aperturas.
- Clicks.
- Conversiones.
- Redención de cupones.
- Coste de contacto.
- Fatiga comercial.

Estas variables son esenciales para no tratar igual a todos los clientes.

### 6.6 Experiencia y voz del cliente

Los tickets, feedback y motivos de devolución explican aspectos que las ventas no muestran. Un cliente puede comprar mucho y estar insatisfecho. Un producto puede vender bien y generar quejas. Una categoría puede crecer por promoción, pero deteriorar NPS.

La voz del cliente permite incorporar una capa cualitativa:

- Sentimiento.
- Motivo de queja.
- Tema principal.
- Incidencia logística.
- Problema de producto.
- Objeción recurrente.

En una sesión posterior, esto también puede conectarse con GenAI y NLP, pero aquí basta con entender su valor comercial.

---

## 7. RFM, segmentación y valor de cliente

La segmentación es una de las herramientas más antiguas y útiles en ventas y marketing. Antes de tener modelos complejos, las empresas ya agrupaban clientes para tratarlos de forma distinta. La pregunta es cómo hacerlo con datos y de forma accionable.

### 7.1 RFM como punto de entrada

RFM significa Recency, Frequency, Monetary. Es simple, comprensible y muy útil como baseline.

Recency mide cuándo compró por última vez. Frequency mide cuántas veces compra. Monetary mide cuánto gasta.

El atractivo de RFM es que traduce comportamiento en una lectura comercial sencilla:

- Clientes recientes están activos.
- Clientes frecuentes están vinculados.
- Clientes con alto gasto aportan valor.

En FraSoHome, podemos usar RFM para identificar clientes campeones, clientes dormidos, compradores recientes, clientes de bajo valor o clientes que necesitan reactivación.

### 7.2 La narrativa de los segmentos RFM

Un RFM no debe quedarse en números. Debe convertirse en historia.

Un cliente con alta frecuencia y alto valor, pero baja recencia, cuenta una historia: fue importante, pero se está alejando. Un cliente con alta recencia pero bajo valor cuenta otra: acaba de entrar, quizá hay oportunidad de desarrollarlo. Un cliente con alto gasto, pero mucha devolución, cuenta una historia más ambigua: compra, pero puede destruir margen.

El docente debe insistir en que segmentar no es asignar etiquetas, sino interpretar comportamientos.

### 7.3 Por qué RFM no basta

RFM clásico puede llevar a decisiones demasiado simplificadas. En FraSoHome hay dimensiones que RFM no ve:

- Margen.
- Devoluciones.
- Descuentos.
- Canal.
- Categoría.
- Stock.
- Respuesta a campañas.
- Consentimiento.
- Engagement digital.

Un cliente con Monetary alto puede ser menos rentable de lo que parece. Un cliente con Frequency baja puede ser normal si compra muebles de ciclo largo. Un cliente con Recency baja puede seguir siendo valioso si acaba de comprar una categoría de reposición lenta.

### 7.4 RFM extendido como puente hacia ML

El RFM extendido incorpora más señales. No sustituye al modelo predictivo, pero crea una base muy útil.

Variables recomendadas:

- Recencia de compra.
- Frecuencia por periodo.
- Gasto neto.
- Margen neto.
- Tasa de devolución.
- Descuento medio.
- Porcentaje de compras online.
- Categoría favorita.
- Número de campañas recibidas.
- Tasa de respuesta a campañas.
- Engagement digital reciente.
- Afinidad local a tienda.

Este conjunto permite que los alumnos vean el paso natural entre analítica descriptiva y features de ML.

### 7.5 Segmentación accionable

Un segmento es accionable si permite hacer algo diferente.

Ejemplos en FraSoHome:

**Clientes premium rentables**

Compran con margen alto, devuelven poco y no necesitan grandes descuentos. La acción comercial debería centrarse en experiencia, preventas, novedades o servicios añadidos.

**Clientes dormidos de alto valor**

Fueron buenos clientes, pero no compran desde hace tiempo. La acción puede ser reactivación con categoría favorita, pero cuidando el incentivo.

**Clientes sensibles a descuento**

Compran cuando hay promociones. La acción debe controlar profundidad de descuento y evitar entrenar al cliente a esperar rebajas.

**Clientes con riesgo de devolución**

No basta con venderles más. Conviene mejorar información, recomendaciones y expectativas.

**Clientes omnicanal**

Interactúan online y compran en tienda, o viceversa. Pueden ser valiosos, pero requieren medición que no atribuya todo al último canal.

---

## 8. Churn y reactivación: cuando el silencio del cliente también es una señal

En retail, el abandono rara vez se anuncia. Un cliente no suele llamar para decir: "he decidido no comprar más en FraSoHome". Simplemente deja de aparecer.

Por eso, churn en retail es un concepto más sutil que en suscripciones. Hay que definirlo.

### 8.1 Definir churn en FraSoHome

Una definición ingenua sería:

> Cliente que no compra en 90 días.

Pero FraSoHome vende muebles y decoración. El ciclo de compra puede variar mucho por categoría. Quien compra una cama no necesita otra en tres meses. Quien compra velas o textil puede tener recurrencia más alta.

Por eso, una definición más razonable debe considerar:

- Categorías compradas.
- Frecuencia histórica del cliente.
- Tiempo desde última compra.
- Valor esperado.
- Comportamiento de clientes similares.

Churn puede definirse como ausencia de compra en una ventana futura, pero esa ventana debe elegirse con criterio.

### 8.2 Churn como priorización, no como sentencia

Un score de churn no dice "este cliente se va seguro". Dice "este cliente tiene mayor riesgo relativo de inactividad". Esto es importante para evitar interpretaciones deterministas.

Comercialmente, el churn sirve para priorizar acciones:

- A quién contactar.
- Con qué intensidad.
- Con qué oferta.
- Por qué canal.
- Con qué coste máximo.

No todos los clientes en riesgo merecen la misma inversión. Un cliente con alto riesgo y bajo margen quizá solo justifica un email automatizado. Un cliente con alto riesgo y alto margen puede justificar una acción más cuidada.

### 8.3 Reactivación

La reactivación busca recuperar clientes inactivos o en riesgo. Pero reactivar no significa regalar descuento indiscriminadamente.

En FraSoHome, una buena reactivación debería tener en cuenta:

- Última categoría comprada.
- Categoría con afinidad.
- Motivos de abandono posibles.
- Historial de devoluciones.
- Respuesta a campañas anteriores.
- Canal preferido.
- Margen esperado.
- Stock disponible.

Ejemplo:

Un cliente que compró decoración varias veces, dejó de comprar hace seis meses, abrió emails recientes y tiene afinidad a tienda local podría recibir una comunicación sobre nueva colección disponible en su tienda cercana.

Otro cliente con alto gasto histórico pero muchas devoluciones quizá no necesita descuento, sino una recomendación más precisa o contenido que reduzca incertidumbre.

### 8.4 Métricas para churn

El modelo puede evaluarse con AUC, lift o recall, pero la acción debe evaluarse con métricas comerciales:

- Recompra incremental.
- Margen incremental.
- Coste por cliente recuperado.
- Reducción de inactividad.
- Baja de comunicaciones.
- Tasa de devolución post-reactivación.

Un buen modelo de churn no es el que mejor predice abandono en abstracto. Es el que ayuda a recuperar clientes rentables de forma eficiente.

---

## 9. Propensión de compra: anticipar intención sin confundir deseo con valor

La propensión es la probabilidad de que ocurra una acción. En ventas, se usa para anticipar quién puede comprar, qué puede comprar o cómo puede responder.

En FraSoHome, un modelo de propensión podría estimar:

- Probabilidad de comprar en los próximos 30 días.
- Probabilidad de comprar una categoría.
- Probabilidad de responder a una campaña.
- Probabilidad de visitar una tienda.
- Probabilidad de redimir un cupón.

### 9.1 Propensión no es valor

Este matiz es clave. Que un cliente tenga alta probabilidad de comprar no significa que sea el mejor cliente a impactar.

Puede tener alta propensión porque iba a comprar igualmente. Puede comprar productos de bajo margen. Puede necesitar descuento. Puede devolver mucho. Puede estar saturado de comunicaciones.

Por tanto, la propensión debe combinarse con valor esperado.

Una fórmula conceptual sería:

> Prioridad comercial = Propensión x Margen esperado x Incrementalidad esperada - Coste - Riesgo

No hace falta usar exactamente esa fórmula en clase, pero sí transmitir la lógica.

### 9.2 Propensión por categoría

En FraSoHome, predecir compra genérica puede ser menos útil que predecir categoría. Saber que un cliente comprará "algo" no ayuda tanto como saber que probablemente comprará iluminación o textil.

Para propensión por categoría podemos usar:

- Histórico de compras por categoría.
- Visitas web a productos.
- Añadidos al carrito.
- Clicks en campañas.
- Estacionalidad.
- Afinidad con tienda.
- Compras de clientes similares.

La acción derivada puede ser:

- Personalizar email.
- Ordenar bloques de una landing.
- Recomendar productos.
- Crear audiencias para paid media.
- Activar una campaña local.

### 9.3 Propensión y momento

El momento importa. Un cliente puede tener afinidad a una categoría, pero no intención inmediata. Las señales digitales recientes ayudan a detectar timing.

Ejemplo:

Un cliente compró muebles hace un año, pero esta semana ha visitado varias páginas de lámparas, ha filtrado por precio y ha añadido un producto al carrito. Esa combinación puede indicar intención actual.

La analítica de ventas debe distinguir afinidad estructural de intención reciente.

### 9.4 Target y ventanas temporales

Para entrenar un modelo de propensión hay que definir:

- Fecha de corte.
- Ventana de observación.
- Ventana de predicción.
- Acción objetivo.

Ejemplo:

Observamos comportamiento de enero a marzo y predecimos si compra iluminación en abril.

Si usamos eventos de abril como features, cometemos leakage. Si no separamos temporalmente, el modelo puede aprender señales imposibles de usar en producción.

---

## 10. Cross-sell, up-sell y recomendación: vender lo siguiente correcto

La analítica de ventas no solo ayuda a decidir a quién contactar, sino también qué ofrecer. Aquí entran cross-sell, up-sell y recomendadores.

### 10.1 Cross-sell

Cross-sell es ofrecer un producto complementario. En FraSoHome es muy natural:

- Mesa y sillas.
- Sofá y cojines.
- Cortinas y barras.
- Lámpara y bombilla.
- Cama y ropa de cama.

El cross-sell bien hecho aumenta valor de cesta y puede mejorar la experiencia, porque ayuda al cliente a completar una solución.

Pero si se hace mal, parece presión comercial. Recomendar productos irrelevantes o sin stock reduce confianza.

### 10.2 Up-sell

Up-sell es proponer una alternativa superior. Puede aumentar margen y satisfacción si realmente aporta valor.

Ejemplo:

Un cliente mira una mesa básica. FraSoHome puede recomendar una mesa extensible de mejor material si encaja con su presupuesto, espacio y comportamiento.

El up-sell requiere sensibilidad. Si el salto de precio es excesivo o la recomendación no considera necesidades, puede bloquear la compra.

### 10.3 Recomendadores

Un recomendador ordena opciones. Puede basarse en reglas simples o modelos complejos.

Niveles posibles:

1. Productos más vendidos.
2. Productos populares por categoría.
3. Productos comprados juntos.
4. Productos similares a los vistos.
5. Productos preferidos por clientes similares.
6. Ranking personalizado con stock, margen y riesgo.

Para docencia, conviene mostrar que no hay que empezar por el recomendador más sofisticado. Un baseline de cesta puede ser suficiente para aprender.

### 10.4 Análisis de cesta

El análisis de cesta busca patrones de co-compra. Las reglas de asociación ayudan a descubrir combinaciones.

Conceptos:

- Soporte: frecuencia de la combinación.
- Confianza: probabilidad de B dado A.
- Lift: cuánto más fuerte es la relación frente al azar.

Ejemplo narrativo:

Si muchas compras de mesas incluyen sillas, eso no sorprende. Pero si ciertos textiles se compran junto con lámparas de una colección, puede aparecer una oportunidad de escaparate, bundle o recomendación.

### 10.5 Recomendación responsable

En FraSoHome, recomendar no debe depender solo de probabilidad de compra. Debe incorporar restricciones:

- Stock disponible.
- Margen mínimo.
- Compatibilidad.
- Riesgo de devolución.
- Saturación comercial.
- Reglas de marca.
- Experiencia del cliente.

Esto permite transmitir una idea fundamental:

> El modelo propone. El sistema de decisión filtra, prioriza y contextualiza.

---

## 11. Promociones y campañas: pasar del score a la intervención

Una campaña es una intervención. La empresa decide impactar a un conjunto de clientes con un mensaje, una oferta o una recomendación. Por eso, las campañas son el lugar donde el modelo se convierte en negocio.

### 11.1 Componentes de una campaña

Una campaña bien diseñada tiene:

- Objetivo.
- Audiencia.
- Canal.
- Mensaje.
- Oferta.
- Calendario.
- Coste.
- Exclusiones.
- Métricas.
- Grupo control.

Si falta alguno de estos elementos, la campaña puede ejecutarse, pero será difícil aprender.

### 11.2 Audiencia

La audiencia no debería definirse solo por "clientes con alto score". Debe incorporar reglas.

Ejemplo de audiencia:

Clientes con alta propensión a decoración, contactables por email, sin compra en los últimos 45 días, con margen histórico positivo, sin incidencia abierta, no impactados en los últimos 7 días y con stock disponible en tienda cercana o canal online.

Esta definición muestra la diferencia entre un score y una decisión operativa.

### 11.3 Oferta

La oferta puede ser descuento, envío gratuito, acceso anticipado, recomendación personalizada, contenido inspiracional o invitación a tienda.

No todas las acciones necesitan descuento. A veces el mejor incentivo es relevancia.

En FraSoHome, ofrecer descuento a clientes que ya tenían alta intención puede destruir margen. En cambio, mostrar una colección alineada con su estilo puede ser suficiente.

### 11.4 Canal

El canal debe elegirse según comportamiento y consentimiento:

- Email.
- SMS.
- Push.
- Web personalizada.
- App.
- Tienda.
- Paid audiences.

Un cliente que compra en tienda y apenas abre email quizá responda mejor a una acción local. Un cliente digital con visitas recientes puede responder mejor a personalización onsite.

### 11.5 Presión comercial

El hecho de poder impactar no significa que debamos hacerlo. La presión comercial acumulada deteriora respuesta y confianza.

Por eso, una campaña debe contemplar:

- Número de impactos recientes.
- Prioridad de campañas simultáneas.
- Fatiga.
- Bajas.
- Reglas de contacto.

La analítica de ventas madura incluye la decisión de no contactar.

---

## 12. Incrementalidad: demostrar que la acción causó el resultado

Uno de los aprendizajes más importantes para el alumnado es distinguir atribución de causalidad.

Si una persona recibe un email y compra, podemos atribuir la venta al email. Pero no sabemos si habría comprado igualmente. Para saberlo necesitamos comparar con un escenario sin email.

### 12.1 El problema de la atribución ingenua

Supongamos que FraSoHome envía una campaña a sus mejores clientes. La conversión es altísima. Parece un éxito. Pero esos clientes ya compraban mucho. Tal vez la campaña no generó nuevas ventas, solo acompañó compras que iban a ocurrir.

Este error es frecuente: impactar a los clientes más propensos produce métricas bonitas, pero no siempre valor incremental.

### 12.2 Grupo control

Un grupo control es un conjunto comparable que no recibe la acción. Permite estimar qué habría pasado sin intervención.

Ejemplo:

- Tratamiento: clientes que reciben campaña.
- Control: clientes similares que no reciben campaña.

Si el tratamiento convierte al 8% y el control al 6%, el efecto incremental aproximado es 2 puntos porcentuales.

### 12.3 Holdout

Holdout es una parte de la audiencia que se reserva sin impacto. En campañas CRM, es una práctica muy útil.

Puede parecer doloroso no contactar a clientes con alta propensión, pero permite aprender. Sin holdout, FraSoHome puede gastar dinero en acciones que parecen funcionar y no funcionan.

### 12.4 Uplift

Uplift mide diferencia causada por la acción. Puede medirse en conversión, revenue o margen.

La versión más útil para negocio es margen incremental:

> Margen incremental = Margen del grupo tratado - Margen esperado según control

Esta métrica obliga a mirar más allá de clicks y ventas brutas.

### 12.5 Modelos de uplift

En una sesión introductoria no hace falta profundizar en uplift modeling, pero sí mencionar la lógica. Un modelo de propensión identifica quién comprará. Un modelo de uplift intenta identificar quién comprará gracias a la acción.

Esto diferencia:

- Clientes que compran aunque no les contactes.
- Clientes que compran si les contactas.
- Clientes que no comprarán aunque les contactes.
- Clientes que podrían reaccionar negativamente.

Para marketing de precisión, esta distinción es muy potente.

---

## 13. Devoluciones, stock y margen: las ventas que el revenue no explica

La analítica de ventas suele empezar mirando revenue, pero FraSoHome permite mostrar que revenue es solo la superficie.

### 13.1 Devoluciones

Las devoluciones reducen ventas netas y margen, pero también revelan problemas de experiencia.

Una devolución puede estar causada por:

- Producto defectuoso.
- Tamaño o medidas mal explicadas.
- Color diferente al esperado.
- Entrega tardía.
- Compra impulsiva por descuento.
- Mala recomendación.

Si FraSoHome analiza motivos de devolución, puede actuar antes de vender más. A veces la mejor analítica de ventas consiste en evitar ventas que no deberían producirse.

### 13.2 Riesgo de devolución

Un modelo de riesgo de devolución puede estimar qué ventas son más propensas a volver. Pero hay que tener cuidado con la acción.

No queremos discriminar clientes ni impedir compras sin justificación. Queremos mejorar decisión:

- Mejorar contenido del producto.
- Mostrar advertencias útiles.
- Recomendar productos menos problemáticos.
- Ajustar promociones.
- Revisar logística.

### 13.3 Stock

El stock convierte la predicción en posibilidad real. Una campaña sobre un producto sin stock frustra al cliente. Una recomendación de producto no disponible es una mala experiencia.

FraSoHome debe incorporar stock en campañas y recomendaciones. Si una tienda tiene exceso de ciertos productos y una audiencia local con afinidad, hay oportunidad. Si una categoría tiene demanda alta y stock bajo, quizá no conviene promocionarla.

### 13.4 Margen

El margen permite distinguir entre crecimiento rentable y crecimiento aparente.

Una acción comercial debería responder:

- ¿Qué margen esperamos?
- ¿Qué descuento requiere?
- ¿Qué coste de contacto tiene?
- ¿Qué riesgo de devolución incorpora?
- ¿Qué coste operativo puede generar?

El objetivo no es maximizar probabilidad de compra, sino optimizar valor esperado.

---

## 14. Diseñar un dataset de entrenamiento: la parte menos vistosa y más decisiva

Aquí está uno de los puntos más importantes para alumnos que ya conocen modelos. El dataset de entrenamiento no aparece por arte de magia. Hay que diseñarlo.

### 14.1 Unidad de predicción

Lo primero es decidir qué representa cada fila.

Para churn:

- Una fila por cliente en una fecha de corte.

Para propensión de categoría:

- Una fila por cliente y categoría en una fecha de corte.

Para riesgo de devolución:

- Una fila por línea de pedido o venta.

Para predicción de demanda:

- Una fila por producto, tienda y semana.

La unidad define todo lo demás: target, features y acción.

### 14.2 Fecha de corte

La fecha de corte separa pasado y futuro. Todo lo que usamos como feature debe estar disponible antes o en esa fecha. Todo lo que queremos predecir ocurre después.

Sin fecha de corte, es muy fácil cometer leakage.

### 14.3 Ventana de observación

La ventana de observación es el periodo histórico usado para crear features.

Ejemplo:

Últimos 180 días de compras, devoluciones, campañas y navegación.

La longitud de la ventana depende del negocio. En FraSoHome, algunas categorías tienen ciclos largos. Para muebles, quizá necesitamos mirar 12 o 24 meses. Para decoración, una ventana más corta puede capturar mejor intención.

### 14.4 Ventana de predicción

La ventana de predicción es el futuro donde observamos el target.

Ejemplo:

Compra de iluminación en los próximos 30 días.

Debe alinearse con la acción. Si la campaña dura una semana, predecir compra a 12 meses no ayuda mucho.

### 14.5 Target

El target debe ser concreto y observable.

Ejemplos:

- Compra o no compra en 30 días.
- Compra o no compra una categoría.
- Devuelve o no devuelve una línea.
- Margen generado en 60 días.
- Visita o no visita tienda.

Un target ambiguo genera modelos ambiguos.

### 14.6 Features

Las features deben tener sentido, estar disponibles y no filtrar futuro.

En FraSoHome:

- RFM.
- Margen histórico.
- Descuento medio.
- Canal preferido.
- Categoría favorita.
- Devoluciones previas.
- Clicks previos.
- Visitas previas.
- Campañas recibidas antes de la fecha de corte.
- Stock disponible si forma parte de la decisión.

### 14.7 Leakage

El leakage merece tratarse con ejemplos. Si queremos predecir conversión a campaña, no podemos usar fecha de conversión. Si queremos predecir devolución, no podemos usar motivo de devolución posterior. Si queremos predecir compra futura, no podemos usar revenue atribuido futuro.

El leakage es peligroso porque da resultados artificialmente buenos. El alumnado debe aprender a desconfiar de modelos "demasiado buenos".

---

## 15. Modelos baseline y evaluación: empezar simple para aprender rápido

Una tentación habitual es empezar por modelos sofisticados. Pero en proyectos de negocio conviene empezar por algo simple.

### 15.1 Por qué baseline

Un baseline permite saber si el proyecto aporta mejora real. Si una regla sencilla de recencia funciona casi igual que un modelo complejo, quizá no necesitamos más complejidad en la primera iteración.

Ejemplos:

- Churn baseline: clientes sin compra en 180 días.
- Propensión baseline: clientes que visitaron una categoría recientemente.
- Recomendación baseline: productos más comprados juntos.
- Campaña baseline: RFM alto y consentimiento válido.

### 15.2 Modelos útiles

Para clasificación:

- Regresión logística.
- Árbol de decisión.
- Random forest.
- Gradient boosting.

Para regresión:

- Regresión lineal.
- Random forest regressor.
- Gradient boosting regressor.

Para recomendación:

- Reglas de asociación.
- Item-based collaborative filtering.
- Popularidad contextual.

Para clustering:

- K-means.
- Modelos jerárquicos.
- DBSCAN en casos concretos.

La elección debe explicarse como una decisión de proyecto, no como concurso de algoritmos.

### 15.3 Evaluar según la acción

No se evalúa igual un modelo que decide una campaña masiva que uno que alerta sobre devoluciones o predice stock.

Si solo podemos contactar a 10.000 clientes, importa mucho el rendimiento en el top del ranking. Si el coste de falso positivo es bajo, podemos aceptar más ruido. Si el coste de falso negativo es alto, necesitamos recall.

La evaluación debe responder:

> ¿El modelo mejora la decisión concreta para la que fue creado?

### 15.4 Umbrales

Un modelo puede producir probabilidades, pero la empresa necesita decidir. El umbral convierte probabilidad en acción.

Ejemplo:

Contactar a clientes con propensión superior a 0,65.

Pero el umbral puede depender de:

- Capacidad de contacto.
- Coste.
- Margen esperado.
- Presión comercial.
- Stock.
- Riesgo.

No hay umbral universal. Hay decisión comercial.

---

## 16. Del modelo al playbook comercial

Un modelo que genera scores pero no se traduce en reglas de actuación queda incompleto. El playbook comercial convierte analítica en comportamiento organizativo.

### 16.1 Qué es un playbook

Un playbook define qué hacer en cada situación. Es una tabla de decisión enriquecida con criterio.

Ejemplo:

- Alto riesgo de churn + alto margen + contactable: campaña de reactivación prioritaria.
- Alto riesgo de churn + bajo margen: comunicación de bajo coste o no actuar.
- Alta propensión a categoría + stock alto: recomendación personalizada.
- Alta propensión + stock bajo: no promocionar o recomendar alternativa.
- Alto riesgo de devolución: contenido preventivo.

### 16.2 Next Best Action

Next Best Action significa elegir la acción más adecuada en un contexto. No siempre es vender. Puede ser informar, esperar, resolver incidencia o no contactar.

En FraSoHome, una Next Best Action debe considerar:

- Probabilidad de compra.
- Margen.
- Riesgo de churn.
- Riesgo de devolución.
- Stock.
- Canal.
- Consentimiento.
- Presión comercial.
- Experiencia.

### 16.3 Acción y responsabilidad

Un score no debe convertirse automáticamente en impacto comercial sin controles. Si el modelo recomienda descuentos a ciertos grupos de forma sistemática, puede erosionar margen o crear trato desigual. Si excluye clientes con datos incompletos, puede reforzar sesgos.

El playbook debe incorporar reglas de gobierno y revisión.

---

## 17. El ciclo completo de un proyecto ML en ventas

Este capítulo resume el recorrido completo. Es importante porque el alumnado puede saber entrenar modelos, pero no haber visto cómo se organiza un proyecto completo.

### 17.1 Formulación

El proyecto empieza con una decisión:

> Queremos mejorar la reactivación rentable de clientes dormidos.

No empieza con:

> Queremos usar XGBoost.

### 17.2 Datos

Se identifican fuentes:

- CRM.
- Ventas.
- Devoluciones.
- Campañas.
- Eventos digitales.
- Productos.
- Stock.
- Costes.

Se evalúa calidad, cobertura, granularidad y disponibilidad.

### 17.3 Preparación

Se construye fact table, Customer 360 y datasets por caso. Se tratan nulos, duplicados, formatos y claves.

### 17.4 Modelización

Se define target, features y división temporal. Se entrena baseline y modelos candidatos.

### 17.5 Evaluación

Se revisan métricas técnicas y económicas. Se analiza rendimiento por segmento, top decile y sensibilidad a umbral.

### 17.6 Activación

Se decide cómo usar el score:

- Audiencia.
- Canal.
- Oferta.
- Mensaje.
- Exclusiones.
- Control.

### 17.7 Medición

Se mide incrementalidad. Se compara tratamiento y control. Se analiza margen, conversión, devoluciones y experiencia.

### 17.8 Operación

Se despliega scoring periódico, monitorización, alertas y reentrenamiento.

Este ciclo permite transmitir una idea clara:

> El modelo es una pieza dentro de un sistema, no el sistema completo.

---

## 18. Métricas técnicas y métricas de negocio: dos idiomas que deben entenderse

Los equipos de datos hablan de AUC, precision, recall, RMSE o lift. Los equipos comerciales hablan de ventas, margen, conversión, ROI, stock y clientes recuperados. Un buen proyecto traduce entre ambos idiomas.

### 18.1 AUC

AUC mide capacidad de ordenar casos positivos por encima de negativos. Es útil para saber si el modelo discrimina.

Pero AUC no dice cuántos clientes debemos contactar ni cuánto margen generaremos.

### 18.2 Precision y recall

Precision mide cuántas predicciones positivas son correctas. Recall mide cuántos positivos reales detectamos.

En campaña, precision alta evita gastar contactos en clientes con baja probabilidad. Recall alto evita dejar escapar oportunidades. El equilibrio depende del coste de acción.

### 18.3 Lift

Lift es especialmente útil en marketing porque se trabaja por rankings. Si el top 10% del modelo convierte tres veces más que la media, el modelo concentra oportunidad.

Pero lift debe leerse con margen. Un top decile de alta conversión y bajo margen puede no ser el mejor.

### 18.4 RMSE y MAE

En predicción de ventas o demanda, MAE y RMSE miden error. RMSE penaliza errores grandes. MAE es más interpretable.

En stock, un error no cuesta igual en todos los productos. Fallar en un producto estratégico puede ser más grave que fallar en uno secundario.

### 18.5 Métricas económicas

Las métricas económicas cierran el proyecto:

- Margen incremental.
- ROI.
- Coste por cliente recuperado.
- Revenue per send.
- Reducción de devolución.
- Mejora de sell-through.
- Disminución de stockout.

La evaluación final debe responder:

> ¿La decisión mejoró el negocio?

---

## 19. Gobierno, privacidad y operación del modelo

La analítica de ventas trabaja con datos de clientes. Por tanto, debe ser responsable.

### 19.1 Privacidad y consentimiento

FraSoHome debe respetar finalidad y consentimiento. No todos los datos disponibles pueden usarse para todo. No todos los clientes pueden recibir cualquier comunicación.

La privacidad debe incluirse desde el diseño de la audiencia, no al final.

### 19.2 Minimización

Minimización significa usar los datos necesarios. Si una variable no aporta al caso o introduce riesgo, puede excluirse.

Esto es importante para ética, cumplimiento y robustez.

### 19.3 Sesgos

Los modelos aprenden de datos históricos. Si la historia está sesgada, el modelo puede reproducir sesgos.

En FraSoHome, puede haber sesgos por:

- Clientes anónimos.
- Diferencias de canal.
- Tiendas con distinta madurez.
- Campañas pasadas mal distribuidas.
- Zonas con menor cobertura.

### 19.4 MLOps

MLOps permite que el modelo funcione de forma repetible:

- Preparación consistente.
- Versionado.
- Scoring periódico.
- Monitorización.
- Alertas.
- Reentrenamiento.

En clase no hace falta profundizar en arquitectura, pero sí explicar que un modelo de aula y un modelo de producción son cosas distintas.

### 19.5 Drift

El comportamiento cambia. Cambian clientes, precios, promociones, competidores, stock y contexto económico. Por eso un modelo puede degradarse.

Monitorizar drift significa vigilar si las variables o resultados se alejan de lo conocido.

---

## 20. Puente hacia interpretabilidad: explicar para poder decidir

La sesión posterior de interpretabilidad encaja de forma natural. Después de diseñar modelos y acciones, llega una pregunta inevitable:

> ¿Por qué el modelo recomienda esto?

### 20.1 Explicación para negocio

Marketing no necesita solo saber que un cliente tiene score 0,82. Necesita entender por qué:

- Hace mucho que no compra.
- Compraba una categoría recurrente y dejó de hacerlo.
- No respondió a campañas recientes.
- Tiene afinidad digital activa.
- Su margen histórico justifica acción.

La explicación convierte score en confianza.

### 20.2 Explicación global

La explicación global ayuda a entender qué factores mueven el modelo en general.

Ejemplo:

En churn, las variables más importantes pueden ser recencia, frecuencia, respuesta a campañas y caída de engagement.

### 20.3 Explicación local

La explicación local justifica una predicción concreta.

Ejemplo:

El cliente C0042 tiene alto riesgo porque su recencia se disparó, dejó de abrir comunicaciones y no ha vuelto a comprar su categoría habitual.

### 20.4 SHAP, LIME y más allá

SHAP y LIME permiten explicar modelos complejos. Pero la sesión posterior debe ir más allá de la técnica: debe enseñar cómo convertir explicaciones en decisiones comprensibles.

Interpretar no es solo abrir la caja negra. Es traducir la lógica del modelo a lenguaje de negocio.

---

## 21. Glosario narrativo de conceptos comerciales y analíticos

### AOV

Average Order Value. Es el valor medio de pedido, especialmente usado en ecommerce. En FraSoHome ayuda a evaluar si las recomendaciones o bundles aumentan el valor de cesta.

### Atribución

Asignar una venta a una campaña o canal. Es útil para reporting, pero no demuestra por sí sola que la campaña causara la venta.

### Audiencia

Conjunto de clientes seleccionados para una acción comercial. Una buena audiencia incorpora score, reglas de negocio, consentimiento, exclusiones y capacidad operativa.

### Baseline

Solución sencilla que sirve de referencia. En FraSoHome puede ser un RFM, una regla de recencia o productos más vendidos.

### Churn

Pérdida o inactividad del cliente. En retail debe definirse con cuidado porque el cliente no cancela; simplemente deja de comprar.

### CLV

Customer Lifetime Value. Valor futuro esperado de un cliente. Debe considerar margen, frecuencia, duración esperada y costes.

### Contactabilidad

Capacidad de contactar a un cliente por un canal válido y con permiso adecuado.

### Conversión

Acción objetivo realizada: compra, click, redención, registro o visita. Siempre debe definirse el denominador.

### Cross-sell

Venta cruzada de productos complementarios. Debe aportar relevancia, no solo presión.

### Customer 360

Vista integrada del cliente orientada a decisión. Incluye identidad, valor, comportamiento, canal, campañas, devoluciones y consentimiento.

### Fact table

Tabla de hechos que registra eventos medibles. En ventas, suele contener líneas de venta, devoluciones o movimientos comerciales.

### Feature

Variable usada por un modelo. Debe estar disponible en el momento de decisión y tener sentido analítico o comercial.

### Granularidad

Nivel de detalle de una tabla. Define qué representa cada fila y condiciona todo el análisis.

### Holdout

Parte de la audiencia que no recibe acción para medir impacto incremental.

### Incrementalidad

Efecto adicional causado por una acción. Es la diferencia entre lo que ocurrió y lo que habría ocurrido sin intervenir.

### KPI

Indicador clave de rendimiento. Debe estar conectado con una decisión.

### Leakage

Uso indebido de información futura o no disponible en el momento de scoring. Produce modelos artificialmente buenos.

### Lift

Mejora respecto a la media o selección aleatoria. Muy útil en rankings comerciales.

### Margen

Valor económico que queda tras costes. Es clave para no optimizar solo revenue.

### MLOps

Prácticas para desplegar, monitorizar y mantener modelos en producción.

### Next Best Action

Siguiente mejor acción para un cliente según contexto, valor, riesgo, canal y restricciones.

### Propensión

Probabilidad de que un cliente realice una acción. Debe combinarse con margen e incrementalidad.

### RFM

Segmentación basada en recencia, frecuencia y valor monetario. Es un buen baseline, pero debe extenderse con margen, devoluciones y canal.

### ROI

Retorno de inversión. En campañas debería calcularse con margen incremental y costes reales.

### Score

Puntuación generada por una regla o modelo. Solo tiene valor si se convierte en acción.

### Stockout

Rotura de stock. Puede hacer fracasar una campaña aunque el modelo acierte la intención.

### Target

Variable objetivo que se quiere predecir. Debe ser observable, relevante y temporalmente correcto.

### Up-sell

Propuesta de una alternativa superior o de mayor valor. Debe respetar necesidades y contexto del cliente.

### Uplift

Incremento causado por una acción frente a control. Es clave para medir campañas.

### Ventana de observación

Periodo histórico usado para construir features.

### Ventana de predicción

Periodo futuro en el que se observa si ocurre el target.

---

## 22. Cierre

FraSoHome enseña que la analítica de ventas es una disciplina de conexión. Conecta datos dispersos con una visión común. Conecta KPIs con decisiones. Conecta modelos con acciones. Conecta campañas con medición. Conecta predicción con responsabilidad.

El mensaje final para el alumnado debería ser claro:

> Saber entrenar modelos es importante, pero en una empresa real el valor aparece cuando sabemos formular el problema, construir el dato correcto, elegir la métrica adecuada, activar la decisión y demostrar impacto.

En FraSoHome, el objetivo no es simplemente predecir quién comprará. El objetivo es decidir mejor:

- A quién contactar.
- Qué ofrecer.
- Por qué canal.
- Con qué incentivo.
- Con qué margen esperado.
- Con qué riesgo.
- Con qué medición.
- Con qué explicación.

Esa última palabra, explicación, abre la puerta a la siguiente sesión. Si un modelo afecta a clientes, campañas, descuentos, stock o recomendaciones, negocio necesita entenderlo. No basta con acertar: hay que poder justificar.

La pregunta que queda abierta es:

> Si FraSoHome usa modelos para decidir acciones comerciales, ¿cómo explicamos esas decisiones de forma clara, responsable y útil para quienes tienen que actuar sobre ellas?
