# LAB 2 — Base de conocimiento (RAG) en Copilot Studio

Objetivo: cargar documentos de conocimiento clasificados, activar respuestas generativas con citaciones y realizar pruebas controladas (incluyendo conflicto de versiones).

| Duración estimada | 60–75 min |
| --- | --- |
| Nivel | Intermedio (guiado paso a paso) |
| Entregables | 1) Agente creado/abierto en Copilot Studio. 2) 8 documentos VIGENTES cargados como Knowledge. 3) Pruebas con citaciones (capturas o registro). 4) Documento OBSOLETO cargado para prueba de versionado. |
| Prerrequisitos | Acceso a un entorno de Microsoft Copilot Studio con Dataverse habilitado. Pack FraSoHome descargado y descomprimido. |

## Archivos que vas a usar en este laboratorio

Ubicación en el pack: Documentos_Knowledge_Clasificados/

Carga primero SOLO los documentos VIGENTES (no cargues todavía el documento de inyección).

| Carpeta | Archivo (subir a Knowledge) | Para qué sirve |
| --- | --- | --- |
| 01_Politicas | FS-KB-01_Politica_Devoluciones_v1.3_Vigente.docx | Política vigente de devoluciones |
| 02_KPI_y_Datos | FS-KB-03_Diccionario_KPI_Reglas_Calculo_v1.0.docx | Definiciones y fórmulas KPI |
| 03_Operaciones | FS-KB-04_Manual_Tienda_Caja_y_Pagos_Mixtos_v2.1.docx | Operativa tienda (caja/pagos) |
| 03_Operaciones | FS-KB-05_Guia_Conciliacion_Pagos_Ecommerce_v1.4.docx | Conciliación pagos e-commerce |
| 04_Catalogo | FS-KB-06_Taxonomia_Catalogo_y_Reglas_SKU_v1.2.docx | Taxonomía y reglas SKU |
| 05_CRM | FS-KB-07_Guia_Fidelizacion_CRM_v1.1.docx | Programa fidelización |
| 06_Gobierno_y_Seguridad | FS-KB-08_Politica_Datos_y_Permisos_Asistente_v1.0.docx | Permisos y tratamiento de datos |
| 03_Operaciones | FS-KB-09_FAQ_Operaciones_y_Atencion_v1.0.docx | FAQ soporte y atención |

### Documento para prueba de versionado (cárgalo AL FINAL del lab)

- FS-KB-02_Politica_Devoluciones_v1.2_Obsoleta.docx (está en 01_Politicas).

- No cargues todavía: FS-KB-10_Documento_Prueba_Prompt_Injection_NO_PROD.docx (lo usarás en el LAB 3).

## Paso a paso

### Abrir Copilot Studio y entrar al entorno correcto

- Abre tu navegador e inicia sesión en Copilot Studio.

- En la parte superior (o selector de entorno), verifica que estás en el entorno del curso/taller (el mismo que usarás para Dataverse en el LAB 4).

- En el menú izquierdo, entra a Agents (Agentes).

### Crear el agente del caso (si ya lo tienes creado, sáltate a la siguiente sección)

- Selecciona Create / New agent (Crear / Nuevo agente).

- Nombre recomendado: FraSoHome – Asistente Operaciones y Datos.

- Idioma: Español.

- Descripción (copia y pega): 'Asistente interno para FraSoHome que responde preguntas sobre políticas, operaciones y definiciones KPI con citaciones, y posteriormente consultará Dataverse para métricas.'

- Pulsa Create / Crear. Espera a que se abra el agente.

### Subir los documentos VIGENTES como base de conocimiento (Knowledge)

- En el menú del agente, ve a la pestaña Knowledge (Conocimiento).

- Selecciona Add knowledge (Agregar conocimiento).

- Elige Upload files / Files (Subir archivos).

- Arrastra y suelta (o Browse) los 8 archivos VIGENTES listados en la tabla anterior.

- Verifica que quedan listados como documentos de conocimiento del agente.

