# 11 · Web transaccional (FraSoHome Live)

Web en `frasohome.dataging.com` para operar FraSoHome sobre Azure SQL y Cosmos DB en niveles gratuitos de Azure. La verdad vive en las bases y un script la exporta a los mismos CSV de [`datos/`](../../datos/README.md) para el resto de escenarios.

Se construye por fases:

| Fase | Contenido | Estado |
| --- | --- | --- |
| [0 · Comprobaciones](fase0/README.md) | Función de prueba, infraestructura mínima y scripts de verificación | Lista para ejecutar en Azure |
| 1 · Infraestructura como código | Bicep completo, alertas de cuota y presupuesto, GitHub Actions | Pendiente |
| 2 · Modelo y carga inicial | DDL, carga de los CSV en SQL y Cosmos, verificación | Pendiente |
| 3 · API y autenticación | Usuarios y contraseñas propios, transacciones | Pendiente |
| 4 · Web | 16 escenarios | Pendiente |
| 5 · Exportación a CSV | Mismo formato que `datos/` | Pendiente |
| 6 · Tráfico, dominio y operación | Generador de tráfico, guía | Pendiente |
| 7 · Documentación | Guiones de demo | Pendiente |
