# Módulo de 8 horas: Interpretabilidad de Modelos de ML aplicada a FraSoHome

## Enfoque general

Este módulo continúa de forma natural la sesión anterior de Analítica de Ventas aplicada a FraSoHome. En la sesión previa el alumnado trabajó el recorrido completo de un proyecto analítico: problema de negocio, mapa de datos, fact table, Customer 360, KPIs, diseño de target, features, modelos baseline, scoring, activación y medición.

Esta segunda sesión responde a la pregunta que quedó abierta:

> Si FraSoHome usa modelos para priorizar clientes, recomendar productos, anticipar churn o decidir incentivos, ¿cómo explicamos esas decisiones de forma clara, útil y responsable para negocio?

La interpretabilidad no se plantea aquí como una colección de librerías, sino como una competencia de proyecto. El objetivo es que el alumnado aprenda a elegir qué tipo de explicación necesita cada audiencia y cómo traducir resultados técnicos a decisiones comerciales comprensibles.

La sesión debe combinar:

- Teoría de interpretabilidad y explicabilidad.
- Motivaciones legales, éticas y de negocio.
- Técnicas globales y locales.
- Limitaciones de cada método.
- Ejemplos concretos sobre modelos de FraSoHome.
- Lecturas de negocio a partir de importancia de variables, PDP, ICE, modelos sustitutos, LIME, SHAP e InterpretML.

## Relación con las sesiones anteriores

En el módulo anterior, FraSoHome se usó para diseñar casos de analítica de ventas:

- Churn y reactivación.
- Propensión de compra por categoría.
- Cross-sell y recomendación.
- Riesgo de devolución.
- Promociones y ROI.
- Activación local con stock.

Ahora esos mismos casos se reinterpretan desde otra perspectiva:

- ¿Por qué el modelo asigna alto riesgo de churn a un cliente?
- ¿Qué variables explican la propensión a comprar textil o iluminación?
- ¿Qué señales hacen que una recomendación sea razonable?
- ¿El modelo está confundiendo sensibilidad al descuento con valor real?
- ¿Qué perfiles aparecen sistemáticamente como poco prioritarios?
- ¿Qué explicación necesita marketing para actuar?
- ¿Qué explicación necesita dirección para confiar?
- ¿Qué explicación sería defendible ante un cliente o un comité de gobierno?

La sesión debe dejar claro que interpretar un modelo no es solo generar un gráfico SHAP. Interpretar significa conectar la lógica del modelo con el negocio, el dato, la acción y la responsabilidad.

## Punto de partida del alumnado

Se asume que el alumnado ya conoce:

- Aprendizaje supervisado y no supervisado.
- Modelos de clasificación y regresión.
- Regresión logística, árboles, random forest, gradient boosting y redes neuronales.
- Métricas como AUC, precision, recall, MAE o RMSE.
- Conceptos de overfitting, train/test y validación.
- El ciclo básico de un proyecto ML.
- El caso FraSoHome y su contexto comercial.

Por tanto, el módulo debe evitar explicar algoritmos desde cero y debe concentrarse en:

- Qué significa explicar.
- Para quién explicamos.
- Qué nivel de explicación necesitamos.
- Qué método encaja con cada pregunta.
- Qué limitaciones tiene cada técnica.
- Cómo convertir una explicación técnica en una lectura accionable de negocio.

## Objetivos de aprendizaje

Al finalizar la sesión, el alumnado debería ser capaz de:

1. Distinguir interpretabilidad, explicabilidad, transparencia y confianza.
2. Diferenciar explicaciones globales, locales, por segmento y por instancia.
3. Identificar cuándo basta con un modelo interpretable y cuándo tiene sentido usar un modelo de caja negra con técnicas post-hoc.
4. Explicar la importancia de variables y sus limitaciones, especialmente con variables correlacionadas.
5. Interpretar PDP e ICE para entender relaciones entre features y predicción.
6. Usar modelos sustitutos globales para aproximar la lógica de una caja negra.
7. Entender LIME como explicación local aproximada.
8. Entender SHAP como atribución aditiva basada en valores de Shapley.
9. Traducir explicaciones de modelos a decisiones comerciales de FraSoHome.
10. Detectar explicaciones engañosas, inestables o poco accionables.
11. Diseñar una estrategia de interpretabilidad para un caso de negocio.
12. Comunicar resultados de interpretabilidad a audiencias no técnicas.