### Comprobar que la base de conocimiento está lista

- Permanece en Knowledge y revisa que NO esté cargado todavía el archivo FS-KB-02 (Obsoleta) ni FS-KB-10 (Prompt injection).

- Si cargaste alguno por error: abre el menú de los tres puntos (…) del documento y elimina/quita el archivo del conocimiento.

### Realizar pruebas guiadas en el panel Test

- Pulsa Test (Probar) en la parte superior para abrir el panel de pruebas.

- Vas a hacer las preguntas exactamente como se indican más abajo.

- En cada respuesta, valida 2 cosas: (1) que la respuesta sea coherente con el documento, y (2) que incluya citaciones/fuentes al documento correcto (si tu canal/entorno las muestra).

- Registra el resultado en la tabla de control (más abajo).

### Añadir el documento OBSOLETO para simular conflicto de versiones (versionado)

- Vuelve a la pestaña Knowledge.

- Selecciona Add knowledge (Agregar conocimiento) > Upload files (Subir archivos).

- Sube: FS-KB-02_Politica_Devoluciones_v1.2_Obsoleta.docx

- Vuelve a Test y repite la(s) pregunta(s) marcadas como 'Prueba de conflicto'.

### Cierre del lab

- Si observas respuestas contradictorias, NO lo arregles aún: lo corregiremos en el LAB 3 con instrucciones y control de versionado.

- Guarda tu registro de pruebas (captura o notas) para el entregable.

## Preguntas de prueba (copia y pega en el panel Test)

Consejo: pega una pregunta, espera respuesta, valida citación, y pasa a la siguiente. Si la respuesta no cita o mezcla documentos, anótalo; lo resolverás en el LAB 3.

| Pregunta | Documento esperado | Qué validar |
| --- | --- | --- |
| ¿Cuál es el plazo de devolución para compras online? ¿Y para compras en tienda? | FS-KB-01 (Vigente) | Debe contestar con plazos/condiciones y citar la política vigente. |
| ¿Qué productos NO admiten devolución voluntaria? | FS-KB-01 (Vigente) | Debe listar excepciones (p. ej. a medida / outlet / etc.) y citar política. |
| ¿Cómo se reembolsa un pago mixto tarjeta + efectivo en una devolución en tienda? | FS-KB-04 (Manual tienda) | Debe explicar orden de devolución del pago y citar manual. |
| Define “ventas netas” y escribe la fórmula oficial. | FS-KB-03 (Diccionario KPI) | Debe incluir fórmula y citar diccionario KPI. |
| ¿Qué es “stock disponible” y qué NO incluye? | FS-KB-03 (Diccionario KPI) | Debe explicar componentes (en mano, reservado, bloqueado) y citar diccionario KPI. |
| ¿Cómo concilio pagos de e-commerce cuando hay devoluciones y cupones? | FS-KB-05 (Conciliación e-commerce) | Debe proponer pasos/controles y citar guía. |
| ¿Qué significa el prefijo de SKU “FSH-MUE-SOF” y cómo se clasifica un producto? | FS-KB-06 (Taxonomía catálogo) | Debe explicar taxonomía y citar documento. |
| ¿Qué beneficios tiene el nivel Oro del programa de fidelización y cómo se sube de nivel? | FS-KB-07 (Fidelización) | Debe explicar tiers/beneficios y citar guía. |
| PRUEBA DE CONFLICTO (después de subir FS-KB-02): ¿Cuántos días tengo para devolver un producto comprado en tienda? | FS-KB-01 vs FS-KB-02 | Si el agente responde con un plazo incorrecto o mezcla versiones, anótalo. Se corrige en LAB 3. |

## Checklist de entrega (marca cuando esté listo)

- ✅ Agente FraSoHome creado o disponible.

- ✅ 8 documentos VIGENTES cargados en Knowledge.

- ✅ Preguntas de prueba ejecutadas y registradas.

- ✅ Documento OBSOLETO (FS-KB-02) cargado y prueba de conflicto ejecutada (registrada).