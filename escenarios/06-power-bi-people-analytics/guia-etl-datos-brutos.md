# Guia_demo_FraSoHome_ETL_datos_brutos

**FraSoHome**

**Guía docente para demostración ETL****
con datos brutos de People Analytics**

Power BI + ChatGPT | Rotación, abandono y voz del empleado

Fecha de corte del caso: 30/04/2026
Paquete de datos: FraSoHome_datos_brutos_ETL_pack.zip

|Uso previsto<br>Los alumnos no necesitan ordenador. La dinámica consiste en que propongan indicadores, definan numerador/denominador y tú construyas en directo el flujo ETL y el modelo analítico con Power BI.|
|---|

## 1. Por qué se generan nuevos datos brutos

Los CSV iniciales del caso estaban pensados para que el alumno trabajase directamente con información ya preparada: variables calculadas, tasas de rotación, scores de abandono y columnas listas para visualización. Para una demostración docente, esa versión reduce el valor pedagógico del ETL, porque oculta las decisiones clave que debe tomar un analista: qué fuente usar, cuál es la granularidad, qué limpiar, qué agregar y cómo convertir un problema de RR.HH. en una métrica.

Este nuevo paquete reproduce una situación más realista: los datos llegan desde sistemas distintos —HRIS, nómina, desempeño, clima, formación, absentismo, horas extra y entrevistas de salida— con formatos heterogéneos y problemas de calidad intencionados. El objetivo es enseñar cómo pensar un modelo analítico desde el dato de origen hasta el dashboard.

|Idea de apertura para la clase<br>“Antes de abrir Power BI no vamos a hablar de gráficos. Vamos a hablar de preguntas, decisiones e indicadores. Cada métrica que pidáis debe tener una fuente, una regla de cálculo y una cautela de interpretación.”|
|---|

## 2. Relación con el caso FraSoHome

El modelo analítico debe responder a los mismos problemas planteados en el caso: dónde se concentra la rotación voluntaria, qué señales explican el riesgo de abandono de empleados activos y qué acciones de retención deberían priorizarse. La diferencia es que ahora el docente muestra cómo se construyen esas respuestas desde datos de origen no preparados.

|Problema del caso|Pregunta analítica|Fuentes brutas necesarias|Resultado esperado|
|---|---|---|---|
|Rotación de personal|¿Qué áreas, meses o perfiles concentran más salidas voluntarias?|HRIS + movimientos de personal + calendario + mapeo de departamentos|Tasa de rotación mensual, bajas voluntarias, headcount inicial/final y áreas críticas.|
|Detección de abandono|¿Qué empleados activos muestran señales de riesgo?|Clima + desempeño + salario + formación + absentismo + horas extra + HRIS|Score de riesgo explicable y tabla de priorización para conversaciones de permanencia.|
|Voz del empleado|¿Qué motivos aparecen en comentarios de salida y clima?|Entrevistas de salida + comentarios de clima|Temas cualitativos clasificados con ChatGPT y contrastados con indicadores cuantitativos.|
|Acción de RR.HH.|¿Qué intervención priorizar y cómo medirla?|Indicadores anteriores + backlog de acciones|Plan de retención con KPI de seguimiento, responsable y plazo.|

## 3. Archivos generados y uso docente

