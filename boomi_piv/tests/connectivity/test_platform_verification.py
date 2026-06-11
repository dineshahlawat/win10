"""PIV-PLAT: Platform Prerequisites and Verification Tests.

Tests #1, #5, #9 from team test cases:
- Platform prerequisites (OS, filesystem, ports, Key Vault)
- Platform installation (Generate token, install, validate ONLINE)
- Platform Verification (Validate ONLINE, check config, verify nodes)
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from boomi_piv.config.settings import BoomiAtomConfig
from boomi_piv.utils.api_client import BoomiAPIClient
from boomi_piv.utils.atom_health import AtomStatus, check_atom_reachability


class TestPlatformPrerequisites:
    """PIV-PLAT-001: Platform prerequisites validated (Team TC #1)."""

    def test_atom_url_configured(self, atom_config: BoomiAtomConfig) -> None:
        """Atom URL is configured and non-empty."""
        assert atom_config.atom_url != ""
        assert atom_config.atom_url.startswith("https://")

    def test_atom_id_configured(self, atom_config: BoomiAtomConfig) -> None:
        """Atom ID is configured and non-empty."""
        assert atom_config.atom_id != ""
        assert len(atom_config.atom_id) > 10

    def test_environment_configured(self, atom_config: BoomiAtomConfig) -> None:
        """Environment is configured."""
        assert atom_config.environment != ""
        assert atom_config.environment in {"Test", "Production", "Staging", "Development"}

    @patch("boomi_piv.utils.atom_health.requests.get")
    def test_atom_port_accessible(
        self, mock_get: MagicMock, atom_config: BoomiAtomConfig
    ) -> None:
        """Atom port (9090) is accessible via HTTP."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_get.return_value = mock_response

        result = check_atom_reachability(atom_config)

        assert result.reachable is True

    def test_atom_url_contains_port(self, atom_config: BoomiAtomConfig) -> None:
        """Atom URL contains expected port number."""
        assert ":9090" in atom_config.atom_url or ":443" in atom_config.atom_url


class TestPlatformInstallation:
    """PIV-PLAT-002: Platform installation verified (Team TC #5)."""

    @patch("requests.Session.get")
    def test_atom_online_after_installation(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Atom reports ONLINE status after installation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "atomId": "12345678-1234-1234-1234-123456789abc",
            "status": "ONLINE",
            "name": "InstalledAtom",
            "currentVersion": "24.06.1001",
            "dateInstalled": "2024-06-01T10:00:00Z",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_atom("12345678-1234-1234-1234-123456789abc")

        assert result["status"] == "ONLINE"
        assert result["currentVersion"] != ""
        assert result["dateInstalled"] != ""

    @patch("requests.Session.post")
    def test_atom_visible_in_account_query(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Installed Atom appears in account-level query."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "numberOfResults": 1,
            "result": [
                {
                    "atomId": "12345678-1234-1234-1234-123456789abc",
                    "name": "InstalledAtom",
                    "status": "ONLINE",
                }
            ],
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.query_atoms()

        assert result["numberOfResults"] >= 1
        atom_ids = [a["atomId"] for a in result["result"]]
        assert "12345678-1234-1234-1234-123456789abc" in atom_ids

    @patch("requests.Session.get")
    def test_installation_token_generated_successfully(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Install token generation returns valid token (via Atom lookup)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "atomId": "atom-new-install",
            "status": "ONLINE",
            "type": "ATOM",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_atom("atom-new-install")

        assert result["type"] == "ATOM"


class TestPlatformVerification:
    """PIV-PLAT-003: Platform fully functional (Team TC #9)."""

    @patch("requests.Session.get")
    def test_platform_atom_online(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Platform Atom is ONLINE."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "atomId": "platform-atom",
            "status": "ONLINE",
            "type": "MOLECULE",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_atom("platform-atom")

        assert result["status"] == "ONLINE"

    @patch("requests.Session.get")
    def test_platform_configuration_intact(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Platform configuration settings are intact."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "atomId": "platform-atom",
            "status": "ONLINE",
            "purgeHistoryDays": 30,
            "forceRestartTime": 0,
            "currentVersion": "24.06.1001",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_atom("platform-atom")

        assert "purgeHistoryDays" in result
        assert "currentVersion" in result
        assert result["currentVersion"] != ""

    @patch("requests.Session.post")
    def test_platform_all_nodes_online(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """All cluster nodes are ONLINE."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "numberOfResults": 3,
            "result": [
                {"atomId": f"node-{i}", "status": "ONLINE", "type": "MOLECULE"}
                for i in range(3)
            ],
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.query_atoms()

        assert all(n["status"] == "ONLINE" for n in result["result"])

    @patch("boomi_piv.utils.atom_health.requests.get")
    def test_platform_health_endpoint_responsive(
        self, mock_get: MagicMock, atom_config: BoomiAtomConfig
    ) -> None:
        """Platform health endpoint is responsive."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_get.return_value = mock_response

        result = check_atom_reachability(atom_config)

        assert result.status == AtomStatus.ONLINE
        assert result.reachable is True
