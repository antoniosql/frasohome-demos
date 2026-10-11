# Laboratorio 5 — inventario y señales de demanda

## Pregunta guía

¿Qué intención digital coincide con riesgo de stock?

## Modelo añadido

- Entidades: `InventoryPosition`, `DemandSignal`.
- Relaciones:
  - `InventoryAtStore`;
  - `InventoryTracksProduct`;
  - `DemandSignalFromCustomer`;
  - `DemandSignalAboutProduct`;
  - `DemandSignalLeadsToOrder`.

## Despliegue

```powershell
pwsh .\deploy.ps1 -ConfigPath .\config.local.json -Stage 5 -SkipDataUpload -SkipNotebookRun
```

## Exploración

1. Filtra `InventoryPosition` por `InventoryGap <= 0`.
2. Navega al producto y la tienda afectados.
3. Desde ese producto, busca señales `add_to_cart` o `begin_checkout`.
4. Recorre la señal hasta el cliente y, si existe, hasta el pedido resultante.
5. Añade `CustomerPrefersStore` al camino para localizar oportunidades accionables.

## Preguntas de demo

- ¿Qué productos tienen intención fuerte y stock en mínimo o por debajo?
- ¿Qué clientes Oro o Platino mostraron esa intención?
- ¿Coincide la tienda con riesgo con la tienda preferida del cliente?

## Aprendizaje

La fuente no contiene una tabla llamada “demanda”. La ontología convierte eventos técnicos en `DemandSignal`, pero conserva una regla esencial: señal no equivale a previsión ni a venta.

## Frase para presentar

“El contexto permite pasar de ‘hubo un evento web’ a ‘hay intención sobre un producto cuyo stock está en riesgo’, sin confundir intención con certeza.”

Siguiente: [Laboratorio 6 — activación y agente](06-activacion-y-agente.md).