|Archivo|Sistema de origen simulado|Granularidad|Uso en la demo|
|---|---|---|---|
|raw_hris_empleados.csv|HRIS / maestro de personas|Una fila por empleado, con duplicados intencionados|DimEmpleado, fechas de alta/salida, contrato, rol, departamento y anonimización.|
|raw_movimientos_personal.csv|HR Operations|Una fila por movimiento|Altas, bajas, promociones, movilidad y cálculo de rotación.|
|raw_evaluaciones_desempeno.csv|Plataforma de desempeño|Una fila por empleado y ciclo|Desempeño, potencial y evolución anual.|
|raw_encuesta_clima_respuestas.csv|Encuesta de clima|Una fila por empleado y dimensión/pregunta|Pivotar dimensiones, satisfacción, engagement y comentarios.|
|raw_absentismo.csv|Gestión de ausencias|Una fila por episodio de ausencia|Días de absentismo 12m y validación de valores anómalos.|
|raw_horas_extra.csv|Control horario|Una fila por empleado y mes|Horas extra medias y señales de carga operativa.|
|raw_formacion.csv|LMS / formación|Una fila por acción formativa|Horas de formación 12m, completadas vs no completadas.|
|raw_salarios_beneficios.csv|Nómina / compensación|Una fila por empleado y periodo|Salario actual, incremento 12m y percepción salarial.|
|raw_exit_interviews.csv|Entrevistas de salida|Una fila por entrevista|Motivos de salida y análisis con ChatGPT.|
|dim_departamentos_mapeo.csv|Tabla de homologación|Una fila por etiqueta raw|Normalizar departamentos y áreas de análisis.|
|dim_calendario.csv|Calendario|Una fila por fecha|Meses, años y relaciones temporales.|
|plantilla_backlog_indicadores.csv|Dinámica docente|Una fila por indicador sugerido|Capturar y ordenar los indicadores que propongan los alumnos.|

## 4. Dinámica con alumnos: backlog de indicadores

Como los alumnos no tendrán ordenador, el valor está en que participen en el diseño analítico. Tú puedes proyectar una tabla vacía y pedirles que propongan indicadores. Cada propuesta se traduce en una decisión de modelado.

1. Presenta el problema: “FraSoHome quiere reducir rotación y anticipar abandono sin automatizar decisiones sobre personas”.
1. Pregunta al grupo: “¿Qué miraríais primero si fuerais RR.HH.?”
1. Anota cada idea en el backlog: indicador, pregunta de negocio, fuente, fórmula y visual.
1. Pide que definan numerador, denominador, periodo y población. Si no pueden definirlos, la métrica todavía no está madura.
1. Construye en Power BI una o dos métricas propuestas y muestra cómo cambian al segmentar por departamento, nivel o mes.
|Lo que suele decir el alumno|Cómo lo conviertes en métrica|Pregunta de calidad que debes hacer|
|---|---|---|
|“Rotación por departamento”|Bajas voluntarias mensuales / headcount medio mensual, filtrado por departamento estándar.|¿Incluimos bajas no voluntarias? ¿Qué hacemos con temporales?|
|“Satisfacción del empleado”|Media de score de dimensión Satisfacción, escalada de 1-5 a 1-10 si hace falta.|¿La encuesta está en formato largo o ancho? ¿Hay respuestas duplicadas?|
|“Riesgo de abandono”|Score explicable con señales de clima, carga, salario, desarrollo y desempeño.|¿Es una alerta para conversar o una decisión automática?|
|“Horas extra y estrés”|Media mensual de horas extra + dimensión Carga de trabajo.|¿Filtramos horas rechazadas? ¿Campañas sesgan el promedio?|
|“Motivos de salida”|Clasificación de comentarios y motivo registrado por RR.HH.|¿La IA está agrupando bien o está inventando categorías?|

## 5. Flujo de modelado recomendado

La demostración debe seguir la lógica de BI explicada en la sesión: descubrimiento de datos, preparación, modelado y visualización. En Power BI Desktop resulta más fácil enseñar el Editor de Power Query, las relaciones y las medidas. Después puedes publicar el informe si quieres mostrar la capa de servicio.

|Capa|Qué haces|Resultado|
|---|---|---|
|1. Origen|Cargar todos los CSV desde carpeta o de forma individual.|Consultas raw sin transformar.|
|2. Staging|Normalizar IDs, fechas, números, textos y categorías. No calcular todavía el informe final.|Stg_HRIS, Stg_Movimientos, Stg_Clima, Stg_Formacion, etc.|
|3. Dimensiones|Crear DimEmpleado, DimDepartamento y DimFecha.|Tablas de filtro y segmentación.|
|4. Hechos|Crear FactMovimientos, FactClima, FactHorasExtra, FactAbsentismo, FactFormacion, FactSalario, FactSalida.|Tablas transaccionales con granularidad clara.|
|5. Agregados analíticos|Agrupar por empleado o mes cuando sea necesario.|AnaliticaEmpleado y RotacionMensual.|
|6. Métricas y narrativa|Crear medidas DAX y visuales con KPIs, tendencias y tablas de priorización.|Informe de rotación, abandono y acciones.|

