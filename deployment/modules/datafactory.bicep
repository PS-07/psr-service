param dataFactoryName string
param location string

resource dataFactory 'Microsoft.DataFactory/factories@2018-06-01' = {
    name: dataFactoryName
    location: location
    identity: {
        type: 'SystemAssigned'
    }
}

output dataFactoryId string = dataFactory.id
output adfObjectId string = dataFactory.identity.principalId
