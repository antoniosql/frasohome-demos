// FraSoHome Live · Fase 0
// Recursos mínimos en niveles gratuitos para comprobar que la arquitectura funciona:
//   - Azure SQL Database con la oferta gratuita (serverless, autopausa al agotar la cuota)
//   - Azure Cosmos DB for NoSQL con free tier (1.000 RU/s compartidas)
//   - Azure Static Web Apps, plan Free
// Estos mismos recursos se reutilizan en la fase 1, que añade alertas, contenedores y CI.

targetScope = 'resourceGroup'

@description('Región de SQL y Cosmos. La oferta gratuita de SQL la fija para todas las bases gratuitas de la suscripción: usa la de la futura capacidad Fabric.')
param dataLocation string

@description('Región de Cosmos DB. Por defecto la de los datos; otra si esa región no tiene capacidad de Cosmos para la suscripción.')
param cosmosLocation string = dataLocation

@description('Región de Static Web Apps (solo algunas regiones admiten el recurso).')
@allowed([ 'westeurope', 'westus2', 'centralus', 'eastus2', 'eastasia' ])
param webLocation string = 'westeurope'

@description('Login del administrador SQL. La función de prueba usa un usuario de base de datos aparte, de solo lectura.')
param sqlAdminLogin string = 'fsh_admin'

@secure()
@description('Contraseña del administrador SQL (la genera desplegar.ps1).')
param sqlAdminPassword string

@description('Object ID en Entra del usuario que despliega; queda como administrador Entra del servidor.')
param entraAdminObjectId string

@description('UPN o nombre del administrador Entra.')
param entraAdminLogin string

@description('Si ya existe una cuenta Cosmos con free tier en la suscripción, pon false (solo se admite una).')
param cosmosFreeTier bool = true

var suffix = uniqueString(resourceGroup().id)
var tags = {
  proyecto: 'frasohome-live'
  fase: '0'
}

resource sqlServer 'Microsoft.Sql/servers@2023-08-01-preview' = {
  name: 'sql-frasohome-${suffix}'
  location: dataLocation
  tags: tags
  identity: {
    type: 'SystemAssigned' // necesaria más adelante para el mirroring a Fabric
  }
  properties: {
    administratorLogin: sqlAdminLogin
    administratorLoginPassword: sqlAdminPassword
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
    administrators: {
      administratorType: 'ActiveDirectory'
      principalType: 'User'
      login: entraAdminLogin
      sid: entraAdminObjectId
      tenantId: subscription().tenantId
      azureADOnlyAuthentication: false // las managed Functions de SWA no tienen identidad administrada
    }
  }
}

// Permite conexiones desde servicios de Azure (las Functions de SWA no tienen IP fija).
resource sqlFirewallAzure 'Microsoft.Sql/servers/firewallRules@2023-08-01-preview' = {
  parent: sqlServer
  name: 'AllowAllWindowsAzureIps'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

resource sqlDb 'Microsoft.Sql/servers/databases@2023-08-01-preview' = {
  parent: sqlServer
  name: 'frasohome-oltp'
  location: dataLocation
  tags: tags
  sku: {
    name: 'GP_S_Gen5_2'
    tier: 'GeneralPurpose'
    family: 'Gen5'
    capacity: 2
  }
  properties: {
    useFreeLimit: true
    freeLimitExhaustionBehavior: 'AutoPause'
    autoPauseDelay: 60
    minCapacity: json('0.5')
    maxSizeBytes: 34359738368 // 32 GB, el límite gratuito
    requestedBackupStorageRedundancy: 'Local'
    zoneRedundant: false
  }
}

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2024-11-15' = {
  name: 'cosmos-frasohome-${suffix}'
  location: cosmosLocation
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    enableFreeTier: cosmosFreeTier
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: cosmosLocation
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    minimalTlsVersion: 'Tls12'
    disableLocalAuth: false // la API usa clave: las managed Functions no tienen identidad administrada
    publicNetworkAccess: 'Enabled'
  }
}

// Base compartida con todo el free tier: hasta 25 contenedores caben en las 1.000 RU/s.
resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-11-15' = {
  parent: cosmos
  name: 'frasohome'
  properties: {
    resource: {
      id: 'frasohome'
    }
    options: {
      throughput: 1000
    }
  }
}

resource cosmosFase0 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-11-15' = {
  parent: cosmosDb
  name: 'fase0'
  properties: {
    resource: {
      id: 'fase0'
      partitionKey: {
        paths: [ '/pk' ]
        kind: 'Hash'
      }
    }
  }
}

resource swa 'Microsoft.Web/staticSites@2023-12-01' = {
  name: 'swa-frasohome-live'
  location: webLocation
  tags: tags
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {
    stagingEnvironmentPolicy: 'Enabled'
    allowConfigFileUpdates: true
  }
}

// Las app settings (Cosmos y SQL) las pone desplegar.ps1: si estuvieran aquí, cada
// redespliegue de Bicep borraría la cadena de SQL que el script añade después.

output sqlServerName string = sqlServer.name
output sqlServerFqdn string = sqlServer.properties.fullyQualifiedDomainName
output sqlDatabaseId string = sqlDb.id
output cosmosAccountName string = cosmos.name
output swaName string = swa.name
output swaHostname string = swa.properties.defaultHostname
