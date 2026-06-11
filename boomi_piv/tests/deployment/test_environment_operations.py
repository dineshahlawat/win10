"""PIV-ENV: Environment Operations Verification Tests.

Tests #10, #11, #12, #13 from team test cases:
- Environment creation (POST Environment)
- Environment deletion (Detach + Delete)
- Environment attach (Resolve IDs, Attach, Verify)
- Environment detach (Query, Delete attachment, Verify)
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from boomi_piv.utils.api_client import BoomiAPIClient


class TestEnvironmentCreation:
    """PIV-ENV-001: Ensure environment creation (Team TC #10)."""

    @patch("requests.Session.post")
    def test_create_environment_returns_id(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """POST Environment returns a valid environmentId."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "@type": "Environment",
            "environmentId": "env-new-1234-abcd",
            "name": "Test_Environment",
            "classification": "TEST",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.create_environment({
            "name": "Test_Environment",
            "classification": "TEST",
        })

        assert "environmentId" in result
        assert result["environmentId"] == "env-new-1234-abcd"
        assert result["classification"] == "TEST"

    @patch("requests.Session.post")
    def test_create_environment_sends_to_correct_endpoint(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """POST request sent to Environment endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"environmentId": "env-001"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        api_client.create_environment({"name": "Test", "classification": "TEST"})

        call_url = mock_post.call_args[0][0]
        assert call_url.endswith("/Environment")

    @patch("requests.Session.post")
    def test_create_environment_with_classification(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Environment created with correct classification."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "environmentId": "env-prod-001",
            "name": "Production",
            "classification": "PRODUCTION",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.create_environment({
            "name": "Production",
            "classification": "PRODUCTION",
        })

        assert result["classification"] == "PRODUCTION"

    @patch("requests.Session.post")
    def test_create_duplicate_environment_returns_error(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Duplicate environment name returns error."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "400 Bad Request: Environment name already exists"
        )
        mock_post.return_value = mock_response

        with pytest.raises(requests.HTTPError, match="400"):
            api_client.create_environment({"name": "Existing_Env"})


class TestEnvironmentDeletion:
    """PIV-ENV-002: Ensure environment deletion (Team TC #11)."""

    @patch("requests.Session.delete")
    def test_delete_environment_success(
        self, mock_delete: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Environment deleted successfully with 200."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        response = api_client.delete_environment("env-to-delete")

        assert response.status_code == 200

    @patch("requests.Session.delete")
    def test_delete_environment_sends_to_correct_endpoint(
        self, mock_delete: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """DELETE request sent to Environment/{environmentId}."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        api_client.delete_environment("env-del-001")

        call_url = mock_delete.call_args[0][0]
        assert "Environment/env-del-001" in call_url

    @patch("requests.Session.delete")
    def test_delete_environment_with_attachments_returns_error(
        self, mock_delete: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Deleting environment with active attachments returns 409."""
        mock_response = MagicMock()
        mock_response.status_code = 409
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "409 Conflict: Environment has active atom attachments"
        )
        mock_delete.return_value = mock_response

        with pytest.raises(requests.HTTPError, match="409"):
            api_client.delete_environment("env-attached")


class TestEnvironmentAttach:
    """PIV-ENV-003: Ensure environment attaches (Team TC #12)."""

    @patch("requests.Session.post")
    def test_attach_environment_to_atom(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Environment attached to Atom successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "@type": "EnvironmentAtomAttachment",
            "attachmentId": "attach-1234",
            "atomId": "atom-target-001",
            "environmentId": "env-source-001",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.attach_environment(
            atom_id="atom-target-001",
            environment_id="env-source-001",
        )

        assert result["attachmentId"] == "attach-1234"
        assert result["atomId"] == "atom-target-001"
        assert result["environmentId"] == "env-source-001"

    @patch("requests.Session.post")
    def test_attach_sends_correct_payload(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Attach sends atomId and environmentId in payload."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"attachmentId": "attach-001"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        api_client.attach_environment("atom-001", "env-001")

        sent_payload = mock_post.call_args[1]["json"]
        assert sent_payload == {"atomId": "atom-001", "environmentId": "env-001"}

    @patch("requests.Session.post")
    def test_attach_sends_to_correct_endpoint(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """POST request sent to EnvironmentAtomAttachment."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"attachmentId": "a-001"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        api_client.attach_environment("atom-001", "env-001")

        call_url = mock_post.call_args[0][0]
        assert "EnvironmentAtomAttachment" in call_url

    @patch("requests.Session.post")
    def test_attach_invalid_atom_returns_404(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Attaching to non-existent Atom returns 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_post.return_value = mock_response

        with pytest.raises(requests.HTTPError, match="404"):
            api_client.attach_environment("nonexistent-atom", "env-001")


class TestEnvironmentDetach:
    """PIV-ENV-004: Ensure environment detaches (Team TC #13)."""

    @patch("requests.Session.delete")
    def test_detach_environment_success(
        self, mock_delete: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Environment attachment deleted successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        response = api_client.detach_environment("attach-to-remove")

        assert response.status_code == 200

    @patch("requests.Session.delete")
    def test_detach_sends_to_correct_endpoint(
        self, mock_delete: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """DELETE sent to EnvironmentAtomAttachment/{attachmentId}."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        api_client.detach_environment("attach-001")

        call_url = mock_delete.call_args[0][0]
        assert "EnvironmentAtomAttachment/attach-001" in call_url

    @patch("requests.Session.delete")
    def test_detach_nonexistent_attachment_returns_404(
        self, mock_delete: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Detaching non-existent attachment returns 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_delete.return_value = mock_response

        with pytest.raises(requests.HTTPError, match="404"):
            api_client.detach_environment("nonexistent-attach")