## 6. Paso a paso ETL en Power Query

### 6.1. Preparación común

- Usa “Obtener datos > Texto/CSV” o “Carpeta” si quieres importar todas las fuentes de una vez.
- Define una convención: todas las consultas raw empiezan por Raw_, las de limpieza por Stg_, las dimensiones por Dim_ y las tablas de hechos por Fact_.
- Desactiva “Cargar” en las consultas Raw_ y Stg_ si solo sirven de paso intermedio. Así el modelo final queda más limpio.
- En cada origen, identifica primero la granularidad: empleado, movimiento, encuesta, curso, ausencia o mes.
### 6.2. Limpieza del maestro de empleados

|Problema intencionado|Transformación|Resultado|
|---|---|---|
|employee_code_raw con espacios, minúsculas o guiones|TRIM, UPPER y reemplazar “FSH-” por “FSH”.|employee_id limpio para relaciones.|
|Fechas en texto y formatos mixtos|Convertir con cultura es-ES y controlar errores.|fecha_alta y fecha_salida tipo fecha.|
|departamento_raw con variantes|Combinar con dim_departamentos_mapeo.|departamento_estandar y area_rrhh.|
|Duplicados de HRIS|Ordenar por fecha_carga y quitar duplicados por employee_id conservando la última fila.|Una fila válida por empleado.|
|Datos personales sintéticos|Mostrar cómo se sustituye nombre por employee_id o nombre anonimizado.|Privacidad y minimización de datos.|

Ejemplo de transformación conceptual en Power Query:
employee_id = Text.Upper(Text.Trim(Text.Replace([employee_code_raw], "FSH-", "FSH")))
fecha_alta = try Date.FromText([fecha_alta_txt], [Culture="es-ES"]) otherwise null
departamento_estandar = Merge con dim_departamentos_mapeo por departamento_raw

### 6.3. Movimientos de personal

Esta fuente es clave porque obliga a distinguir eventos de personas. Una baja no es un atributo del empleado; es un movimiento con fecha, motivo y tipo. Para rotación mensual, la tabla de movimientos es más útil que el maestro de empleados.

- Homologa tipo_movimiento_raw en categorías: Alta, Baja voluntaria, Baja no voluntaria, Promoción, Movilidad, Revisión salarial.
- Convierte fecha_movimiento_txt a fecha y crea periodo_mes.
- Filtra registros inválidos o sin employee_id correspondiente en DimEmpleado.
- Agrupa por periodo_mes y departamento para contar altas, bajas voluntarias y bajas no voluntarias.
### 6.4. Encuesta de clima

La encuesta llega en formato largo: una fila por empleado y dimensión. Esto permite enseñar una transformación muy didáctica: limpiar score, filtrar valores fuera de rango y pivotar dimensiones para crear variables analíticas.

|Dimensión raw|Campo final recomendado|Uso|
|---|---|---|
|Satisfacción|satisfaccion_1_10|Explicar experiencia general. Escalar de 1-5 a 1-10 si se desea.|
|Engagement|engagement_1_10|Compromiso y recomendación.|
|Calidad manager|calidad_manager_1_5|Relación con manager.|
|Desarrollo carrera|desarrollo_carrera_1_5|Señal de estancamiento.|
|Reconocimiento|reconocimiento_1_5|Cultura y valoración.|
|Percepción salario|percepcion_salario_1_5|Equidad y competitividad retributiva.|
|Balance vida trabajo|balance_vida_trabajo_1_5|Conciliación.|
|Carga trabajo|carga_trabajo_1_5|Sobrecarga y estrés.|

### 6.5. Formación, absentismo, horas extra y salario