## Hilo narrativo recomendado

La narrativa de la sesión puede organizarse alrededor de una situación concreta:

> FraSoHome ha entrenado modelos de churn, propensión de compra por categoría y riesgo de devolución. Los modelos funcionan razonablemente bien en métricas técnicas, pero marketing, dirección comercial y cumplimiento piden entender por qué recomiendan ciertas acciones antes de desplegarlos a escala.

Desde ahí se plantean cuatro preguntas:

1. **Confianza:** ¿podemos confiar en el modelo?
2. **Comprensión:** ¿qué señales mueven sus predicciones?
3. **Acción:** ¿qué puede hacer negocio con esa explicación?
4. **Responsabilidad:** ¿hay riesgos legales, éticos o comerciales?

## Estructura de la sesión de 8 horas

### Hora 1. Por qué interpretar modelos: confianza, negocio, ética y regulación

**Objetivo:** establecer por qué la interpretabilidad importa más allá de la curiosidad técnica.

**Contenidos:**

- Qué significa interpretar un modelo.
- Diferencia entre:
  - Interpretabilidad.
  - Explicabilidad.
  - Transparencia.
  - Auditabilidad.
  - Confianza.
- Por qué un modelo con buen AUC puede no ser aceptado por negocio.
- Motivaciones legales:
  - Uso de datos personales.
  - Decisiones automatizadas.
  - Necesidad de información significativa sobre la lógica de decisión.
  - Derecho a intervención humana y posibilidad de impugnar decisiones en determinados contextos.
- Motivaciones éticas:
  - Sesgos.
  - Trato desigual.
  - Variables proxy.
  - Opacidad en decisiones que afectan a personas.
- Motivaciones de negocio:
  - Ganar confianza de usuarios internos.
  - Depurar modelos.
  - Mejorar feature engineering.
  - Detectar variables problemáticas.
  - Identificar necesidad de nuevos datos.
  - Convertir predicciones en acciones.

**Ejemplo FraSoHome:**

El modelo de churn prioriza clientes para una campaña de reactivación. Marketing pregunta:

- ¿Por qué estos clientes y no otros?
- ¿Estamos priorizando clientes rentables o solo clientes que compran con descuento?
- ¿Qué pasa con clientes sin historial online?
- ¿Podemos justificar por qué un cliente recibe incentivo y otro no?

**Actividad de aula:**

Presentar tres decisiones de FraSoHome y pedir al alumnado que identifique quién necesita la explicación y para qué:

- Dirección comercial aprueba presupuesto de campaña.
- Marketing define una audiencia de reactivación.
- Atención al cliente revisa clientes con alto riesgo de devolución.

**Mensaje clave:**

> Interpretar no es explicar el algoritmo por curiosidad; es hacer que una predicción pueda ser usada, cuestionada y mejorada.

### Hora 2. Marco conceptual: tipos, niveles y propiedades de las explicaciones

**Objetivo:** construir el vocabulario común de interpretabilidad.

**Contenidos:**

- Interpretabilidad intrínseca vs post-hoc.
- Modelos glassbox vs blackbox.
- Interpretabilidad global:
  - Cómo se comporta el modelo en conjunto.
  - Qué variables pesan más.
  - Qué relaciones generales aprende.
- Interpretabilidad local:
  - Por qué una instancia concreta recibe una predicción.
  - Qué variables empujan el score hacia arriba o hacia abajo.
- Interpretabilidad por grupo:
  - Explicar un segmento, audiencia o cluster.
  - Ejemplo: clientes dormidos de alto valor.
- Transparencia del algoritmo:
  - Cómo aprende el algoritmo.
  - Qué restricciones tiene.
- Interpretabilidad holística del modelo:
  - Cómo predice globalmente el modelo ya entrenado.
- Interpretabilidad modular:
  - Cómo afectan partes del modelo o subconjuntos de variables.

**Propiedades de las explicaciones:**

- Precisión.
- Fidelidad.
- Consistencia.
- Estabilidad.
- Comprensión.
- Certeza.
- Representatividad.
- Complejidad.
- Portabilidad.

**Ejemplo FraSoHome:**

