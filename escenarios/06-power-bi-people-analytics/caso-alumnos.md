# Caso_FraSoHome_PeopleAnalytics_Alumnos

**Introducción.**

FraSoHome es una cadena ficticia de muebles, decoración y equipamiento del hogar que opera en varias tiendas físicas, un canal e-commerce y un centro logístico. El negocio ya trabajaba con datos de ventas, clientes y stock; ahora la Dirección de Personas quiere aplicar el mismo enfoque data-driven a la gestión de talento para entender la rotación, anticipar el abandono voluntario y diseñar acciones de retención basadas en evidencias.

El caso conecta tres ideas centrales de la sesión de People Analytics: transformar datos en conocimiento para tomar mejores decisiones, utilizar IA generativa para analizar texto y generar hipótesis, y construir informes de negocio con Power BI respetando criterios de ética, privacidad, explicabilidad y supervisión humana.

**Propósito formativo**

El alumno debe actuar como analista de People Analytics de FraSoHome. Primero realizará pruebas de prompt engineering con ChatGPT sobre comentarios de salida y clima. Después utilizará Power BI Service para construir análisis de rotación y detección de riesgo de abandono con datos sintéticos en CSV.

**1. Contexto de negocio de ****FraSoHome**

Durante los últimos 24 meses FraSoHome ha crecido en venta online, ha ampliado horarios de atención al cliente y ha incrementado la presión logística en campañas como rebajas, Black Friday y Navidad. El crecimiento ha generado más oportunidades, pero también síntomas de tensión interna: salidas voluntarias en posiciones de tienda, rotación en atención al cliente, pérdida de perfiles senior en e-commerce y dudas sobre si los planes de carrera son visibles para la plantilla.

La organización cuenta con datos de RR.HH., encuestas de clima, entrevistas de salida y registros de formación y desempeño. Sin embargo, la información se ha usado principalmente para reporting operativo y no para priorizar acciones de retención. La Dirección de Personas solicita un informe que responda a tres preguntas:

**• **¿Dónde se concentra la rotación voluntaria y cómo evoluciona por mes y departamento?

**• **¿Qué señales explican el riesgo de abandono de los empleados activos?

**• **¿Qué acciones de retención deberían priorizarse y cómo comunicarlas a Dirección?

**2. Reto del caso**

El reto consiste en preparar un diagnóstico ejecutivo para el Comité de Dirección de FraSoHome. El análisis no debe limitarse a contar bajas: debe combinar datos cuantitativos, comentarios cualitativos y visualización de indicadores. El alumno deberá distinguir entre rotación histórica y predicción de abandono, evitando tratar un score de riesgo como una decisión automática.

|Dimensión|Pregunta de negocio|Evidencia esperada|
|---|---|---|
|Rotación de personal|¿Qué áreas, meses o perfiles acumulan más salidas voluntarias?|Tasa de rotación por mes y departamento, bajas voluntarias, headcount, comparativas por área.|
|Detección de abandono|¿Qué empleados activos presentan señales de riesgo?|Probabilidad de abandono, nivel de riesgo, satisfacción, engagement, manager, desarrollo, salario, absentismo y horas extra.|
|Voz del empleado|¿Qué motivos aparecen en comentarios de salida y clima?|Categorías de motivos, sentimiento, temas recurrentes y ejemplos representativos generados con ChatGPT.|
|Acción|¿Qué debería hacer RR.HH. con los hallazgos?|Plan de retención con acciones, responsables, prioridad e impacto esperado.|

**3. Objetivos pedagógicos**

**• **Aplicar conceptos de People Analytics a un problema realista de RR.HH.: retención de talento y rotación voluntaria.

**• **Comparar tipos de prompts en ChatGPT: zero-shot, one-shot, few-shot, razonamiento estructurado y formato de salida.

**• **Usar ChatGPT como apoyo para analizar texto, generar hipótesis y redactar recomendaciones, manteniendo criterio humano.

**• **Cargar CSV en Power BI Service, crear un modelo semántico y diseñar informes con visuales, filtros y KPIs.

**• **Construir un análisis de rotación de personal y una detección de abandono basada en score de riesgo.

**• **Incorporar criterios de ética, privacidad, sesgos y explicabilidad en el uso de IA aplicada a personas.

**4. Datos disponibles**

