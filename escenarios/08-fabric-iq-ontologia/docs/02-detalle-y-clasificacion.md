# Laboratorio 2 — detalle y clasificación

## Pregunta guía

¿Qué líneas componen el pedido y cómo se clasifica cada producto?

## Modelo añadido

- Entidades: `OrderLine`, `Category`.
- Relaciones: `OrderHasLine`, `LineReferencesProduct`, `ProductInCategory`.

## Despliegue

```powershell
pwsh .\deploy.ps1 -ConfigPath .\config.local.json -Stage 2 -SkipDataUpload -SkipNotebookRun
```

## Exploración

1. Compara `OrderIncludesProduct` con el camino detallado `OrderHasLine → LineReferencesProduct`.
2. Revisa cantidad, precio unitario, porcentaje de descuento e importe de línea.
3. Navega desde `Product` hasta `Category`.
4. Observa que `decoración`, `Decoración` y otras variantes de fuente se presentan como un solo concepto normalizado.

## Preguntas de demo

- ¿Qué categorías concentran más líneas con descuento?
- ¿Qué productos forman parte de los pedidos de mayor importe?
- ¿Qué diferencia hay entre contar pedidos, líneas y unidades?

## Aprendizaje

Una relación muchos-a-muchos puede ser válida para navegar, pero una entidad intermedia conserva el significado económico de la operación. La ontología no elimina el modelo de datos; lo vuelve explícito y comprensible.

## Frase para presentar

“Una línea de pedido no es ruido técnico: es el lugar donde viven cantidad, precio y descuento, y por eso merece identidad semántica.”

Siguiente: [Laboratorio 3 — geografía y preferencia](03-geografia-y-preferencia.md).
