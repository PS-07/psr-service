import azure.functions as func
import os
import json
import time
import logging
from azure.identity import DefaultAzureCredential
from azure.mgmt.datafactory import DataFactoryManagementClient
from azure.mgmt.datafactory.models import *
from azure.storage.filedatalake import DataLakeServiceClient
from azure.keyvault.secrets import SecretClient

def get_env_var(key: str) -> str:
    """Retrieves an environment variable or raises an error if not found."""
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(json.dumps({
            "component": "Environment",
            "message": f"Missing environment variable: {key}",
            "status_code": 500
        }))
    return value

def create_or_update_linked_service(adf_client: DataFactoryManagementClient, resource_group: str, factory_name: str, ls_name: str, ls_properties: dict):
    try:
        response = adf_client.linked_services.create_or_update(resource_group, factory_name, ls_name, ls_properties)
        logging.info(f"Linked service '{ls_name}' created/updated. Response: {response.as_dict()}")
        return response
    except Exception as e:
        error = {
            "component": "LinkedService",
            "message": f"Error creating/updating linked service '{ls_name}'",
            "status_code": 500,
            "details": str(e)
        }
        logging.error(json.dumps(error))
        raise RuntimeError(json.dumps(error))

def create_or_update_dataset(adf_client: DataFactoryManagementClient, resource_group: str, factory_name: str, ds_name: str, ds_properties: dict):
    try:
        response = adf_client.datasets.create_or_update(resource_group, factory_name, ds_name, ds_properties)
        logging.info(f"Dataset '{ds_name}' created/updated. Response: {response.as_dict()}")
        return response
    except Exception as e:
        error = {
            "component": "Dataset",
            "message": f"Error creating/updating dataset '{ds_name}'",
            "status_code": 500,
            "details": str(e)
        }
        logging.error(json.dumps(error))
        raise RuntimeError(json.dumps(error))

def create_or_update_dataflow(adf_client: DataFactoryManagementClient, resource_group: str, factory_name: str, df_name: str, df_properties: dict):
    try:
        response = adf_client.data_flows.create_or_update(resource_group, factory_name, df_name, df_properties)
        logging.info(f"Data flow '{df_name}' created/updated. Response: {response.as_dict()}")
        return response
    except Exception as e:
        error = {
            "component": "DataFlow",
            "message": f"Error creating/updating data flow '{df_name}'",
            "status_code": 500,
            "details": str(e)
        }
        logging.error(json.dumps(error))
        raise RuntimeError(json.dumps(error))

def create_or_update_pipeline(adf_client: DataFactoryManagementClient, resource_group: str, factory_name: str, pipeline_name: str, pipeline_properties: dict):
    try:
        response = adf_client.pipelines.create_or_update(resource_group, factory_name, pipeline_name, pipeline_properties)
        logging.info(f"Pipeline '{pipeline_name}' created/updated. Response: {response.as_dict()}")
        return response
    except Exception as e:
        error = {
            "component": "Pipeline",
            "message": f"Error creating/updating pipeline '{pipeline_name}'",
            "status_code": 500,
            "details": str(e)
        }
        logging.error(json.dumps(error))
        raise RuntimeError(json.dumps(error))

def create_adls_container_directory(account_url: str, account_key: str, container_name: str, directory_name: str):
    try:
        adlsgen2_client = DataLakeServiceClient(account_url, credential=account_key)
        file_system_client = adlsgen2_client.get_file_system_client(file_system=container_name)

        if not file_system_client.exists():
            file_system_client = adlsgen2_client.create_file_system(file_system=container_name)
            logging.info(f"Container '{container_name}' created.")
        else:
            logging.info(f"Container '{container_name}' already exists.")

        directory_client = file_system_client.get_directory_client(directory_name)

        if not directory_client.exists():
            directory_client.create_directory()
            logging.info(f"Directory '{directory_name}' created in '{container_name}'.")
        else:
            logging.info(f"Directory '{directory_name}' already exists in '{container_name}'.")
    except Exception as e:
        error = {
            "component": "ADLS",
            "message": f"Error creating ADLS container/directory '{container_name}/{directory_name}'",
            "status_code": 500,
            "details": str(e)
        }
        logging.error(json.dumps(error))
        raise RuntimeError(json.dumps(error))


def monitor_pipeline_run(adf_client: DataFactoryManagementClient, resource_group: str, factory_name: str, run_id: str):
    """Monitors the status of an ADF pipeline run and throws an error with details if it fails."""
    while True:
        pipeline_run = adf_client.pipeline_runs.get(resource_group_name=resource_group, factory_name=factory_name, run_id=run_id)
        logging.info(f"Pipeline Run Status: {pipeline_run.status}")
        if pipeline_run.status == "Succeeded":
            return pipeline_run.status
        elif pipeline_run.status in ["Failed", "Cancelled"]:
            error_info = {
                "pipelineRunId": run_id,
                "pipelineName": pipeline_run.pipeline_name,
                "status": pipeline_run.status,
                "startTime": str(pipeline_run.run_start),
                "endTime": str(pipeline_run.run_end),
                "durationInMs": pipeline_run.duration_in_ms,
                "errorMessage": pipeline_run.message,
            }
            logging.error(f"ADF Pipeline Run Failed: {json.dumps(error_info, indent=2)}")
            raise RuntimeError(json.dumps(error_info))
        time.sleep(5)

