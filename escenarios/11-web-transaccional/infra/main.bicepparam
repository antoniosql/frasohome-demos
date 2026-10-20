// Parámetros de main.bicep. Los datos personales (correo, administrador Entra) no se guardan
// en el repositorio, que es público: se leen de variables de entorno que ponen
// desplegar_infra.ps1 en local o el workflow de GitHub Actions desde sus secretos.
using 'main.bicep'

param sqlLocation = 'westeurope'
param cosmosLocation = 'swedencentral'
param webLocation = 'westeurope'
param sqlAdminLogin = 'fsh_admin'
param cosmosFreeTier = true

param entraAdminObjectId = readEnvironmentVariable('FSH_ENTRA_ADMIN_OBJECT_ID')
param entraAdminLogin = readEnvironmentVariable('FSH_ENTRA_ADMIN_LOGIN')
param alertEmail = readEnvironmentVariable('FSH_ALERT_EMAIL')
param sqlAdminPassword = readEnvironmentVariable('FSH_SQL_ADMIN_PASSWORD', '')
