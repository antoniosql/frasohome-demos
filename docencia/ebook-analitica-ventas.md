# Analítica de Ventas aplicada al caso FraSoHome

## Ebook narrativo para una sesión de 8 horas

### Autoría y contexto

Material docente elaborado para una sesión de Analítica de Ventas, usando el caso FraSoHome como hilo conductor. El alumnado ya ha trabajado contenidos de Inteligencia de Clientes, fuentes de datos, modelización y explotación de la información. Este ebook no pretende repetir esa teoría desde cero, sino mostrar cómo se articula un proyecto analítico completo en un contexto comercial realista.

FraSoHome es una empresa ficticia, pero los problemas que representa son muy reales: datos dispersos, clientes no identificados, ventas en tienda y online, devoluciones, campañas, stock, costes, feedback de clientes y la presión constante de vender más sin destruir margen.

---

## Índice

1. [La pregunta de partida: vender mejor, no solo vender más](#1-la-pregunta-de-partida-vender-mejor-no-solo-vender-más)
2. [FraSoHome: una empresa omnicanal con datos imperfectos](#2-frasohome-una-empresa-omnicanal-con-datos-imperfectos)
3. [Del dato transaccional a la visión analítica](#3-del-dato-transaccional-a-la-visión-analítica)
4. [KPIs comerciales: medir ventas con criterio](#4-kpis-comerciales-medir-ventas-con-criterio)
5. [Customer 360: construir una vista accionable del cliente](#5-customer-360-construir-una-vista-accionable-del-cliente)
6. [Segmentación, RFM y valor de cliente](#6-segmentación-rfm-y-valor-de-cliente)
7. [Churn, propensión y modelos predictivos en ventas](#7-churn-propensión-y-modelos-predictivos-en-ventas)
8. [Cross-sell, up-sell, recomendación y cesta de la compra](#8-cross-sell-up-sell-recomendación-y-cesta-de-la-compra)
9. [Promociones, campañas e incrementalidad](#9-promociones-campañas-e-incrementalidad)
10. [Devoluciones, stock y margen: la otra cara de las ventas](#10-devoluciones-stock-y-margen-la-otra-cara-de-las-ventas)
11. [Del score a la acción comercial](#11-del-score-a-la-acción-comercial)
12. [El ciclo completo de un proyecto ML en ventas](#12-el-ciclo-completo-de-un-proyecto-ml-en-ventas)
13. [Métricas analíticas y métricas de negocio](#13-métricas-analíticas-y-métricas-de-negocio)
14. [Gobierno, privacidad y operación del modelo](#14-gobierno-privacidad-y-operación-del-modelo)
15. [Puente hacia la interpretabilidad](#15-puente-hacia-la-interpretabilidad)
16. [Glosario de conceptos comerciales y analíticos](#16-glosario-de-conceptos-comerciales-y-analíticos)

---

## 1. La pregunta de partida: vender mejor, no solo vender más

Cuando una empresa pide "analítica de ventas", muchas veces está formulando una necesidad de forma incompleta. Vender más puede parecer el objetivo evidente, pero en una empresa real no todas las ventas tienen el mismo valor.

Una venta puede ser poco rentable si exige mucho descuento. Puede ser problemática si termina en devolución. Puede generar tensión operativa si consume stock escaso. Puede incluso perjudicar la relación con el cliente si se consigue mediante una presión comercial excesiva o una recomendación poco adecuada.

Por eso, en FraSoHome la pregunta no debe ser simplemente:

> ¿Cómo vendemos más?

La pregunta madura es:

> ¿Cómo usamos los datos para decidir mejor qué vender, a quién, cuándo, por qué canal, con qué incentivo, con qué margen esperado y cómo medimos si la decisión ha generado valor real?

Esta diferencia es fundamental. La analítica de ventas no consiste en aplicar modelos sobre tablas. Consiste en diseñar un sistema de decisión. Ese sistema conecta cinco piezas:

- Un problema de negocio.
- Datos adecuados y gobernados.
- Un análisis o modelo.
- Una acción comercial.
- Una medición del impacto.

Si falta una de estas piezas, el proyecto queda cojo. Un modelo con muy buen AUC que no cambia ninguna decisión comercial aporta poco. Un dashboard precioso que no responde a una pregunta concreta aporta poco. Una campaña con buenos clicks pero sin grupo control puede aparentar éxito sin haber generado ventas incrementales.

FraSoHome es un buen caso para aprender esto porque obliga a mirar las ventas desde varios ángulos: cliente, producto, canal, campaña, stock, devolución y margen.

---

## 2. FraSoHome: una empresa omnicanal con datos imperfectos

FraSoHome es una cadena de muebles y decoración para el hogar. Vende en tiendas físicas y en ecommerce, tiene un programa de fidelización, gestiona campañas de marketing, recibe feedback de clientes, atiende incidencias y mantiene inventario por tienda y producto.

En apariencia, FraSoHome tiene muchos datos. El problema es que tener datos no equivale a tener capacidad analítica.

La empresa dispone de varias fuentes:

- CRM, con datos de clientes, fidelización y consentimiento.
- POS, con ventas realizadas en tienda física.
- Ecommerce, con pedidos online y líneas de pedido.
- Devoluciones online y en tienda.
- Maestro de productos, con categorías, precios y costes.
- Maestro de tiendas.
- Stock diario por producto y ubicación.
- Campañas de marketing.
- Contactos de campaña.
- Eventos web/app.
- Cupones.
- Costes operativos por transacción.
- Tickets de atención al cliente.
- Feedback y valoraciones.
- Señales de identidad de cliente.

Desde el punto de vista comercial, esto permite abordar preguntas muy ricas:

- ¿Qué categorías venden mejor por canal?
- ¿Qué clientes compran con más frecuencia?
- ¿Qué clientes han dejado de comprar?
- ¿Qué productos se devuelven más?
- ¿Qué campañas generan margen real?
- ¿Qué clientes responden a descuentos?
- ¿Qué productos conviene recomendar juntos?
- ¿Qué tiendas tienen stock disponible para campañas locales?

Desde el punto de vista analítico, también aparecen retos:

- Clientes duplicados.
- Clientes anónimos en ventas.
- Identificadores inconsistentes entre sistemas.
- Fechas en formatos distintos.
- Importes con símbolos, comas y puntos.
- Productos sin correspondencia limpia.
- Devoluciones con referencias incompletas.
- Campañas con conversiones difíciles de atribuir.
- Costes no siempre enlazados a todas las transacciones.

Estos problemas no son detalles técnicos menores. Afectan directamente a las decisiones de negocio.

Si un cliente aparece duplicado, su valor puede dividirse entre dos registros. Si una venta no se enlaza con CRM, no se puede activar a ese cliente. Si no se incorporan devoluciones, se sobreestima la rentabilidad. Si no se considera stock, se pueden recomendar productos no disponibles.

La primera lección de FraSoHome es clara:

> La calidad del dato no es un asunto técnico. Es una condición para decidir bien.

---

## 3. Del dato transaccional a la visión analítica

Una empresa como FraSoHome genera datos en sistemas operacionales. Estos sistemas están diseñados para que el negocio funcione: cobrar, registrar pedidos, gestionar devoluciones, actualizar stock o enviar campañas.

Los sistemas operacionales suelen tener una lógica transaccional. Un sistema POS registra cada venta de tienda. Una plataforma ecommerce registra pedidos. Un CRM registra clientes. Una herramienta de marketing registra envíos, aperturas y clicks.

El problema es que cada sistema mira el mundo desde su propia necesidad. Para analizar ventas de forma integrada necesitamos construir una visión analítica.

### 3.1 Sistemas transaccionales

Un sistema transaccional está pensado para registrar operaciones. Su prioridad es que cada operación quede guardada de forma correcta y rápida.

Ejemplos en FraSoHome:

- Un ticket de tienda.
- Un pedido online.
- Un pago.
- Una devolución.
- Una actualización de stock.
- Un contacto de campaña.

Estos sistemas no están necesariamente diseñados para responder preguntas de negocio complejas. Por ejemplo:

> ¿Qué margen neto generaron los clientes de alto valor impactados por una campaña de decoración, teniendo en cuenta devoluciones a 30 días?

Responder a eso exige combinar varias fuentes.

### 3.2 Data warehouse, datamart y modelo analítico

Un data warehouse es una capa donde los datos se integran, limpian y organizan para análisis. Un datamart es una parte más concreta, orientada a un área o dominio, como ventas o marketing.

En FraSoHome podríamos imaginar:

- Un data warehouse corporativo con todas las fuentes integradas.
- Un datamart comercial con ventas, clientes, productos, campañas y margen.
- Un datamart de operaciones con stock, devoluciones y logística.

La analítica de ventas necesita una estructura pensada para responder preguntas. Aquí aparecen dos conceptos esenciales: hechos y dimensiones.

### 3.3 Hechos y dimensiones

Una tabla de hechos registra eventos medibles. En ventas, un hecho puede ser una línea de venta, una devolución o un contacto de campaña.

Una dimensión describe el contexto del hecho:

- Cliente.
- Producto.
- Tienda.
- Canal.
- Fecha.
- Campaña.
- Cupón.

Si una línea de venta indica que se vendieron dos lámparas por 80 euros, las dimensiones nos dicen quién compró, dónde, cuándo, por qué canal, a qué categoría pertenece el producto y si hubo una campaña asociada.

### 3.4 Granularidad

La granularidad es el nivel de detalle de una tabla. Es uno de los conceptos más importantes en analítica aplicada.

Una tabla puede tener una fila por:

- Cliente.
- Pedido.
- Línea de pedido.
- Ticket.
- Línea de ticket.
- Producto.
- Producto y tienda por día.
- Contacto de campaña.
- Evento web.

La granularidad condiciona lo que podemos calcular. Si solo tenemos una fila por pedido, perdemos detalle de producto. Si solo tenemos una fila por cliente, perdemos secuencia temporal. Si mezclamos granularidades sin cuidado, duplicamos importes o calculamos mal los KPIs.

En FraSoHome, una buena fact table comercial debería permitir representar ventas y devoluciones a nivel de movimiento o línea, con referencias a cliente, producto, canal, tienda, fecha y campaña cuando existan.

### 3.5 Fact table comercial de FraSoHome

Una fact table comercial debería incluir, como mínimo:

- Identificador del movimiento.
- Fecha.
- Tipo de movimiento: venta o devolución.
- Canal: tienda, online, marketplace u otro.
- Cliente identificado si existe.
- Producto.
- Tienda o ubicación.
- Cantidad.
- Importe bruto.
- Descuento.
- Importe neto.
- Coste de producto.
- Coste operativo si está disponible.
- Margen.
- Campaña o cupón si aplica.

El objetivo no es construir una tabla bonita. El objetivo es poder responder preguntas con consistencia.

Por ejemplo:

- Ventas netas por categoría.
- Margen por canal.
- Tasa de devolución por producto.
- Rentabilidad por campaña.
- Valor neto por cliente.
- Stock disponible frente a demanda.

---

## 4. KPIs comerciales: medir ventas con criterio

Un KPI es un indicador clave de rendimiento. En inglés, Key Performance Indicator. Su función no es decorar un dashboard, sino ayudar a tomar decisiones.

Un buen KPI debe cumplir varias condiciones:

- Responde a una pregunta concreta.
- Está definido de forma inequívoca.
- Se calcula siempre igual.
- Es comparable en el tiempo.
- Está conectado con una acción posible.

En ventas, los KPIs más habituales pueden parecer sencillos, pero hay que definirlos con cuidado.

### 4.1 Ventas brutas

Las ventas brutas son el importe total vendido antes de restar descuentos, devoluciones u otros ajustes.

Sirven para medir actividad comercial, pero pueden ser engañosas. Si FraSoHome vende mucho aplicando descuentos agresivos, las ventas brutas pueden crecer mientras el margen cae.

### 4.2 Ventas netas

Las ventas netas son las ventas después de restar devoluciones, cancelaciones y ajustes relevantes.

Para FraSoHome son más útiles que las ventas brutas porque el negocio tiene devoluciones online y en tienda. Una campaña que genera muchas compras pero también muchas devoluciones puede no ser rentable.

### 4.3 Unidades vendidas

Las unidades vendidas miden volumen físico. Son especialmente útiles para operaciones y stock.

No deben confundirse con importe. Un sofá puede aportar más revenue que veinte velas decorativas, pero las velas pueden tener mayor rotación y margen.

### 4.4 Ticket medio y AOV

El ticket medio es el importe medio por transacción en tienda.

El AOV, Average Order Value, es el valor medio de pedido en ecommerce. En la práctica ambos reflejan cuánto compra un cliente en una operación.

Se calculan como:

> Importe total / Número de tickets o pedidos

Estos indicadores son útiles para medir estrategias de cross-sell, packs, promociones o recomendación.

### 4.5 Frecuencia de compra

La frecuencia indica cuántas veces compra un cliente en un periodo. Es una variable central para entender fidelidad.

En FraSoHome, la frecuencia debe interpretarse según categoría. Un cliente no compra sofás cada mes, pero puede comprar decoración o textil de forma más recurrente.

### 4.6 Recencia

La recencia mide cuánto tiempo ha pasado desde la última compra. Es un indicador muy utilizado en RFM y churn.

Cuanto menor es la recencia, más reciente es la relación. Un cliente que compró ayer está más activo que uno que no compra desde hace un año.

### 4.7 Margen bruto

El margen bruto mide la diferencia entre ingreso de venta y coste del producto.

> Margen bruto = Ingreso neto - Coste del producto

Es clave porque no todos los productos aportan el mismo beneficio. En FraSoHome, dos categorías pueden vender importes similares pero generar márgenes muy distintos.

### 4.8 Margen neto aproximado

El margen neto incorpora otros costes, como coste de contacto, coste logístico, coste de devolución o coste operativo.

> Margen neto = Ingreso neto - Coste producto - Costes operativos

En proyectos comerciales, el margen neto es esencial para decidir si una campaña compensa.

### 4.9 Tasa de devolución

La tasa de devolución mide qué proporción de ventas acaba devuelta.

Puede calcularse por unidades o por importe:

> Tasa de devolución por unidades = Unidades devueltas / Unidades vendidas

> Tasa de devolución por importe = Importe devuelto / Importe vendido

En FraSoHome es una métrica crítica. Una categoría con mucha devolución puede indicar problemas de calidad, expectativas mal gestionadas, fichas de producto pobres o promociones mal orientadas.

### 4.10 Conversión

La conversión mide cuántos usuarios realizan una acción deseada.

Ejemplos:

- Comprar tras visitar la web.
- Comprar tras recibir una campaña.
- Redimir un cupón.
- Añadir un producto al carrito.

La conversión se calcula como:

> Conversiones / Oportunidades

El reto es definir bien qué cuenta como oportunidad. En una campaña, puede ser un cliente contactado. En ecommerce, puede ser una sesión. En tienda, puede ser una visita.

### 4.11 Revenue per send

Revenue per send mide el ingreso generado por cada envío de campaña.

> Revenue per send = Revenue atribuido / Número de envíos

Es útil en email, SMS o push. Sin embargo, debe usarse con cuidado: revenue atribuido no siempre significa revenue incremental.

### 4.12 ROI

ROI significa Return on Investment. Mide el retorno de una inversión.

> ROI = (Beneficio generado - Coste de la acción) / Coste de la acción

En campañas, conviene calcular ROI sobre margen incremental, no solo sobre ventas atribuidas. Si una campaña ofrece un descuento grande a clientes que habrían comprado igualmente, puede tener buen revenue y mal ROI.

### 4.13 Sell-through

Sell-through mide qué proporción del stock disponible se ha vendido en un periodo.

> Sell-through = Unidades vendidas / Stock disponible inicial o stock recibido

Es útil para decidir promociones, reposición y campañas locales. En FraSoHome, si una tienda tiene mucho stock de una categoría con buena afinidad local, puede activarse una campaña específica.

### 4.14 Stockout y sobrestock

Stockout significa rotura de stock: el cliente quiere comprar, pero no hay disponibilidad.

Sobrestock significa exceso de inventario: hay producto inmovilizado que consume espacio y capital.

Ambos problemas afectan a ventas:

- El stockout limita revenue y empeora experiencia.
- El sobrestock presiona descuentos y reduce margen.

---

## 5. Customer 360: construir una vista accionable del cliente

Customer 360 es una vista integrada del cliente. No es solo una tabla con muchos campos. Es una representación útil para tomar decisiones comerciales.

En FraSoHome, un Customer 360 debería responder preguntas como:

- ¿Quién es el cliente?
- ¿Está identificado de forma fiable?
- ¿Se le puede contactar?
- ¿Qué ha comprado?
- ¿Dónde compra?
- ¿Cuánto margen genera?
- ¿Qué categorías le interesan?
- ¿Responde a campañas?
- ¿Devuelve mucho?
- ¿Es sensible al descuento?
- ¿Está activo o dormido?
- ¿Qué acción comercial tiene más sentido?

### 5.1 Identidad de cliente

La identidad de cliente consiste en reconocer que varias señales pertenecen a la misma persona.

En retail omnicanal esto es complicado. Un cliente puede:

- Comprar online con email.
- Comprar en tienda sin identificarse.
- Usar una tarjeta de fidelización.
- Navegar con una cookie.
- Abrir una app con un device_id.
- Usar distintos emails.

La resolución de identidad intenta consolidar esas señales en un customer_id canónico.

En FraSoHome existen señales de identidad y también ventas anónimas. Esto abre una cuestión comercial importante: aumentar la identificación de clientes no es solo una mejora técnica, sino una palanca de activación.

Si no identificamos al cliente, no podemos calcular bien su valor ni personalizar acciones.

### 5.2 Contactabilidad y consentimiento

Contactabilidad significa que podemos contactar con el cliente por algún canal válido: email, SMS, teléfono, app, etc.

Consentimiento significa que tenemos permiso para usar sus datos o impactarle con comunicaciones comerciales según la finalidad correspondiente.

En marketing basado en datos, no basta con tener un email. Hay que saber si se puede usar, para qué finalidad y bajo qué condiciones.

En FraSoHome, el consentimiento aparece con valores heterogéneos. Eso obliga a normalizarlo antes de activar campañas.

### 5.3 Valor de cliente

El valor de cliente puede medirse de varias formas:

- Revenue total.
- Margen total.
- Frecuencia de compra.
- Valor futuro esperado.
- CLV.

CLV significa Customer Lifetime Value. Es el valor económico esperado de un cliente durante su relación futura con la empresa.

En una versión simple, podemos aproximarlo con:

> Valor esperado = Frecuencia esperada x Margen medio x Duración esperada de la relación

En una empresa como FraSoHome, conviene ajustar el valor con devoluciones, descuentos y costes.

### 5.4 Preferencia de canal

La preferencia de canal describe dónde interactúa o compra más el cliente:

- Tienda física.
- Ecommerce.
- App.
- Email.
- SMS.
- Atención telefónica.

No todos los clientes responden igual al mismo canal. Una acción comercial eficaz debe tener en cuenta dónde es más probable que el cliente actúe.

### 5.5 Sensibilidad al descuento

La sensibilidad al descuento indica hasta qué punto un cliente compra principalmente cuando hay promociones.

Puede medirse con variables como:

- Porcentaje de compras con descuento.
- Descuento medio recibido.
- Conversión en campañas promocionales frente a no promocionales.
- Diferencia de compra en periodos promocionales y no promocionales.

Comercialmente, es un concepto delicado. Un cliente muy sensible al descuento puede aumentar ventas, pero reducir margen. Además, si se le acostumbra a descuentos constantes, puede dejar de comprar a precio normal.

### 5.6 Engagement digital

Engagement digital mide la interacción con canales digitales:

- Visitas web.
- Sesiones app.
- Vistas de producto.
- Añadidos al carrito.
- Clicks en campañas.
- Búsquedas.
- Abandono de checkout.

Estas señales son útiles para propensión de compra porque aparecen antes de la venta. Si un cliente ha visitado varias fichas de lámparas y ha añadido una al carrito, puede estar mostrando intención.

### 5.7 Voz del cliente

La voz del cliente agrupa feedback, valoraciones, tickets, comentarios, motivos de devolución y cualquier texto donde el cliente exprese experiencia, satisfacción o problemas.

En FraSoHome puede servir para:

- Detectar productos problemáticos.
- Entender motivos de devolución.
- Mejorar fichas de producto.
- Adaptar mensajes comerciales.
- Identificar objeciones recurrentes.

La voz del cliente conecta analítica de ventas con experiencia de cliente.

---

## 6. Segmentación, RFM y valor de cliente

Segmentar es dividir la base de clientes en grupos con significado. El objetivo no es etiquetar por etiquetar, sino decidir tratamientos diferentes.

Una segmentación comercial útil debe cumplir tres condiciones:

- Los segmentos son comprensibles.
- Los segmentos se comportan de forma diferente.
- Los segmentos permiten acciones diferentes.

### 6.1 RFM clásico

RFM es una técnica clásica de segmentación basada en tres variables:

- Recency: cuánto tiempo ha pasado desde la última compra.
- Frequency: cuántas veces ha comprado.
- Monetary: cuánto ha gastado.

La lógica es sencilla:

- Un cliente que ha comprado recientemente está más activo.
- Un cliente que compra con frecuencia está más vinculado.
- Un cliente que gasta mucho aporta más valor.

El scoring RFM suele asignar puntuaciones, por ejemplo de 1 a 5, a cada dimensión. Luego se combinan para formar segmentos.

Ejemplo:

- R=5, F=5, M=5: clientes excelentes.
- R=1, F=5, M=5: clientes de alto valor dormidos.
- R=5, F=1, M=1: compradores recientes pero todavía poco valiosos.

### 6.2 Limitaciones del RFM

RFM es potente como baseline, pero no basta para FraSoHome.

Sus limitaciones:

- Mira gasto, pero no margen.
- No considera devoluciones.
- No diferencia categorías.
- No entiende preferencias de canal.
- No considera respuesta a campañas.
- No incluye señales digitales previas a la compra.
- No distingue sensibilidad al descuento.
- No incorpora stock ni restricciones operativas.

Un cliente con alto Monetary puede parecer muy valioso, pero si devuelve mucho o compra solo con descuentos profundos, su valor real puede ser menor.

### 6.3 RFM extendido

En FraSoHome conviene evolucionar hacia un RFM extendido:

- Recencia de compra.
- Frecuencia de compra.
- Margen neto.
- Tasa de devolución.
- Categorías preferidas.
- Canal preferido.
- Porcentaje de compras con descuento.
- Engagement digital.
- Contactabilidad.
- Respuesta histórica a campañas.

Este enfoque permite construir segmentos más accionables.

### 6.4 Segmentos comerciales posibles

Algunos segmentos útiles en FraSoHome:

**Clientes VIP rentables**

Compran con frecuencia, generan margen alto y devuelven poco. Deben cuidarse con experiencia, prioridad, novedades o beneficios no necesariamente basados en descuento.

**Clientes de alto valor dormidos**

Compraron mucho en el pasado, pero llevan tiempo sin comprar. Son candidatos a reactivación, siempre que sigan siendo contactables y tengan margen esperado suficiente.

**Clientes promocionales**

Compran sobre todo con descuento. Pueden activar volumen, pero hay que controlar margen y dependencia promocional.

**Clientes con alta devolución**

Generan ventas, pero también coste y fricción. La acción no siempre debe ser venderles más, sino venderles mejor: información, asesoramiento, fichas de producto claras o categorías menos problemáticas.

**Clientes digitales con intención**

Navegan, visitan productos o añaden al carrito, pero no siempre compran. Son candidatos a acciones de conversión o remarketing.

**Clientes locales**

Tienen afinidad con una tienda concreta. Pueden activarse con campañas de stock local, eventos en tienda o click & collect.

### 6.5 Clustering

El clustering es una técnica no supervisada que agrupa observaciones según similitud. En ventas puede usarse para descubrir grupos de clientes sin definir previamente las etiquetas.

Ejemplos de variables para clustering:

- Recencia.
- Frecuencia.
- Margen.
- Tasa de devolución.
- Descuento medio.
- Porcentaje online.
- Categorías compradas.
- Engagement digital.

El resultado de un clustering no es automáticamente útil. Hay que interpretarlo y convertirlo en segmentos con sentido comercial.

Un cluster llamado "Cluster 3" no sirve a negocio. Un segmento llamado "Decoración recurrente sensible a promociones" sí puede servir.

---

## 7. Churn, propensión y modelos predictivos en ventas

Los modelos predictivos intentan anticipar comportamientos futuros. En ventas y marketing suelen usarse para priorizar acciones.

La clave es entender que un modelo no decide por sí solo. Un modelo genera una señal. La empresa decide cómo usarla.

### 7.1 Churn

Churn significa abandono. En negocios de suscripción, churn suele significar que el cliente cancela. En retail como FraSoHome es más ambiguo, porque los clientes no anuncian que abandonan; simplemente dejan de comprar.

Por eso hay que definir churn de forma operativa.

Ejemplos:

- Cliente que no compra en los próximos 180 días.
- Cliente cuya frecuencia cae por debajo de su patrón histórico.
- Cliente que no vuelve a comprar tras una devolución negativa.
- Cliente activo el año pasado que no compra en el año actual.

La definición debe adaptarse al ciclo de compra. En muebles, los ciclos son más largos que en alimentación o moda.

### 7.2 Reactivación

Reactivación es la acción comercial dirigida a clientes inactivos o en riesgo de abandono.

No todos los clientes en riesgo deben reactivarse con la misma intensidad. Hay que tener en cuenta:

- Margen esperado.
- Probabilidad de respuesta.
- Coste de contacto.
- Incentivo necesario.
- Riesgo de devolución.
- Consentimiento.

Un modelo de churn debe conectarse con una estrategia de reactivación. Si no hay acción, el score no sirve.

### 7.3 Propensión

Propensión es la probabilidad de que un cliente realice una acción.

Ejemplos:

- Propensión a comprar.
- Propensión a comprar una categoría.
- Propensión a responder a una campaña.
- Propensión a redimir un cupón.
- Propensión a visitar una tienda.
- Propensión a devolver.

En FraSoHome, un caso muy útil es propensión de compra por categoría. Por ejemplo, estimar qué clientes tienen más probabilidad de comprar iluminación, textil o decoración en los próximos 30 días.

### 7.4 Target

El target es la variable objetivo que queremos predecir.

En clasificación, suele ser una variable binaria o categórica:

- Compra / no compra.
- Churn / no churn.
- Devuelve / no devuelve.
- Categoría comprada.

En regresión, puede ser una variable continua:

- Importe esperado.
- Margen esperado.
- Unidades vendidas.

Definir bien el target es una de las partes más importantes del proyecto. Un target mal definido genera modelos inútiles aunque el algoritmo sea sofisticado.

### 7.5 Ventana de observación y ventana de predicción

La ventana de observación es el periodo histórico usado para construir features.

La ventana de predicción es el periodo futuro donde observamos si ocurre el target.

Ejemplo:

- Observación: compras, visitas y campañas de enero a junio.
- Predicción: compra en julio.

Esta separación temporal evita usar información del futuro para predecir el pasado.

### 7.6 Leakage

Leakage, o fuga de información, ocurre cuando el modelo usa información que no estaría disponible en el momento real de la decisión.

Ejemplos en FraSoHome:

- Usar "fecha_conversion_30d" para predecir si convertirá en 30 días.
- Usar "cupón redimido" para predecir respuesta a campaña antes de enviarla.
- Usar una devolución posterior para predecir riesgo antes de la venta.
- Usar revenue atribuido a campaña para decidir a quién enviar la campaña.

El leakage puede hacer que el modelo parezca excelente en validación y fracase en producción.

### 7.7 Features

Las features son variables explicativas usadas por el modelo.

Ejemplos:

- Días desde última compra.
- Número de compras en 12 meses.
- Margen neto acumulado.
- Porcentaje de compras online.
- Categoría favorita.
- Descuento medio.
- Número de devoluciones.
- Clicks en campañas.
- Visitas web recientes.
- Stock disponible en tienda cercana.

Una buena feature debe estar disponible en el momento de scoring, tener sentido de negocio y aportar señal.

### 7.8 Baseline

Un baseline es una primera solución sencilla que sirve como referencia.

Ejemplos:

- Regla RFM.
- Regresión logística.
- Árbol sencillo.
- Ranking por recencia.
- Recomendación de productos más vendidos.

El baseline permite responder:

> ¿La solución compleja mejora de verdad algo simple?

En proyectos reales, empezar por un baseline evita perder tiempo en complejidad prematura.

---

## 8. Cross-sell, up-sell, recomendación y cesta de la compra

En ventas, no todo consiste en captar nuevos clientes. Gran parte del valor está en vender mejor a clientes existentes.

### 8.1 Cross-sell

Cross-sell, o venta cruzada, consiste en ofrecer un producto complementario al que el cliente ya compra o muestra intención de comprar.

Ejemplos en FraSoHome:

- Si compra una mesa, recomendar sillas.
- Si compra una funda nórdica, recomendar cojines.
- Si compra una lámpara, recomendar bombillas compatibles.

El cross-sell busca aumentar valor de cesta y mejorar experiencia si la recomendación es útil.

### 8.2 Up-sell

Up-sell consiste en ofrecer una versión superior, más completa o de mayor valor del producto que el cliente está considerando.

Ejemplos:

- Recomendar una mesa extensible en lugar de una fija.
- Ofrecer un sofá de mejor material.
- Proponer un pack premium.

El up-sell debe manejarse con cuidado. Si se percibe agresivo, puede perjudicar la experiencia.

### 8.3 Recomendadores

Un sistema recomendador prioriza productos para un cliente o contexto.

Tipos sencillos:

- Productos más vendidos.
- Productos relacionados por categoría.
- Productos comprados juntos.
- Recomendación basada en historial del cliente.
- Recomendación basada en clientes similares.

En FraSoHome, una recomendación responsable debería incorporar:

- Afinidad del cliente.
- Complementariedad del producto.
- Stock disponible.
- Margen.
- Riesgo de devolución.
- Restricciones de marca o campaña.

### 8.4 Análisis de cesta

El análisis de cesta estudia qué productos se compran juntos.

Una técnica habitual son las reglas de asociación. Estas reglas tienen forma:

> Si un cliente compra A, también suele comprar B.

Conceptos clave:

**Soporte**

Frecuencia con la que aparece una combinación en las cestas.

**Confianza**

Probabilidad de comprar B cuando se ha comprado A.

**Lift**

Mide cuánto más probable es comprar B cuando se compra A frente a comprar B en general.

Ejemplo:

Si quienes compran mesas compran sillas mucho más que la media, hay una relación útil para cross-sell.

### 8.5 Recomendación con restricciones

En clase conviene insistir en que recomendar no es solo maximizar probabilidad de compra.

FraSoHome debería evitar:

- Recomendar productos sin stock.
- Recomendar productos con margen negativo.
- Recomendar productos con alta devolución sin avisos.
- Recomendar productos incompatibles.
- Saturar al cliente con demasiadas ofertas.

La buena recomendación combina modelo y reglas de negocio.

---

## 9. Promociones, campañas e incrementalidad

Las campañas son el puente entre analítica y acción comercial. Una campaña convierte una hipótesis en una intervención sobre clientes.

### 9.1 Campaña

Una campaña es una acción planificada para impactar a una audiencia con un mensaje, oferta o incentivo.

Elementos:

- Objetivo.
- Audiencia.
- Canal.
- Mensaje.
- Oferta.
- Calendario.
- Coste.
- Métrica de éxito.

En FraSoHome puede haber campañas de decoración, iluminación, rebajas, lanzamiento de colección o reactivación.

### 9.2 Audiencia

La audiencia es el conjunto de clientes seleccionados para una acción.

Puede definirse por:

- Segmento RFM.
- Propensión.
- Categoría favorita.
- Canal preferido.
- Tienda cercana.
- Stock disponible.
- Riesgo de churn.
- Consentimiento.

Una audiencia bien diseñada incluye exclusiones. Por ejemplo, excluir clientes sin consentimiento, clientes saturados por impactos recientes o clientes con incidencias abiertas.

### 9.3 Presión comercial

La presión comercial mide cuántos impactos recibe un cliente en un periodo.

Demasiada presión puede causar:

- Fatiga.
- Bajas de comunicaciones.
- Menor tasa de apertura.
- Peor percepción de marca.

En marketing de precisión no se trata de impactar más, sino de impactar mejor.

### 9.4 Atribución

Atribución es el proceso de asignar una venta a una campaña o canal.

Ejemplo:

Un cliente recibe un email, hace click y compra a los tres días. Podemos atribuir esa venta al email.

El problema es que atribuir no demuestra causalidad. Tal vez el cliente habría comprado igualmente.

### 9.5 Incrementalidad

Incrementalidad mide el efecto adicional causado por una acción.

La pregunta no es:

> ¿Cuánto compraron los clientes impactados?

La pregunta correcta es:

> ¿Cuánto compraron de más gracias a la campaña respecto a lo que habrían comprado sin campaña?

Esta diferencia es central.

### 9.6 Grupo control y holdout

Un grupo control es un conjunto de clientes similares a la audiencia tratada, pero que no recibe la acción.

El holdout es una parte retenida sin impacto para medir qué habría pasado sin campaña.

Ejemplo:

- 90% recibe campaña.
- 10% no recibe campaña.

Si el grupo tratado convierte al 8% y el control al 5%, el uplift observado es de 3 puntos porcentuales.

### 9.7 Uplift

Uplift mide el incremento de respuesta causado por una acción.

> Uplift = Conversión tratamiento - Conversión control

También puede medirse en margen:

> Margen incremental = Margen tratamiento - Margen esperado según control

En FraSoHome, uplift es más relevante que conversión bruta porque permite separar clientes persuadidos de clientes que habrían comprado de todos modos.

### 9.8 Promociones y elasticidad

Una promoción reduce precio o añade incentivo para estimular compra.

Elasticidad promocional mide cómo cambia la demanda ante cambios de precio o descuento.

Clientes o categorías con alta elasticidad reaccionan mucho al descuento. Clientes o categorías con baja elasticidad apenas cambian.

El riesgo comercial es promocionar donde no hace falta. Si un cliente iba a comprar sin descuento, el incentivo destruye margen.

---

## 10. Devoluciones, stock y margen: la otra cara de las ventas

La analítica de ventas suele centrarse en revenue, pero en retail hay tres dimensiones que cambian completamente la lectura: devoluciones, stock y margen.

### 10.1 Devoluciones

Una devolución no es solo una venta anulada. Tiene costes:

- Reembolso.
- Logística inversa.
- Reacondicionamiento.
- Atención al cliente.
- Posible pérdida de producto.
- Mala experiencia.

Analizar devoluciones permite detectar:

- Productos con problemas.
- Categorías con expectativas mal gestionadas.
- Canales con más incidencias.
- Clientes con comportamiento anómalo.
- Promociones que generan compras poco reflexivas.

### 10.2 Riesgo de devolución

Un modelo de riesgo de devolución estima la probabilidad de que una venta acabe devuelta.

Puede usar:

- Producto.
- Categoría.
- Precio.
- Descuento.
- Canal.
- Histórico del cliente.
- Motivos previos de devolución.
- Tiempo de entrega.
- Feedback.

La acción no tiene por qué ser bloquear la venta. Puede ser:

- Mejorar ficha de producto.
- Mostrar medidas más claras.
- Añadir contenido preventivo.
- Recomendar alternativa con menor devolución.
- Revisar campañas que empujan productos problemáticos.

### 10.3 Stock

Stock es disponibilidad de producto.

En analítica comercial, el stock condiciona qué podemos vender. Un modelo puede detectar alta propensión a comprar una lámpara, pero si no hay stock, la recomendación no sirve.

Variables útiles:

- Stock actual.
- Stock mínimo.
- Stock reservado.
- Stock en tránsito.
- Días sin stock.
- Rotación.
- Sell-through.

### 10.4 Stock-aware marketing

Stock-aware marketing significa activar campañas teniendo en cuenta disponibilidad.

Ejemplo:

Si una tienda de A Coruña tiene sobrestock de textil y existe una audiencia local con afinidad a esa categoría, FraSoHome puede lanzar una campaña local.

Esto conecta marketing con operaciones.

### 10.5 Margen

El margen es lo que permite distinguir venta de valor.

Una campaña puede generar mucho revenue pero poco margen si:

- Usa descuentos altos.
- Empuja productos de bajo margen.
- Genera devoluciones.
- Tiene costes logísticos elevados.
- Contacta a clientes que habrían comprado igualmente.

Por eso, los modelos comerciales deberían priorizar valor esperado, no solo probabilidad de compra.

---

## 11. Del score a la acción comercial

Un score es una puntuación generada por una regla o modelo. Puede representar probabilidad, riesgo, prioridad o valor esperado.

Ejemplos:

- Score de churn.
- Score de propensión.
- Score de valor.
- Score de riesgo de devolución.
- Score de afinidad de categoría.

El error habitual es pensar que el proyecto termina al generar el score. En realidad, el score solo empieza a ser útil cuando se convierte en acción.

### 11.1 Ranking

Un ranking ordena clientes, productos o acciones según prioridad.

Por ejemplo:

- Clientes ordenados por riesgo de churn.
- Productos ordenados por probabilidad de compra.
- Clientes ordenados por margen incremental esperado.

El ranking permite trabajar con capacidad limitada. Si solo podemos contactar al 20% de la base, hay que elegir.

### 11.2 Umbral

El umbral define a partir de qué score se toma una acción.

Ejemplo:

- Contactar clientes con propensión superior a 0,70.
- Revisar ventas con riesgo de devolución superior a 0,60.

El umbral no debe elegirse solo por métrica técnica. Debe considerar:

- Coste de contacto.
- Margen esperado.
- Capacidad operativa.
- Saturación del cliente.
- Riesgo de error.

### 11.3 Next Best Action

Next Best Action es la siguiente mejor acción para un cliente en un contexto concreto.

No es solo "qué producto vender". Puede ser:

- No contactar.
- Enviar contenido inspiracional.
- Ofrecer descuento.
- Recomendar producto complementario.
- Invitar a tienda.
- Pedir feedback.
- Resolver incidencia antes de vender.

En FraSoHome, una Next Best Action debería combinar:

- Valor de cliente.
- Intención.
- Canal preferido.
- Stock.
- Margen.
- Riesgo de devolución.
- Consentimiento.

### 11.4 Playbook comercial

Un playbook comercial traduce scores y segmentos en acciones.

Ejemplo:

| Situación | Acción |
| --- | --- |
| Alto churn y alto margen | Reactivación prioritaria con categoría favorita |
| Alto churn y bajo margen | Contacto de bajo coste o exclusión |
| Alta propensión y stock alto | Recomendación personalizada |
| Alta devolución | Mensaje preventivo o mejora de contenido |
| Alta sensibilidad a descuento | Incentivo controlado |
| Cliente VIP | Experiencia preferente, no necesariamente descuento |

El playbook es lo que permite que marketing, ventas y operaciones usen el modelo de forma consistente.

---

## 12. El ciclo completo de un proyecto ML en ventas

Los alumnos suelen conocer algoritmos, pero muchas veces no han visto el ciclo completo de un proyecto ML. FraSoHome permite recorrerlo de principio a fin.

### 12.1 Problema de negocio

Todo empieza con una decisión a mejorar.

Mal planteado:

> Hacer un modelo de churn.

Bien planteado:

> Priorizar clientes contactables de alto valor con riesgo de inactividad para una campaña de reactivación rentable.

### 12.2 Unidad de decisión

La unidad de decisión define sobre qué elemento se decide:

- Cliente.
- Pedido.
- Línea de pedido.
- Producto.
- Tienda.
- Campaña.
- Contacto.

Para churn, la unidad suele ser cliente. Para riesgo de devolución, puede ser línea de pedido. Para stock, puede ser producto-tienda-semana.

### 12.3 Datos disponibles

Hay que inventariar fuentes y evaluar si realmente contienen lo necesario.

En FraSoHome:

- CRM aporta identidad y atributos.
- Fact transacciones aporta histórico comercial.
- Campañas aportan exposición y respuesta.
- Eventos web/app aportan intención.
- Productos aportan categoría y coste.
- Devoluciones aportan fricción.
- Stock aporta restricción operativa.
- Costes aportan rentabilidad.

### 12.4 Preparación de datos

Incluye:

- Tipado.
- Limpieza.
- Normalización de IDs.
- Parseo de fechas.
- Tratamiento de nulos.
- Detección de duplicados.
- Integridad referencial.
- Construcción de fact table.
- Agregación a nivel de unidad de decisión.

Esta fase no es burocracia. Define qué podrá aprender el modelo.

### 12.5 Diseño del target

El target debe ser observable, relevante y temporalmente correcto.

Ejemplo:

Para churn:

- Fecha de corte: 30 de junio.
- Features: comportamiento hasta el 30 de junio.
- Target: compra o no compra entre julio y septiembre.

### 12.6 Feature engineering

Feature engineering es el proceso de crear variables útiles para el modelo.

En ventas suele incluir:

- Agregaciones temporales.
- Ratios.
- Indicadores de comportamiento.
- Variables de canal.
- Variables de categoría.
- Variables de campaña.
- Variables de margen.
- Variables de devolución.

Ejemplo:

> Porcentaje de compras con descuento en los últimos 12 meses.

Esta variable puede capturar sensibilidad promocional.

### 12.7 División entrenamiento/test

La evaluación debe respetar el tiempo. En problemas comerciales, muchas veces conviene entrenar con periodos antiguos y validar con periodos posteriores.

Una división aleatoria puede ser peligrosa si mezcla futuro y pasado.

### 12.8 Entrenamiento

Entrenar consiste en ajustar el modelo con datos históricos.

Modelos posibles:

- Regresión logística.
- Árbol de decisión.
- Random forest.
- Gradient boosting.
- Redes neuronales.
- Modelos de supervivencia.
- Reglas de asociación.
- Recomendadores.

La elección depende del problema, datos, necesidad de explicación, tiempo y capacidad de despliegue.

### 12.9 Evaluación técnica

Se mide si el modelo predice razonablemente bien.

Métricas:

- AUC.
- Precision.
- Recall.
- F1.
- Lift.
- MAE.
- RMSE.
- Precision@K.

Pero la evaluación técnica no basta.

### 12.10 Evaluación económica

Se mide si el modelo ayuda a ganar dinero, ahorrar coste o mejorar una decisión.

Preguntas:

- ¿Aumenta margen incremental?
- ¿Reduce devoluciones?
- ¿Mejora conversión frente a grupo control?
- ¿Reduce contactos innecesarios?
- ¿Optimiza stock?
- ¿Mejora experiencia de cliente?

### 12.11 Scoring

Scoring es aplicar el modelo a datos nuevos para generar puntuaciones.

Ejemplo:

Cada lunes, FraSoHome calcula:

- Riesgo de churn por cliente.
- Propensión por categoría.
- Recomendaciones.
- Riesgo de devolución por producto/pedido.

### 12.12 Activación

Activar significa usar el scoring en un proceso real:

- CRM.
- Email.
- SMS.
- App.
- Web.
- Tienda.
- Dashboard comercial.
- Sistema de recomendación.

### 12.13 Monitorización

Una vez desplegado, el modelo debe monitorizarse.

Aspectos:

- Calidad de datos de entrada.
- Distribución de features.
- Distribución de scores.
- Performance técnica.
- Performance comercial.
- Drift.
- Incidencias.

### 12.14 Reentrenamiento

Los modelos envejecen. Cambian clientes, campañas, precios, stock, contexto económico y comportamiento.

Reentrenar significa actualizar el modelo con datos más recientes.

No siempre debe hacerse automáticamente. Conviene definir criterios:

- Deterioro de métricas.
- Cambio fuerte de distribución.
- Nuevo catálogo.
- Nueva política comercial.
- Estacionalidad.

---

## 13. Métricas analíticas y métricas de negocio

Una de las competencias clave en analítica aplicada es distinguir métricas técnicas de métricas de negocio.

### 13.1 AUC

AUC mide la capacidad de un modelo de clasificación para ordenar positivos por encima de negativos.

Es útil cuando queremos saber si el modelo discrimina bien. Pero no dice directamente cuánto dinero gana la empresa.

Un modelo con AUC alto puede no ser el mejor si sus errores afectan a clientes de alto valor o si selecciona clientes poco rentables.

### 13.2 Precision

Precision mide, de los casos que el modelo predice como positivos, cuántos realmente lo son.

> Precision = Verdaderos positivos / Predichos positivos

En campañas, alta precision significa que muchos contactados convierten.

### 13.3 Recall

Recall mide, de todos los positivos reales, cuántos detecta el modelo.

> Recall = Verdaderos positivos / Positivos reales

Es importante cuando perder positivos tiene coste alto.

### 13.4 Matriz de confusión

La matriz de confusión cruza predicción y realidad:

- Verdadero positivo.
- Falso positivo.
- Verdadero negativo.
- Falso negativo.

En ventas, cada tipo de error tiene coste distinto.

Contactar a un cliente que no iba a convertir puede costar poco si es email, pero mucho si implica un descuento alto o llamada comercial.

### 13.5 Lift

Lift mide cuánto mejora el modelo respecto a una selección aleatoria.

Ejemplo:

Si en el top 10% del ranking la conversión es tres veces superior a la media, el lift es 3.

Lift es muy útil en marketing porque normalmente se actúa sobre una parte limitada de la base.

### 13.6 Top decile

Top decile es el 10% superior del ranking de score.

Analizar el top decile permite responder:

> Si solo puedo contactar a pocos clientes, ¿cuánta concentración de oportunidad tengo?

### 13.7 MAE, MSE y RMSE

Son métricas para regresión.

**MAE**, error absoluto medio, mide el error promedio en unidades originales.

**MSE**, error cuadrático medio, penaliza más los errores grandes.

**RMSE**, raíz del MSE, devuelve el error a la escala original.

En previsión de ventas o demanda, estas métricas ayudan a estimar desviación frente a la realidad.

### 13.8 Precision@K

Precision@K se usa en recomendadores. Mide cuántas de las K recomendaciones superiores son relevantes.

Ejemplo:

Si recomendamos 5 productos y 2 son comprados o clicados, precision@5 sería 2/5.

### 13.9 Coverage

Coverage mide qué proporción del catálogo o de clientes recibe recomendaciones.

Un recomendador que solo propone los tres productos más vendidos puede tener buena conversión, pero poca diversidad.

### 13.10 Métricas de negocio

Las métricas de negocio responden al impacto real:

- Margen incremental.
- ROI.
- Conversión incremental.
- Reducción de churn.
- Reducción de devoluciones.
- Incremento de ticket medio.
- Incremento de frecuencia.
- Reducción de stockout.
- Mejora de sell-through.

La regla práctica:

> La métrica técnica valida el modelo. La métrica de negocio valida el proyecto.

---

## 14. Gobierno, privacidad y operación del modelo

La analítica comercial usa datos sensibles. Por eso debe trabajar con gobierno y responsabilidad.

### 14.1 Privacidad

Privacidad implica respetar derechos, finalidades y límites del uso de datos personales.

En FraSoHome, antes de activar una campaña, no basta con saber que un cliente tiene alto score. Hay que saber si puede ser contactado para esa finalidad.

### 14.2 Minimización de datos

Minimización significa usar solo los datos necesarios para el propósito definido.

No todo dato disponible debe entrar en un modelo. Hay que justificar su uso.

### 14.3 Transparencia

Transparencia significa poder explicar, al menos a nivel adecuado, cómo se usan los datos y con qué finalidad.

En contexto comercial, esto afecta a confianza del cliente y cumplimiento normativo.

### 14.4 Sesgos

Un sesgo aparece cuando el modelo genera decisiones sistemáticamente desfavorables o distorsionadas para ciertos grupos.

En ventas, los sesgos pueden aparecer por:

- Datos históricos incompletos.
- Clientes anónimos.
- Diferencias de canal.
- Promociones pasadas.
- Zonas con menor cobertura.
- Variables que actúan como proxies.

### 14.5 MLOps

MLOps es el conjunto de prácticas para llevar modelos a producción y mantenerlos.

Incluye:

- Versionado de datos.
- Versionado de código.
- Versionado de modelos.
- Pipelines de entrenamiento.
- Pipelines de scoring.
- Monitorización.
- Alertas.
- Reentrenamiento.
- Trazabilidad.

En una sesión de ventas no hace falta profundizar en toda la ingeniería, pero sí transmitir que el modelo debe funcionar de forma repetible.

### 14.6 Consistencia entrenamiento/scoring

Una regla esencial:

> Los datos de scoring deben prepararse igual que los datos de entrenamiento.

Si durante entrenamiento se imputaron nulos, se escalaron variables o se codificaron categorías, el scoring debe aplicar el mismo proceso.

Si no, el modelo recibe datos en un formato distinto y sus predicciones dejan de ser fiables.

### 14.7 Drift

Drift es el cambio en la distribución de datos o en la relación entre variables y target.

Ejemplos:

- Cambia el comportamiento tras una campaña masiva.
- Entra una nueva categoría de producto.
- Cambia la política de devoluciones.
- Aumenta la inflación.
- Cambia el mix online/tienda.

El drift puede degradar modelos aunque originalmente fueran buenos.

---

## 15. Puente hacia la interpretabilidad

Esta sesión prepara de forma natural una sesión posterior de interpretabilidad. Al terminar, el alumnado debería entender que no basta con predecir; hay que explicar y justificar decisiones.

La interpretabilidad responde preguntas como:

- ¿Por qué un cliente tiene alto riesgo de churn?
- ¿Qué variables impulsan la propensión a comprar textil?
- ¿Por qué el modelo recomienda una categoría y no otra?
- ¿El modelo está premiando clientes de bajo margen?
- ¿Está confundiendo sensibilidad al descuento con valor real?
- ¿Qué segmentos se ven afectados por una regla de decisión?
- ¿Qué explicación necesita marketing para confiar en el modelo?
- ¿Qué explicación necesita dirección para aprobar una campaña?

### 15.1 Importancia de variables

La importancia de variables indica qué features influyen más en el modelo a nivel global.

Es útil para una primera lectura, pero no explica necesariamente una predicción concreta.

Ejemplo:

El modelo de churn puede indicar que recencia, frecuencia y respuesta a campañas son variables importantes.

### 15.2 Explicación global y local

Una explicación global describe cómo funciona el modelo en conjunto.

Una explicación local describe por qué un caso concreto recibió una predicción.

En FraSoHome:

- Global: qué factores suelen aumentar churn.
- Local: por qué el cliente C0123 tiene score alto de churn.

### 15.3 SHAP y LIME

SHAP y LIME son técnicas de explicabilidad.

SHAP asigna contribuciones de cada variable a una predicción. LIME aproxima localmente un modelo complejo con uno más simple.

En esta sesión basta con dejar preparada la necesidad. La sesión posterior puede entrar en detalle técnico.

### 15.4 Interpretabilidad comercial

La interpretabilidad no es solo técnica. Debe traducirse a negocio.

No basta con decir:

> La variable recency aporta +0,18 al score.

Hay que poder explicar:

> Este cliente lleva más tiempo sin comprar que otros clientes similares, no ha respondido a las últimas campañas y su categoría favorita no aparece en compras recientes. Por eso se prioriza una acción de reactivación suave.

---

## 16. Glosario de conceptos comerciales y analíticos

### AOV

Average Order Value. Valor medio de pedido. Se usa sobre todo en ecommerce.

### Atribución

Asignación de una venta o conversión a una campaña, canal o contacto. No implica necesariamente causalidad.

### Audiencia

Grupo de clientes seleccionado para una campaña o acción comercial.

### AUC

Métrica de clasificación que mide la capacidad de ordenar positivos por encima de negativos.

### Baseline

Modelo o regla sencilla que sirve como referencia inicial.

### Campaña

Acción planificada de marketing o ventas dirigida a una audiencia.

### Churn

Abandono o pérdida de actividad de un cliente. En retail debe definirse según ausencia de compra o caída de comportamiento.

### CLV

Customer Lifetime Value. Valor económico esperado de un cliente durante su relación con la empresa.

### Contactabilidad

Capacidad de contactar con un cliente por un canal válido y permitido.

### Conversión

Realización de una acción objetivo: compra, click, redención de cupón, registro, etc.

### Coverage

Cobertura de un recomendador: proporción de productos o clientes alcanzados por recomendaciones.

### Cross-sell

Venta cruzada. Oferta de productos complementarios.

### Customer 360

Vista integrada y accionable del cliente.

### Data warehouse

Sistema analítico que integra y organiza datos históricos para análisis y toma de decisiones.

### Datamart

Subconjunto de datos analíticos orientado a un dominio concreto, como ventas o marketing.

### Devolución

Retorno de un producto comprado. Afecta a ventas netas, margen y experiencia.

### Drift

Cambio en la distribución de datos o comportamiento que puede degradar un modelo.

### Elasticidad promocional

Sensibilidad de la demanda ante cambios de precio o descuento.

### Fact table

Tabla de hechos con eventos medibles, como ventas, devoluciones o contactos.

### Feature

Variable explicativa usada por un modelo.

### Feature engineering

Proceso de creación de variables útiles para análisis o modelización.

### Granularidad

Nivel de detalle de una tabla o análisis.

### Holdout

Grupo retenido sin acción para medir impacto incremental.

### Incrementalidad

Efecto adicional causado por una acción frente a no hacerla.

### KPI

Indicador clave de rendimiento.

### Leakage

Fuga de información del futuro o no disponible en el momento de decisión hacia el entrenamiento del modelo.

### Lift

Mejora respecto a una selección aleatoria o media.

### Margen bruto

Ingreso neto menos coste de producto.

### Margen incremental

Margen adicional generado por una acción frente a un escenario sin acción.

### Margen neto

Margen después de incorporar costes operativos relevantes.

### MLOps

Prácticas para desplegar, monitorizar y mantener modelos de machine learning en producción.

### Next Best Action

Siguiente mejor acción recomendada para un cliente en un contexto concreto.

### Precision

Proporción de predicciones positivas que son realmente positivas.

### Precision@K

Precisión de las K primeras recomendaciones.

### Propensión

Probabilidad de que un cliente realice una acción.

### Recall

Proporción de positivos reales detectados por el modelo.

### Recomendador

Sistema que prioriza productos, contenidos o acciones para un cliente.

### Recencia

Tiempo desde la última compra o interacción.

### RFM

Segmentación basada en recencia, frecuencia y valor monetario.

### ROI

Return on Investment. Retorno de una inversión.

### Score

Puntuación generada por una regla o modelo.

### Sell-through

Proporción de stock vendido en un periodo.

### Stockout

Rotura de stock.

### Target

Variable objetivo que se quiere predecir.

### Ticket medio

Importe medio de una transacción.

### Top decile

10% superior de un ranking.

### Up-sell

Venta de una versión superior o de mayor valor.

### Uplift

Incremento de respuesta causado por una acción respecto a un grupo control.

### Ventana de observación

Periodo histórico usado para construir variables.

### Ventana de predicción

Periodo futuro en el que se observa si ocurre el target.

### Ventas brutas

Importe vendido antes de devoluciones y ajustes.

### Ventas netas

Importe vendido después de devoluciones y ajustes.

---

## Cierre

FraSoHome permite enseñar una idea fundamental: la analítica de ventas no empieza en el algoritmo y no termina en el score. Empieza en una decisión comercial y termina en una acción medible.

El valor aparece cuando conectamos correctamente todos los elementos:

- Datos fiables.
- KPIs bien definidos.
- Vista de cliente.
- Segmentos accionables.
- Modelos orientados a decisión.
- Métricas técnicas.
- Métricas económicas.
- Activación comercial.
- Medición incremental.
- Gobierno e interpretabilidad.

La pregunta final para llevar a la siguiente sesión es:

> Si FraSoHome usa un modelo para priorizar clientes, recomendar productos o decidir incentivos, ¿cómo explicamos esas decisiones de forma que negocio pueda confiar en ellas y actuar con responsabilidad?
