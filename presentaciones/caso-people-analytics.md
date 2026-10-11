# FraSoHome_presentacion_caso

## Slide 1: FraSoHome

- Presentación del caso práctico
- People Analytics con Power BI y ChatGPT
- Guía para introducir el reto, las actividades y los entregables del alumno

## Slide 2: CONTEXTO


- Dónde encaja el caso FraSoHome
El caso convierte contenidos previos de RR.HH. en preguntas, datos, análisis y decisiones.

- Contenidos previos
Digitalización de RR.HH.

- automatización y uso de datos
- Clima organizacional
- voz del empleado
- Evaluación del desempeño
- hechos, feedback y desarrollo
- HR Balanced Scorecard
- indicadores para Dirección
- FraSoHome
- un reto de personas
- con datos sintéticos
- Hoy lo aplicamos
- ChatGPT
- hipótesis, temas y prompts
- Power BI
- visualización y KPIs
- Ética
- sesgos, privacidad y límites humanos
Idea fuerza: no empezamos por la herramienta; empezamos por una pregunta de RR.HH. que puede analizarse.


## Slide 3: CASO

- FraSoHome en 60 segundos
Una empresa retail omnicanal que quiere convertir datos de personas en decisiones accionables.

FraSoHome es una cadena ficticia de muebles, decoración y equipamiento del hogar. Opera con tiendas físicas, e-commerce y centro logístico.

- 820
- registros de empleados en el dataset principal
- 669
- empleados activos en la fecha de corte
- 2026
- fecha de corte: 30/04
- Tiendas
- físicas
- E-commerce
- crecimiento online
- Logística
- presión en campañas
- Personas
- rotación y clima
Señales del negocio: crecimiento online, ampliación de horarios, campañas con presión logística y dudas sobre carrera interna.

El reto no es “contar bajas”; es entender patrones, priorizar acciones y comunicar con criterio humano.


## Slide 4: RETO


- El reto de Dirección de Personas
Preparar un diagnóstico ejecutivo sobre rotación, abandono y acciones de retención.

- 1
- ¿Dónde se concentra la rotación voluntaria?
- 2
- ¿Qué señales explican el riesgo de abandono?
- 3
- ¿Qué acciones debería priorizar RR.HH.?
- Dimensiones del diagnóstico
- Rotación
- histórica
- Riesgo
- actual
- Acción
RR.HH.

- Rotación
- tasas, bajas y headcount
- Abandono
- score y segmento de riesgo
- Voz del empleado
- comentarios de clima y salida
- Gobierno
- privacidad, sesgos y explicabilidad
Resultado esperado: un informe con evidencias, hipótesis y recomendaciones defendibles ante Comité de Dirección.


## Slide 5: OBJETIVOS


- Qué van a practicar los alumnos
Un recorrido completo: de texto y datos dispersos a un informe de People Analytics.

- 1
- Formular
- prompts
- ChatGPT
- 2
- Analizar
- texto
- Voz del empleado
- 3
- Construir
- informe
- Power BI
- 4
- Detectar
- patrones
- Rotación y riesgo
- 5
- Recomendar
- acciones
- Ética y negocio
La clave didáctica es comparar herramientas: ChatGPT ayuda a estructurar lenguaje e hipótesis; Power BI permite contrastarlas con datos.


## Slide 6: DATOS


- Datos disponibles para el caso
CSV sintéticos y anonimizados para trabajar texto, rotación y riesgo de abandono.

- Regla de privacidad
- Aunque los datos son sintéticos, se trabajarán como si fueran reales:
- • usar identificadores anonimizados
- • no pegar información sensible real
- • no tomar decisiones automáticas
- • documentar límites del análisis
- 6
- archivos CSV de trabajo
- 2
- informes principales en Power BI

## Slide 7: VARIABLES


- Variables clave: de la evidencia al indicador
El alumno debe distinguir entre pasado, señal de riesgo y acción recomendada.

- Histórico
- abandono voluntario 24m
- fecha salida
- tipo salida
- Score
- probabilidad abandono
- riesgo abandono
- alto riesgo flag
- Experiencia
- satisfacción
- engagement
- manager · carrera · reconocimiento
- Presión operativa
- carga trabajo
- horas extra
- absentismo
- Dato
- Pregunta
- Visual
- Insight
- Acción
Criterio: el score de abandono es una señal para priorizar conversaciones y análisis, no una sentencia sobre una persona.


