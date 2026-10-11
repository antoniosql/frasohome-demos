# Procedencia y alcance

## Referencia pedagógica

El diseño progresivo toma como referencia:

- repositorio: `microsoft/Ontology-Playground`;
- ruta: `content/learn/iq-lab-retail-supply-chain`;
- revisión analizada: `683adcc8d5a449b9ca9c82e92aaf51c066025c25`;
- consulta realizada el 22 de julio de 2026.

El laboratorio original presenta seis pasos y un modelo de retail/supply chain con entidades como Customer, Order, Product, Shipment, Carrier, Warehouse, Inventory, Forecast y DemandSignal. Es un material conceptual basado en OWL/RDF y no incluye bindings a los datos FraSoHome ni un despliegue completo mediante las APIs de Fabric.

## Adaptación FraSoHome

Se conserva:

- la progresión acumulativa en seis etapas;
- el paso de comercio esencial a detalle, geografía, operación, inventario/demanda y modelo completo;
- la combinación de entidades, propiedades y relaciones como unidad didáctica.

Se sustituye:

- shipment/carrier/warehouse, que no cuentan con evidencia suficiente en `datos`;
- forecast, que no debe inventarse a partir de eventos;
- promoción genérica por las fuentes reales de campaña, contacto y promoción de FraSoHome.

`DemandSignal` sí se conserva como concepto, pero se vincula explícitamente a eventos web/app y se documenta que no es una previsión.

## Implementación original de este repositorio

Son específicos de FraSoHome:

- selección y perfilado de fuentes;
- modelo de 15 entidades y 25 relaciones;
- limpieza, normalización y tablas Delta;
- definición pública de Ontology y bindings;
- automatización de Lakehouse, notebooks, Graph refresh y Data Agent;
- instrucciones, preguntas, guion y laboratorios en español.

No se copian los archivos OWL/RDF del repositorio de Microsoft. Los enlaces se mantienen para atribución y consulta del material original.
