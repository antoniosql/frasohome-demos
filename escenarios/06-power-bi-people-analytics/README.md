# 06 · People Analytics con Power BI

| Capítulo | Audiencia | Duración | Tecnología |
| --- | --- | --- | --- |
| 4 · Las personas detrás de la tienda | RR. HH., dirección, alumnos de analítica aplicada | 2 h (demo ETL) · 3–4 h (caso completo con alumnos) | Power BI Desktop o Service · Power Query · DAX · ChatGPT u otro asistente de IA |

## La historia en este punto

En 24 meses FraSoHome ha crecido online, ha ampliado horarios de atención al cliente y ha sufrido la presión logística de rebajas, Black Friday y Navidad. Llegan las señales: bajas voluntarias en tienda, rotación en el contact center, salida de perfiles senior en ecommerce y dudas sobre si los planes de carrera son visibles. La Dirección de Personas quiere responder tres preguntas ante el comité:

1. ¿Dónde se concentra la rotación voluntaria y cómo evoluciona por mes y departamento?
2. ¿Qué señales explican el riesgo de abandono de quienes siguen en la empresa?
3. ¿Qué acciones de retención hay que priorizar y cómo se comunican?

Con una condición: **un *score* de riesgo no es una decisión sobre una persona**.

## Qué se demuestra

- ETL en Power Query desde fuentes de RR. HH. sucias: HRIS con duplicados, departamentos con variantes, fechas mixtas, importes como texto.
- Modelo analítico con `DimEmpleado`, `DimDepartamento`, calendario y hechos de movimientos, clima, formación, absentismo, horas extra y salario.
- KPI de rotación bien definidos (numerador, denominador y baja voluntaria) y un *score* de abandono explicable.
- El visual **Influenciadores clave** para entender patrones agregados de riesgo.
- *Prompt engineering* (zero-shot, one-shot, few-shot) sobre comentarios de salida y clima, contrastando la salida de la IA con los datos.
- Ética, privacidad y supervisión humana como parte del entregable.

## Recursos necesarios

### Entorno

| Recurso | Para qué |
| --- | --- |
| Power BI Desktop (ETL completo) o Power BI Service (carga directa de CSV) | Modelo e informe |
| ChatGPT, Copilot u otro asistente | Análisis de comentarios (solo con la muestra anonimizada) |

### Datos

Todos en [`datos/people_analytics/raw_csv`](../../datos/people_analytics/README.md).

**Para la demo ETL (datos brutos)**

| Fichero | Sistema simulado | Grano |
| --- | --- | --- |
| [`raw_hris_empleados.csv`](../../datos/people_analytics/raw_csv/raw_hris_empleados.csv) | HRIS | Empleado (con duplicados) |
| [`raw_movimientos_personal.csv`](../../datos/people_analytics/raw_csv/raw_movimientos_personal.csv) | HR Operations | Movimiento |
| [`raw_evaluaciones_desempeno.csv`](../../datos/people_analytics/raw_csv/raw_evaluaciones_desempeno.csv) | Desempeño | Empleado × ciclo |
| [`raw_encuesta_clima_respuestas.csv`](../../datos/people_analytics/raw_csv/raw_encuesta_clima_respuestas.csv) | Encuesta de clima | Empleado × pregunta |
| [`raw_absentismo.csv`](../../datos/people_analytics/raw_csv/raw_absentismo.csv) | Ausencias | Episodio |
| [`raw_horas_extra.csv`](../../datos/people_analytics/raw_csv/raw_horas_extra.csv) | Control horario | Empleado × mes |
| [`raw_formacion.csv`](../../datos/people_analytics/raw_csv/raw_formacion.csv) | LMS | Acción formativa |
| [`raw_salarios_beneficios.csv`](../../datos/people_analytics/raw_csv/raw_salarios_beneficios.csv) | Nómina | Empleado × periodo |
| [`raw_exit_interviews.csv`](../../datos/people_analytics/raw_csv/raw_exit_interviews.csv) | Entrevistas de salida | Entrevista |
| [`dim_departamentos_mapeo.csv`](../../datos/people_analytics/raw_csv/dim_departamentos_mapeo.csv) · [`dim_calendario.csv`](../../datos/people_analytics/raw_csv/dim_calendario.csv) | Apoyo | Homologación y calendario |
| [`diccionario_fuentes_brutas.csv`](../../datos/people_analytics/raw_csv/diccionario_fuentes_brutas.csv) · [`plantilla_backlog_indicadores.csv`](../../datos/people_analytics/raw_csv/plantilla_backlog_indicadores.csv) | Documentación | Campos y dinámica de indicadores |

