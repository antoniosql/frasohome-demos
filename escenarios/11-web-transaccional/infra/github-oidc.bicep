// FraSoHome Live · identidad de GitHub Actions sin secretos (OIDC).
// Crea una identidad administrada asignada por el usuario con una credencial federada que
// solo acepta tokens del entorno "frasohome-live" del repositorio, y le da Colaborador
// sobre este grupo de recursos. Así el workflow no guarda contraseñas ni tokens de Azure:
// también lee el token de despliegue de la Static Web App con esta identidad.
// Lo despliega el propietario de la suscripción (crear asignaciones de rol lo exige).

targetScope = 'resourceGroup'

@description('Repositorio de GitHub en formato propietario/nombre.')
param githubRepo string = 'antoniosql/frasohome-demos'

@description('Entorno de GitHub desde el que se despliega (admite reglas de aprobación).')
param githubEnvironment string = 'frasohome-live'

@description('Id numérico del propietario del repositorio (gh api users/<propietario> --jq .id).')
param githubOwnerId string = '11750421'

@description('Id numérico del repositorio (gh api repos/<propietario>/<nombre> --jq .id).')
param githubRepoId string = '1414212531'

param location string = resourceGroup().location

var contributorRoleId = 'b24988ac-6180-42a0-ab88-20f7382dd24c'

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-frasohome-live-github'
  location: location
  tags: {
    proyecto: 'frasohome-live'
  }
}

resource federated 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2023-01-31' = {
  parent: identity
  name: 'github-${githubEnvironment}'
  properties: {
    issuer: 'https://token.actions.githubusercontent.com'
    subject: 'repo:${githubRepo}:environment:${githubEnvironment}'
    audiences: [ 'api://AzureADTokenExchange' ]
  }
}

// GitHub emite ahora el subject con los ids inmutables del propietario y del repositorio
// (repo:propietario@id/nombre@id:...). Se acepta también, además del formato clásico.
// Las credenciales federadas de una misma identidad se crean una tras otra.
resource federatedIds 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2023-01-31' = {
  parent: identity
  name: 'github-${githubEnvironment}-ids'
  dependsOn: [ federated ]
  properties: {
    issuer: 'https://token.actions.githubusercontent.com'
    subject: 'repo:${split(githubRepo, '/')[0]}@${githubOwnerId}/${split(githubRepo, '/')[1]}@${githubRepoId}:environment:${githubEnvironment}'
    audiences: [ 'api://AzureADTokenExchange' ]
  }
}

resource contributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, identity.id, contributorRoleId)
  properties: {
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', contributorRoleId)
    description: 'GitHub Actions de FraSoHome Live: despliegue de infraestructura y de la web'
  }
}

output clientId string = identity.properties.clientId
output tenantId string = subscription().tenantId
output subscriptionId string = subscription().subscriptionId
