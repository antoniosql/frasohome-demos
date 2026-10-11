# People Analytics

Datos de RR. HH. de FraSoHome en dos niveles:

- **Fuentes brutas** (`raw_*`, `dim_*`): para enseñar ETL en Power Query, con IDs con espacios o guiones, departamentos con variantes, fechas mixtas, importes como texto, duplicados y registros huérfanos.
- **Datasets preparados** (`frasohome_*`): para el caso de alumnos en Power BI Service y las prácticas de *prompting*.

**Escenarios que lo usan**: [03](../../escenarios/03-sql-raw-core-analytics/README.md) · [06](../../escenarios/06-power-bi-people-analytics/README.md)

## Ficheros

| Fichero | Descripción | Grano | Filas | Columnas |
| --- | --- | --- | ---: | ---: |
| [`diccionario_fuentes_brutas.csv`](raw_csv/diccionario_fuentes_brutas.csv) | Diccionario de las fuentes brutas | Campo | 14 | 4 |
| [`dim_calendario.csv`](raw_csv/dim_calendario.csv) | Calendario diario | Día | 1096 | 7 |
| [`dim_departamentos_mapeo.csv`](raw_csv/dim_departamentos_mapeo.csv) | Homologación de departamentos | Variante de departamento | 44 | 5 |
| [`frasohome_comentarios_clima.csv`](raw_csv/frasohome_comentarios_clima.csv) | Comentarios de clima | Comentario | 820 | 9 |
| [`frasohome_comentarios_salida.csv`](raw_csv/frasohome_comentarios_salida.csv) | Comentarios de salida con motivo registrado | Comentario | 151 | 11 |
| [`frasohome_diccionario_datos.csv`](raw_csv/frasohome_diccionario_datos.csv) | Diccionario de los datasets preparados | Variable | 72 | 3 |
| [`frasohome_muestra_prompt_chatgpt.csv`](raw_csv/frasohome_muestra_prompt_chatgpt.csv) | Muestra corta para practicar prompts | Comentario | 40 | 11 |
| [`frasohome_people_analytics.csv`](raw_csv/frasohome_people_analytics.csv) | Dataset preparado: una fila por empleado con clima, desempeño y riesgo | Empleado | 820 | 45 |
| [`frasohome_rotacion_mensual.csv`](raw_csv/frasohome_rotacion_mensual.csv) | Rotación mensual por departamento | Mes × departamento | 280 | 16 |
| [`plantilla_backlog_indicadores.csv`](raw_csv/plantilla_backlog_indicadores.csv) | Plantilla para la dinámica de indicadores | Indicador | 5 | 5 |
| [`raw_absentismo.csv`](raw_csv/raw_absentismo.csv) | Episodios de absentismo | Episodio | 1521 | 8 |
| [`raw_encuesta_clima_respuestas.csv`](raw_csv/raw_encuesta_clima_respuestas.csv) | Encuesta de clima en formato largo | Empleado × pregunta | 6581 | 11 |
| [`raw_evaluaciones_desempeno.csv`](raw_csv/raw_evaluaciones_desempeno.csv) | Evaluaciones anuales y comentarios de manager | Empleado × ciclo | 1132 | 11 |
| [`raw_exit_interviews.csv`](raw_csv/raw_exit_interviews.csv) | Entrevistas de salida | Entrevista | 155 | 10 |
| [`raw_formacion.csv`](raw_csv/raw_formacion.csv) | Acciones formativas y horas | Acción formativa | 3033 | 12 |
| [`raw_horas_extra.csv`](raw_csv/raw_horas_extra.csv) | Horas extra mensuales | Empleado × mes | 7823 | 8 |
| [`raw_hris_empleados.csv`](raw_csv/raw_hris_empleados.csv) | Maestro de empleados tal como sale del HRIS | Empleado (con duplicados) | 839 | 20 |
| [`raw_movimientos_personal.csv`](raw_csv/raw_movimientos_personal.csv) | Altas, bajas, promociones, movilidad y revisiones salariales | Movimiento | 1438 | 12 |
| [`raw_salarios_beneficios.csv`](raw_csv/raw_salarios_beneficios.csv) | Histórico salarial 2025–2026 | Empleado × periodo | 1641 | 9 |

La nota original del paquete de datos brutos está en [`README_datos_brutos_FraSoHome.txt`](README_datos_brutos_FraSoHome.txt).

## Casos de uso

- Rotación y riesgo de salida.
- Clima laboral y comentarios abiertos.
- Absentismo y horas extra.
- Desempeño, formación y compensación.
- Modelo Power BI para la dirección de personas.

Para cruzar personas con tiendas retail, usa [`employee_store_assignment.csv`](../relaciones/employee_store_assignment.csv): solo el 52,68 % de la plantilla se asigna a una tienda o canal (el resto es sede, contact center o almacén).
