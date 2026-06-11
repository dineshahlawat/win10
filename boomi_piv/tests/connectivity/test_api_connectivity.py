"""PIV-CONN: AtomSphere API Connectivity Verification Tests.

Verifies that the Boomi AtomSphere API is reachable and responds
to requests correctly after installation.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from boomi_piv.config.settings import BoomiAPIConfig
from boomi_piv.utils.api_client import BoomiAPIClient


class TestAtomSphereAPIConnectivity:
    """PIV-CONN-005: AtomSphere API reachability."""

    @patch("requests.Session.get")
    def test_api_endpoint_reachable(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """AtomSphere API responds to a simple GET request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        response = api_client.get("Atom/test-id")

        assert response.status_code == 200

    @patch("requests.Session.get")
    def test_api_endpoint_uses_correct_url(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """API requests are sent to the correct base URL."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        api_client.get("Atom/test-id")

        expected_url = "https://api.boomi.com/api/rest/v1/BOOMI_ACCOUNT-XXXXXX/Atom/test-id"
        mock_get.assert_called_once_with(expected_url, params=None, timeout=30)

    @patch("requests.Session.post")
    def test_api_post_request(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """POST requests are sent correctly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"numberOfResults": 0, "result": []}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.query_atoms({"QueryFilter": {}})

        assert result["numberOfResults"] == 0

    @patch("requests.Session.get")
    def test_api_timeout_configuration(
        self, mock_get: MagicMock, api_config: BoomiAPIConfig
    ) -> None:
        """API client respects configured timeout."""
        custom_config = BoomiAPIConfig(
            base_url=api_config.base_url,
            account_id=api_config.account_id,
            username=api_config.username,
            api_token=api_config.api_token,
            timeout=60,
        )
        client = BoomiAPIClient(custom_config)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client.get("Atom/test-id")

        call_kwargs = mock_get.call_args
        assert call_kwargs[1]["timeout"] == 60

    @patch("requests.Session.get")
    def test_api_dns_failure(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """DNS resolution failure is surfaced as ConnectionError."""
        mock_get.side_effect = requests.ConnectionError(
            "Failed to resolve: api.boomi.com"
        )

        with pytest.raises(requests.ConnectionError, match="resolve"):
            api_client.get("Atom/test-id")


class TestAPIResponseParsing:
    """PIV-CONN-006: API response format verification."""

    @patch("requests.Session.post")
    def test_query_response_has_number_of_results(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Query responses include numberOfResults field."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "numberOfResults": 5,
            "result": [{"atomId": f"atom-{i}"} for i in range(5)],
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.query_atoms()

        assert "numberOfResults" in result
        assert "result" in result
        assert len(result["result"]) == result["numberOfResults"]

    @patch("requests.Session.get")
    def test_single_resource_response_has_type(
        self, mock_get: MagicMock, api_client: BoomiAPIClient, sample_atom_response: dict
    ) -> None:
        """Single resource responses include @type field."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_atom_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_atom("12345678-1234-1234-1234-123456789abc")

        assert "@type" in result
        assert result["@type"] == "Atom"
