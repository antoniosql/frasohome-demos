# 11 · Web transaccional (FraSoHome Live)

Web en `frasohome.dataging.com` para operar FraSoHome sobre Azure SQL y Cosmos DB en niveles gratuitos de Azure. La verdad vive en las bases y un script la exporta a los mismos CSV de [`datos/`](../../datos/README.md) para el resto de escenarios.

Se construye por fases:

| Fase | Contenido | Estado |
| --- | --- | --- |
| [0 · Comprobaciones](fase0/README.md) | Función de prueba, infraestructura mínima y scripts de verificación | Validada en Azure (falta el dominio) |
| [1 · Infraestructura como código](infra/README.md) | Bicep completo, alertas de cuota y presupuesto, GitHub Actions | Desplegada en Azure |
| [2 · Modelo y carga inicial](seed/README.md) | DDL, carga de los CSV en SQL y Cosmos, verificación | Cargada en Azure |
| [3 · API y autenticación](api/README.md) | Usuarios y contraseñas propios, transacciones, 143 endpoints | Desplegada en Azure |
| [4 · Web](web.md) | 16 escenarios | Publicada en Azure |
| 5 · Exportación a CSV | Mismo formato que `datos/` | Pendiente |
| 6 · Tráfico, dominio y operación | Generador de tráfico, guía | Pendiente |
| 7 · Documentación | Guiones de demo | Pendiente |