|Fuente|Limpieza|Agregación final|
|---|---|---|
|raw_formacion.csv|Horas con coma decimal, estados “Completado/Finalizado/En curso”.|Horas realizadas 12m por employee_id, solo completadas o finalizadas.|
|raw_absentismo.csv|Fechas fin anteriores, días negativos y justificación pendiente.|Días laborables de absentismo 12m por employee_id.|
|raw_horas_extra.csv|Periodo mes mixto, horas como texto y estados de aprobación.|Media mensual de horas extra aprobadas por employee_id.|
|raw_salarios_beneficios.csv|Importes con símbolo €, separadores y porcentajes como texto.|Salario actual e incremento 12m por employee_id.|

## 7. Modelo analítico final

El modelo puede tener dos niveles: uno relacional para explicar buenas prácticas de BI, y otro agregado para acelerar la visualización. En una clase sin ordenadores para alumnos, conviene enseñar ambos: primero el modelo conceptual y después una tabla analítica que permita construir visuales rápidamente.

|Tabla final|Tipo|Clave|Para qué sirve|
|---|---|---|---|
|DimEmpleado|Dimensión|employee_id|Segmentar por departamento, nivel, rol, contrato, ubicación y estado.|
|DimDepartamento|Dimensión|departamento_estandar|Agrupar variantes y definir áreas críticas.|
|DimFecha|Dimensión|fecha|Analizar por mes, trimestre y año.|
|FactMovimientos|Hecho|movimiento_id|Altas, bajas, promociones y movilidad.|
|FactClima|Hecho|employee_id + dimension + fecha|Scores y comentarios de clima.|
|FactFormacion|Hecho|formacion_id|Horas de formación y estado.|
|FactAbsentismo|Hecho|ausencia_id|Días de absentismo y tipos de ausencia.|
|FactHorasExtra|Hecho|employee_id + periodo_mes|Carga operativa mensual.|
|FactSalario|Hecho|employee_id + periodo|Salario e incremento.|
|AnaliticaEmpleado|Agregado|employee_id|Base para detección de abandono.|
|RotacionMensual|Agregado|periodo_mes + departamento|Base para página de rotación.|

## 8. Métricas: de la pregunta al cálculo

La parte más importante de la sesión es que los alumnos entiendan que una métrica no es solo una tarjeta de Power BI. Es una definición de negocio. Por eso, cada indicador debe responder cuatro preguntas: qué evento cuenta, sobre qué población, en qué periodo y con qué fuente.

|Indicador|Numerador|Denominador / base|Fuente y regla|
|---|---|---|---|
|Headcount fin de mes|Empleados con alta <= fin de mes y sin salida anterior al fin de mes|No aplica|HRIS o movimientos. Se calcula por fecha de corte.|
|Bajas voluntarias mes|Movimientos de baja voluntaria en el mes|No aplica|FactMovimientos con tipo_movimiento homologado.|
|Tasa rotación voluntaria|Bajas voluntarias mes|Headcount medio del mes|Headcount medio = (inicio + fin) / 2.|
|Promociones 24m|Movimientos de promoción entre 01/05/2024 y 30/04/2026|Empleado|FactMovimientos. Puede ser conteo por empleado o porcentaje de empleados promocionados.|
|Horas formación 12m|Suma de horas realizadas completadas/finalizadas|Empleado|FactFormacion. Excluir canceladas/no completadas.|
|Absentismo 12m|Suma de días laborables válidos|Empleado|FactAbsentismo. Excluir días negativos o errores.|
|Horas extra media mes|Horas extra aprobadas de los últimos 12 meses|Número de meses activos|FactHorasExtra. Filtrar aprobadas.|
|Riesgo de abandono|Score ponderado de señales de riesgo|Empleado activo|Agregado de clima, salario, carga, formación, desempeño y movimientos.|

## 9. Medidas y fórmulas útiles

### 9.1. DAX para rotación

Empleados = DISTINCTCOUNT(DimEmpleado[employee_id])