Los datos se han generado sintéticamente para el caso y no contienen información real de empleados. La fecha de corte del análisis es 30/04/2026. El paquete incluye los siguientes CSV:

|Archivo|Uso principal|Contenido|
|---|---|---|
|frasohome_people_analytics.csv|Power BI: análisis de abandono y perfil de empleados.|820 registros a nivel empleado con estado, departamento, desempeño, satisfacción, engagement, variables de clima, score de abandono y comentarios.|
|frasohome_rotacion_mensual.csv|Power BI: análisis mensual de rotación.|Serie mensual 2024-2026 por departamento con headcount, altas, bajas voluntarias, bajas no voluntarias y tasa de rotación.|
|frasohome_comentarios_salida.csv|ChatGPT: análisis cualitativo de entrevistas de salida.|151 comentarios sintéticos de salida con motivo registrado por RR.HH. para validar clasificaciones.|
|frasohome_comentarios_clima.csv|ChatGPT: análisis de temas de clima.|Comentarios sintéticos de empleados activos y no activos para identificar temas recurrentes.|
|frasohome_muestra_prompt_chatgpt.csv|ChatGPT: muestra breve para practicar prompts.|Subconjunto de comentarios para probar zero-shot, one-shot y few-shot sin pegar demasiados datos.|
|frasohome_diccionario_datos.csv|Consulta y documentación.|Diccionario de variables de los datasets principales.|

**Nota de privacidad**

Aunque los datos son sintéticos, se trabajará como si fueran datos reales: no se deben pegar nombres reales, salarios individualizados reales ni información sensible en herramientas públicas. Para el ejercicio se permite usar los identificadores anonimizados FSH0001, FSH0002, etc.

**5. Variables clave del ****dataset**** principal**

|Variable|Interpretación para el caso|
|---|---|
|abandono_voluntario_24m|Variable histórica: 1 si el empleado salió voluntariamente en el periodo de análisis.|
|probabilidad_abandono|Score sintético entre 0 y 1. Debe interpretarse como señal de priorización, no como decisión automática.|
|riesgo_abandono|Segmento derivado del score: Bajo, Medio, Alto o Crítico.|
|alto_riesgo_flag|1 si el empleado activo supera el umbral de alto riesgo definido para el caso.|
|talento_clave_flag|1 si combina alto desempeño con rol crítico para FraSoHome.|
|satisfaccion_1_10 / engagement_1_10|Indicadores de experiencia de empleado. Ayudan a explicar riesgo y priorizar acciones.|
|calidad_manager_1_5 / desarrollo_carrera_1_5 / reconocimiento_1_5|Dimensiones de clima y gestión que pueden estar asociadas al abandono.|
|carga_trabajo_1_5 / horas_extra_media_mes / absentismo_dias_12m|Señales de presión operativa y bienestar.|
|comentario_salida / comentario_clima|Texto no estructurado para pruebas con ChatGPT.|

**6. Secuencia de trabajo del caso**

|Bloque|Duración orientativa|Resultado|
|---|---|---|
|A. ChatGPT y prompt engineering|45-60 min|Comparación de prompts y tabla de motivos de salida/clima.|
|B. Power BI Service: carga y primer informe|30-45 min|Modelo semántico desde CSV y página de indicadores generales.|
|C. Análisis de rotación|45 min|Visualización de rotación por mes, departamento y área crítica.|
|D. Detección de abandono|45-60 min|Informe de empleados activos con alto riesgo y factores explicativos.|
|E. Síntesis ejecutiva|30 min|Conclusiones, recomendaciones y límites éticos del análisis.|

**7. Actividad A: pruebas en ChatGPT**

Antes de abrir Power BI, los alumnos utilizarán ChatGPT para comprobar cómo cambia la respuesta según el tipo de prompt. El objetivo no es “delegar” el diagnóstico, sino aprender a formular instrucciones útiles, contrastar la salida con los datos y documentar qué prompt genera mejor evidencia para RR.HH.

**7.1 Preparación**

**• **Abrir frasohome_muestra_prompt_chatgpt.csv y copiar entre 10 y 20 comentarios de salida.

**• **No modificar el contenido de los comentarios antes de la primera prueba.

**• **Guardar las respuestas de ChatGPT en un documento o bloc de notas: prompt usado, salida obtenida, fortalezas y debilidades.

**• **Comparar la clasificación generada por ChatGPT con motivo_salida_sistema del CSV.

**8. Actividad B: Power BI Service**

