# App Streamlit · FraSoHome

App formativa para explorar KPI, calidad de datos, clientes (RFM y churn), productos, stock y cesta de FraSoHome.

## Ejecución

Desde la raíz del repositorio:

```bash
pip install -r escenarios/02-fabric-preparacion-datos/streamlit_app/requirements_streamlit.txt
streamlit run escenarios/02-fabric-preparacion-datos/streamlit_app/app_frasohome_streamlit.py
```

La app lee por defecto [`datos/retail_omnicanal/raw_csv`](../../../datos/retail_omnicanal/README.md); el directorio se puede cambiar desde la barra lateral. Si encuentra `output_scoring/churn_scoring.csv` (generado por el notebook 8) en la carpeta desde la que se lanza, muestra también el *scoring*.

[`Notebook_Streamlit_App_FraSoHome.ipynb`](Notebook_Streamlit_App_FraSoHome.ipynb) se conserva como artefacto docente que genera y explica la app.
