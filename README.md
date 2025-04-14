# PSR SERVICE

## Intoduction
Processity Salesforce Replication Service (PSR Service) replicates Salesfoce objects into Delta tables in Azure Data Lake.

## Architecture
This architecture enables the replication of Salesforce data into Delta Lake tables stored in Azure Data Lake Storage Gen2 (ADLS Gen2) using Azure Data Factory (ADF) and Azure Function.

An actor makes a POST request the Azure Function at /api/replicateSalesforce with a JSON body: 
```
{
    "objectName": "<salesforce-object-name>"
}
```
The Azure function receives the object name and injects it as a dynamic parameter to create and trigger an Azure Data Factory (ADF) pipeline. 

ADF orchestrates the data movement and transformation in two major steps: \
a. Copy Activity \
Source: Salesforce Object (e.g., Account) accessed using the Salesforce OAuth 2.0 Client via a Linked Service. \
Sink: Writes raw data as Parquet files into ADLS Gen2, using a dataset defined for Parquet storage.

b. Mapping Data Flow \
Source: Parquet dataset stored in ADLS Gen2. \
Sink: Writes transformed data into a Delta Lake table in ADLS Gen2.

![](https://github.com/PS-07/psr-service/blob/main/PSR%20Service.jpg)


## Setup instructions
1. Create a Salesforce Connected App with OAuth 2.0
2. Create a parameters.json in the root directory with keys `location` (Azure region eg. eastasia), `salesforceUrl`, `salesforceOauthKey`, `salesforceOauthSecret` and values from the Salesforce Connected App
3. Run `make validate-bicep RESOURCE_GROUP=<azure-resource-group>` - Validate azure deployment
4. Run `make deploy-bicep RESOURCE_GROUP=<azure-resource-group>` - Deploy azure resources
5. Run `make deploy-function` - Deploy function app
6. Run the following curl by passing the `salesforce-object-name`
```
curl --location 'https://psrfunc.azurewebsites.net/api/replicateSalesforce?code=<code-from-function-app>' \
--header 'Content-Type: application/json' \
--data '{
    "objectName": "<salesforce-object-name>"
}'
```
7. Verify the pipeline run in Azure Data Factory and check the `temp/<salesforce-object-name>/delta` path in storage account for delta table.