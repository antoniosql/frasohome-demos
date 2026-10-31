# 08 · Fabric IQ: ontología, grafo y agente

| Capítulo | Audiencia | Duración | Tecnología |
| --- | --- | --- | --- |
| 6 · Del dato al contexto | Estrategia de datos, IA empresarial, arquitectura, preventa, responsables de agentes | 15 min de demo · 6 laboratorios acumulativos | Microsoft Fabric IQ: Lakehouse, Ontology (preview), Graph (preview), Fabric Data Agent (preview) · PowerShell 7 · Azure CLI |

## La historia en este punto

FraSoHome ya integra sus tablas, pero cada área sigue hablando su idioma: ecommerce habla de pedidos y líneas, la tienda de tickets y pagos, operaciones de stock mínimo y reservado, marketing de contactos, señales y conversiones. Una pregunta como esta sigue costando días:

> ¿Qué clientes de alto valor muestran intención sobre productos con riesgo de stock en su tienda preferida y estuvieron expuestos a una campaña que terminó en pedido?

Los datos existen. Lo que falta es **un acuerdo explícito sobre conceptos, relaciones y límites de interpretación** que puedan compartir analistas, copilotos y agentes.

## Qué se demuestra

- Una ontología acumulativa en seis etapas (15 entidades, 25 relaciones) vinculada a tablas Delta reales.
- Un grafo que materializa instancias y relaciones navegables.
- Un Fabric Data Agent con instrucciones explícitas sobre significado, privacidad y límites de inferencia.
- Decisiones semánticas que marcan la diferencia:
    - `Order` y `StoreSale` son conceptos distintos.
    - `eventos_web_app` se eleva a `DemandSignal`, pero nunca se trata como previsión.
    - `InventoryGap <= 0` formaliza el riesgo de stock.
    - Una campaña solo se atribuye a un pedido cuando existe `ContactConvertsToOrder`.
    - Email y teléfono no se publican en `Customer`.
    - Una relación ausente es ausencia de evidencia, no negación del hecho.

| Etapa | Entidades añadidas | Pregunta que habilita |
| --- | --- | --- |
| 1 | `Customer`, `Order`, `Product` | Quién compra qué |
| 2 | `OrderLine`, `Category` | Detalle del pedido y taxonomía |
| 3 | `Store`, `Region` | Geografía y tienda preferida |
| 4 | `StoreSale`, `Payment`, `Return` | Operación omnicanal y posventa |
| 5 | `InventoryPosition`, `DemandSignal` | Intención digital frente a disponibilidad |
| 6 | `Campaign`, `Promotion`, `CampaignContact` | Activación, conversión y agente |

## Recursos necesarios

### Entorno

| Recurso | Detalle |
| --- | --- |
| PowerShell 7 y Azure CLI | Sesión iniciada con `az login` en el tenant correcto |
| Capacidad de Fabric | Compatible con IQ, o un workspace ya asignado a capacidad |
| Rol en el workspace | Contributor o superior |
| Opciones de tenant (administrador) | **Enable Ontology item (preview)**, **User can create Graph (preview)** y, para la etapa 6, **Users can create and share Data agent item types (preview)** |
| OneLake security | Deshabilitado en el Lakehouse de la demo (los *bindings* estáticos de Ontology no lo admiten todavía) |

