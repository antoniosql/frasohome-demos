# Laboratorio 6 — activación y agente

## Pregunta guía

¿Qué campaña, contacto y promoción explican una conversión?

## Modelo añadido

- Entidades: `Campaign`, `Promotion`, `CampaignContact`.
- Relaciones:
  - `CampaignHasContact`;
  - `ContactAddressesCustomer`;
  - `ContactRecommendsProduct`;
  - `ContactConvertsToOrder`;
  - `CampaignOffersPromotion`;
  - `PromotionAtStore`.

## Despliegue

```powershell
pwsh .\deploy.ps1 -ConfigPath .\config.local.json -Stage 6 -SkipDataUpload -SkipNotebookRun
```

La etapa 6 crea o actualiza `FraSoHome_Context_Agent`, conecta la ontología, selecciona sus entidades, carga las instrucciones y publica el agente.

## Exploración del grafo

1. Parte de una campaña con conversiones.
2. Recorre `CampaignHasContact`.
3. Desde el contacto, navega al cliente, los productos recomendados y el pedido convertido.
4. Comprueba si existe una promoción y si está restringida a una tienda.

## Prueba del agente

Pregunta:

> ¿Qué clientes Oro o Platino mostraron intención fuerte sobre productos con riesgo de stock en su tienda preferida? Explica el camino semántico y separa señales de compras confirmadas.

La respuesta correcta debe:

- usar `DemandSignal`, no llamar previsión al evento;
- aplicar `InventoryGap <= 0`;
- recorrer `CustomerPrefersStore`;
- distinguir señal de pedido o venta;
- declarar si faltan relaciones para algún cliente.

## Aprendizaje

El agente no recibe una lista arbitraria de tablas. Recibe un contrato de significado, relaciones con dirección y reglas de interpretación. Esa es la diferencia entre acceso a datos y contexto empresarial.

## Frase para cerrar

“El modelo genera lenguaje; la ontología genera entendimiento compartido; el agente convierte ese entendimiento en una interacción útil.”

Continúa con [Preguntas para la demo](preguntas-demo.md) o el [guion de 15 minutos](guion-demo-15-min.md).
