param dataLakeName string
param location string

resource dataLake 'Microsoft.Storage/storageAccounts@2021-04-01' = {
    name: dataLakeName
    location: location
    kind: 'StorageV2'
    sku: {
        name: 'Standard_LRS'
    }
    properties: {
        isHnsEnabled: true
    }
}

output dataLakeId string = dataLake.id
