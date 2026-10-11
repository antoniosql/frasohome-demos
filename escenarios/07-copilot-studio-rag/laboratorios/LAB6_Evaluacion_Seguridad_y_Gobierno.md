# LAB 6 — Evaluación, seguridad y gobierno del asistente

Objetivo: ejecutar una evaluación automatizada (test sets), revisar trazas con Activity Map y dejar el agente preparado para un ciclo de mejora/gobierno (con control de documentos, versiones y conexiones).

| Duración estimada | 60–90 min |
| --- | --- |
| Entregables | 1) 2 evaluaciones ejecutadas (documental y métrica). 2) Lista de fallos y acciones correctivas. 3) Checklist de gobierno (qué documentos quedan, qué se retira para producción). |
| Prerrequisitos | LAB 2–5 completados. Tools Dataverse configurados y topics guardados. |

## Archivos que vas a usar

Ubicación en el pack: TestSets/

- FS_TestSet_Documental.csv (preguntas documentales + respuestas esperadas)

- FS_TestSet_Metrico_Mixto.csv (preguntas métricas + expectativas de uso de tools)

## Paso a paso

### 1) Prueba manual rápida con Activity Map (diagnóstico)

- En Copilot Studio, abre tu agente.

- Pulsa Test (Probar) para abrir el panel de pruebas.

- En el menú de los tres puntos (…) del panel Test, activa: Show activity map when testing (Mostrar mapa de actividad al probar).

- (Opcional) Activa también Track between topics (Rastrear entre temas) para ver el salto entre topics.

- Haz una pregunta documental y una métrica (ejemplos abajo) y observa el plan: qué topic se dispara, qué tool se llama y qué fuentes usa.

#### Preguntas para esta prueba rápida:

- ¿Cuál es el plazo de devolución para compras online?

- Dame las ventas netas online entre 2026-02-01 y 2026-02-15

### 2) Crear la evaluación 1 (documental) importando un test set

- Ve a la pestaña Evaluation (Evaluación) del agente.

- Selecciona New evaluation (Nueva evaluación).

- Elige Import test cases from a file (Importar casos desde archivo).

- Arrastra el archivo FS_TestSet_Documental.csv a la zona de carga (o Browse para seleccionarlo).

- Asigna un nombre al test set, por ejemplo: 'FS_Documental_v1'.

- Selecciona los métodos de evaluación (recomendado): Keyword match + Text similarity.

- Verifica que cada test case tiene su Expected response (se importa desde la columna 'Expected response').

- Guarda el test set y ejecuta la evaluación (Run / Ejecutar).

### 3) Revisar resultados de la evaluación documental

- Abre los resultados y revisa el estado (Pass/Fail) por pregunta.

- En las preguntas fallidas, abre el detalle y revisa:

- Transcript: qué contestó el agente.

- Resources used: qué documento citó/usó.

- Activity map: qué plan siguió (si se fue a un topic incorrecto, o no citó).

- Anota 2–3 cambios concretos para mejorar (por ejemplo: ajustar triggers, mejorar instrucciones, limitar Knowledge en un nodo, etc.).

### 4) Crear la evaluación 2 (métrica/híbrida) importando el segundo test set

- En Evaluation, crea otra evaluación: New evaluation.

- Importa FS_TestSet_Metrico_Mixto.csv.

- Nombre sugerido: 'FS_MetricoMixto_v1'.

- Selecciona métodos de evaluación (recomendado):

- Keyword match (para validar que menciona periodo/canal/NetSalesEUR/etc.)

- Capability use (para exigir que use las Tools Dataverse en preguntas métricas).

- En 'Capability use', marca como capacidades esperadas los tools que creaste (por ejemplo DV_ListSalesSummary y DV_ListReturns).

- Ejecuta la evaluación.

### 5) Interpretar resultados y cerrar 'lista de acciones'

Completa esta mini-matriz de cierre (ejemplo):

| Fallo observado | Dónde se ve | Causa probable | Acción correctiva |
| --- | --- | --- | --- |
| No cita fuentes en documental | Evaluación documental / Transcript | Instrucciones insuficientes o nodo generativo sin prompt modification | Añadir prompt modification / reforzar instrucciones |
| Usa política obsoleta (FS-KB-02) | Pregunta conflicto | Falta regla de versionado o demasiadas fuentes | Instrucciones: priorizar VIGENTE; retirar obsoleta en prod |
| No llama a Tool en pregunta métrica | Evaluación métrica / Capability use fail | Topic no se dispara o tool mal descrita | Mejorar triggers + descripción del tool; revisar variables obligatorias |

### 6) Checklist de gobierno (antes de pensar en producción)

- ✅ Documentos en Knowledge: solo VIGENTES (retirar FS-KB-02 y FS-KB-10 antes de producción).

- ✅ Seguridad: instrucciones del agente incluyen rechazo a prompt injection y no exfiltración de datos (ver FS-KB-08).

- ✅ Conexiones/Tools: revisa credenciales y permisos. Evita exponer conexiones innecesarias.

- ✅ Versionado: define un proceso simple (quién actualiza, cómo se retira obsoleto, cómo se comunica).

- ✅ Evaluación continua: conserva los test sets como regresión y ejecútalos tras cada cambio relevante.