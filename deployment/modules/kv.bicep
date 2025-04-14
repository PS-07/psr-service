param keyVaultName string
param location string
@secure()
param salesforceOauthKey string
@secure()
param salesforceOauthSecret string
@secure()
param salesforceUrl string

resource keyVault 'Microsoft.KeyVault/vaults@2021-06-01-preview' = {
    name: keyVaultName
    location: location
    properties: {
        sku: {
            family: 'A'
            name: 'standard'
        }
        tenantId: subscription().tenantId
        accessPolicies: [] 
        enableRbacAuthorization: true
    }
}

resource sfOauthKey 'Microsoft.KeyVault/vaults/secrets@2021-10-01' = {
    parent: keyVault
    name: 'sf-oauth-key'
    properties: {
        value: salesforceOauthKey
    }
}

resource sfOauthSecret 'Microsoft.KeyVault/vaults/secrets@2021-10-01' = {
    parent: keyVault
    name: 'sf-oauth-secret'
    properties: {
        value: salesforceOauthSecret
    }
}

resource sfUrl 'Microsoft.KeyVault/vaults/secrets@2021-10-01' = {
    parent: keyVault
    name: 'sf-url'
    properties: {
        value: salesforceUrl
    }
}

output keyVaultUri string = keyVault.properties.vaultUri
