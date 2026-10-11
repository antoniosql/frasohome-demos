# Origen del material

Este repositorio reúne y reorganiza dos fuentes:

| Fuente | Qué aportó |
| --- | --- |
| Carpeta de materiales FraSoHome (repositorio documental con caso, datos, demos, docencia y presentaciones) | Narrativa, casos de uso, todos los dominios de datos, demos de Fabric, Fabric IQ, Copilot Studio, Power BI, analítica de ventas, interpretabilidad GenAI, agentes Foundry, scripts SQL, temarios y ebooks |
| [antoniosql/frasohome](https://github.com/antoniosql/frasohome) | Notebooks 09–18 de marketing de precisión con sus *helpers* y salidas de ejemplo, la app Streamlit de marketing de precisión y el ejemplo de *Data Quality Report* |

Los datos de retail y marketing eran idénticos en ambas fuentes; se conserva una sola copia en [`datos/`](datos/README.md).

## Qué no se ha incluido

- Paquetes `.zip` históricos (su contenido ya está descomprimido aquí) y la copia comprimida de los CSV de retail.
- Entornos virtuales de Python, configuraciones locales, estado de despliegues y ficheros con credenciales o cadenas de conexión.
- El artefacto de modelos que generan los alumnos (`alumnos_sales_models_artifact.joblib`), que se recrea al resolver el ejercicio.

## Cambios respecto al material original

**Estructura.** `00_caso` pasa a `historia/` y a cada escenario; `01_datos` a `datos/`; `02_demos` y `scripts` a `escenarios/NN-*`; `03_docencia` a `docencia/` (las guías y rúbricas de Copilot Studio viven ahora en su escenario); `04_presentaciones` a `presentaciones/`.

**Rutas en el código.** Notebooks, módulos Python, scripts PowerShell, manifiestos y plantillas SQL apuntan a la nueva estructura (`datos/…`, `escenarios/…`, `.local/…`). Los notebooks y apps de marketing de precisión localizan los datos del repositorio en lugar de la antigua carpeta `FraSoHome_case`.

**Correcciones para que las demos se ejecuten de principio a fin** (notebooks del escenario 02):

| Notebook | Cambio |
| --- | --- |
| 1–5 | `DATA_DIR` apunta a `datos/retail_omnicanal/raw_csv`; las salidas se escriben junto a los notebooks |
| 2 y 4 | Eliminado `infer_datetime_format`, que ya no existe en pandas 3 |
| 4 | Columnas ausentes tratadas de forma segura, variable sombreada en una comprensión de lista y DataFrames de salida creados con el índice correcto (antes los canales y tipos de movimiento quedaban vacíos) |
| 5 | Usa la *fact* de referencia si la del notebook 4 no tiene su esquema, filtra la ventana operativa 2024–2025 (las fechas de 2030–2031 generaban *snapshots* absurdos) y el RFM tolera clientes sin recencia |
| 6 | La etiqueta de propensión se usa como objetivo y las demás etiquetas se excluyen como variables (fuga de información) |
| 7 | Columnas repetidas y métricas no numéricas ya no rompen la evaluación |
| 8 | El *scoring* alinea las columnas con las del modelo entrenado y es compatible con pandas 3 |

La app Streamlit del escenario 02 usa `width="stretch"` en lugar del parámetro retirado `use_container_width`.

**Verificación.** Los notebooks de los escenarios 02, 04 (01), 05 y 09, y las dos apps Streamlit, se han ejecutado de principio a fin sobre esta estructura. Los notebooks del escenario 02 se han probado con pandas 2.3 y 3.0. El notebook de interpretabilidad del escenario 04 necesita `lime`, que no se pudo instalar en el entorno de prueba.

**Nuevo material.** La historia en siete capítulos, las fichas de los diez escenarios, el catálogo de datos (CSV y Excel), la matriz de recursos por escenario, los tres diagramas draw.io y el sitio MkDocs.