## Slide 8: ACTIVIDAD A


- Pruebas en ChatGPT: comparar tipos de prompt
Antes de abrir Power BI, los alumnos trabajan la voz del empleado y la calidad de las instrucciones.

- +
- criterio
RR.HH.

- Motivos registrados en el dataset
- Falta de desarrollo
- 27
- Carga/estrés
- 23
- Oferta salarial
- 21
- Manager
- 21
- Reconocimiento
- 19
Objetivo: no delegar el diagnóstico, sino aprender a pedir, revisar y contrastar la salida de la IA.


## Slide 9: ACTIVIDAD A


- Cómo evaluar los prompts
El mejor prompt no es el más largo: es el que ayuda a generar evidencia útil y revisable.

- Claridad
- ¿Explica el contexto de FraSoHome y la tarea?
- Consistencia
- ¿Respeta categorías y formato?
- Trazabilidad
- ¿Distingue evidencia textual de interpretación?
- Utilidad
- ¿Genera hipótesis o acciones que se pueden analizar?
- Ética
- ¿Evita inventar, etiquetar personas o automatizar decisiones?
- Prompt base recomendado
Actúa como analista de People Analytics.

Contexto: FraSoHome detecta rotación voluntaria y dispone de comentarios de salida.

Tarea: clasifica motivos y propone acciones, sin inventar información.

Formato: tabla con motivo, evidencia, acción y confianza.

Entregable: tabla comparativa con prompt usado, salida obtenida, fortalezas, limitaciones y prompt elegido.


## Slide 10: ACTIVIDAD B

- Power BI Service: cargar CSV y crear informe
La parte de BI se trabaja desde el navegador y con modelos semánticos creados desde CSV.

- 1
- Workspace
- 2
- New item
- 3
- Semantic model
- 4
- CSV
- 5
- Vista previa
- 6
- Create report
- Recomendación de trabajo
• Crear dos informes: uno para rotación mensual y otro para riesgo de abandono.

• Verificar tipos de dato: fechas, números y porcentajes.

• Nombrar modelos de forma clara para evitar confusión en el workspace.

Consejo de aula: si Power BI no reconoce una fecha o decimal por configuración regional, continuar con los campos preagregados y comentar la incidencia como parte del aprendizaje.


## Slide 11: INFORME 1

- Análisis de rotación de personal
Objetivo: responder dónde y cuándo se concentran las salidas voluntarias.

- 135
- salidas voluntarias históricas en 24 meses
- 0,82%
- rotación voluntaria media mensual total
- 280
- registros mensuales por departamento
- Visuales recomendados
- Tarjetas KPI
- headcount, bajas y tasa
- Línea temporal
- tasa por mes
- Barras
- bajas por departamento
- Matriz
- departamento × mes
- Segmentadores
- periodo, departamento y área crítica
- Bajas voluntarias acumuladas por área
- Tienda física
- 61
- Atención cliente
- 21
- E-commerce
- 17
- Logística
- 14
- Compras
- 9
- Pregunta guía: ¿hay un patrón temporal o departamental que sugiera causas operativas, de liderazgo o de desarrollo?

## Slide 12: INFORME 2

- Detección de abandono: empleados activos con señales de riesgo
El informe debe priorizar revisión y conversación, no decisiones automáticas.

- Filtro de página obligatorio: estado_actual = Activo
- 669
- plantilla activa actual
- 143
- activos en alto riesgo
- 12
- talento clave en alto riesgo
- Distribución de riesgo en activos
- Bajo
- 190
- Medio
- 336
- Alto
- 106
- Crítico
- 37
- Visuales recomendados
- • Barras: alto_riesgo_flag por departamento
- • Dispersión: satisfacción × probabilidad de abandono
- • Tabla: employee_id, riesgo, talento clave y prioridad
- • Segmentadores: departamento, nivel, riesgo y talento clave
Mensaje de interpretación: el score ayuda a priorizar conversaciones de permanencia, revisión de carrera y apoyo al manager.


## Slide 13: FACTORES

- Factores explicativos: conectar causas cuantitativas y cualitativas
El objetivo es contrastar si los temas detectados por ChatGPT coinciden con patrones en Power BI.