La parte de BI se realiza en Power BI Service, desde el navegador. El material de referencia actual de Microsoft indica que un archivo CSV puede incorporarse a un workspace como modelo semántico desde New item > Semantic model > CSV, con vista previa y opción de crear informe. En este caso se recomienda crear dos informes separados: uno con frasohome_rotacion_mensual.csv y otro con frasohome_people_analytics.csv.

**8.1 Cargar un CSV como modelo semántico**

**1. **Entrar en app.powerbi.com con una cuenta que permita crear contenido en “My workspace” o en un workspace de formación.

**2. **Ir al workspace elegido y seleccionar New item.

**3. **En Store data, seleccionar Semantic model.

**4. **Elegir CSV y después Upload file si el archivo está en el ordenador, o seleccionar OneDrive/SharePoint si el docente lo ha compartido en la nube.

**5. **Seleccionar el CSV, pulsar Next y revisar la vista previa. Verificar que los campos numéricos se reconocen como números y los campos fecha como fecha.

**6. **Elegir Create a report para abrir la creación del informe. Asignar un nombre claro al modelo semántico, por ejemplo “FraSoHome Rotación Mensual”.

**Consejo de aula**

Si Power BI no reconoce alguna fecha o número por configuración regional, continuar con el informe usando los campos ya preagregados del CSV. Para transformaciones avanzadas, se puede repetir el ejercicio en Power BI Desktop, pero el objetivo de este caso es practicar el servicio web.

**8.2 Informe 1: análisis de rotación de personal**

CSV recomendado: frasohome_rotacion_mensual.csv. Este informe debe responder de un vistazo dónde y cuándo aumenta la rotación. Crear una página llamada “Rotación mensual”.

|Visual|Campos sugeridos|Pregunta que responde|
|---|---|---|
|Tarjeta KPI|Promedio de tasa_rotacion_voluntaria_pct filtrado por departamento = Total.|¿Cuál es la rotación voluntaria mensual media?|
|Tarjeta KPI|Suma de bajas_voluntarias_mes.|¿Cuántas salidas voluntarias se acumulan en el periodo?|
|Línea temporal|Eje: periodo_mes. Valor: tasa_rotacion_voluntaria_pct. Filtro: departamento = Total.|¿Cómo evoluciona la rotación por mes?|
|Barras por departamento|Eje: departamento. Valor: suma de bajas_voluntarias_mes. Excluir Total.|¿Qué áreas concentran más bajas?|
|Matriz|Filas: departamento. Columnas: periodo_mes. Valores: tasa_rotacion_voluntaria_pct.|¿Qué meses y áreas son más críticas?|
|Segmentadores|departamento, periodo_mes, area_critica_rotacion_flag.|Permite explorar campañas y áreas específicas.|

**Pasos recomendados para la página de rotación**

**7. **Insertar tres tarjetas en la parte superior: headcount_fin_mes, bajas_voluntarias_mes y tasa_rotacion_voluntaria_pct.

**8. **Colocar debajo una línea temporal de tasa_rotacion_voluntaria_pct por periodo_mes para el departamento Total.

**9. **Añadir un gráfico de barras con bajas_voluntarias_mes por departamento, excluyendo el valor Total para no duplicar.

**10. **Añadir una matriz de departamentos por meses para detectar áreas críticas. Aplicar formato condicional si está disponible.

**11. **Usar segmentadores para filtrar por periodo y departamento. Probar campañas de mayor actividad.

**12. **Redactar en un cuadro de texto dos conclusiones: dónde está el problema y qué hipótesis se conectan con los comentarios de salida.

**8.3 Informe 2: detección de abandono**

CSV recomendado: frasohome_people_analytics.csv. Crear una página llamada “Riesgo de abandono”. El objetivo es identificar empleados activos con señales de riesgo y explicar qué variables podrían estar asociadas. El informe no debe usarse para tomar decisiones automáticas sobre personas.

