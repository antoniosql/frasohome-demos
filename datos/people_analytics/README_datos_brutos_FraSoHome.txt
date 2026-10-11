FraSoHome - Datos brutos para demostración ETL de People Analytics
======================================================================

Contenido del paquete
---------------------
Este paquete contiene fuentes CSV sintéticas en bruto para transformar el caso FraSoHome desde datos de origen hasta un modelo analítico de People Analytics.
Los archivos finales anteriores del caso ya contenían información preparada y métricas recalculadas. Estos nuevos CSV están diseñados para enseñar los pasos de ETL: normalización, limpieza, deduplicación, integración, agregación y cálculo de métricas.

Archivos principales
--------------------
- raw_hris_empleados.csv: maestro de empleados tal como llegaría de HRIS.
- raw_movimientos_personal.csv: altas, bajas, promociones, movilidad y revisiones salariales.
- raw_evaluaciones_desempeno.csv: evaluaciones anuales y comentarios de manager.
- raw_encuesta_clima_respuestas.csv: encuesta de clima en formato largo por pregunta/dimensión.
- raw_absentismo.csv: episodios de absentismo.
- raw_horas_extra.csv: horas extra mensuales por empleado.
- raw_formacion.csv: acciones formativas y horas realizadas.
- raw_salarios_beneficios.csv: histórico salarial de 2025 y 2026.
- raw_exit_interviews.csv: entrevistas de salida y comentarios.
- dim_departamentos_mapeo.csv: tabla de homologación de departamentos.
- dim_calendario.csv: calendario diario para modelo de fechas.
- diccionario_fuentes_brutas.csv: diccionario y uso analítico de campos.
- plantilla_backlog_indicadores.csv: plantilla para dinámica de indicadores con alumnos.

Problemas de calidad intencionados
----------------------------------
- IDs con espacios, minúsculas o guiones.
- Departamentos y categorías con variantes textuales.
- Fechas en formatos mixtos.
- Números y porcentajes en formato texto, con coma decimal, símbolo euro o valores no válidos.
- Duplicados en HRIS, movimientos, clima, formación y horas extra.
- Registros inválidos o sin correspondencia con el maestro de empleados.
- Valores fuera de rango, negativos o pendientes.

Uso docente sugerido
--------------------
1. Mostrar primero el problema de negocio: rotación, riesgo de abandono y voz del empleado.
2. Pedir a los alumnos que propongan indicadores antes de abrir Power BI.
3. Cargar las fuentes en Power Query y explicar la granularidad de cada tabla.
4. Transformar fuentes en queries de staging y luego en dimensiones/facts.
5. Calcular indicadores y construir una narrativa: qué ocurrió, por qué pudo ocurrir y qué debería hacer RR.HH.

Fecha de corte del caso: 30/04/2026.
Datos sintéticos: no contienen información real de empleados.
