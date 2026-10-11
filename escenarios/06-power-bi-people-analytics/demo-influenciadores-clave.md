# Demo influenciadores clave

**No usarlo para “decidir sobre personas”, sino para identificar patrones agregados que ayuden a RR.HH. a priorizar conversaciones, acciones de retención y análisis adicionales.**

Esto encaja con el caso, donde el objetivo es analizar rotación, señales de abandono, comentarios de clima/salida y acciones de retención, evitando convertir el score de abandono en una decisión automática.

**1. Demo principal: ¿qué factores aumentan el riesgo de abandono?**

Esta es la demo que más valor aporta.

**Pregunta analítica**

¿Qué factores explican que un empleado activo aparezca como alto riesgo de abandono?

**Configuración en Power BI**

Usa el CSV: frasohome_people_analytics.csv

Este dataset es el más adecuado porque tiene una fila por empleado y contiene estado, departamento, desempeño, satisfacción, engagement, variables de clima, score de abandono y comentarios.

En el visual **Influenciadores clave**:

|Campo del visual|Qué poner|
|---|---|
|Analyze / Analizar|alto_riesgo_flag|
|Valor a explicar|1 o “Sí”|
|Explain by / Explicar por|satisfaccion_1_10, engagement_1_10, calidad_manager_1_5, desarrollo_carrera_1_5, reconocimiento_1_5, percepcion_salario_1_5, carga_trabajo_1_5, horas_extra_media_mes, absentismo_dias_12m, departamento, nivel, tipo_contrato, antiguedad_meses, promociones_24m, incremento_salarial_12m_pct, horas_formacion_12m|
|Filtro de página|estado_actual = Activo|

Es importante filtrar por empleados activos, porque aquí no quieres explicar quién se fue, sino **quién presenta señales actuales de riesgo**.

**Resultado que puedes mostrar en clase**

Con los datos actuales, el patrón más valioso es este:

|Factor observado|Resultado aproximado en los datos|
|---|---|
|Satisfacción ≤ 5|58% de alto riesgo frente a una base de 21%|
|Engagement ≤ 5|54% de alto riesgo|
|Reconocimiento bajo|42% de alto riesgo|
|Calidad de manager baja|39% de alto riesgo|
|Horas extra ≥ 15 al mes|37% de alto riesgo|
|Departamento Logística|37% de alto riesgo|
|Carga de trabajo alta|34% de alto riesgo|
|Percepción salarial baja|34% de alto riesgo|
|Desarrollo de carrera bajo|33% de alto riesgo|

**Mensaje de negocio**

El resultado de valor no es “estas personas se van a ir”, sino:

“El riesgo de abandono no parece depender de una sola causa. En FraSoHome aparece una combinación de baja satisfacción, bajo engagement, poco reconocimiento, baja calidad percibida del manager, carga de trabajo y horas extra.”

Esto conecta muy bien con la dinámica inicial: los alumnos habían planteado problemas de rotación en tienda/logística, clima, desarrollo, salario y anticipación del abandono.

**Acción que puedes proponer**

Entrevistas de permanencia en colectivos de alto riesgo.

Revisión de carga y turnos en logística y atención al cliente.

Formación a managers en feedback, reconocimiento y conversaciones de desarrollo.

Plan de carrera visible para perfiles con bajo desarrollo percibido.

Revisión salarial solo donde la evidencia lo acompañe, no como explicación única.

**2. Demo histórica: ¿qué factores se asocian con la rotación voluntaria real?**

Esta demo sirve para diferenciar **rotación histórica** de **riesgo futuro**.

**Pregunta analítica**

¿Qué factores aparecen asociados a las salidas voluntarias de los últimos 24 meses?

**Configuración en Power BI**

|Campo del visual|Qué poner|
|---|---|
|Analyze / Analizar|abandono_voluntario_24m|
|Valor a explicar|1|
|Explain by / Explicar por|Los mismos factores de clima, carga, salario, formación, desempeño, departamento, nivel, antigüedad y contrato|
|Filtro|Sin filtrar por activo, porque quieres analizar el histórico completo|

**Campos que debes evitar en este análisis**

No metas en **Explain**** by** estos campos:

estado_actual

tipo_salida

fecha_salida

motivo_salida

comentario_salida

probabilidad_abandono

riesgo_abandono

alto_riesgo_flag

La razón es que algunos son consecuencia de la salida o están derivados del propio modelo de riesgo. Meterlos haría que el análisis fuese circular.

**Resultado que puedes mostrar**

Con el CSV actual, los factores que más ayudan a contar la historia son:

|Factor observado|Resultado aproximado|
|---|---|
|Horas extra ≥ 15 al mes|29% de abandono voluntario frente a 16% base|
|Contrato fijo discontinuo|26%|
|Antigüedad 49-72 meses|25%|
|Atención al Cliente|23%|
|Absentismo ≥ 13 días|23%|
|Carga de trabajo alta|22%|
|Engagement ≤ 5|22%|
|Desarrollo de carrera bajo|22%|

**Mensaje de negocio**

“En las salidas reales, la presión operativa y el estancamiento parecen pesar más que una explicación única basada en salario.”

Esta demo es muy potente para desmontar hipótesis simplistas del tipo “todo es salario”.

**3. Demo para la tarjeta de salario: ¿realmente el problema es el salario?**

Esta es una de las más útiles para debate, porque responde directamente a la tarjeta 7 de la dinámica: “los managers creen que el problema es el salario, pero no tienen datos que lo demuestren”.

**Pregunta analítica**

¿Qué factores explican una baja percepción salarial y cómo se relaciona con rotación o riesgo?

**Preparación**

Crea una columna calculada:

Percepcion Salarial Baja =

IF(

'frasohome_people_analytics'[percepcion_salario_1_5] <= 2.5,

"Sí",

"No"

)

**Configuración**

|Campo del visual|Qué poner|
|---|---|
|Analyze / Analizar|Percepcion Salarial Baja|
|Valor a explicar|Sí|
|Explain by / Explicar por|departamento, nivel, salario_anual_eur, incremento_salarial_12m_pct, promociones_24m, satisfaccion_1_10, engagement_1_10, reconocimiento_1_5, desarrollo_carrera_1_5, antiguedad_meses|
|Filtro recomendado|estado_actual = Activo|

**Resultado que puedes mostrar**

En los datos actuales:

|Factor observado|Resultado aproximado|
|---|---|
|Edad 50+|58% con baja percepción salarial|
|Satisfacción ≤ 5|49%|
|Engagement ≤ 5|47%|
|IT y Datos|45%|
|E-commerce|38%|
|Incremento salarial 0%|37%|
|Salario en cuartil bajo|36%|

**Mensaje de negocio**

“La percepción salarial aparece relacionada con la insatisfacción, el bajo engagement y algunos colectivos concretos. Pero no basta con decir ‘el problema es el salario’: hay que contrastarlo con desarrollo, reconocimiento, carga y promociones.”

Aquí podemos lanzar una pregunta al aula:

“Si el salario aparece como factor, ¿la acción correcta es subir salarios a todos o analizar dónde hay inequidad, falta de reconocimiento o falta de carrera?”

**4. Demo para desarrollo profesional: ¿dónde se percibe falta de crecimiento?**

Esta conecta directamente con los comentarios de clima que mencionan falta de desarrollo profesional.

**Pregunta analítica**

¿Qué factores explican que un empleado perciba bajo desarrollo de carrera?

**Preparación**

Desarrollo Bajo =

IF(

'frasohome_people_analytics'[desarrollo_carrera_1_5] <= 2.5,

"Sí",

"No"

)

**Configuración**

|Campo del visual|Qué poner|
|---|---|
|Analyze / Analizar|Desarrollo Bajo|
|Valor a explicar|Sí|
|Explain by / Explicar por|departamento, nivel, antiguedad_meses, horas_formacion_12m, promociones_24m, evaluacion_desempeno_1_5, satisfaccion_1_10, engagement_1_10, reconocimiento_1_5, calidad_manager_1_5|
|Filtro recomendado|estado_actual = Activo|

**Resultado que puedes mostrar**

Con los datos actuales:

|Factor observado|Resultado aproximado|
|---|---|
|E-commerce|41% con desarrollo bajo|
|Engagement ≤ 5|41%|
|Satisfacción ≤ 5|35%|
|IT y Datos|34%|
|Formación 0-10 horas|34%|
|Jornada parcial|32%|

**Mensaje de negocio**

“La falta de desarrollo no es solo un comentario cualitativo: puede convertirse en una señal cuantitativa analizable por área, formación, promociones y engagement.”

Esto permite enlazar Power BI con ChatGPT: primero ChatGPT clasifica comentarios de clima/salida como “falta de desarrollo”; después Power BI comprueba si ese tema aparece asociado a indicadores cuantitativos.

**5. Demo de abandono temprano de buen desempeño**

Esta es interesante porque conecta con la tarjeta 3: “algunos empleados con buen desempeño se marchan antes de los 24 meses”.

**Pregunta analítica**

¿Qué señales aparecen en empleados de buen desempeño que abandonan antes de los 24 meses?

**Preparación**

Abandono Temprano Buen Desempeno =

IF(

'frasohome_people_analytics'[abandono_voluntario_24m] = 1

&& 'frasohome_people_analytics'[antiguedad_meses] <= 24

&& 'frasohome_people_analytics'[evaluacion_desempeno_1_5] >= 4,

"Sí",

"No"

)

**Configuración**

|Campo del visual|Qué poner|
|---|---|
|Analyze / Analizar|Abandono Temprano Buen Desempeno|
|Valor a explicar|Sí|
|Explain by / Explicar por|departamento, nivel, salario_anual_eur, satisfaccion_1_10, engagement_1_10, desarrollo_carrera_1_5, reconocimiento_1_5, promociones_24m, horas_formacion_12m, tipo_contrato|

**Resultado que puedes mostrar**

En los datos actuales, los casos son pocos, pero aparecen señales en:

talento clave,

perfiles senior/manager,

empleados de E-commerce e IT y Datos,

salario alto,

antigüedad inferior a 24 meses.

**Mensaje **

“Este análisis no sirve para concluir de forma robusta, pero sí para enseñar una lección clave: no todos los problemas tienen suficiente base estadística. A veces el mejor insight es saber que necesitamos más datos o complementar con entrevistas.”

**6. Demo de rotación mensual y campañas**

Para este análisis puedes usar:

frasohome_rotacion_mensual.csv

El caso ya recomienda usarlo para analizar evolución mensual, tasa de rotación, bajas voluntarias, departamentos y áreas críticas.

**Pregunta analítica**

¿Qué factores mensuales explican los picos de rotación voluntaria?

**Configuración**

Aquí usaría el visual de Influenciadores clave con una variable numérica:

|Campo del visual|Qué poner|
|---|---|
|Analyze / Analizar|tasa_rotacion_voluntaria_pct|
|Tipo de análisis|Continuo|
|Explain by / Explicar por|departamento, periodo_mes, headcount_fin_mes, altas_mes, empleados_alto_riesgo_fin_mes, talento_clave_alto_riesgo_fin_mes, salario_medio_activos_mes_eur, satisfaccion_media_activos_mes, engagement_medio_activos_mes|

Para que se entienda mejor en clase, añade una columna de campaña:

Campaña =

SWITCH(

TRUE(),

MONTH('frasohome_rotacion_mensual'[periodo_mes]) IN {1, 7}, "Rebajas",

MONTH('frasohome_rotacion_mensual'[periodo_mes]) = 11, "Black Friday",

MONTH('frasohome_rotacion_mensual'[periodo_mes]) = 12, "Navidad",

"Normal"

)

Y mete Campaña en **Explain**** by**.

**Resultado que puedes mostrar**

Con los datos actuales:

|Factor / periodo|Resultado aproximado|
|---|---|
|Black Friday|tasa media cercana a 1,9%|
|Navidad|tasa media cercana a 1,4%|
|Atención al Cliente|tasa media cercana a 1,1%|
|Compras|tasa media cercana a 1,0%|
|Tienda física|tasa media cercana a 0,8%|
|Logística|tasa media cercana a 0,6%|

Hay que tratar con cuidado departamentos pequeños como Finanzas, porque pocos movimientos pueden generar tasas altas.

**Mensaje de negocio**

