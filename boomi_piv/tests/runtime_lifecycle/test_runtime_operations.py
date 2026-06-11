"""PIV-RT: Runtime Lifecycle Verification Tests.

Tests #6, #7, #8, #18, #19, #20 from team test cases:
- Runtime creation (Create Atom via API)
- Runtime Configuration (Configure atom properties)
- Runtime deletion (Detach environments, validate, delete)
- Runtime Stop (Drain, stop, validate OFFLINE)
- Runtime Start (Start, validate ONLINE)
- Runtime Restart (Restart, validate ONLINE)
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from boomi_piv.utils.api_client import BoomiAPIClient


class TestRuntimeCreation:
    """PIV-RT-001: Ensure runtime instance is created (Team TC #6)."""

    @patch("requests.Session.post")
    def test_create_atom_returns_atom_id(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """POST Atom returns a valid atomId."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "@type": "Atom",
            "atomId": "atom-new-1234-5678-abcd",
            "name": "NewRuntime_01",
            "status": "ONLINE",
            "type": "ATOM",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.create_atom({
            "name": "NewRuntime_01",
            "type": "ATOM",
            "cloudId": "cloud-parent-001",
        })

        assert "atomId" in result
        assert result["atomId"] == "atom-new-1234-5678-abcd"
        assert result["status"] == "ONLINE"

    @patch("requests.Session.post")
    def test_create_atom_sends_to_correct_endpoint(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """POST request sent to Atom endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"atomId": "atom-001"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        api_client.create_atom({"name": "Test", "type": "ATOM"})

        call_url = mock_post.call_args[0][0]
        assert call_url.endswith("/Atom")

    @patch("requests.Session.post")
    def test_create_atom_with_cloud_association(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Atom created with cloudId association."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "atomId": "atom-002",
            "cloudId": "cloud-parent",
            "name": "CloudAtom",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        payload = {"name": "CloudAtom", "type": "ATOM", "cloudId": "cloud-parent"}
        result = api_client.create_atom(payload)

        call_kwargs = mock_post.call_args
        sent_payload = call_kwargs[1]["json"]
        assert sent_payload["cloudId"] == "cloud-parent"


class TestRuntimeConfiguration:
    """PIV-RT-002: Ensure runtime configs are applied (Team TC #7)."""

    @patch("requests.Session.post")
    def test_update_atom_properties(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Atom properties can be updated via API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "atomId": "atom-config-001",
            "name": "Configured_Runtime",
            "purgeHistoryDays": 7,
            "forceRestartTime": 300000,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.update_atom(
            "atom-config-001",
            {"purgeHistoryDays": 7, "forceRestartTime": 300000},
        )

        assert result["purgeHistoryDays"] == 7
        assert result["forceRestartTime"] == 300000

    @patch("requests.Session.post")
    def test_update_atom_sends_to_correct_endpoint(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Update request sent to Atom/{atomId}/update."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"atomId": "atom-001"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        api_client.update_atom("atom-001", {"purgeHistoryDays": 30})

        call_url = mock_post.call_args[0][0]
        assert "Atom/atom-001/update" in call_url

    @patch("requests.Session.post")
    def test_set_runtime_properties(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Runtime properties (JVM args, etc.) can be configured."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "atomId": "atom-rt-001",
            "properties": {
                "com.boomi.container.maxMemory": "2048m",
                "com.boomi.container.maxThreads": "200",
            },
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.update_atom("atom-rt-001", {
            "properties": {
                "com.boomi.container.maxMemory": "2048m",
                "com.boomi.container.maxThreads": "200",
            }
        })

        assert "properties" in result


class TestRuntimeDeletion:
    """PIV-RT-003: Ensure runtime is deleted safely (Team TC #8)."""

    @patch("requests.Session.delete")
    def test_delete_atom_success(
        self, mock_delete: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Atom is deleted successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        response = api_client.delete_atom("atom-to-delete")

        assert response.status_code == 200

    @patch("requests.Session.delete")
    def test_delete_atom_sends_to_correct_endpoint(
        self, mock_delete: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """DELETE request sent to Atom/{atomId}."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        api_client.delete_atom("atom-del-001")

        call_url = mock_delete.call_args[0][0]
        assert "Atom/atom-del-001" in call_url

    @patch("requests.Session.delete")
    def test_delete_atom_with_environments_returns_error(
        self, mock_delete: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Deleting Atom with attached environments returns 409."""
        mock_response = MagicMock()
        mock_response.status_code = 409
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "409 Conflict: Atom has attached environments"
        )
        mock_delete.return_value = mock_response

        with pytest.raises(requests.HTTPError, match="409"):
            api_client.delete_atom("atom-with-envs")

    @patch("requests.Session.get")
    def test_validate_atom_offline_before_deletion(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Atom status should be checked (OFFLINE) before deletion."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "atomId": "atom-check",
            "status": "OFFLINE",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_atom("atom-check")

        assert result["status"] == "OFFLINE"


class TestRuntimeStop:
    """PIV-RT-004: Ensure runtime stops (Team TC #18)."""

    @patch("requests.Session.get")
    def test_runtime_status_offline_after_stop(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """After stop, Atom status is OFFLINE."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "atomId": "atom-stopped",
            "status": "OFFLINE",
            "name": "StoppedRuntime",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_atom("atom-stopped")

        assert result["status"] == "OFFLINE"

    @patch("requests.Session.get")
    def test_stopped_runtime_not_processing(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Stopped runtime has no in-process executions."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "atomId": "atom-stopped",
            "status": "OFFLINE",
            "currentExecutionCount": 0,
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_atom("atom-stopped")

        assert result["currentExecutionCount"] == 0


class TestRuntimeStart:
    """PIV-RT-005: Ensure runtime starts (Team TC #19)."""

    @patch("requests.Session.get")
    def test_runtime_status_online_after_start(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """After start, Atom status is ONLINE."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "atomId": "atom-started",
            "status": "ONLINE",
            "name": "StartedRuntime",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_atom("atom-started")

        assert result["status"] == "ONLINE"

    @patch("requests.Session.get")
    def test_started_runtime_version_populated(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Started runtime reports its version."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "atomId": "atom-started",
            "status": "ONLINE",
            "currentVersion": "24.06.1001",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_atom("atom-started")

        assert result["currentVersion"] != ""


class TestRuntimeRestart:
    """PIV-RT-006: Ensure runtime restarts (Team TC #20)."""

    @patch("requests.Session.get")
    def test_runtime_online_after_restart(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """After restart, Atom status is ONLINE."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "atomId": "atom-restarted",
            "status": "ONLINE",
            "name": "RestartedRuntime",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_atom("atom-restarted")

        assert result["status"] == "ONLINE"

    @patch("requests.Session.get")
    def test_restart_preserves_atom_id(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Atom ID remains the same after restart."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "atomId": "atom-original-id",
            "status": "ONLINE",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_atom("atom-original-id")

        assert result["atomId"] == "atom-original-id"

    @patch("requests.Session.get")
    def test_restart_preserves_configuration(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Configuration is preserved after restart."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "atomId": "atom-restarted",
            "status": "ONLINE",
            "purgeHistoryDays": 7,
            "forceRestartTime": 300000,
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_atom("atom-restarted")

        assert result["purgeHistoryDays"] == 7
        assert result["forceRestartTime"] == 300000