Bajas voluntarias =
CALCULATE(
 COUNTROWS(FactMovimientos),
 FactMovimientos[tipo_movimiento] = "Baja voluntaria"
)

Headcount fin mes =
VAR FechaCorte = MAX(DimFecha[fecha])
RETURN
CALCULATE(
 DISTINCTCOUNT(DimEmpleado[employee_id]),
 DimEmpleado[fecha_alta] <= FechaCorte,
 ISBLANK(DimEmpleado[fecha_salida]) || DimEmpleado[fecha_salida] > FechaCorte
)

Tasa rotación voluntaria = DIVIDE([Bajas voluntarias], [Headcount medio mes])

|Consejo docente<br>En directo, no empieces por DAX. Empieza preguntando: “¿Qué es una baja voluntaria? ¿Cuál es la población de referencia? ¿Qué fecha usamos?” Después enseña la fórmula como traducción técnica de esa definición.|
|---|

### 9.2. Score explicable de abandono

Para una demostración sin entrenamiento de modelo predictivo, puedes construir un score heurístico. No pretende ser un modelo real de machine learning; sirve para enseñar la lógica de una señal de priorización.

Riesgo_abandono =
0,18 * (1 - Satisfacción_normalizada)
+ 0,14 * (1 - Engagement_normalizado)
+ 0,12 * (1 - Desarrollo_carrera_normalizado)
+ 0,10 * (1 - Calidad_manager_normalizada)
+ 0,10 * (1 - Percepción_salarial_normalizada)
+ 0,10 * Carga_trabajo_normalizada
+ 0,08 * Horas_extra_normalizadas
+ 0,06 * Absentismo_normalizado
+ 0,06 * Sin_promoción_24m
+ 0,04 * Incremento_salarial_bajo
+ 0,02 * Contrato_temporal

- Segmentación sugerida: Bajo < 0,35; Medio 0,35-0,55; Alto 0,55-0,75; Crítico >= 0,75.
- El score debe explicarse como una alerta para conversar, no como una sentencia sobre una persona.
- Nunca comuniques a un empleado que “el algoritmo predice que se va”. La conversación debe centrarse en desarrollo, bienestar y escucha.
## 10. Páginas de informe para construir en la demo

|Página|Visuales|Mensaje que debe quedar claro|
|---|---|---|
|Resumen ejecutivo|3 KPI arriba: headcount, bajas voluntarias, tasa rotación. Gráfico principal y texto de conclusión.|La rotación existe, se concentra en áreas concretas y requiere priorización.|
|Rotación mensual|Línea por periodo, barras por departamento, matriz mes x departamento.|Qué ocurrió, cuándo y dónde.|
|Factores de abandono|Comparativas por riesgo: satisfacción, desarrollo, manager, carga, salario, horas extra.|Qué señales podrían explicar el riesgo.|
|Priorización de empleados activos|Tabla con employee_id, departamento, riesgo, talento clave y factores explicativos.|A quién revisar con intervención humana y por qué.|
|Voz del empleado|Tabla de motivos de salida y resumen de comentarios con ChatGPT.|Qué dicen los empleados y si coincide con los datos.|
|Plan de acción|Matriz impacto-esfuerzo y KPIs de seguimiento.|Qué hará RR.HH. y cómo medirá si funciona.|

## 11. Uso de ChatGPT dentro de la demostración

Usa ChatGPT en dos momentos: primero para clasificar comentarios de salida y clima; después para ayudarte a redactar una conclusión ejecutiva. La clave pedagógica es que ChatGPT no sustituye el análisis, sino que convierte texto no estructurado en hipótesis que después se contrastan con los datos.

Prompt para clasificar comentarios:
Actúa como analista de People Analytics de FraSoHome.
Clasifica los siguientes comentarios de salida en estas categorías:
Mejor oferta salarial, Falta de desarrollo, Carga de trabajo y estrés,
Relación con manager, Conciliación, Cultura y reconocimiento, Otro.
Devuelve una tabla con: employee_id, motivo_chatgpt, sentimiento, evidencia breve,
acción_recomendada y confianza_1_5.
No inventes información si el comentario no contiene evidencia suficiente.

