// FraSoHome Live · infraestructura (fase 1)
// Adopta los recursos creados en la fase 0 (mismos nombres) y añade:
//   - los 9 contenedores de Cosmos DB de la aplicación (clave de partición /pk)
//   - un grupo de acciones por correo y dos alertas de métrica:
//       * cuota gratuita de Azure SQL por debajo del 20 % (la base se pausaría hasta fin de mes)
//       * consumo normalizado de RU en Cosmos DB por encima del 90 % (riesgo de errores 429)
// Las alertas entran en las 10 series de métricas gratuitas al mes de Azure Monitor.
// El presupuesto va aparte (presupuesto.bicep) y la identidad de GitHub Actions también
// (github-oidc.bicep): crear asignaciones de rol exige ser propietario, y el workflow no lo es.

targetScope = 'resourceGroup'

@description('Región de Azure SQL. La oferta gratuita ya la fijó en West Europe para la suscripción.')
param sqlLocation string = 'westeurope'

@description('Región de Cosmos DB. West Europe no tenía capacidad para la suscripción en la fase 0.')
param cosmosLocation string = 'swedencentral'

@description('Región de Static Web Apps.')
@allowed([ 'westeurope', 'westus2', 'centralus', 'eastus2', 'eastasia' ])
param webLocation string = 'westeurope'

@description('Login del administrador SQL (no se puede cambiar una vez creado el servidor).')
param sqlAdminLogin string = 'fsh_admin'

@secure()
@description('Contraseña del administrador SQL. Solo hace falta al crear el servidor; vacía conserva la actual.')
param sqlAdminPassword string = ''

@description('Object ID en Entra del administrador del servidor SQL.')
param entraAdminObjectId string

@description('UPN del administrador Entra del servidor SQL.')
param entraAdminLogin string

@description('Free tier de Cosmos DB. No se puede cambiar después de crear la cuenta.')
param cosmosFreeTier bool = true

@description('Correo que recibe las alertas.')
param alertEmail string

@description('Segundos de vCore restantes por debajo de los cuales avisa (20 % de 100.000).')
param sqlFreeRemainingThreshold int = 20000

@description('Porcentaje de RU normalizadas por encima del cual avisa.')
param cosmosRuThresholdPct int = 90

var suffix = uniqueString(resourceGroup().id)
var tags = {
  proyecto: 'frasohome-live'
}

// Contenedores de la aplicación. pk = sesión, campaña, cliente o empleado según el contenedor.
var cosmosContainers = [
  'eventos_web'          // pk: session_id
  'eventos_campana'      // pk: campaign_id
  'senales_identidad'    // pk: customer_id_raw o SIN_CLIENTE
  'feedback'             // pk: customer_id
  'atencion_cliente'     // pk: customer_id
  'creatividades'        // pk: campaign_id
  'encuesta_clima'       // pk: employee_id
  'entrevistas_salida'   // pk: employee_id
  'carritos'             // pk: customer_id (un carrito vivo por cliente)
]

// ---------- Azure SQL ----------

resource sqlServer 'Microsoft.Sql/servers@2023-08-01-preview' = {
  name: 'sql-frasohome-${suffix}'
  location: sqlLocation
  tags: tags
  identity: {
    type: 'SystemAssigned' // necesaria para el mirroring futuro a Fabric
  }
  properties: {
    administratorLogin: sqlAdminLogin
    administratorLoginPassword: empty(sqlAdminPassword) ? null : sqlAdminPassword
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
  location: sqlLocation
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

// ---------- Cosmos DB ----------

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

// Sin TTL: los borrados por caducidad no se replicarían en el mirroring futuro a Fabric.
resource containers 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-11-15' = [for name in cosmosContainers: {
  parent: cosmosDb
  name: name
  properties: {
    resource: {
      id: name
      partitionKey: {
        paths: [ '/pk' ]
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [ { path: '/*' } ]
        excludedPaths: [ { path: '/"_etag"/?' } ]
      }
    }
  }
}]

// ---------- Static Web Apps ----------

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
// Las app settings (cadenas de conexión) no van aquí: un redespliegue de Bicep las borraría.

// ---------- Alertas ----------

resource actionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = {
  name: 'ag-frasohome-live'
  location: 'global'
  tags: tags
  properties: {
    groupShortName: 'frasohome'
    enabled: true
    emailReceivers: [
      {
        name: 'responsable'
        emailAddress: alertEmail
        useCommonAlertSchema: true
      }
    ]
  }
}

resource alertSqlQuota 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: 'alerta-sql-cuota-gratuita'
  location: 'global'
  tags: tags
  properties: {
    description: 'Quedan menos del 20 % de los segundos de vCore gratuitos del mes. Al agotarse, la base se pausa hasta el mes siguiente.'
    severity: 2
    enabled: true
    scopes: [ sqlDb.id ]
    evaluationFrequency: 'PT1H'
    windowSize: 'PT1H'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          criterionType: 'StaticThresholdCriterion'
          name: 'cuota-restante'
          metricNamespace: 'Microsoft.Sql/servers/databases'
          metricName: 'free_amount_remaining'
          operator: 'LessThan'
          threshold: sqlFreeRemainingThreshold
          timeAggregation: 'Minimum'
        }
      ]
    }
    autoMitigate: true
    actions: [ { actionGroupId: actionGroup.id } ]
  }
}

resource alertCosmosRu 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: 'alerta-cosmos-ru'
  location: 'global'
  tags: tags
  properties: {
    description: 'Cosmos DB usa más del 90 % de las 1.000 RU/s gratuitas: pueden aparecer errores 429.'
    severity: 3
    enabled: true
    scopes: [ cosmos.id ]
    evaluationFrequency: 'PT15M'
    windowSize: 'PT15M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          criterionType: 'StaticThresholdCriterion'
          name: 'ru-normalizadas'
          metricNamespace: 'Microsoft.DocumentDB/databaseAccounts'
          metricName: 'NormalizedRUConsumption'
          operator: 'GreaterThan'
          threshold: cosmosRuThresholdPct
          timeAggregation: 'Maximum'
        }
      ]
    }
    autoMitigate: true
    actions: [ { actionGroupId: actionGroup.id } ]
  }
}

output sqlServerName string = sqlServer.name
output sqlServerFqdn string = sqlServer.properties.fullyQualifiedDomainName
output sqlDatabaseId string = sqlDb.id
output sqlServerPrincipalId string = sqlServer.identity.principalId
output cosmosAccountName string = cosmos.name
output cosmosEndpoint string = cosmos.properties.documentEndpoint
output cosmosContainers array = cosmosContainers
output swaName string = swa.name
output swaHostname string = swa.properties.defaultHostname
