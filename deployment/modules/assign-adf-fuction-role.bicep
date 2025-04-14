param dataFactoryName string
param functionAppPrincipalId string

@description('Built-in role definition ID for Data Factory Contributor')
var dataFactoryContributorRoleId = '673868aa-7521-48a0-acc6-0f60742d39f5'

resource dataFactory 'Microsoft.DataFactory/factories@2018-06-01' existing = {
  name: dataFactoryName
}

resource adfRoleAssignment 'Microsoft.Authorization/roleAssignments@2020-10-01-preview' = {
  name: guid(dataFactory.id, functionAppPrincipalId, dataFactoryContributorRoleId)
  scope: dataFactory
  properties: {
    principalId: functionAppPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', dataFactoryContributorRoleId)
    principalType: 'ServicePrincipal'
  }
}