**Para el caso de alumnos (datos preparados)**

| Fichero | Uso |
| --- | --- |
| [`frasohome_people_analytics.csv`](../../datos/people_analytics/raw_csv/frasohome_people_analytics.csv) | Una fila por empleado (820): estado, desempeño, clima, *score* de abandono y comentarios |
| [`frasohome_rotacion_mensual.csv`](../../datos/people_analytics/raw_csv/frasohome_rotacion_mensual.csv) | Serie mensual por departamento: plantilla, altas, bajas y tasa de rotación |
| [`frasohome_comentarios_salida.csv`](../../datos/people_analytics/raw_csv/frasohome_comentarios_salida.csv) · [`frasohome_comentarios_clima.csv`](../../datos/people_analytics/raw_csv/frasohome_comentarios_clima.csv) | Texto para la IA |
| [`frasohome_muestra_prompt_chatgpt.csv`](../../datos/people_analytics/raw_csv/frasohome_muestra_prompt_chatgpt.csv) | Muestra corta para practicar *prompts* |
| [`frasohome_diccionario_datos.csv`](../../datos/people_analytics/raw_csv/frasohome_diccionario_datos.csv) | Diccionario de variables |

**Opcional**: [`employee_store_assignment.csv`](../../datos/relaciones/employee_store_assignment.csv) para cruzar personas con tiendas retail.

### Material de la demo

| Fichero | Contenido |
| --- | --- |
| [Guía de la demo ETL](guia-etl-datos-brutos.md) | Paso a paso en Power Query, modelo, DAX, páginas del informe y guion minuto a minuto |
| [Demo de influenciadores clave](demo-influenciadores-clave.md) | Configuración del visual y lectura de resultados |
| [Caso para alumnos](caso-alumnos.md) | Enunciado, actividades y entregables |
| [Caso con Power BI y ChatGPT](caso-powerbi-chatgpt.md) | Versión con las dos actividades integradas |
| [Fuentes simuladas](fuentes-simuladas.md) | Tabla de sistemas, granularidad y uso |
| [Presentación del caso](../../presentaciones/caso-people-analytics.md) | Guion de diapositivas |

## Cómo ejecutarla

**Demo ETL en Power BI Desktop (2 h)**

1. Recuerda el reto y enseña dos o tres CSV brutos: granularidad, duplicados y claves.
2. En Power Query, limpia `raw_hris_empleados` y homologa departamentos con `dim_departamentos_mapeo`.
3. Construye movimientos y el KPI de rotación (define antes qué es una baja voluntaria y cuál es el denominador).
4. Pivota la encuesta de clima y agrega formación, absentismo, horas extra y salario por empleado.
5. Crea el *score* explicable y la página de factores con **Influenciadores clave**, filtrando `estado_actual = Activo`.
6. Cierra con la IA: clasifica comentarios de salida y compara con `motivo_salida_sistema`.

La [guía ETL](guia-etl-datos-brutos.md) tiene los pasos, las fórmulas DAX y el guion minuto a minuto.

**Caso de alumnos en Power BI Service**: carga `frasohome_rotacion_mensual.csv` y `frasohome_people_analytics.csv` como modelos semánticos y sigue el [caso para alumnos](caso-alumnos.md).

## Guion sugerido (2 h)

| Tiempo | Actividad | Resultado |
| --- | --- | --- |
| 0–10 min | Reto y fuentes brutas | *Backlog* inicial de métricas |
| 10–25 min | *Data discovery* | Lista de problemas de calidad |
| 25–45 min | Power Query: HRIS y departamentos | `DimEmpleado` y `DimDepartamento` |
| 45–65 min | Movimientos y rotación | Primer KPI de rotación |
| 65–85 min | Clima, formación, absentismo y horas extra | Tabla analítica por empleado |
| 85–105 min | *Score* de abandono y visuales | Página de factores y priorización |
| 105–120 min | IA con comentarios de salida y cierre | Conclusiones y plan de acción |

## Mensajes clave

- Contar bajas no es medir rotación: sin denominador no hay KPI.
- El riesgo de abandono es una combinación (satisfacción, *engagement*, reconocimiento, manager, carga), no una causa.
- La IA ayuda a leer texto; las conclusiones se validan contra los datos.
- Los datos de personas exigen anonimización, propósito claro y supervisión humana.
