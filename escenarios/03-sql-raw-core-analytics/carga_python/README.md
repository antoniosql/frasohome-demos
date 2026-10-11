# Carga con Python

Utilidades para cargar los CSV de retail en Azure SQL con pandas y pyodbc.

| Fichero | Uso |
| --- | --- |
| [`run-sql.py`](run-sql.py) | Ejecuta un script `.sql` por lotes (`python run-sql.py --file <ruta.sql>`) |
| [`carga-csv.py`](carga-csv.py) | Carga los once CSV de `CSV_FOLDER` en el esquema `schema`, aplicando conversiones mínimas por tabla |
| [`csvee.py`](csvee.py) · [`csvee.ipynb`](csvee.ipynb) | Utilidades exploratorias del material original |
| `.env.example` | Variables que necesitan los scripts (servidor, base, usuario, contraseña, carpeta y esquema) |

Los scripts leen la configuración de variables de entorno. No guardes credenciales en el repositorio: define las variables en tu sesión o en un `.env` local (está en `.gitignore`).

Datos fuente: [`datos/retail_omnicanal/raw_csv`](../../../datos/retail_omnicanal/README.md). Pasos completos en la [ficha del escenario 03](../README.md#opción-c--carga-desde-python).
