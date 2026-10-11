# Relaciones entre dominios

Tablas puente para seguir el hilo de FraSoHome entre retail, People Analytics, RAG y marketing **sin modificar las fuentes originales**.

**Escenarios que lo usan**: [03](../../escenarios/03-sql-raw-core-analytics/README.md) · [05](../../escenarios/05-marketing-precision/README.md) · [06](../../escenarios/06-power-bi-people-analytics/README.md) · [07](../../escenarios/07-copilot-studio-rag/README.md)

## Ficheros

| Fichero | Descripción | Grano | Filas | Columnas |
| --- | --- | --- | ---: | ---: |
| [`coherence_check_summary.csv`](coherence_check_summary.csv) | Resultado de los checks de coherencia tras aplicar alias | Check | 30 | 8 |
| [`employee_operational_aliases.csv`](employee_operational_aliases.csv) | Cajeros POS EMP### hacia empleados FSH#### | Cajero | 106 | 8 |
| [`employee_store_assignment.csv`](employee_store_assignment.csv) | Empleados asignados a tienda o canal cuando la ubicación lo permite | Empleado | 820 | 6 |
| [`marketing_precision_operational_links.csv`](marketing_precision_operational_links.csv) | Columnas de marketing que enlazan con entidades retail | Columna | 42 | 5 |
| [`product_aliases_rag_to_retail.csv`](product_aliases_rag_to_retail.csv) | Productos RAG FSH-* hacia productos retail P* | Producto RAG | 32 | 12 |
| [`store_aliases.csv`](store_aliases.csv) | Alias de tiendas y ubicaciones hacia store_id retail | Alias | 42 | 5 |

## Uso recomendado

1. Mantén los CSV originales intactos.
2. Carga primero los dominios originales.
3. Aplica los alias de esta carpeta para navegar entre demos.
4. Conserva los fallos de enlace intencionados como ejemplos de calidad de datos.

Los alias `EMP###` → `FSH####` son sintéticos y solo sirven para la demo; no son un maestro oficial de RR. HH. El resultado de los checks está en la [auditoría de coherencia](../coherencia.md).