|Visual|Campos sugeridos|Uso|
|---|---|---|
|Tarjeta KPI|Suma de activo_actual.|Plantilla activa actual.|
|Tarjeta KPI|Suma de alto_riesgo_flag filtrado por estado_actual = Activo.|Número de activos con alto riesgo.|
|Tarjeta KPI|Promedio de probabilidad_abandono filtrado por estado_actual = Activo.|Riesgo medio actual.|
|Barras|Eje: departamento. Valor: promedio probabilidad_abandono o suma alto_riesgo_flag.|Áreas con mayor exposición a abandono.|
|Dispersión|X: satisfaccion_1_10. Y: probabilidad_abandono. Tamaño: salario_anual_eur. Leyenda: departamento.|Relación entre satisfacción y riesgo.|
|Tabla de priorización|employee_id, departamento, rol, nivel, probabilidad_abandono, riesgo_abandono, talento_clave_flag, prioridad_retencion.|Lista de revisión para RR.HH. con enfoque humano.|
|Segmentadores|departamento, nivel, riesgo_abandono, talento_clave_flag.|Permite focalizar perfiles.|

**Pasos recomendados para la página de abandono**

**13. **Aplicar un filtro de página: estado_actual = Activo. Así el score se interpreta sobre la plantilla actual.

**14. **Crear tarjetas con plantilla activa, empleados de alto riesgo y probabilidad media de abandono.

**15. **Crear un gráfico de barras por departamento con suma de alto_riesgo_flag. Ordenar de mayor a menor.

**16. **Crear una dispersión con satisfacción en el eje X y probabilidad_abandono en el eje Y. Revisar si los puntos de mayor riesgo tienen baja satisfacción, baja percepción salarial o carga elevada.

**17. **Crear una tabla de empleados priorizados y filtrar riesgo_abandono = Alto o Crítico. Mantener employee_id anonimizado.

**18. **Añadir un texto de interpretación: “El score no decide; ayuda a priorizar conversaciones de permanencia, revisión de carrera y apoyo al manager”.

**8.4 Visual de factores explicativos**

Para conectar el abandono con posibles causas, crear una página adicional llamada “Factores de riesgo”. Utilizar gráficos de barras o tarjetas comparando los promedios de las siguientes variables por riesgo_abandono: satisfacción, engagement, calidad de manager, desarrollo de carrera, reconocimiento, percepción salarial, carga de trabajo, horas extra y absentismo. El alumno debe identificar al menos tres señales asociadas al grupo Alto/Crítico.

**Pregunta guía**

¿Qué variables tienen mayor diferencia entre el grupo Bajo/Medio y el grupo Alto/Crítico?

¿Las causas que aparecen en ChatGPT coinciden con los patrones cuantitativos?

¿Qué acción concreta propondrías para el departamento con más exposición?

**8.5 Medidas opcionales en DAX**

Si el entorno de Power BI Service permite crear medidas en el modelo semántico, los alumnos avanzados pueden usar las siguientes expresiones. Si no aparece la opción de medida, se puede trabajar con los campos preagregados incluidos en los CSV.

**DAX opcional**

Empleados = SUM(frasohome_people_analytics[conteo_empleado])

Bajas voluntarias = SUM(frasohome_people_analytics[abandono_voluntario_24m])

Tasa abandono 24m = DIVIDE([Bajas voluntarias], [Empleados])

Activos = SUM(frasohome_people_analytics[activo_actual])

Alto riesgo activos = SUM(frasohome_people_analytics[alto_riesgo_flag])

Riesgo medio = AVERAGE(frasohome_people_analytics[probabilidad_abandono])

**9. Narrativa del informe**

El informe debe seguir una narrativa de negocio sencilla: presentación, nudo y desenlace. Primero se muestran indicadores globales; después se exploran áreas, perfiles y tendencias; por último se resumen acciones. Aplicar la regla de los 5 segundos: un usuario directivo debe entender el mensaje principal de cada página sin descifrar demasiados elementos.

|Página|Mensaje esperado|Diseño recomendado|
|---|---|---|
|Resumen ejecutivo|La rotación existe, tiene focos concretos y requiere acciones priorizadas.|3-4 KPIs arriba, 2 visuales centrales, texto breve de conclusión.|
|Rotación mensual|Las salidas varían por mes y departamento.|Línea temporal + barras por departamento + matriz.|
|Riesgo de abandono|Existen empleados activos con alto riesgo que deben ser revisados con intervención humana.|Tarjetas + barras + tabla priorizada.|
|Factores de riesgo|La combinación de satisfacción, desarrollo, manager, carga y salario explica parte del riesgo.|Comparativas por segmento de riesgo y texto de hipótesis.|
|Plan de acción|RR.HH. propone acciones concretas medibles.|Tabla impacto-esfuerzo y próximos pasos.|
