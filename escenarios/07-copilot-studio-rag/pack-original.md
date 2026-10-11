# FraSoHome — Pack de documentos, datos y laboratorios (versión guiada)

Este pack contiene todo lo necesario para ejecutar el caso **FraSoHome** en un taller de **RAG + Copilot Studio**:

- Documentos para RAG
- Datos estructurados de ejemplo (Dataverse)
- Guías de laboratorio paso a paso para alumnos

---

## 📦 Contenido del pack

Incluye:

- Plantillas (caso + canvas)
- Documentos de conocimiento clasificados
- CSVs para Dataverse
- Laboratorios (LAB2–LAB6 guiados)
- TestSets para evaluación

> ⚠️ Nota  
> LAB1 existe como material opcional de diseño, pero en esta versión guiada se comienza directamente en LAB2.

---

# 1️⃣ Estructura del pack

| Carpeta / Archivo | Qué contiene |
|------------------|--------------|
| `Plantillas/` | Caso y lienzos (canvas) para diseño del asistente |
| `Documentos_Knowledge/` | Documentos Word que actúan como base documental para RAG |
| `Documentos_Knowledge_Clasificados/` | Los mismos documentos ordenados por carpetas temáticas (recomendado para el taller) |
| `../../datos/rag_copilot_studio/knowledge_base/Indice_Documentos_Conocimiento.md` | Índice + reglas de uso (qué subir por lab, qué NO subir en producción) |
| `Datos_Estructurados/` | CSVs para cargar en Dataverse (ventas, devoluciones, stock, catálogo, clientes) |
| `Laboratorios/` | Guías paso a paso para alumnos (LAB2–LAB6) |
| `TestSets/` | CSVs para importar como test sets en la funcionalidad de Evaluation de Copilot Studio |

---

# 2️⃣ Ruta recomendada del taller (sin LAB1)

1. Leer el caso: [caso.md](caso.md)
2. (Opcional) Completar el RAG Canvas: plantillas/RAG_Canvas_FraSoHome_Plantilla_Blanco.md
3. Ejecutar los laboratorios GUIADOS en orden: LAB2 → LAB3 → LAB4 → LAB5 → LAB6
4. Usar `Documentos_Knowledge_Clasificados` para subir conocimiento de forma controlada:
- Vigente
- Obsoleta
- NO_PROD

5. Usar los CSV de `Datos_Estructurados` para construir el bloque de consultas métricas (híbrido) en Dataverse.

6. Importar `TestSets` para evaluación automatizada en el LAB6.

---

# 3️⃣ Notas importantes

- FraSoHome es un caso ficticio.
- Los datos son sintéticos y no contienen información real.
- `FS-KB-02` es un documento OBSOLETO a propósito (para practicar control de versiones).  
👉 Retíralo en un escenario de producción.
- `FS-KB-10` contiene texto simulado de *prompt injection* para pruebas de seguridad (NO usar en producción).  
👉 En el LAB3 se sube temporalmente y se retira al finalizar.
- Si usas herramientas (Tools) con conectores, revisa credenciales y permisos antes de publicar el agente.