Ontology, Graph y la gestión programática del Data Agent estaban en preview cuando se preparó la demo. Revisa el estado actual en la [documentación de Fabric IQ](https://learn.microsoft.com/fabric/iq/).

### Datos

Quince CSV, sin modificar, declarados en [`source-manifest.json`](fabric/data/source-manifest.json):

| Dominio | Ficheros |
| --- | --- |
| [Retail omnicanal](../../datos/retail_omnicanal/README.md) | `crm`, `productos`, `tiendas`, `pedidos`, `lineas_pedido`, `ventas_pos`, `pagos_tienda`, `devoluciones_online`, `devoluciones_tienda`, `stock_diario` |
| [Marketing de precisión](../../datos/marketing_precision/README.md) | `campanas_marketing`, `contactos_campana`, `promociones_calendario`, `eventos_web_app`, `afinidad_tienda_cliente` |

### Material de la demo

| Fichero | Contenido |
| --- | --- |
| [`deploy.ps1`](deploy.ps1) | Despliegue idempotente por etapas: sube datos, ejecuta notebooks, publica ontología, refresca grafo y crea el agente |
| [`cleanup.ps1`](cleanup.ps1) | Borrado protegido de lo creado por el despliegue |
| [`config.example.json`](config.example.json) | Plantilla de configuración (copiar a `config.local.json`, que no se versiona) |
| [`fabric/notebooks/FraSoHome_IQ_01_Prepare.py`](fabric/notebooks/FraSoHome_IQ_01_Prepare.py) · [`FraSoHome_IQ_02_Validate.py`](fabric/notebooks/FraSoHome_IQ_02_Validate.py) | Limpieza, normalización, tablas enlazables y validación |
| [`fabric/ontology/ontology-model.json`](fabric/ontology/ontology-model.json) | Modelo de la ontología |
| [`fabric/agent/instructions.md`](fabric/agent/instructions.md) | Instrucciones del Data Agent |
| [`scripts/`](scripts/FabricApi.psm1) | Módulos [`FabricApi.psm1`](scripts/FabricApi.psm1) y [`OntologyDefinition.psm1`](scripts/OntologyDefinition.psm1) |
| [`tests/Test-Repository.ps1`](tests/Test-Repository.ps1) · [`tests/agent-prompts.json`](tests/agent-prompts.json) | Validación local y preguntas de prueba |
| [Caso de negocio](caso.md) | La ventaja está en el contexto |
| [Guía de despliegue](despliegue.md) | Qué despliega, requisitos, ejecución completa y progresiva, limpieza |
| [Arquitectura y decisiones](docs/arquitectura.md) · [Datos y modelo](docs/datos-y-modelo.md) | Diseño |
| Laboratorios [0](docs/00-preparacion.md) · [1](docs/01-comercio-esencial.md) · [2](docs/02-detalle-y-clasificacion.md) · [3](docs/03-geografia-y-preferencia.md) · [4](docs/04-operacion-omnicanal.md) · [5](docs/05-inventario-y-demanda.md) · [6](docs/06-activacion-y-agente.md) | Progresión guiada |
| [Guion de 15 minutos](docs/guion-demo-15-min.md) · [Preguntas para el agente](docs/preguntas-demo.md) | Presentación |
| [Solución de problemas](docs/troubleshooting.md) · [Procedencia](docs/provenance.md) | Soporte y créditos |

## Cómo ejecutarla

Desde `escenarios/08-fabric-iq-ontologia`:

```powershell
Copy-Item .\config.example.json .\config.local.json
# Edita config.local.json: workspace.id si ya existe, o workspace.capacityId para crearlo
pwsh .\deploy.ps1 -ConfigPath .\config.local.json -ValidateOnly   # valida sin tocar Fabric
pwsh .\deploy.ps1 -ConfigPath .\config.local.json -Stage 6        # despliegue completo con agente
```

Para un laboratorio progresivo, despliega la etapa 1 y avanza sin volver a subir datos:

```powershell
pwsh .\deploy.ps1 -ConfigPath .\config.local.json -Stage 1
pwsh .\deploy.ps1 -ConfigPath .\config.local.json -Stage 2 -SkipDataUpload -SkipNotebookRun
# ... hasta -Stage 6
```

`config.example.json` apunta a `../../datos`, así que los CSV se toman directamente de este repositorio. El estado del despliegue se guarda en `.local/fabric_iq_ontology/deployment-state.json` (fuera del control de versiones). Para limpiar: `pwsh .\cleanup.ps1` (añade `-DeleteWorkspace` si el workspace se creó para la demo).

## Guion sugerido (15 min)

| Minuto | Bloque | Mensaje |
| --- | --- | --- |
| 0:00–1:30 | El problema | FraSoHome ya tiene datos; le falta un acuerdo sobre conceptos |
| 1:30–3:00 | Calidad e identidad | 100 clientes y 100 productos canónicos; relaciones inválidas fuera del grafo, no borradas |
| 3:00–5:30 | De tablas a lenguaje | Una unión técnica se convierte en una relación con nombre y propósito |
| 5:30–8:30 | El momento diferencial | `DemandSignal` frente a `InventoryPosition` en la tienda preferida |
| 8:30–11:00 | Activación y trazabilidad | Resultado de campaña frente a conversión atribuida |
| 11:00–14:00 | El agente | Preguntas que cruzan dominios y explican su camino semántico |
| 14:00–15:00 | Cierre | Datos = hechos · ontología = significado · agente = interacción |

Si el grafo o el agente tardan en refrescar, el [guion](docs/guion-demo-15-min.md) incluye un plan B.

## Mensajes clave

- La ventaja no está en acumular otra tabla, sino en que personas, analítica y agentes compartan el mismo modelo mental del negocio.
- Formalizar el significado también es formalizar sus límites: una señal no es una previsión.
- La privacidad se diseña en el contrato semántico: lo que no se publica no se puede filtrar.

## Con datos vivos (opcional)

Esta demo usa los CSV de retail y de marketing: una fotografía de 2024–2025 con errores intencionados. Si quieres trabajar con datos que cambien, el [escenario 11](../11-web-transaccional/README.md) es una web real donde se venden, devuelven y atienden pedidos sobre Azure SQL y Cosmos DB, y su exportación (`tools/export_csv.py` `--dominio retail,marketing`) los devolverá al mismo formato que `datos/`, sin tocar el código de esta demo.

La exportación todavía no está construida (fase 5 del escenario 11). Hasta entonces, usa `datos/` como hasta ahora.