Prompt para conclusión ejecutiva:
Con estos resultados de Power BI y los temas de comentarios, redacta una síntesis
para Comité de Dirección en 5 puntos: situación, evidencias, hipótesis, acciones
priorizadas y cautelas éticas. Distingue claramente entre correlación, hipótesis y conclusión.

## 12. Guion minuto a minuto para la demo

|Tiempo|Actividad|Participación de alumnos|Resultado|
|---|---|---|---|
|0-10 min|Recordatorio del reto FraSoHome y presentación de fuentes brutas.|Dicen qué indicadores mirarían primero.|Backlog inicial de métricas.|
|10-25 min|Data discovery: abrir 2-3 CSV y revisar granularidad, errores y claves.|Detectan problemas: duplicados, fechas, IDs, categorías.|Lista de problemas de calidad.|
|25-45 min|Power Query: limpiar HRIS y departamentos.|Deciden qué hacer con duplicados y categorías no mapeadas.|DimEmpleado y DimDepartamento.|
|45-65 min|Movimientos: altas, bajas y rotación.|Definen baja voluntaria y denominador.|Primer KPI de rotación.|
|65-85 min|Clima y factores: pivotar encuesta y agregar formación/ausencias/horas extra.|Proponen señales de riesgo.|AnaliticaEmpleado.|
|85-105 min|Construcción del score de abandono y visuales de riesgo.|Debaten cautelas éticas y uso responsable.|Página de factores y priorización.|
|105-120 min|ChatGPT con comentarios de salida y cierre ejecutivo.|Validan si la salida de IA coincide con los datos.|Conclusión y plan de acción.|

## 13. Preguntas para dinamizar durante la demo

- ¿Qué diferencia hay entre contar bajas y calcular una tasa de rotación?
- ¿Por qué necesitamos headcount medio y no solo número de empleados actuales?
- ¿Qué pasa si mezclamos bajas voluntarias con fin de contrato?
- ¿Qué variable usaríais para explicar riesgo: satisfacción, manager, desarrollo, salario o carga?
- ¿Qué datos no usaríais para tomar decisiones individuales?
- ¿Qué haríais si ChatGPT clasifica un comentario de forma distinta al motivo registrado por RR.HH.?
- ¿Qué acción de retención sería de alto impacto y bajo esfuerzo?
## 14. Checklist de calidad y gobierno

|Control|Pregunta de validación|Acción recomendada|
|---|---|---|
|Claves|¿Todos los employee_id de hechos existen en DimEmpleado?|Crear tabla de registros no emparejados y revisarlos.|
|Duplicados|¿Hay empleados o movimientos duplicados?|Quitar duplicados con regla explícita y documentada.|
|Fechas|¿Todas las fechas son válidas y están en rango?|Convertir con cultura, controlar errores y excluir fechas imposibles.|
|Categorías|¿Los departamentos están homologados?|Usar dim_departamentos_mapeo y crear “Sin clasificar”.|
|Numéricos|¿Los importes y horas son números reales?|Eliminar €, %, puntos de miles y convertir coma decimal.|
|Privacidad|¿Mostramos información personal innecesaria?|Usar employee_id y agregados. Evitar nombres en visuales.|
|Ética|¿El score se usa como decisión automática?|Usarlo solo como priorización para revisión humana.|

## 15. Cierre docente sugerido

Cierra la demostración volviendo al punto de partida: los datos brutos no tienen valor por sí solos. El valor aparece cuando RR.HH. formula buenas preguntas, define indicadores con rigor, limpia las fuentes, modela relaciones y convierte el análisis en acciones responsables. Power BI ayuda a visualizar patrones; ChatGPT ayuda a estructurar texto e hipótesis; el criterio humano decide qué hacer y cómo actuar con las personas.

|Mensaje final<br>“People Analytics no consiste en predecir quién se va para etiquetarlo. Consiste en detectar señales sistémicas, priorizar conversaciones y diseñar mejores experiencias de empleado.”|
|---|
