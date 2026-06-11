"""PIV-DEPLOY: Deployment and Environment Verification Tests.

Verifies that Boomi packages are correctly deployed, environments
are configured, and the Atom is properly set up after installation.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from boomi_piv.config.settings import BoomiAtomConfig, PIVConfig
from boomi_piv.utils.api_client import BoomiAPIClient
from boomi_piv.utils.validators import (
    validate_atom_id,
    validate_deployment_response,
    validate_environment_classification,
    validate_iso_timestamp,
    validate_process_id,
    validate_url,
)


class TestAtomDeploymentVerification:
    """PIV-DEPLOY-001: Atom registration and deployment status."""

    @patch("requests.Session.get")
    def test_atom_registered_in_platform(
        self, mock_get: MagicMock, api_client: BoomiAPIClient, sample_atom_response: dict
    ) -> None:
        """Atom is registered and visible in the platform."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_atom_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_atom("12345678-1234-1234-1234-123456789abc")

        assert result["atomId"] == "12345678-1234-1234-1234-123456789abc"
        assert result["status"] == "ONLINE"
        assert result["name"] == "TestAtom_01"

    @patch("requests.Session.get")
    def test_atom_has_current_version(
        self, mock_get: MagicMock, api_client: BoomiAPIClient, sample_atom_response: dict
    ) -> None:
        """Atom reports a valid version number."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_atom_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_atom("12345678-1234-1234-1234-123456789abc")

        assert "currentVersion" in result
        assert result["currentVersion"] != ""
        # Version follows pattern: YY.MM.BUILD
        version_parts = result["currentVersion"].split(".")
        assert len(version_parts) >= 2

    @patch("requests.Session.get")
    def test_atom_has_valid_install_date(
        self, mock_get: MagicMock, api_client: BoomiAPIClient, sample_atom_response: dict
    ) -> None:
        """Atom has a valid installation date."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_atom_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_atom("12345678-1234-1234-1234-123456789abc")

        assert "dateInstalled" in result
        assert validate_iso_timestamp(result["dateInstalled"])


class TestPackageDeploymentVerification:
    """PIV-DEPLOY-002: Package deployment verification."""

    @patch("requests.Session.get")
    def test_deployed_package_exists(
        self, mock_get: MagicMock, api_client: BoomiAPIClient, sample_deployment_response: dict
    ) -> None:
        """Deployed package is retrievable by ID."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_deployment_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_deployed_package("deploy-1234-5678-abcd")

        assert result["deploymentId"] == "deploy-1234-5678-abcd"
        assert result["active"] is True
        assert result["current"] is True

    @patch("requests.Session.post")
    def test_query_deployed_packages_in_environment(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Deployed packages can be queried per environment."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "numberOfResults": 3,
            "result": [
                {"deploymentId": f"deploy-{i}", "active": True, "current": True}
                for i in range(3)
            ],
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.query_deployed_packages(
            {"QueryFilter": {"expression": {"property": "environmentId", "operator": "EQUALS", "argument": ["env-001"]}}}
        )

        assert result["numberOfResults"] == 3
        assert all(pkg["active"] for pkg in result["result"])

    def test_deployment_response_validation_pass(
        self, sample_deployment_response: dict
    ) -> None:
        """Valid deployment response passes validation."""
        issues = validate_deployment_response(sample_deployment_response)
        assert len(issues) == 0

    def test_deployment_response_validation_missing_fields(self) -> None:
        """Missing required fields are detected."""
        incomplete_response = {"deploymentId": "deploy-001", "packageId": "pkg-001"}

        issues = validate_deployment_response(incomplete_response)

        assert len(issues) > 0
        assert any("environmentId" in issue for issue in issues)
        assert any("componentId" in issue for issue in issues)

    def test_deployment_response_validation_empty_id(self) -> None:
        """Empty deployment ID is flagged."""
        bad_response = {
            "deploymentId": "",
            "packageId": "pkg-001",
            "environmentId": "env-001",
            "componentId": "comp-001",
        }

        issues = validate_deployment_response(bad_response)

        assert any("Empty deploymentId" in issue for issue in issues)


class TestEnvironmentConfiguration:
    """PIV-DEPLOY-003: Environment configuration verification."""

    @patch("requests.Session.get")
    def test_environment_exists(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Target environment exists in the account."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "environmentId": "env-test-001",
            "name": "Test Environment",
            "classification": "TEST",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_environment("env-test-001")

        assert result["environmentId"] == "env-test-001"
        assert result["classification"] == "TEST"

    @pytest.mark.parametrize(
        "classification,is_valid",
        [
            ("TEST", True),
            ("PRODUCTION", True),
            ("STAGING", True),
            ("DEVELOPMENT", True),
            ("test", True),
            ("INVALID", False),
            ("", False),
        ],
    )
    def test_environment_classification_validation(
        self, classification: str, is_valid: bool
    ) -> None:
        """Environment classifications are validated correctly."""
        assert validate_environment_classification(classification) == is_valid

    def test_atom_config_environment_matches(self, atom_config: BoomiAtomConfig) -> None:
        """Atom configuration environment matches expected value."""
        assert atom_config.environment == "Test"
        assert validate_environment_classification(atom_config.classification)


class TestIDFormatValidation:
    """PIV-DEPLOY-004: ID format validation for deployment artifacts."""

    @pytest.mark.parametrize(
        "atom_id,is_valid",
        [
            ("12345678-1234-1234-1234-123456789abc", True),
            ("AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE", True),
            ("invalid-id", False),
            ("12345678-1234-1234-1234", False),
            ("", False),
            ("12345678123412341234123456789abc", False),
        ],
    )
    def test_atom_id_format(self, atom_id: str, is_valid: bool) -> None:
        """Atom IDs follow UUID format."""
        assert validate_atom_id(atom_id) == is_valid

    @pytest.mark.parametrize(
        "process_id,is_valid",
        [
            ("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", True),
            ("12345678-ABCD-EF12-3456-789012345678", True),
            ("not-a-uuid", False),
            ("", False),
        ],
    )
    def test_process_id_format(self, process_id: str, is_valid: bool) -> None:
        """Process IDs follow UUID format."""
        assert validate_process_id(process_id) == is_valid

    @pytest.mark.parametrize(
        "url,is_valid",
        [
            ("https://api.boomi.com/api/rest/v1", True),
            ("http://localhost:9090/ws/status", True),
            ("ftp://files.example.com", False),
            ("not-a-url", False),
            ("", False),
        ],
    )
    def test_url_format(self, url: str, is_valid: bool) -> None:
        """URLs are validated correctly."""
        assert validate_url(url) == is_valid


class TestTimestampValidation:
    """PIV-DEPLOY-005: Timestamp format and recency validation."""

    @pytest.mark.parametrize(
        "timestamp,is_valid",
        [
            ("2024-06-01T12:00:00Z", True),
            ("2024-06-01T12:00:00+00:00", True),
            ("2024-01-15T10:30:00Z", True),
            ("not-a-timestamp", False),
            ("2024-13-01T12:00:00Z", False),
            ("", False),
        ],
    )
    def test_iso_timestamp_validation(self, timestamp: str, is_valid: bool) -> None:
        """ISO 8601 timestamps are validated correctly."""
        assert validate_iso_timestamp(timestamp) == is_valid
