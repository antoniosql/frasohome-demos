// FraSoHome Live · presupuesto mensual del grupo de recursos.
// Avisa por correo si el gasto real o el previsto del mes supera el importe (1 por defecto,
// en la moneda de facturación de la suscripción). Las notificaciones de presupuesto son gratis.
// Se despliega una sola vez: la fecha de inicio de un presupuesto no se cambia después.

targetScope = 'resourceGroup'

@description('Importe mensual en la moneda de facturación.')
param amount int = 1

@description('Correo que recibe los avisos.')
param alertEmail string

@description('Primer día del mes de inicio (formato AAAA-MM-01).')
param startDate string = utcNow('yyyy-MM-01')

resource budget 'Microsoft.Consumption/budgets@2023-11-01' = {
  name: 'presupuesto-frasohome-live'
  properties: {
    category: 'Cost'
    amount: amount
    timeGrain: 'Monthly'
    timePeriod: {
      startDate: startDate
    }
    notifications: {
      gastoReal: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 100
        thresholdType: 'Actual'
        contactEmails: [ alertEmail ]
        locale: 'es-es'
      }
      gastoPrevisto: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 100
        thresholdType: 'Forecasted'
        contactEmails: [ alertEmail ]
        locale: 'es-es'
      }
    }
  }
}
