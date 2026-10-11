# Laboratorio 0 — preparación

## Objetivo

Dejar el workspace, el lakehouse y las tablas verificadas antes de construir el vocabulario de negocio.

## Antes de empezar

Confirma con el administrador que Ontology, Graph y —para la etapa 6— Data Agent están habilitados en el tenant. El workspace debe estar en una capacidad compatible y tu usuario debe tener rol Contributor o superior.

## Pasos

1. Copia `config.example.json` como `config.local.json`.
2. Informa un `workspace.id` existente o un `capacityId` para que el script cree el workspace.
3. Ejecuta la validación local:

   ```powershell
   pwsh .\deploy.ps1 -ConfigPath .\config.local.json -ValidateOnly
   ```

4. Despliega la primera etapa:

   ```powershell
   pwsh .\deploy.ps1 -ConfigPath .\config.local.json -Stage 1
   ```

5. En Fabric, comprueba:

   - lakehouse `FraSoHome_IQ`;
   - 15 fuentes bajo `Files/frasohome_iq/raw`;
   - tablas `dbo.iq_*` y `dbo.rel_*`;
   - notebooks de preparación y validación con última ejecución correcta;
   - ontología `FraSoHome_Context`.

## Punto de conversación

La capa raw conserva las anomalías. La capa semántica no las oculta: decide qué identidades y relaciones tienen evidencia suficiente para publicarse.

## Criterio de éxito

El notebook de validación termina correctamente y `dbo.iq_deployment_manifest` contiene 40 filas: 15 entidades y 25 relaciones.

Siguiente: [Laboratorio 1 — comercio esencial](01-comercio-esencial.md).
