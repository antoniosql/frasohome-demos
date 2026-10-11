# Laboratorio 1 — comercio esencial

## Pregunta guía

¿Quién compra qué y mediante qué pedido?

## Modelo acumulado

- Entidades: `Customer`, `Order`, `Product`.
- Relaciones: `CustomerPlacesOrder`, `OrderIncludesProduct`.

## Despliegue

```powershell
pwsh .\deploy.ps1 -ConfigPath .\config.local.json -Stage 1
```

Si los datos ya se prepararon:

```powershell
pwsh .\deploy.ps1 -ConfigPath .\config.local.json -Stage 1 -SkipDataUpload -SkipNotebookRun
```

## Exploración

1. Abre `FraSoHome_Context`.
2. Revisa las propiedades de `Customer`: tier, puntos, ciudad, consentimiento, estado y canal preferido.
3. Abre `Order` y localiza el binding a `dbo.iq_order`.
4. Abre el detalle de un cliente y recorre `CustomerPlacesOrder`.
5. Desde un pedido, usa `OrderIncludesProduct` para ver el catálogo adquirido.

## Preguntas de demo

- ¿Qué productos aparecen en pedidos de clientes Oro o Platino?
- ¿Qué pedidos entregados tienen un total superior a 1.000 EUR?
- ¿Qué origen —web, app o marketplace— está asociado a esos pedidos?

## Aprendizaje

Con tres tablas ya existe un grafo útil, pero la relación pedido-producto sigue siendo una simplificación. Aún no podemos explicar cantidad, precio o descuento. Esa necesidad justifica la siguiente ampliación.

## Frase para presentar

“El dato nos dice que dos IDs coinciden; el contexto declara que un cliente realiza un pedido y que ese pedido incluye un producto.”

Siguiente: [Laboratorio 2 — detalle y clasificación](02-detalle-y-clasificacion.md).