Para un modelo de propensión a compra de textil:

- Explicación global: la recencia, visitas a categoría y compras previas de textil son las variables más influyentes.
- Explicación local: el cliente C014 tiene alto score porque visitó textil tres veces, compró decoración recientemente y responde a emails.
- Explicación por grupo: los clientes omnicanal con alta afinidad local muestran patrones distintos a los clientes puramente online.

**Actividad de aula:**

Clasificar varias preguntas según tipo de explicación:

- "¿Qué variables mueven el modelo de churn?"
- "¿Por qué este cliente recibe descuento?"
- "¿Por qué los clientes de tienda física tienen menor score?"
- "¿El modelo usa demasiado la variable descuento?"

**Mensaje clave:**

> Antes de elegir SHAP, LIME o PDP, hay que saber qué pregunta de explicación queremos responder.

### Hora 3. Modelos interpretables y técnicas tradicionales: utilidad y límites

**Objetivo:** revisar técnicas interpretables y métricas tradicionales como base, pero mostrar por qué no bastan.

**Contenidos:**

- Modelos intrínsecamente interpretables:
  - Regresión lineal.
  - Regresión logística.
  - Árboles de decisión.
  - Naive Bayes.
  - GAM / Explainable Boosting Machines.
- Criterios de interpretabilidad:
  - Linealidad.
  - Monotonicidad.
  - Interacciones.
  - Complejidad visual.
  - Número de variables.
- Técnicas tradicionales:
  - EDA.
  - Correlaciones.
  - PCA.
  - Matriz de confusión.
  - Accuracy, precision, recall, F1.
  - ROC/AUC.
  - MAE/RMSE en regresión.
- Límites de las métricas de rendimiento:
  - Miden error, no necesariamente comprensión.
  - No explican por qué se produce una predicción.
  - No garantizan justicia.
  - No garantizan transparencia.
  - No detectan siempre leakage o proxies.

**Ejemplo FraSoHome:**

Comparar dos modelos de churn:

- Regresión logística: algo menos precisa, pero fácil de explicar.
- Gradient boosting: mejor lift en top decile, pero requiere explicabilidad post-hoc.

Discusión:

- ¿Cuál conviene para una primera campaña?
- ¿Cuál conviene si el impacto económico es alto?
- ¿Cuál necesita más gobierno?

**Actividad de aula:**

Mostrar una matriz de decisión:

| Contexto | Modelo preferible | Razón |
| --- | --- | --- |
| Primer MVP comercial | Regresión logística / árbol | explicable y rápido |
| Alta precisión en ranking | Gradient boosting | mejor performance |
| Decisión sensible | Modelo interpretable o caja negra explicada | más trazabilidad |
| Comunicación a dirección | Modelo + explicación ejecutiva | confianza |

**Mensaje clave:**

> Un modelo interpretable no es siempre mejor, pero una explicación pobre puede bloquear el mejor modelo.

### Hora 4. Importancia de variables y diagnóstico global del modelo

**Objetivo:** aprender a interpretar qué variables influyen globalmente y qué errores de lectura evitar.

**Contenidos:**

- Qué es importancia de variables.
- Importancia propia del modelo:
  - Coeficientes en regresión.
  - Importancia Gini / split en árboles.
  - Ganancia en boosting.
- Permutation feature importance:
  - Permutar una variable.
  - Medir incremento de error.
  - Comparar importancia relativa.
- Diferencia entre:
  - Variable predictiva.
  - Variable causal.
  - Variable proxy.
  - Variable accionable.
- Limitaciones:
  - Correlación entre variables.
  - Variables con muchas categorías.
  - Importancia dependiente de la métrica.
  - Importancia global que oculta segmentos.
  - Importancia no equivale a causalidad.

**Ejemplo FraSoHome: churn**

Variables importantes del modelo:

- `days_since_last_purchase`.
- `purchase_frequency_12m`.
- `margin_net_12m`.
- `discount_share`.
- `email_click_rate`.
- `return_rate`.
- `preferred_channel_online`.

Lectura de negocio:

- Si la recencia domina, el modelo está capturando inactividad real.
- Si `discount_share` pesa mucho, quizá el modelo identifica clientes promocionales, no necesariamente clientes de valor.
- Si `return_rate` aparece alto, el abandono puede estar relacionado con mala experiencia.
- Si las variables digitales dominan, puede haber sesgo contra clientes de tienda física con poca trazabilidad online.