- Promedios en activos
- Alto/Crítico
- Bajo/Medio
- Satisfacción
- 5.7
- 7.0
- Engagement
- 5.5
- 6.6
- Manager
- 3.1
- 3.6
- Carrera
- 2.7
- 3.2
- Reconocimiento
- 2.7
- 3.3
- Carga
- 3.9
- 3.3
- Lectura esperada
- 1
- Detectar diferencias
- 2
- Cruzar con comentarios
- 3
- Diseñar acciones
- Pregunta de debate: ¿qué haría RR.HH. primero si los datos cuantitativos y los comentarios no coinciden?

## Slide 14: NARRATIVA

- Narrativa del informe: presentación, nudo y desenlace
El dashboard debe contar una historia sencilla y accionable para Dirección.

- 1. Presentación
- indicadores globales
- 2. Nudo
- patrones y focos
- 3. Evidencia
- texto + datos
- 4. Desenlace
- plan de acción
- Páginas sugeridas
- Resumen ejecutivo
- 3-4 KPIs, 2 visuales y mensaje principal
- Rotación mensual
- meses y departamentos críticos
- Riesgo de abandono
- activos a priorizar con revisión humana
- Factores de riesgo
- satisfacción, carrera, manager, carga y salario
- Plan de acción
- acciones, responsables, prioridad e impacto
Regla de los 5 segundos: cada página debe permitir entender el mensaje principal sin descifrar demasiados elementos.


## Slide 15: ENTREGABLES

- Qué deben entregar los alumnos
El caso combina evidencia analítica, comparación de prompts y síntesis ejecutiva.

- 01
- Informe Power BI
Al menos dos páginas: Rotación mensual y Riesgo de abandono.

- 02
- Tabla de prompts
Tipo de prompt, objetivo, salida, hallazgos y limitaciones.

- 03
- Resumen ejecutivo
1 página con 3 insights y 3 recomendaciones de retención.

- 04
- Priorización
Colectivos o perfiles de riesgo sin exponer datos personales innecesarios.

- 05
- Nota ética
Límites del score, datos que no deben usarse y mitigación de sesgos.

Criterio transversal: cada conclusión debe estar conectada con evidencia cuantitativa, cualitativa o ambas.


## Slide 16: EVALUACIÓN

- Criterios de evaluación del caso
Una rúbrica sencilla para valorar diagnóstico, herramienta, recomendaciones y gobierno.

- Peso relativo
- Diagnóstico
- 25
- Power BI
- 25
- ChatGPT
- 20
- Recomendaciones
- 20
- Ética
- 10
- Qué se espera
- Diagnóstico
Identifica focos de rotación y no repite gráficos.

- Power BI
Visuales claros, filtros útiles y narrativa comprensible.

- ChatGPT
Compara prompts y contrasta limitaciones.

- Recomendaciones
Acciones conectadas con evidencia.

- Ética
Reconoce límites del score y sesgos.

La evaluación debe premiar el razonamiento: explicar por qué un visual, un prompt o una acción ayuda a tomar mejores decisiones.


## Slide 17: ÉTICA

- Ética y gobierno: el score no decide
La analítica de personas debe reforzar la confianza, no convertir empleados en etiquetas.

- Score de abandono = señal de priorización
No es una decisión automática, ni una predicción infalible, ni una etiqueta que deba comunicarse al empleado.

- Anonimización
- usar employee_id y evitar datos personales innecesarios
- Variables sensibles
- no usarlas para decisiones individuales
- Intervención humana
- priorizar conversaciones, no sanciones
- Trazabilidad
- documentar datos, filtros y recomendaciones
Cierre ético para el alumno: “Las decisiones finales dependen de profesionales de RR.HH. y managers formados”.


## Slide 18: GUÍA

- Secuencia de facilitación sugerida
Una ruta práctica para presentar el caso y acompañar el trabajo de los alumnos.

- 1
- 0–10’
- Presentar FraSoHome
- contexto, reto y materiales
- 2
- 45–60’
- Actividad A
- prompts y análisis cualitativo
- 3
- 30–45’
- Power BI Service
- carga CSV y primer informe
- 4
- 45’
- Rotación mensual
- tendencias y áreas críticas
- 5
- 45–60’
- Riesgo de abandono
- priorización y factores
- 6
- 30’
- Síntesis ejecutiva
- insights, acciones y ética
Frase de transición: “Ahora vamos a comprobar cómo una hipótesis de RR.HH. se convierte en prompt, visualización e insight accionable”.


## Slide 19: Manos a la obra

- Convertir datos de personas en decisiones responsables
- Prompt → evidencia textual → informe Power BI → recomendación → cautela ética

