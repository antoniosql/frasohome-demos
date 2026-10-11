# Solución de problemas

## La creación de Ontology falla

Comprueba:

- que **Enable Ontology item (preview)** está habilitado para tu usuario o grupo;
- que el workspace está asignado a una capacidad compatible;
- que tienes rol Contributor o superior;
- que el nombre del objeto no está en uso por otro tipo de item.

## No aparece el grafo hijo

Ontology crea un `GraphModel` hijo. El script intenta localizarlo mediante relaciones upstream/downstream, una API beta.

1. Espera un minuto y vuelve a ejecutar con `-SkipDataUpload -SkipNotebookRun`.
2. Abre el workspace y localiza el GraphModel asociado a `FraSoHome_Context`.
3. En su menú, selecciona **Schedule > Refresh now**.
4. Confirma que **User can create Graph (preview)** está habilitado.

## El grafo no contiene datos recientes

Actualizar tablas Delta no refresca automáticamente las instancias visibles. Ejecuta de nuevo el despliegue sin `-SkipGraphRefresh` o usa **Refresh now** en el GraphModel.

## Un binding de Lakehouse falla

La demo presupone:

- lakehouse con esquemas y tablas bajo `dbo`;
- tablas Delta administradas;
- column mapping deshabilitado;
- OneLake security deshabilitado.

Si reutilizas un lakehouse existente creado sin esquemas, crea uno nuevo con el nombre configurado o cambia el nombre en `config.local.json`.

## La subida a OneLake devuelve 401 o 403

- Ejecuta `az login` en el tenant correcto.
- Comprueba que el token de Storage puede obtenerse.
- Verifica permisos de escritura en el lakehouse.
- En entornos con private link, confirma que el endpoint de OneLake del workspace es accesible.

## El notebook no encuentra los CSV

Comprueba que existan rutas como:

`Files/frasohome_iq/raw/retail_omnicanal/crm.csv`

Si se usó `-SkipDataUpload` antes de una primera carga, repite el despliegue sin ese modificador.

## El notebook de validación detecta menos de 40 objetos

Vuelve a ejecutar primero `FraSoHome_IQ_01_Prepare`. No construyas la ontología sobre tablas parciales.

## El Data Agent no muestra entidades

1. Confirma que el grafo terminó su refresco.
2. Espera unos segundos y repite la etapa 6 con `-SkipDataUpload -SkipNotebookRun`.
3. Comprueba el tenant setting **Users can create and share Data agent item types (preview)**.
4. Abre el agente y verifica que la fuente sea el item `FraSoHome_Context`, no el lakehouse.

## El agente responde como si una señal fuera una venta

Revisa que las instrucciones de `fabric/agent/instructions.md` aparezcan en la configuración staging y publicada del agente. La respuesta debe separar:

- `DemandSignal` como intención;
- `Order` como pedido online;
- `StoreSale` como ticket POS.

## Repetir desde cero

Ejecuta `cleanup.ps1`, confirma la eliminación y vuelve a desplegar. El script conserva por defecto los objetos que ya existían y fueron reutilizados. Usa `-DeleteWorkspace` solo si el workspace fue creado exclusivamente para esta demo; `-DeleteReusedItems` amplía el borrado a recursos preexistentes y no debe usarse en un workspace compartido.
