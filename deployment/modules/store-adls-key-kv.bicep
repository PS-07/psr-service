param storageAccountName string
param keyVaultName string

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

resource keyVault 'Microsoft.KeyVault/vaults@2021-06-01-preview' existing = {
  name: keyVaultName
}

resource adlsKeySecret 'Microsoft.KeyVault/vaults/secrets@2021-10-01' = {
  parent: keyVault
  name: 'adlsgen2-key'
  properties: {
    value: storageAccount.listKeys().keys[0].value
  }
}

output adlsKeyVaultSecretId string = adlsKeySecret.id
