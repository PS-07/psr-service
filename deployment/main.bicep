param location string
param prefix string = 'ps'
param functionAppName string = 'psrfunc'
param keyVaultName string = 'ps-kv2'
@secure()
param salesforceOauthKey string
@secure()
param salesforceOauthSecret string
@secure()
param salesforceUrl string

module dataFactory 'modules/datafactory.bicep' = {
    name: 'deployDataFactory'
    params: {
        dataFactoryName: '${prefix}-adf2'
        location: location
    }
}

module dataLake 'modules/adls.bicep' = {
    name: 'deployDataLake'
    params: {
        dataLakeName: '${prefix}adlsgen2storageaccount'
        location: location
    }
}

module functionApp 'modules/function.bicep' = {
    name: 'deployFunctionApp'
    params: {
        functionAppName: functionAppName
        location: location
        storageAccountName: '${prefix}funcsa'
        appServicePlanName: '${prefix}-plan'
    }
}

module keyVault 'modules/kv.bicep' = {
    name: 'deployKeyVault'
    params: {
        keyVaultName: keyVaultName
        location: location
        salesforceOauthKey: salesforceOauthKey 
        salesforceOauthSecret: salesforceOauthSecret 
        salesforceUrl: salesforceUrl
    }
}

module assignAdfKeyVaultRole 'modules/assign-adf-kv-role.bicep' = {
    name: 'assignAdfKeyVaultRole'
    params: {
      keyVaultName: keyVaultName
      adfObjectId: dataFactory.outputs.adfObjectId
      functionAppObjectId: functionApp.outputs.functionAppPrincipalId
    }
}

module assignAdfFunctionRole 'modules/assign-adf-fuction-role.bicep' = {
    name: 'assignAdfFunctionRole'
    params: {
        dataFactoryName: '${prefix}-adf2'
        functionAppPrincipalId: functionApp.outputs.functionAppPrincipalId
    }
}

module storeAdlsKeyInKv 'modules/store-adls-key-kv.bicep' = {
    name: 'storeAdlsKeyInKv'
    params: {
        storageAccountName: '${prefix}adlsgen2storageaccount'
        keyVaultName: keyVaultName
    }
    dependsOn: [
        dataLake
        keyVault
        assignAdfKeyVaultRole
    ]
}

// Outputs from the deployment
output dataFactoryName string = dataFactory.outputs.dataFactoryId
output dataLakeName string = dataLake.outputs.dataLakeId
output functionAppName string = functionApp.outputs.functionAppId
output functionAppHostname string = functionApp.outputs.functionAppDefaultHostname
output keyVaultUri string = keyVault.outputs.keyVaultUri
output adlsKeyVaultSecretId string = storeAdlsKeyInKv.outputs.adlsKeyVaultSecretId