“La rotación no solo depende del departamento; también puede concentrarse en momentos operativos de alta presión.”

**7. Demo con motivos de salida: conectar ChatGPT con Power BI**

Esta es muy buena para enlazar IA generativa y BI.

**Pregunta analítica**

¿Qué factores explican que una salida se clasifique como falta de desarrollo, carga de trabajo, salario o relación con manager?

**Configuración**

Usa:

frasohome_comentarios_salida.csv

|Campo del visual|Qué poner|
|---|---|
|Analyze / Analizar|motivo_salida_sistema|
|Valor a explicar|Falta de desarrollo o Carga de trabajo y estrés|
|Explain by / Explicar por|departamento, nivel, rol, satisfaccion_1_10, probabilidad_abandono|

**Resultado que puedes mostrar**

En los datos actuales, los motivos más frecuentes son:

|Motivo de salida|Casos aproximados|
|---|---|
|Falta de desarrollo|27|
|Carga de trabajo y estrés|23|
|Mejor oferta salarial|21|
|Relación con manager|21|
|Cultura y reconocimiento|19|
|Conciliación|14|

**Mensaje**

“ChatGPT puede ayudarnos a clasificar comentarios, pero Power BI nos permite cuantificar qué temas pesan más, en qué departamentos aparecen y cómo se conectan con satisfacción y riesgo.”

Esto enlaza con el objetivo del caso de combinar datos cuantitativos, comentarios cualitativos y acciones de retención.

**8. Demo de segmentos: no solo factores aislados, sino combinaciones**

En el visual de Power BI, no te quedes solo en la pestaña **Key ****influencers**. Cambia a **Top ****segments**.

Microsoft indica que **Top ****segments** muestra combinaciones de factores que contribuyen al resultado analizado, no solo factores individuales. ()

Para FraSoHome, esta es la parte con más valor directivo.

**Ejemplo de segmento que puedes buscar**

Con el análisis de alto_riesgo_flag, pueden aparecer segmentos del tipo:

|Segmento|Lectura de negocio|
|---|---|
|Satisfacción baja + reconocimiento bajo + manager bajo|Riesgo asociado a experiencia directa con el equipo/manager|
|Carga alta + horas extra altas + bajo balance vida-trabajo|Riesgo asociado a presión operativa|
|Desarrollo bajo + antigüedad media/alta + pocas promociones|Riesgo asociado a estancamiento|
|Percepción salarial baja + bajo engagement|Riesgo asociado a recompensa total y motivación|

**Cómo lo explicaría en clase**

“Un factor aislado nos da una pista. Un segmento nos da un colectivo accionable.”

Por ejemplo:

“No vamos a actuar sobre ‘todos los empleados con baja satisfacción’. Vamos a priorizar empleados activos de áreas operativas que combinan baja satisfacción, alto volumen de horas extra y bajo reconocimiento.”

**Columnas calculadas recomendadas para preparar la demo**

Para que el visual sea más claro y no dependa solo de variables continuas, prepararía estas columnas antes de la sesión.

Riesgo Alto Critico =

IF(

'frasohome_people_analytics'[riesgo_abandono] IN {"Alto", "Crítico"},

"Alto/Crítico",

"Bajo/Medio"

)

Satisfaccion Baja =

IF(

'frasohome_people_analytics'[satisfaccion_1_10] <= 5,

"Sí",

"No"

)

Engagement Bajo =

IF(

'frasohome_people_analytics'[engagement_1_10] <= 5,

"Sí",

"No"

)

Desarrollo Bajo =

IF(

'frasohome_people_analytics'[desarrollo_carrera_1_5] <= 2.5,

"Sí",

"No"

)

Percepcion Salarial Baja =

IF(

'frasohome_people_analytics'[percepcion_salario_1_5] <= 2.5,

"Sí",

"No"

)

Reconocimiento Bajo =

IF(

'frasohome_people_analytics'[reconocimiento_1_5] <= 2.5,

"Sí",

"No"

)

Carga Alta =

IF(

'frasohome_people_analytics'[carga_trabajo_1_5] >= 4,

"Sí",

"No"

)

Horas Extra Altas =

