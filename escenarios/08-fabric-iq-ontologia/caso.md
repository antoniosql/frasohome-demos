# Caso FraSoHome — la ventaja está en el contexto

## Situación

FraSoHome dispone de CRM, ecommerce, POS, pagos, devoluciones, inventario y marketing. Los sistemas registran hechos, pero cada área utiliza un lenguaje parcialmente distinto:

- ecommerce habla de pedidos y líneas;
- tienda habla de tickets, cajas y pagos;
- operaciones habla de stock mínimo y reservado;
- marketing habla de contactos, señales, promociones y conversiones;
- atención al cliente habla de devoluciones y motivos.

La empresa puede integrar tablas, pero aún le cuesta responder preguntas que atraviesan esos dominios sin volver a definir cada unión y cada término.

## Reto de negocio

FraSoHome quiere que analistas, copilots y agentes respondan de forma consistente a preguntas como:

> ¿Qué clientes de alto valor muestran intención sobre productos con riesgo de stock en su tienda preferida y estuvieron expuestos a una campaña que terminó en pedido?

Los datos existen, pero la pregunta exige compartir significado:

- qué es un cliente de alto valor;
- qué diferencia un pedido online de una venta POS;
- cuándo un evento es una señal de intención y no una previsión;
- cómo se define el riesgo de stock;
- qué relación demuestra una conversión atribuida;
- qué significa “tienda preferida”.

## Hipótesis

Una ontología empresarial, vinculada a datos reales y consumida por un grafo y un agente, reduce la ambigüedad y hace reutilizable el contexto que normalmente queda enterrado en SQL, informes o conocimiento tácito.

## Solución de demostración

Se construye en Microsoft Fabric una capa acumulativa de seis etapas:

1. comercio esencial;
2. detalle y clasificación;
3. geografía y preferencia;
4. operación omnicanal y devoluciones;
5. inventario y señales de demanda;
6. campañas, promociones, conversión y agente.

La ontología completa contiene 15 entidades y 25 relaciones. Los bindings apuntan a tablas Delta creadas desde `datos`; el grafo materializa instancias y el Data Agent recibe instrucciones explícitas sobre significado, privacidad y límites de inferencia.

## Decisiones diferenciales

- `Order` y `StoreSale` permanecen separados para no borrar diferencias operativas.
- `eventos_web_app` se eleva a `DemandSignal`, pero se prohíbe tratarlo como forecast.
- `InventoryGap <= 0` formaliza el riesgo de stock de la demo.
- una campaña solo se atribuye a un pedido cuando existe `ContactConvertsToOrder`.
- email y teléfono quedan fuera de la ontología.
- una arista ausente significa ausencia de evidencia en las fuentes, no negación del hecho.

## Valor para FraSoHome

- Lenguaje compartido entre negocio, datos e IA.
- Relaciones gobernadas que no dependen de que cada consumidor rehaga joins.
- Trazabilidad desde una respuesta del agente hasta las entidades y evidencias usadas.
- Menor exposición de datos personales al publicar solo propiedades necesarias.
- Base extensible para incorporar reglas, documentos, métricas o acciones futuras.

## Éxito de la demo

La demo es satisfactoria si el agente:

1. distingue intención de compra confirmada;
2. diferencia pedido online y venta POS;
3. recorre cliente, producto, inventario, tienda y campaña;
4. explica el camino semántico utilizado;
5. reconoce las lagunas de evidencia;
6. rechaza entregar PII no publicada.

## Material ejecutable

Consulta [la demo Fabric IQ](despliegue.md), sus [laboratorios](docs/00-preparacion.md) y el [guion de presentación](docs/guion-demo-15-min.md).
