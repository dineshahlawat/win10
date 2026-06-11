"""PIV-AUTH: API Authentication Verification Tests.

Verifies that Boomi AtomSphere API authentication is correctly
configured and operational after installation.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from boomi_piv.config.settings import BoomiAPIConfig
from boomi_piv.utils.api_client import BoomiAPIClient


class TestAPIBasicAuthentication:
    """PIV-AUTH-001: Basic authentication to AtomSphere API."""

    def test_client_uses_basic_auth(self, api_client: BoomiAPIClient) -> None:
        """API client is initialized with Basic authentication."""
        assert api_client.session.auth is not None
        username, token = api_client.session.auth.username, api_client.session.auth.password
        assert username == "test_user@example.com"
        assert token == "test-api-token-12345"

    def test_client_sets_json_headers(self, api_client: BoomiAPIClient) -> None:
        """API client sends JSON content-type headers."""
        assert api_client.session.headers["Content-Type"] == "application/json"
        assert api_client.session.headers["Accept"] == "application/json"

    @patch("requests.Session.get")
    def test_successful_authentication(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Successful auth returns 200 on API query."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"@type": "Atom", "atomId": "test"}
        mock_get.return_value = mock_response

        response = api_client.get("Atom/test-atom-id")

        assert response.status_code == 200

    @patch("requests.Session.get")
    def test_invalid_credentials_returns_401(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Invalid credentials return HTTP 401."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")
        mock_get.return_value = mock_response

        response = api_client.get("Atom/test-atom-id")

        assert response.status_code == 401

    @patch("requests.Session.get")
    def test_expired_token_returns_403(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Expired or revoked token returns HTTP 403."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        response = api_client.get("Atom/test-atom-id")

        assert response.status_code == 403


class TestAPIAccountAccess:
    """PIV-AUTH-002: Account-level API access verification."""

    def test_base_url_includes_account_id(self, api_client: BoomiAPIClient) -> None:
        """API client base URL includes the account ID."""
        assert "BOOMI_ACCOUNT-XXXXXX" in api_client.base_url

    def test_base_url_format(self, api_client: BoomiAPIClient) -> None:
        """API base URL is correctly constructed."""
        expected = "https://api.boomi.com/api/rest/v1/BOOMI_ACCOUNT-XXXXXX"
        assert api_client.base_url == expected

    @patch("requests.Session.post")
    def test_query_atoms_requires_account_access(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Querying Atoms requires valid account access."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"numberOfResults": 1, "result": []}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.query_atoms()

        assert "numberOfResults" in result
        call_url = mock_post.call_args[0][0]
        assert "BOOMI_ACCOUNT-XXXXXX" in call_url


class TestAPITokenConfiguration:
    """PIV-AUTH-003: API token configuration validation."""

    def test_config_username_not_empty(self, api_config: BoomiAPIConfig) -> None:
        """Username/email must be configured."""
        assert api_config.username != ""
        assert "@" in api_config.username

    def test_config_token_not_empty(self, api_config: BoomiAPIConfig) -> None:
        """API token must be configured."""
        assert api_config.api_token != ""
        assert len(api_config.api_token) > 10

    def test_config_account_id_not_empty(self, api_config: BoomiAPIConfig) -> None:
        """Account ID must be configured."""
        assert api_config.account_id != ""
        assert api_config.account_id.startswith("BOOMI_ACCOUNT")

    def test_config_timeout_positive(self, api_config: BoomiAPIConfig) -> None:
        """API timeout must be a positive value."""
        assert api_config.timeout > 0

    def test_config_base_url_is_https(self, api_config: BoomiAPIConfig) -> None:
        """API base URL must use HTTPS."""
        assert api_config.base_url.startswith("https://")