**Ejemplo FraSoHome: riesgo de devolución**

Variables importantes:

- Categoría.
- Descuento.
- Canal.
- Motivo histórico de devolución.
- Tiempo de entrega.
- Rating del producto.

Lectura de negocio:

- Si categoría y producto pesan más que cliente, la acción debe centrarse en contenido, calidad o proveedor.
- Si descuento pesa mucho, algunas promociones pueden estar provocando compras poco reflexivas.

**Actividad de aula:**

Dar un ranking de importancia de variables y pedir:

1. Interpretación técnica.
2. Interpretación comercial.
3. Riesgo de mala lectura.
4. Acción derivada.

**Mensaje clave:**

> La importancia de variables dice qué usa el modelo, pero no demuestra causalidad ni prescribe automáticamente qué debe hacer negocio.

### Hora 5. PDP, ICE y relaciones entre variables y predicción

**Objetivo:** pasar de "qué variable importa" a "cómo cambia la predicción cuando cambia una variable".

**Contenidos:**

- Partial Dependence Plot (PDP):
  - Efecto marginal medio de una variable sobre la predicción.
  - Relación lineal, monótona o no lineal.
  - Uso con una o dos variables.
- Individual Conditional Expectation (ICE):
  - Curvas por individuo.
  - Heterogeneidad que el PDP puede ocultar.
- Accumulated Local Effects (ALE), como alternativa cuando hay correlación.
- Cuándo usar cada técnica.
- Limitaciones:
  - PDP asume independencia.
  - Puede evaluar combinaciones irreales.
  - Media efectos y oculta extremos.
  - Difícil de interpretar con muchas interacciones.

**Ejemplo FraSoHome: churn**

PDP de `days_since_last_purchase`:

- El riesgo de churn aumenta lentamente hasta 90 días.
- A partir de 120 días sube de forma más intensa.
- A partir de 240 días se estabiliza porque el cliente ya está muy inactivo.

Lectura de negocio:

- La ventana óptima de reactivación puede estar entre 90 y 150 días.
- Contactar demasiado tarde reduce probabilidad de recuperación.
- Contactar demasiado pronto puede gastar presión comercial innecesaria.

**Ejemplo FraSoHome: descuento**

PDP de `discount_share` sobre propensión:

- La propensión sube en clientes con cierto historial promocional.
- Pero el margen esperado puede caer.

Lectura de negocio:

- No confundir "responde a descuento" con "cliente valioso".
- Combinar PDP con análisis de margen.

**Ejemplo FraSoHome: riesgo de devolución**

PDP de `discount_pct`:

- Descuentos altos pueden aumentar riesgo de devolución en ciertas categorías.

Lectura de negocio:

- Revisar promociones agresivas en categorías con incertidumbre de tamaño, color o material.

**Actividad de aula:**

Interpretar tres curvas PDP/ICE simuladas:

- Recencia vs churn.
- Descuento vs margen esperado.
- Visitas web vs propensión.

Para cada una:

- Qué patrón se observa.
- Qué hipótesis de negocio genera.
- Qué acción podría tomarse.
- Qué limitación tiene la interpretación.

**Mensaje clave:**

> PDP e ICE ayudan a pasar de "esta variable importa" a "así parece influir", pero siguen siendo herramientas de interpretación, no pruebas causales.

### Hora 6. Modelos sustitutos globales y explicaciones locales con LIME

**Objetivo:** entender cómo aproximar una caja negra globalmente o alrededor de una predicción individual.

**Contenidos:**

#### Modelos sustitutos globales

- Qué son:
  - Modelo interpretable entrenado para imitar las predicciones de una caja negra.
- Proceso:
  1. Seleccionar datos X.
  2. Obtener predicciones de la caja negra.
  3. Entrenar un modelo interpretable sobre X y predicciones.
  4. Medir fidelidad.
  5. Interpretar el sustituto.
- Modelos posibles:
  - Árbol de decisión.
  - Regresión lineal/logística.
  - Reglas.
- Ventajas:
  - Intuitivo.
  - Flexible.
  - Útil para explicar lógica general.
