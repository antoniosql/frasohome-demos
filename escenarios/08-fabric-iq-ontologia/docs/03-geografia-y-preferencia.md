# Laboratorio 3 — geografía y preferencia

## Pregunta guía

¿Dónde opera FraSoHome y qué tienda prefiere cada cliente?

## Modelo añadido

- Entidades: `Store`, `Region`.
- Relaciones: `StoreInRegion`, `CustomerPrefersStore`.

## Despliegue

```powershell
pwsh .\deploy.ps1 -ConfigPath .\config.local.json -Stage 3 -SkipDataUpload -SkipNotebookRun
```

## Exploración

1. Abre `Store` y diferencia canal físico de online.
2. Recorre `StoreInRegion`; comprueba que `Centro` y `Central` comparten el concepto normalizado `Centro`.
3. Desde un cliente, navega a su tienda preferida.
4. Compara ciudad de residencia con ciudad de tienda sin asumir que son equivalentes.

## Preguntas de demo

- ¿Cuántos clientes tienen preferencia por una tienda de Levante?
- ¿Qué tiendas activas hay en cada región?
- ¿Qué clientes de alto valor prefieren una tienda física?

## Aprendizaje

`CustomerPrefersStore` expresa afinidad calculada; no afirma que todas las compras del cliente ocurran allí. Una ontología útil codifica también los límites de interpretación.

## Frase para presentar

“Contexto es distinguir ubicación, pertenencia y preferencia: tres relaciones que una coincidencia de texto no puede sustituir.”

Siguiente: [Laboratorio 4 — operación omnicanal](04-operacion-omnicanal.md).