def run(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        object_name = req_body.get("objectName")
        if not object_name:
            return func.HttpResponse("Missing 'objectName' in request body", status_code=400)

        subscription_id = get_env_var("AZURE_SUBSCRIPTION_ID")
        resource_group = get_env_var("AZURE_RESOURCE_GROUP")
        factory_name = get_env_var("AZURE_DATA_FACTORY_NAME")
        kv_name = get_env_var("AZURE_KEY_VAULT_NAME")
        pipeline_name = get_env_var("AZURE_ADF_PIPELINE_NAME")
        adlsgen2_key_name = get_env_var("ADLSGEN2_KEY_NAME")
        kv_url = f"https://{kv_name}.vault.azure.net/"

        credential = DefaultAzureCredential()
        adf_client = DataFactoryManagementClient(credential, subscription_id)
        kv_client = SecretClient(kv_url, credential)

        adlsgen2_key = kv_client.get_secret(adlsgen2_key_name).value
        print(f"Successfully retrieved secret: {adlsgen2_key_name}")

        azure_kv_linked_service_name = "ps-akv2"
        azure_kv_linked_service_properties = {
            "name": azure_kv_linked_service_name,
            "type": "Microsoft.DataFactory/factories/linkedservices",
            "properties": {
                "annotations": [],
                "type": "AzureKeyVault",
                "typeProperties": {
                    "baseUrl": kv_url
                }
            }
        }
        create_or_update_linked_service(adf_client, resource_group, factory_name, azure_kv_linked_service_name, azure_kv_linked_service_properties)

        salesforcev2_linked_service_name = 'sfv2_lks2'
        salesforcev2_linked_service_properties = {
            "name": salesforcev2_linked_service_name,
            "properties": {
                "type": "SalesforceV2",
                "typeProperties": {
                    "environmentUrl": {"type": "AzureKeyVaultSecret", "secretName": "sf-url", "store": {"referenceName": azure_kv_linked_service_name, "type": "LinkedServiceReference"}},
                    "authenticationType": "OAuth2ClientCredentials",
                    "clientId": {"type": "AzureKeyVaultSecret", "secretName": "sf-oauth-key", "store": {"referenceName": azure_kv_linked_service_name, "type": "LinkedServiceReference"}},
                    "clientSecret": {"type": "AzureKeyVaultSecret", "secretName": "sf-oauth-secret", "store":{"referenceName": azure_kv_linked_service_name, "type": "LinkedServiceReference"}},
                    "apiVersion": "54.0"
                }
            }
        }
        create_or_update_linked_service(adf_client, resource_group, factory_name, salesforcev2_linked_service_name, salesforcev2_linked_service_properties)

        adlsgen2_linked_service_name = "adlsgen2_lks2"
        adlsgen2_account_name = "psadlsgen2storageaccount"
        adlsgen2_linked_service_properties = {
            "name": adlsgen2_linked_service_name,
            "type": "Microsoft.DataFactory/factories/linkedservices",
            "properties": {
                "annotations": [],
                "type": "AzureBlobFS",
                "typeProperties": {
                    "url": f"https://{adlsgen2_account_name}.dfs.core.windows.net/",
                    "accountKey": {"type": "SecureString", "value": adlsgen2_key}
                }
            }
        }
        create_or_update_linked_service(adf_client, resource_group, factory_name, adlsgen2_linked_service_name, adlsgen2_linked_service_properties)

        container_name = "test"
        directory_name = "pqt"
        create_adls_container_directory(f"https://{adlsgen2_account_name}.dfs.core.windows.net/", adlsgen2_key, container_name, directory_name)

        salesforce_dataset_name = f"sf_dataset_{object_name}"
        salesforce_dataset_properties = {
            "name": salesforce_dataset_name,
            "properties": {
                "linkedServiceName": {"referenceName": salesforcev2_linked_service_name, "type": "LinkedServiceReference"},
                "annotations": [],
                "type": "SalesforceV2Object",
                "schema": [],
                "typeProperties": {"objectApiName": f"{object_name}"}
            },
            "type": "Microsoft.DataFactory/factories/datasets"
        }
        create_or_update_dataset(adf_client, resource_group, factory_name, salesforce_dataset_name, salesforce_dataset_properties)

        intermediate_parquet_dataset_name = f"parquet_dataset_{object_name}"
        intermediate_parquet_dataset_properties = {
            "name": intermediate_parquet_dataset_name,
            "properties": {
                "linkedServiceName": {"referenceName": adlsgen2_linked_service_name, "type": "LinkedServiceReference"},
                "annotations": [],
                "type": "Parquet",
                "schema": [],
                "typeProperties": {
                    "location": {"type": "AzureBlobFSLocation", "folderPath": directory_name, "fileSystem": container_name},
                    "compressionCodec": "snappy"
                }
            },
            "type": "Microsoft.DataFactory/factories/datasets"
        }
        create_or_update_dataset(adf_client, resource_group, factory_name, intermediate_parquet_dataset_name, intermediate_parquet_dataset_properties)

        pqt_to_delta_dataflow_name = "pqt_to_delta"
        delta_directory = f"{object_name}/delta"
        pqt_to_delta_dataflow_properties = {
            "name": pqt_to_delta_dataflow_name,
            "properties": {
                "type": "MappingDataFlow",
                "typeProperties": {
                    "sources": [{"dataset": {"referenceName": intermediate_parquet_dataset_name, "type": "DatasetReference"}, "name": "source1"}],
                    "sinks": [{"linkedService": {"referenceName": adlsgen2_linked_service_name, "type": "LinkedServiceReference"}, "name": "sink1"}],
                    "transformations": [],
                    "scriptLines": [
                        "source(allowSchemaDrift: true,",
                        "          validateSchema: false,",
                        "          ignoreNoFilesFound: false,",
                        "          format: 'parquet') ~> source1",
                        "source1 sink(allowSchemaDrift: true,",
                        "          validateSchema: false,",
                        "          format: 'delta',",
                        "          fileSystem: 'test',",
                        f"          folderPath: '{delta_directory}',",
                        "          mergeSchema: false,",
                        "          autoCompact: false,",
                        "          optimizedWrite: false,",
                        "          vacuum: 0,",
                        "          deletable: false,",
                        "          insertable: true,",
                        "          updateable: false,",
                        "          upsertable: false,",
                        "          umask: 0022,",
                        "          preCommands: [],",
                        "          postCommands: [],",
                        "          skipDuplicateMapInputs: true,",
                        "          skipDuplicateMapOutputs: true) ~> sink1"
                    ]
                }
            }
        }
        create_or_update_dataflow(adf_client, resource_group, factory_name, pqt_to_delta_dataflow_name, pqt_to_delta_dataflow_properties)

        copy_activity = {
            "name": "CopySalesforceToParquet",
            "type": "Copy",
            "dependsOn": [],
            "policy": {"timeout": "0.12:00:00", "retry": 0, "retryIntervalInSeconds": 30, "secureOutput": False, "secureInput": False},
            "typeProperties": {
                "source": {"type": "SalesforceV2Source", "includeDeletedObjects": False},
                "sink": {"type": "ParquetSink", "storeSettings": {"type": "AzureBlobFSWriteSettings"}, "formatSettings": {"type": "ParquetWriteSettings"}},
                "enableStaging": False
            },
            "inputs": [{"referenceName": salesforce_dataset_name, "type": "DatasetReference"}],
            "outputs": [{"referenceName": intermediate_parquet_dataset_name, "type": "DatasetReference"}]
        }

        mapping_activity = {
            "name": "pqt_to_delta",
            "type": "ExecuteDataFlow",
            "dependsOn": [{"activity": "CopySalesforceToParquet", "dependencyConditions": ["Succeeded"]}],
            "policy": {"timeout": "0.12:00:00", "retry": 0, "retryIntervalInSeconds": 30, "secureOutput": False, "secureInput": False},
            "typeProperties": {
                "dataflow": {"referenceName": pqt_to_delta_dataflow_name, "type": "DataFlowReference"},
                "compute": {"coreCount": 8, "computeType": "General"},
                "traceLevel": "Fine"
            }
        }

        pipeline_payload = {"properties": {"activities": [copy_activity, mapping_activity], "annotations": []}}
        create_or_update_pipeline(adf_client, resource_group, factory_name, pipeline_name, pipeline_payload)

        run_response = adf_client.pipelines.create_run(resource_group, factory_name, pipeline_name)
        logging.info(f"Pipeline run initiated with ID: {run_response.run_id}")
        
        try:
            pipeline_status = monitor_pipeline_run(adf_client, resource_group, factory_name, run_response.run_id)
            return func.HttpResponse(f"ADF components created and pipeline run completed with status: {pipeline_status}", status_code=200)
        except RuntimeError as e:
            return func.HttpResponse(
                e.args[0], 
                status_code=500,
                mimetype="application/json"
            )

        except Exception as e:
            logging.exception("Unexpected error occurred during pipeline execution")
            return func.HttpResponse(
                json.dumps({"error": str(e)}),
                status_code=500,
                mimetype="application/json"
            )

    except ValueError as ve:
        logging.error(f"Configuration error: {ve}")
        return func.HttpResponse(
            json.dumps({"error": str(ve)}),
            status_code=400,
            mimetype="application/json"
        )
        return func.HttpResponse(str(ve), status_code=400)
    except Exception as e:
        logging.exception("Error during ADF operations")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
        return func.HttpResponse(f"Exception: {str(e)}", status_code=500)
