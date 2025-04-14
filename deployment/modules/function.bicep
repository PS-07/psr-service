param functionAppName string
param location string
param storageAccountName string
param appServicePlanName string

resource storageAccount 'Microsoft.Storage/storageAccounts@2021-04-01' = {
    name: storageAccountName
    location: location
    kind: 'StorageV2'
    sku: {
        name: 'Standard_LRS'
    }
    properties: {
        isHnsEnabled: false
    }
}

resource appServicePlan 'Microsoft.Web/serverfarms@2020-12-01' = {
    name: appServicePlanName
    location: location
    kind: 'linux' 
    sku: {
      name: 'Y1'
      tier: 'Dynamic'
    }
    properties: {
      reserved: true 
    }
}

var dependsOn = [
  storageAccount
  appServicePlan
]

resource functionApp 'Microsoft.Web/sites@2020-12-01' = {
    name: functionAppName
    location: location
    kind: 'functionapp,linux'
    identity: {
        type: 'SystemAssigned'
    }
    properties: {
        serverFarmId: appServicePlan.id
        siteConfig: {
            linuxFxVersion: 'Python|3.10'
            appSettings: [
                {
                    name: 'AzureWebJobsStorage'
                    value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
                }
                {
                    name: 'FUNCTIONS_EXTENSION_VERSION'
                    value: '~4'
                }
                {
                    name: 'FUNCTIONS_WORKER_RUNTIME'
                    value: 'python'
                }
                {
                    name: 'AZURE_SUBSCRIPTION_ID'
                    value: '732f53e7-1e6c-4721-83fe-545071992989'
                }
                {
                    name: 'AZURE_RESOURCE_GROUP'
                    value: 'rg2'
                }
                {
                    name: 'AZURE_DATA_FACTORY_NAME'
                    value: 'ps-adf2'
                }
                {
                    name: 'AZURE_KEY_VAULT_NAME'
                    value: 'ps-kv2'
                }
                {
                    name: 'AZURE_ADF_PIPELINE_NAME'
                    value: 'SalesforceToDeltaLake'
                }
                {
                    name: 'ADLSGEN2_KEY_NAME'
                    value: 'adlsgen2-key'
                }
            ]
        }
    }
    dependsOn: dependsOn
}

output functionAppId string = functionApp.id
output functionAppDefaultHostname string = functionApp.properties.defaultHostName
output functionAppPrincipalId string = functionApp.identity.principalId
