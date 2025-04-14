import pytest
from unittest import mock
import json
import azure.functions as func
from psrfunc_app.replicateSalesforce.run import run, get_env_var, create_or_update_linked_service, create_or_update_dataset, create_or_update_dataflow, create_or_update_pipeline, create_adls_container_directory, monitor_pipeline_run

@pytest.fixture
def mock_env_vars():
    with mock.patch.dict("os.environ", {
        "AZURE_SUBSCRIPTION_ID": "fake-subscription-id",
        "AZURE_RESOURCE_GROUP": "fake-resource-group",
        "AZURE_DATA_FACTORY_NAME": "fake-factory-name",
        "AZURE_KEY_VAULT_NAME": "fake-kv-name",
        "AZURE_ADF_PIPELINE_NAME": "fake-pipeline-name",
        "ADLSGEN2_KEY_NAME": "fake-key-name",
    }):
        yield

@pytest.fixture
def mock_adf_client():
    return mock.MagicMock()

@pytest.fixture
def mock_kv_client():
    return mock.MagicMock()

@pytest.fixture
def mock_datalake_client():
    return mock.MagicMock()

@pytest.fixture
def mock_req():
    mock_request = mock.MagicMock()
    mock_request.get_json.return_value = {"objectName": "test_object"}
    return mock_request

def test_get_env_var(mock_env_vars):
    assert get_env_var("AZURE_SUBSCRIPTION_ID") == "fake-subscription-id"
    with pytest.raises(RuntimeError):
        get_env_var("NON_EXISTENT_VAR")

def test_create_or_update_linked_service(mock_adf_client):
    mock_adf_client.linked_services.create_or_update.return_value = mock.MagicMock()

    response = create_or_update_linked_service(mock_adf_client, "fake-resource-group", "fake-factory-name", "fake-ls-name", {"fake": "property"})
    assert response is not None
    mock_adf_client.linked_services.create_or_update.assert_called_once()

def test_create_or_update_dataset(mock_adf_client):
    mock_adf_client.datasets.create_or_update.return_value = mock.MagicMock()

    response = create_or_update_dataset(mock_adf_client, "fake-resource-group", "fake-factory-name", "fake-dataset-name", {"fake": "property"})
    assert response is not None
    mock_adf_client.datasets.create_or_update.assert_called_once()

def test_monitor_pipeline_run(mock_adf_client):
    mock_adf_client.pipeline_runs.get.return_value = mock.MagicMock(status="Succeeded")

    status = monitor_pipeline_run(mock_adf_client, "fake-resource-group", "fake-factory-name", "fake-run-id")
    assert status == "Succeeded"
    mock_adf_client.pipeline_runs.get.assert_called_once()

def test_monitor_pipeline_run_failure():
    mock_adf_client = mock.MagicMock()
    mock_pipeline_run = mock.MagicMock()
    mock_pipeline_run.status = "Failed"
    mock_pipeline_run.pipeline_name = "test_pipeline"
    mock_pipeline_run.run_start = "2025-04-14T00:00:00Z"
    mock_pipeline_run.run_end = "2025-04-14T01:00:00Z"
    mock_pipeline_run.duration_in_ms = 3600000 
    mock_pipeline_run.message = "Some error message"

    mock_adf_client.pipeline_runs.get.return_value = mock_pipeline_run

    with pytest.raises(RuntimeError) as excinfo:
        monitor_pipeline_run(mock_adf_client, "fake-resource-group", "fake-factory-name", "fake-run-id")
    
    error_message = str(excinfo.value)
    assert '"pipelineRunId": "fake-run-id"' in error_message
    assert '"pipelineName": "test_pipeline"' in error_message
    assert '"status": "Failed"' in error_message
    assert '"errorMessage": "Some error message"' in error_message

    mock_adf_client.pipeline_runs.get.assert_called_once_with(
        resource_group_name="fake-resource-group",
        factory_name="fake-factory-name",
        run_id="fake-run-id"
    )
