"""Shared fixtures for Boomi PIV tests."""

import pytest

from boomi_piv.config.settings import (
    BoomiAPIConfig,
    BoomiAtomConfig,
    ConnectorConfig,
    PIVConfig,
)
from boomi_piv.utils.api_client import BoomiAPIClient


@pytest.fixture()
def atom_config() -> BoomiAtomConfig:
    """Provide a test BoomiAtomConfig."""
    return BoomiAtomConfig(
        atom_url="https://atom-test.example.com:9090",
        atom_id="12345678-1234-1234-1234-123456789abc",
        environment="Test",
        classification="Test",
    )


@pytest.fixture()
def api_config() -> BoomiAPIConfig:
    """Provide a test BoomiAPIConfig."""
    return BoomiAPIConfig(
        base_url="https://api.boomi.com/api/rest/v1",
        account_id="BOOMI_ACCOUNT-XXXXXX",
        username="test_user@example.com",
        api_token="test-api-token-12345",
        timeout=30,
    )


@pytest.fixture()
def connector_config() -> ConnectorConfig:
    """Provide a test ConnectorConfig."""
    return ConnectorConfig(
        database_url="jdbc:mysql://db.example.com:3306/testdb",
        sftp_host="sftp.example.com",
        sftp_port=22,
        http_endpoint="https://api.example.com/webhook",
        jms_broker_url="tcp://broker.example.com:61616",
    )


@pytest.fixture()
def piv_config(
    atom_config: BoomiAtomConfig,
    api_config: BoomiAPIConfig,
    connector_config: ConnectorConfig,
) -> PIVConfig:
    """Provide a full PIVConfig for testing."""
    return PIVConfig(
        atom=atom_config,
        api=api_config,
        connectors=connector_config,
        retry_attempts=3,
        retry_delay_seconds=1.0,
    )


@pytest.fixture()
def api_client(api_config: BoomiAPIConfig) -> BoomiAPIClient:
    """Provide a BoomiAPIClient instance."""
    return BoomiAPIClient(api_config)


@pytest.fixture()
def sample_atom_response() -> dict:
    """Sample Atom API response."""
    return {
        "@type": "Atom",
        "atomId": "12345678-1234-1234-1234-123456789abc",
        "name": "TestAtom_01",
        "status": "ONLINE",
        "currentVersion": "24.01.1234",
        "hostName": "atom-host-01.example.com",
        "type": "ATOM",
        "dateInstalled": "2024-01-15T10:30:00Z",
        "cloudId": "",
        "purgeHistoryDays": 30,
        "forceRestartTime": 0,
    }


@pytest.fixture()
def sample_execution_response() -> dict:
    """Sample execution record API response."""
    return {
        "@type": "ExecutionRecord",
        "executionId": "execution-1234-5678-abcd",
        "processId": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "processName": "Test_Integration_Process",
        "atomId": "12345678-1234-1234-1234-123456789abc",
        "atomName": "TestAtom_01",
        "status": "COMPLETE",
        "executionTime": "2024-06-01T12:00:00Z",
        "executionDuration": 2500,
        "message": "",
        "inboundDocumentCount": 10,
        "outboundDocumentCount": 10,
        "inboundErrorDocumentCount": 0,
        "outboundErrorDocumentCount": 0,
    }


@pytest.fixture()
def sample_deployment_response() -> dict:
    """Sample deployed package API response."""
    return {
        "@type": "DeployedPackage",
        "deploymentId": "deploy-1234-5678-abcd",
        "packageId": "pkg-1234-5678-abcd",
        "environmentId": "env-1234-5678-abcd",
        "componentId": "comp-1234-5678-abcd",
        "packageVersion": "1.0",
        "version": 3,
        "componentType": "process",
        "deployedBy": "test_user@example.com",
        "deployedDate": "2024-06-01T10:00:00Z",
        "active": True,
        "current": True,
        "deleted": False,
        "pending": False,
    }
