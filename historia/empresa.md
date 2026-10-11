# La empresa en cifras

Ficha de FraSoHome tal y como aparece en los datos del repositorio. Las cifras son las de los CSV originales, antes de limpiar, así que incluyen duplicados y errores a propósito.

## Identidad

| | |
| --- | --- |
| Sector | Retail B2C de muebles, iluminación, textil hogar y decoración |
| Modelo | Omnicanal: tiendas físicas, ecommerce y programa de fidelización |
| Origen | Ecommerce y almacén central en Madrid (noviembre de 2015) |
| Sede corporativa | A Coruña (sede, almacén central y contact center según RR. HH.) |
| Periodo principal de datos | 2024–2025 (con fechas anómalas fuera de rango a propósito) |

## Red de tiendas

| Código | Tienda | Apertura | m² | Región |
| --- | --- | --- | ---: | --- |
| `ONLINE` | eCommerce / Almacén Central (Madrid) | 2015-11-01 | 5.200 | Central |
| `S001` | Madrid Centro · Gran Vía | 2016-03-15 | 1.850 | Centro |
| `S002` | Barcelona Eixample · Diagonal | 2017-07-15 | 2.100 | Cataluña |
| `S003` | Valencia Ruzafa | 2019-01-10 | 1.600 | Levante |
| `S004` | Sevilla Nervión | 2020-09-30 | 1.400 | Andalucía |
| `S005` | Bilbao Abando | 2021-02-28 | 1.250 | Norte |
| `S006` | Málaga Centro *(planificada)* | 2027-05-01 | 1.500 | Andalucía |

Fuente: [`tiendas.csv`](../datos/retail_omnicanal/raw_csv/tiendas.csv). Contiene un duplicado de `S003`, un código postal vacío y una latitud imposible en Málaga.

## Catálogo

Unos 100 productos en cuatro categorías:

| Categoría | SKU | Ejemplos de subcategoría |
| --- | ---: | --- |
| Decoración | 32 | Cuadros, espejos, figuras, velas, jarrones |
| Iluminación | 28 | Bombillas, apliques, lámparas de pie, techo y mesa |
| Muebles | 23 | Sofás, camas, armarios, estanterías |
| Textil hogar | 18 | Sábanas, cortinas, cojines, mantas, alfombras |

Fuente: [`productos.csv`](../datos/retail_omnicanal/raw_csv/productos.csv).

## Clientes y actividad comercial

| Indicador | Valor en los datos |
| --- | ---: |
| Clientes en el programa de fidelización | ~100 (103 filas con duplicados) |
| Niveles de fidelización | Bronce, Plata, Oro, Platino (+ variantes mal capturadas) |
| Pedidos online | 656 cabeceras, 1.949 líneas |
| Líneas de ticket en tienda | 2.521 |
| Pagos en tienda | 1.646 (con pagos mixtos) |
| Devoluciones | 224 online, 211 en tienda |
| Movimientos en la *fact table* integrada | 4.973 (4.522 ventas, 451 devoluciones) |
| Campañas de marketing | 26 (email, SMS y push) |
| Eventos web y app | ~9.000 |
| Tickets de atención al cliente | 560 |

## Personas

| Indicador | Valor en los datos |
| --- | ---: |
| Empleados en el histórico | 820 (669 activos, 151 bajas) |
| Departamentos | Tienda física, Logística, E-commerce, Atención al Cliente, Compras, Marketing, IT y Datos, Finanzas, RR. HH. |
| Ubicaciones | Sede y almacén central en A Coruña, almacenes en Madrid y Barcelona, contact centers, equipos online y tiendas |

Fuente: [`frasohome_people_analytics.csv`](../datos/people_analytics/raw_csv/frasohome_people_analytics.csv).

## Conocimiento interno

Diez documentos `FS-KB-01` a `FS-KB-10`: política de devoluciones (vigente y obsoleta), diccionario de KPI, manuales de tienda y conciliación de pagos, taxonomía de catálogo, guía de fidelización, política de datos del asistente, FAQ de operaciones y un documento de pruebas de *prompt injection*. Están en [`datos/rag_copilot_studio/knowledge_base`](../datos/rag_copilot_studio/knowledge_base/Indice_Documentos_Conocimiento.md).
