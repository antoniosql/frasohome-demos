# Caso FraSoHome — Laboratorios (Copilot Studio + RAG + Dataverse)

## Introducción del caso

**FraSoHome** es una cadena ficticia B2C de muebles y decoración con operación omnicanal (tiendas físicas, e-commerce y fidelización en CRM). En los últimos meses, la compañía sufre:

- **Fragmentación de la información** (CRM, POS, e-commerce, ERP) y dificultad para “unir” datos.
- **Problemas de calidad y consistencia** (duplicados, claves que no encajan, formatos heterogéneos, nulos y anomalías).
- **Dependencia del equipo de datos** para responder preguntas recurrentes y falta de consistencia en definiciones y procedimientos.

El objetivo del taller es construir un **asistente en Copilot Studio** con enfoque **híbrido**:

- **RAG (documentos)** para preguntas “documentales” (políticas, procedimientos, definiciones de KPI).
- **Tools / acciones (Dataverse)** para preguntas “métricas” (ventas, devoluciones, stock) que requieren cálculos o consulta a datos estructurados.
- **Respuesta con evidencia**: citaciones para lo documental y trazabilidad de la consulta para lo métrico.

> Nota: Estos laboratorios empiezan en **LAB 2** (LAB 1 se omite intencionalmente).

## Qué construirás al final

Un agente capaz de:

1. Responder preguntas internas con **citaciones** desde conocimiento controlado.
2. Consultar datos en Dataverse mediante **Tools** y devolver métricas con supuestos claros.
3. Integrar “métrica + definición/política” en respuestas mixtas.
4. Pasar una evaluación básica con test sets y aplicar controles mínimos de seguridad.

## Índice de laboratorios

- [LAB 2 — Base de conocimiento (RAG) en Copilot Studio](LAB2_Base_de_conocimiento_RAG_en_Copilot_Studio.md)  
  Carga de documentos vigentes, activación de citaciones y prueba controlada de conflicto de versiones.

- [LAB 3 — Prompting, citaciones y seguridad (control de versionado + prompt injection)](LAB3_Prompting_Citaciones_y_Control_de_Fallback.md)  
  Instrucciones del agente, prompt modification, formato, abstención y pruebas de seguridad.

- [LAB 4 — Dataverse: crear tablas e importar datos estructurados (CSV)](LAB4_Dataverse_y_Datos_Estructurados.md)  
  Creación de tablas y carga de CSV para ventas, devoluciones y stock.

- [LAB 5 — Arquitectura híbrida: Tools (Dataverse) + RAG (documentos)](LAB5_Arquitectura_Hibrida_Tools_y_RAG.md)  
  Añadir Tools de Dataverse (solo lectura), crear topic métrico y responder preguntas con datos + definiciones.

- [LAB 6 — Evaluación, seguridad y gobierno del asistente](LAB6_Evaluacion_Seguridad_y_Gobierno.md)  
  Ejecutar evaluaciones con test sets, diagnosticar fallos y aplicar acciones correctivas.

## Estructura recomendada (referencia)

Este repo de markdown asume que tienes disponible el pack del caso con estas carpetas:

- `Documentos_Knowledge_Clasificados/` (políticas, KPI, operaciones, catálogo, CRM, gobierno, tests)
- `Datos_Estructurados/` (CSV)
- `TestSets/` (CSV)