IF(

'frasohome_people_analytics'[horas_extra_media_mes] >= 15,

"Sí",

"No"

)

Antiguedad Tramo =

SWITCH(

TRUE(),

'frasohome_people_analytics'[antiguedad_meses] <= 12, "0-12 meses",

'frasohome_people_analytics'[antiguedad_meses] <= 24, "13-24 meses",

'frasohome_people_analytics'[antiguedad_meses] <= 48, "25-48 meses",

'frasohome_people_analytics'[antiguedad_meses] <= 72, "49-72 meses",

"73+ meses"

)

Abandono Temprano Buen Desempeno =

IF(

'frasohome_people_analytics'[abandono_voluntario_24m] = 1

&& 'frasohome_people_analytics'[antiguedad_meses] <= 24

&& 'frasohome_people_analytics'[evaluacion_desempeno_1_5] >= 4,

"Sí",

"No"

)

Talento Clave en Riesgo =

IF(

'frasohome_people_analytics'[talento_clave_flag] = 1

&& 'frasohome_people_analytics'[alto_riesgo_flag] = 1,

"Sí",

"No"

)

**Campos que no usaría como “explicadores”**

Para evitar resultados pobres o engañosos, no pondría estos campos en **Explain**** by**:

|Campo|Motivo|
|---|---|
|employee_id|Demasiadas categorías; no generaliza.|
|nombre_anonimizado|No aporta patrón y puede distraer.|
|comentario_salida|Texto libre, mejor clasificarlo antes con ChatGPT.|
|comentario_clima|Igual: primero convertir a tema/categoría.|
|fecha_salida|Es consecuencia de la salida.|
|tipo_salida|Directamente relacionado con el target.|
|motivo_salida|Es posterior a la salida.|
|probabilidad_abandono|Es un score derivado; circular si explica alto_riesgo_flag.|
|riesgo_abandono|Circular si explica alto_riesgo_flag.|
|prioridad_retencion|Derivada del propio riesgo.|

**La secuencia que usaría en clase**

**Pregunta a los alumnos:**
“¿Qué factores creéis que explican el riesgo de abandono?”

**Escribe 6-8 candidatos en la pizarra:**
salario, carga, manager, desarrollo, reconocimiento, horas extra, satisfacción, departamento.

**Abre Power BI y crea el visual de Influenciadores clave.**

**Primer análisis:**
alto_riesgo_flag con filtro estado_actual = Activo.

**Compara con las hipótesis de los alumnos:**
“¿El salario aparece? Sí, pero no solo. ¿Qué otros factores pesan?”

**Cambia a Top ****segments****:**
Busca combinaciones accionables.

**Cierra con decisión de RR.HH.:**
“¿Qué haríamos con esta evidencia?”

**Remata con ética:**
“Este análisis no etiqueta personas; prioriza conversaciones y acciones.”

**Mi recomendación final**

Para mostrar resultados con valor, haría estos tres análisis en directo:

|Orden|Análisis|Por qué aporta valor|
|---|---|---|
|1|Factores que explican alto riesgo de abandono|Es el más conectado con la necesidad de actuar preventivamente.|
|2|Factores asociados a abandono voluntario histórico|Permite contrastar el riesgo actual con salidas reales.|
|3|¿Es realmente el salario?|Genera debate y obliga a distinguir hipótesis de evidencia.|

Y dejaría como análisis complementarios:

|Análisis complementario|Uso|
|---|---|
|Desarrollo bajo|Conecta clima, formación, promociones y carrera.|
|Motivos de salida|Conecta ChatGPT con Power BI.|
|Rotación mensual por campaña|Conecta People Analytics con operación y calendario.|
|Abandono temprano de buen desempeño|Útil para hablar de talento clave y límites por bajo volumen de datos.|

La historia quedaría así:

“FraSoHome no tiene solo un problema de rotación. Tiene varios focos: presión operativa, falta de reconocimiento, baja percepción de desarrollo, señales de manager y, en algunos colectivos, percepción salarial. Power BI nos ayuda a identificar los factores clave; ChatGPT nos ayuda a interpretar la voz del empleado; RR.HH. debe convertir ambos en acciones humanas, medibles y éticas.”