- Limitaciones:
  - Explica el modelo, no necesariamente la realidad.
  - Puede aproximar mal regiones concretas.
  - La fidelidad debe medirse.

#### LIME

- Local Interpretable Model-agnostic Explanations.
- Explica una predicción concreta.
- Genera perturbaciones alrededor del caso.
- Consulta la caja negra.
- Entrena un modelo simple local.
- Devuelve variables que empujan la predicción.
- Ventajas:
  - Agnóstico al modelo.
  - Útil para casos individuales.
  - Explicaciones cortas.
- Limitaciones:
  - Sensible a definición de cercanía.
  - Puede ser inestable.
  - Perturbaciones pueden generar casos irreales.
  - Necesita validar fidelidad local.

**Ejemplo FraSoHome: sustituto global**

Caja negra: gradient boosting de churn.

Sustituto: árbol de decisión de profundidad 3 que aproxima los scores.

Reglas aprendidas:

- Si recencia > 150 días y frecuencia < 2, churn alto.
- Si recencia > 90 días y no hay clicks recientes, churn medio.
- Si recencia baja y margen alto, churn bajo.

Lectura de negocio:

- El modelo está usando una lógica razonable basada en inactividad y engagement.
- Sirve para presentar una explicación ejecutiva.
- No reemplaza al modelo original si la fidelidad no es suficiente.

**Ejemplo FraSoHome: LIME local**

Cliente C023:

- Score churn: 0,82.
- Factores que suben score:
  - 170 días desde última compra.
  - No abre campañas desde hace 90 días.
  - Frecuencia baja reciente.
- Factores que bajan score:
  - Margen histórico alto.
  - Alta afinidad a decoración.

Lectura de negocio:

- No es un cliente perdido, sino dormido de valor.
- Acción recomendada: reactivación suave con categoría de afinidad, no descuento masivo.

**Actividad de aula:**

Dar tres perfiles de cliente y una explicación LIME simplificada. Pedir:

- Traducción a lenguaje de negocio.
- Acción comercial.
- Riesgo de interpretación.
- Qué información adicional pedirían.

**Mensaje clave:**

> Los sustitutos y LIME ayudan a explicar, pero siempre hay que preguntar si la aproximación es fiel y si la explicación es estable.

### Hora 7. SHAP, valores de Shapley e interpretabilidad accionable

**Objetivo:** comprender SHAP como técnica central para explicaciones globales y locales, y practicar su traducción a negocio.

**Contenidos:**

- Intuición de teoría de juegos:
  - Predicción como "premio".
  - Variables como "jugadores".
  - Contribución marginal promedio.
- Valor base:
  - Predicción media.
- Contribución de cada feature:
  - Empuja la predicción hacia arriba o hacia abajo.
- Propiedad aditiva:
  - Base value + contribuciones = predicción.
- Tipos de visualización:
  - SHAP summary plot.
  - Bar plot global.
  - Beeswarm.
  - Waterfall plot.
  - Force plot.
  - Dependence plot.
- Diferencia entre:
  - Importancia global SHAP.
  - Explicación local SHAP.
  - Interacciones SHAP.
- Ventajas:
  - Base teórica sólida.
  - Coherencia aditiva.
  - Explicaciones globales y locales.
  - Muy extendido.
- Limitaciones:
  - Coste computacional.
  - Complejidad de explicación.
  - Correlación entre variables.
  - Riesgo de lectura causal.
  - Puede abrumar a negocio si se presenta sin traducción.

**Ejemplo FraSoHome: churn local**

Cliente C041:

- Base churn: 0,32.
- Recencia elevada: +0,22.
- Baja frecuencia reciente: +0,13.
- Sin clicks recientes: +0,08.
- Margen alto: -0,05.
- Nivel fidelización oro: -0,04.
- Score final: 0,66.

Lectura técnica:

- Varias señales de inactividad suben el riesgo.
- Variables de valor y fidelización lo reducen parcialmente.

Lectura de negocio:

- Cliente de valor que se está enfriando.
- No necesita necesariamente un descuento profundo.
- Puede activarse con contenido relevante, categoría favorita o beneficio de fidelización.

**Ejemplo FraSoHome: propensión a textil**

Variables SHAP positivas:

- Visitas recientes a textil.
- Compras previas de decoración.
- Click en campaña de inspiración.
- Tienda cercana con stock.

Variables SHAP negativas:

- Compra reciente de textil.
- Alta presión comercial.

Lectura de negocio:

- Si ya compró textil hace pocos días, no conviene insistir.
- Si hay interés reciente y stock local, activar campaña de categoría.

**Ejemplo FraSoHome: riesgo de devolución**

Variables SHAP positivas:

- Categoría con alta devolución.
- Descuento alto.
- Historial de devoluciones.
- Producto con rating bajo.

Lectura de negocio:

- La acción puede ser mejorar contenido, no bloquear cliente.
- Marketing debe revisar promociones de productos con baja confianza.

**Actividad de aula:**

Traducir tres waterfalls SHAP a una recomendación de negocio:

1. Cliente con churn alto.
2. Cliente con propensión alta a iluminación.
3. Línea de pedido con riesgo de devolución.

Para cada una:

- Explicación técnica.
- Explicación ejecutiva.
- Acción.
- Precaución.

**Mensaje clave:**

> SHAP explica contribuciones a la predicción; negocio necesita convertir esas contribuciones en una historia útil y responsable.

### Hora 8. InterpretML, comunicación ejecutiva y estrategia de interpretabilidad FraSoHome

**Objetivo:** cerrar el módulo diseñando una estrategia completa de interpretabilidad para FraSoHome.

**Contenidos:**

- InterpretML:
  - Glassbox.
  - Blackbox.
  - Explainable Boosting Machine (EBM).
- EBM:
  - Modelo interpretable con rendimiento competitivo.
  - Relación con GAM.
  - Funciones por variable.
  - Interacciones controladas.
- Cuándo usar modelos glassbox:
  - Decisiones sensibles.
  - Necesidad alta de explicación.
  - MVP de negocio.
- Cuándo usar blackbox + post-hoc:
  - Mayor rendimiento necesario.
  - Ranking comercial con alto impacto.
  - Datos no lineales o muchas interacciones.
- Cómo comunicar interpretabilidad:
  - A data science.
  - A marketing.
  - A dirección.
  - A compliance.
  - A operaciones.
- Cómo construir una slide de explicación de modelo:
  - Qué predice.
  - Qué datos usa.
  - Qué variables pesan globalmente.
  - Qué patrones son razonables.
  - Qué casos individuales ilustran la lógica.
  - Qué límites tiene.
  - Qué acción se recomienda.
  - Qué control se mantiene.

**Estrategia FraSoHome recomendada:**

Para cada modelo:

#### Modelo de churn

- Explicación global:
  - Importancia de variables.
  - SHAP summary.
  - PDP de recencia.
- Explicación local:
  - SHAP waterfall para clientes prioritarios.
  - LIME como contraste opcional.
- Negocio:
  - Playbook de reactivación.
  - Explicaciones por segmento.

#### Modelo de propensión por categoría

- Explicación global:
  - Variables de intención, afinidad y canal.
  - PDP de visitas recientes.
- Explicación local:
  - SHAP por cliente-categoría.
- Negocio:
  - Por qué se recomienda una categoría.
  - Qué restricciones de stock/margen aplican.

#### Modelo de riesgo de devolución

- Explicación global:
  - Categoría, producto, descuento y canal.
  - PDP de descuento.
- Explicación local:
  - SHAP de línea de pedido.
- Negocio:
  - Mejorar contenido.
  - Revisar promociones.
  - Activar mensajes preventivos.

**Actividad final:**

Cada grupo diseña una "ficha de interpretabilidad" para un modelo FraSoHome:

- Modelo.
- Decisión que soporta.
- Audiencia de la explicación.
- Tipo de explicación necesaria.
- Técnicas elegidas.
- Visuales recomendados.
- Riesgos de mala interpretación.
- Traducción a negocio.
- Acción derivada.

**Mensaje clave:**

> La interpretabilidad no termina en un gráfico. Termina cuando una persona de negocio entiende qué puede hacer, qué no debe hacer y con qué nivel de confianza.

## Propuesta de secuencia minuto a minuto

