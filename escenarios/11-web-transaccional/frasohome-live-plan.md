# FraSoHome Live — web transaccional con servicios gratuitos de Azure (plan operacional, 2026-10-17)

Documento completo: https://claude.ai/code/artifact/b3c9f4d6-80f4-4660-917f-879c39732e77

Alcance: solo la parte operacional. La carga en el BI de Fabric queda para una fase posterior. Se ejecuta fase a fase, con aprobación entre fases.

- Azure SQL y Cosmos DB son la única fuente de verdad. De los 64 CSV de `datos/`, 58 se guardan (27 SQL operados, 23 SQL semilla/referencia/meta, 8 Cosmos) y 6 los recalcula la exportación (fact_transacciones, comentarios de clima y salida, validaciones, coherencia, catálogo).
- `tools/export_csv.py` regenerará los 64 CSV con el mismo contrato que `datos/`.
- 16 escenarios en la web; autenticación propia (usuarios creados a mano, scrypt, sesión en SQL, /.auth/* de SWA bloqueado).
- Hosting: Static Web Apps Free + managed Functions Python 3.11.

## Estado

- Fase 0 (validada en Azure, 2026-10-19): `rg-frasohome-live`; SQL `frasohome-oltp` y SWA `swa-frasohome-live` en westeurope; Cosmos en swedencentral. Hallazgos: azure-functions 1.25 (2.x exige Python 3.13); mssql-python no admite `Connection Timeout`; SWA descarta Set-Cookie si el worker emite `domain=` vacío → Domain explícito; /.auth/me 200 con clientPrincipal null. Pendiente: medir cuota 24 h y dominio (CNAME en Cloudflare, proxy desactivado, configurar_dominio.ps1).
- Fase 1 (desplegada, 2026-10-24): `infra/` con main.bicep, alertas, presupuesto, identidad OIDC y workflows `frasohome-live-infra` y `frasohome-live-web`.
- Fase 2 (cargada en Azure, 2026-10-24): `sql/` y `seed/`. En Azure: SQL 108 s, Cosmos 297 s y 223.000 RU (~12 RU/documento); 58 de 58 ficheros cuadran. Rama `frasohome-live-fase0` (commit ade1b3e «web-fase2») en GitHub; main solo tiene la fase 0.
- Fase 3 (desplegada en Azure el 2026-10-31 con `configurar_api.ps1` y `desplegar_api.ps1`; 8/8 comprobaciones; la SWA seguía con la web de la fase 0 hasta entonces. Escrita el 2026-10-24): `api/` (143 endpoints (los dos últimos, `GET /admin/tiendas` y `GET /tpv/pedidos/{id}`, se añadieron en la fase 4; `/rrhh/departamentos` admite también a dirección), un enrutador propio dentro de una sola función HTTP, sesión scrypt + cookie con Domain, CSRF, rol y ámbito, Idempotency-Key en checkout/TPV/devoluciones, outbox a Cosmos), `sql/03_procedimientos.sql` (44 procedimientos), `tools/` (users.py, crear_usuario_api.py con usuario `fsh_api` SELECT+EXECUTE por esquema, configurar_api.ps1, desplegar_api.ps1, usuarios.ps1, comprobar_api.py), `app/` consola mínima (sustituida por la web en la fase 4). 30 pruebas pytest con fsh_api contra SQL Server y emulador; e2e con host Functions 3.11 + emulador SWA (11/11). Se aplica con `tools\configurar_api.ps1` y `tools\desplegar_api.ps1`. El workflow web apunta ya a app/ y api/.
- Fase 4 (los 16 escenarios publicados, 2026-10-31): `app/` con HTML, CSS y JS plano (módulos ES, sin htmx ni dependencias por la CSP `script-src 'self'`). Publicado: acceso, cambio de contraseña, menú por rol y los 16 escenarios (rama frasohome-live-fase4-escenarios-6-10; el 15 sin exportación ni reinicio, que son de la fase 5). Probado en Chrome contra Azure con 30 pasos (anónimo, cliente, almacén online, atención, cajero, admin y móvil).
- Fases 5–7: pendientes.
- Entrega: Claude escribe los ficheros en C:\repos\frasohome-demos (o los entrega en zip si el puente se cae) y Antonio hace commit y push (sin permiso de push para Claude; .github no se puede escribir desde el puente).
