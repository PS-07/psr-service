param keyVaultName string
param adfObjectId string
param functionAppObjectId string

@description('Built-in role definition ID for Key Vault Secrets User')
var keyVaultSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'

resource keyVault 'Microsoft.KeyVault/vaults@2021-06-01-preview' existing = {
  name: keyVaultName
}

resource adfRoleAssignment 'Microsoft.Authorization/roleAssignments@2020-10-01-preview' = {
  name: guid(keyVault.id, adfObjectId, keyVaultSecretsUserRoleId)
  scope: keyVault
  properties: {
    principalId: adfObjectId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalType: 'ServicePrincipal'
  }
}

resource functionRoleAssignment 'Microsoft.Authorization/roleAssignments@2020-10-01-preview' = {
  name: guid(keyVault.id, functionAppObjectId, keyVaultSecretsUserRoleId)
  scope: keyVault
  properties: {
    principalId: functionAppObjectId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalType: 'ServicePrincipal'
  }
}