| Bloque | Duración | Tema | Salida esperada |
| --- | ---: | --- | --- |
| 1 | 60 min | Motivaciones y confianza | mapa de audiencias y necesidades de explicación |
| 2 | 60 min | Tipos y niveles de interpretación | taxonomía global/local/grupo/instancia |
| 3 | 60 min | Modelos interpretables y métricas tradicionales | matriz rendimiento vs interpretabilidad |
| 4 | 60 min | Importancia de variables | lectura técnica y comercial de drivers |
| 5 | 60 min | PDP, ICE y relaciones | hipótesis de negocio a partir de curvas |
| 6 | 60 min | Sustitutos globales y LIME | explicación global aproximada y caso individual |
| 7 | 75 min | SHAP aplicado a FraSoHome | traducción de waterfalls y summary plots |
| 8 | 75 min | InterpretML y estrategia de comunicación | ficha de interpretabilidad por modelo |

## Casos FraSoHome para usar durante la sesión

### Caso 1. Interpretar churn para reactivación

**Pregunta de negocio:** ¿por qué este cliente está en alto riesgo y qué acción tiene sentido?

**Modelo:** clasificación binaria churn/no churn.

**Variables esperadas:**

- Recencia.
- Frecuencia.
- Margen neto.
- Canal preferido.
- Respuesta a campañas.
- Tasa de devolución.
- Engagement digital.
- Nivel de fidelización.

**Técnicas de interpretación:**

- Importancia de variables.
- PDP de recencia.
- SHAP summary.
- SHAP waterfall por cliente.
- Árbol sustituto global.

**Lectura de negocio esperada:**

- Churn no es solo ausencia de compra.
- Puede deberse a mala experiencia, falta de engagement o ciclo de compra largo.
- La acción debe variar según valor y causa probable.

### Caso 2. Interpretar propensión de compra por categoría

**Pregunta de negocio:** ¿por qué recomendamos textil, iluminación o decoración a un cliente concreto?

**Modelo:** clasificación/ranking por categoría.

**Variables esperadas:**

- Compras previas por categoría.
- Visitas web/app recientes.
- Clicks en campañas.
- Carritos.
- Stock disponible.
- Canal preferido.
- Estacionalidad.

**Técnicas de interpretación:**

- SHAP local cliente-categoría.
- PDP de visitas recientes.
- ICE por segmento.
- Importancia global.

**Lectura de negocio esperada:**

- La recomendación debe explicar intención y afinidad.
- Hay que cruzar con stock, margen y presión comercial.
- Una categoría probable no siempre es una categoría conveniente.

### Caso 3. Interpretar riesgo de devolución

**Pregunta de negocio:** ¿por qué esta venta tiene riesgo de devolución y cómo podemos prevenirlo?

**Modelo:** clasificación de devolución a nivel línea/pedido.

**Variables esperadas:**

- Categoría.
- Producto.
- Canal.
- Descuento.
- Historial de devoluciones.
- Rating/feedback.
- Tiempo de entrega.
- Motivos previos.

**Técnicas de interpretación:**

- Importancia global.
- PDP de descuento.
- SHAP waterfall.
- Análisis por segmentos de producto/canal.

**Lectura de negocio esperada:**

- La explicación no debe usarse para castigar al cliente.
- Debe orientar contenido, logística, recomendación y política promocional.

### Caso 4. Interpretar una recomendación cross-sell

**Pregunta de negocio:** ¿por qué este producto complementario aparece como siguiente mejor oferta?

**Modelo:** reglas de asociación o recomendador.

**Variables/señales esperadas:**

- Co-compra.
- Categoría.
- Afinidad del cliente.
- Stock.
- Margen.
- Riesgo de devolución.

**Técnicas de interpretación:**

- Reglas de asociación.
- Lift/confianza/soporte.
- Explicaciones de ranking.
- SHAP si se usa modelo de ranking supervisado.

**Lectura de negocio esperada:**

- Recomendación explicable: "clientes con esta cesta suelen comprar X".
- La regla debe filtrarse por stock y margen.
- No toda recomendación con alto lift es comercialmente adecuada.

## Visuales recomendados para la sesión

