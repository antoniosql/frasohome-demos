# Guion de demo — 15 minutos

## 0:00–1:30 · El problema

Muestra brevemente los CSV de CRM, pedidos, POS, stock y marketing.

Mensaje: FraSoHome ya posee datos; lo que falta es un acuerdo explícito sobre conceptos, relaciones y límites de interpretación.

## 1:30–3:00 · Calidad e identidad

Abre `dbo.iq_source_profile` y `dbo.iq_deployment_manifest`.

Señala:

- duplicados y variantes de mayúsculas en raw;
- 100 clientes y 100 productos canónicos tras normalización;
- relaciones inválidas excluidas del grafo, no borradas de la fuente;
- ausencia deliberada de email y teléfono en `Customer`.

## 3:00–5:30 · De tablas a lenguaje

Abre la ontología en etapa 2 o muestra la progresión en el modelo:

- `CustomerPlacesOrder`;
- `OrderHasLine`;
- `LineReferencesProduct`;
- `ProductInCategory`.

Mensaje: una unión técnica se convierte en una relación con nombre, dirección y propósito.

## 5:30–8:30 · El momento diferencial

Abre `DemandSignal` e `InventoryPosition`.

Recorre:

`Customer ← DemandSignal → Product ← InventoryPosition → Store ← CustomerPrefersStore`

Filtra por señales `add_to_cart` o `begin_checkout` y por `InventoryGap <= 0`.

Mensaje: la tabla se llama `eventos_web_app`; el negocio necesita “señal de demanda”. La ontología formaliza esa elevación sin convertir señal en previsión.

## 8:30–11:00 · Activación y trazabilidad

Parte de `Campaign`, sigue hasta `CampaignContact`, `Customer`, `Product` y `Order`.

Muestra la diferencia entre:

- resultado agregado de campaña;
- conversión atribuida a un contacto;
- pedido confirmado;
- promoción restringida a una tienda.

## 11:00–14:00 · El agente

Pregunta al agente:

> ¿Qué clientes de alto valor mostraron intención fuerte sobre productos con riesgo de stock en su tienda preferida? Separa señales de compras confirmadas y explica el camino semántico.

Pide después:

> De esos casos, ¿cuáles estuvieron expuestos a una campaña que convirtió en pedido y qué evidencia existe?

Busca que el agente nombre las entidades y relaciones utilizadas y reconozca lagunas.

## 14:00–15:00 · Cierre

Tres frases:

1. Los datos aportan hechos.
2. La ontología aporta significado y límites.
3. El agente aporta interacción, pero su utilidad depende de los dos anteriores.

Remate sugerido: “La ventaja competitiva no está en acumular otra tabla; está en conseguir que personas, analítica y agentes compartan el mismo modelo mental del negocio.”

## Plan B sin agente

Si Data Agent o Graph están tardando en refrescar:

- muestra el modelo y los bindings ya desplegados;
- abre las tablas `rel_*` para demostrar que las relaciones están materializadas;
- usa las preguntas de [preguntas-demo.md](preguntas-demo.md) para explicar qué camino seguiría el agente;
- evita improvisar una respuesta no validada.
