# Laboratorio 4 — operación omnicanal

## Pregunta guía

¿Cómo se conectan venta, pago, tienda, producto y devolución?

## Modelo añadido

- Entidades: `StoreSale`, `Payment`, `Return`.
- Relaciones:
  - `CustomerCompletesSale`;
  - `SaleAtStore`;
  - `SaleIncludesProduct`;
  - `PaymentSettlesSale`;
  - `ReturnForOrder`;
  - `ReturnForSale`;
  - `ReturnConcernsProduct`.

## Despliegue

```powershell
pwsh .\deploy.ps1 -ConfigPath .\config.local.json -Stage 4 -SkipDataUpload -SkipNotebookRun
```

## Exploración

1. Compara `Order` con `StoreSale`: un pedido online no es un ticket POS.
2. Navega desde `Payment` hasta la venta que liquida.
3. Elige una `Return` y comprueba si está vinculada a `Order`, `StoreSale` o ambos.
4. Sigue la devolución hasta el producto afectado.

## Preguntas de demo

- ¿Qué productos aparecen en devoluciones de ambos canales?
- ¿Qué métodos de pago están asociados a ventas posteriormente devueltas?
- ¿Qué ventas tienen más de un pago?

## Aprendizaje

“Venta” es una palabra demasiado amplia para automatizar decisiones. Separar `Order` y `StoreSale`, y unirlos a una `Return` común, crea una vista omnicanal sin borrar las diferencias operativas.

## Frase para presentar

“Un modelo contextual puede unificar el recorrido del cliente sin fingir que ecommerce y POS son el mismo proceso.”

Siguiente: [Laboratorio 5 — inventario y demanda](05-inventario-y-demanda.md).