- Matriz global vs local / modelo vs post-hoc.
- Tabla de audiencias y necesidades de explicación.
- Matriz rendimiento vs interpretabilidad.
- Ranking de importancia de variables con lectura de negocio.
- PDP de recencia vs churn.
- PDP de descuento vs riesgo de devolución.
- ICE por segmento de canal.
- Árbol sustituto global de churn.
- LIME local de cliente dormido.
- SHAP waterfall para cliente individual.
- SHAP summary para modelo de propensión.
- Ficha de interpretabilidad por modelo.
- Playbook "explicación -> acción -> cautela".

## Dinámicas docentes sugeridas

### Dinámica 1. ¿Quién necesita la explicación?

Dar una predicción y pedir al alumnado que diseñe explicaciones para:

- Data scientist.
- Responsable de marketing.
- Director comercial.
- Compliance.
- Store manager.

La misma predicción requiere mensajes distintos.

### Dinámica 2. Técnica vs negocio

Mostrar una explicación técnica:

> `days_since_last_purchase` aporta +0,22 al score de churn.

Pedir tres traducciones:

- Técnica.
- Ejecutiva.
- Acción comercial.

Ejemplo esperado:

> El cliente lleva mucho más tiempo sin comprar que clientes similares. Conviene reactivarlo antes de que pase a inactividad profunda, priorizando una comunicación de bajo incentivo si conserva margen alto.

### Dinámica 3. Interpretación engañosa

Presentar un ranking de variables donde `discount_share` aparece como muy importante.

Preguntas:

- ¿El descuento causa compra?
- ¿Identifica clientes sensibles a promoción?
- ¿Puede estar capturando campañas anteriores?
- ¿Qué test haríamos antes de subir descuentos?

### Dinámica 4. Waterfall a playbook

Dar un waterfall SHAP simplificado y pedir:

- Diagnóstico.
- Acción.
- Guardrail.
- Métrica de seguimiento.

### Dinámica 5. El comité de despliegue

Simular un comité donde el equipo debe defender el despliegue del modelo de churn:

- Performance.
- Variables principales.
- Explicaciones por segmento.
- Riesgos.
- Plan de monitorización.
- Plan de intervención humana.

## Materiales y demos sugeridas

### Material base del módulo

- PDF `Interpretando Modelos de ML.pdf`.
- Markdown del módulo anterior:
  - `docencia/temario-analitica-ventas-8h.md`
  - `docencia/ebook-analitica-ventas-narrativa-extendida.md`
- Notebooks FraSoHome:
  - Notebook 5: features RFM, churn, basket y propensión.
  - Notebook 7: baseline modeling.
  - Notebook 8: scoring y exportación BI.

### Demos prácticas sugeridas

1. Entrenar un baseline de churn.
2. Calcular importancia de variables.
3. Generar PDP para recencia y descuento.
4. Entrenar un árbol sustituto de un modelo más complejo.
5. Generar explicación local con LIME para un cliente.
6. Generar SHAP summary y waterfall.
7. Traducir explicaciones a una ficha de negocio.

No es imprescindible ejecutar todas las demos en vivo. Para una sesión de 8 horas, conviene preparar outputs visuales y ejecutar solo 2-3 momentos clave para no convertir la sesión en un taller de librerías.

## Entregable docente recomendado

Aunque no sea una evaluación formal, conviene que el alumnado termine la sesión con una ficha de interpretabilidad de un modelo FraSoHome.

La ficha debería incluir:

- Nombre del modelo.
- Decisión que soporta.
- Audiencia de la explicación.
- Tipo de explicación necesaria.
- Variables principales.
- Visuales de interpretación.
- Lectura de negocio.
- Riesgos de mala interpretación.
- Acción recomendada.
- Métrica de seguimiento.
- Preguntas abiertas.

## Cierre del módulo

La conclusión de la sesión debe ser práctica:

> Un modelo interpretable no es el que produce más gráficos, sino el que permite que una persona entienda suficientemente la lógica de la predicción para actuar mejor, cuestionar cuando haga falta y asumir responsabilidad sobre la decisión.

En FraSoHome, la interpretabilidad debe ayudar a:

- Priorizar clientes sin destruir margen.
- Recomendar categorías con sentido.
- Reducir devoluciones sin penalizar injustamente.
- Detectar sesgos por canal o calidad de datos.
- Comunicar modelos a marketing y dirección.
- Diseñar acciones medibles y responsables.

La idea final para el alumnado:

> La interpretabilidad es el puente entre la precisión técnica y la confianza de negocio.
