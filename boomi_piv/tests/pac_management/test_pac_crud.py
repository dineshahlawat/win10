"""PIV-PAC: Private Atom Cloud (PAC) CRUD Verification Tests.

Tests #2, #3, #4, #14 from team test cases:
- PAC creation (POST RuntimeCloud)
- PAC update (Update RuntimeCloud)
- PAC deletion (Delete RuntimeCloud + attachments)
- PAC Configuration (AccountCloudAttachmentProperties)
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from boomi_piv.utils.api_client import BoomiAPIClient


class TestPACCreation:
    """PIV-PAC-001: Ensure PAC is created successfully (Team TC #2)."""

    @patch("requests.Session.post")
    def test_create_pac_returns_cloud_id(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """POST RuntimeCloud returns a valid cloudId."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "@type": "RuntimeCloud",
            "cloudId": "cloud-1234-abcd-5678-efgh",
            "name": "Test_PAC_01",
            "status": "ONLINE",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.create_runtime_cloud({
            "name": "Test_PAC_01",
            "cloudType": "PRIVATE",
        })

        assert "cloudId" in result
        assert result["cloudId"] == "cloud-1234-abcd-5678-efgh"
        assert result["name"] == "Test_PAC_01"

    @patch("requests.Session.post")
    def test_create_pac_with_all_fields(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """PAC creation with full configuration payload."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "@type": "RuntimeCloud",
            "cloudId": "cloud-new-001",
            "name": "Production_PAC",
            "status": "ONLINE",
            "cloudType": "PRIVATE",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        payload = {
            "name": "Production_PAC",
            "cloudType": "PRIVATE",
            "maxAtoms": 10,
        }
        result = api_client.create_runtime_cloud(payload)

        assert result["@type"] == "RuntimeCloud"
        assert result["cloudType"] == "PRIVATE"

    @patch("requests.Session.post")
    def test_create_pac_sends_post_to_correct_endpoint(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """POST request is sent to RuntimeCloud endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"cloudId": "cloud-001"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        api_client.create_runtime_cloud({"name": "Test"})

        call_url = mock_post.call_args[0][0]
        assert call_url.endswith("/RuntimeCloud")

    @patch("requests.Session.post")
    def test_create_pac_duplicate_name_returns_error(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Duplicate PAC name returns an error response."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "400 Bad Request: Cloud name already exists"
        )
        mock_post.return_value = mock_response

        with pytest.raises(requests.HTTPError, match="400"):
            api_client.create_runtime_cloud({"name": "Existing_PAC"})


class TestPACUpdate:
    """PIV-PAC-002: Ensure PAC is updated correctly (Team TC #3)."""

    @patch("requests.Session.post")
    def test_update_pac_name(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """PAC name can be updated via API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "cloudId": "cloud-1234",
            "name": "Updated_PAC_Name",
            "status": "ONLINE",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.update_runtime_cloud(
            "cloud-1234", {"name": "Updated_PAC_Name"}
        )

        assert result["name"] == "Updated_PAC_Name"
        assert result["cloudId"] == "cloud-1234"

    @patch("requests.Session.post")
    def test_update_pac_preserves_cloud_id(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Cloud ID remains unchanged after update."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "cloudId": "cloud-original-id",
            "name": "New_Name",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.update_runtime_cloud(
            "cloud-original-id", {"name": "New_Name"}
        )

        assert result["cloudId"] == "cloud-original-id"

    @patch("requests.Session.post")
    def test_update_pac_sends_to_correct_endpoint(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Update request sent to RuntimeCloud/{cloudId}/update."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"cloudId": "cloud-123"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        api_client.update_runtime_cloud("cloud-123", {"name": "X"})

        call_url = mock_post.call_args[0][0]
        assert "RuntimeCloud/cloud-123/update" in call_url

    @patch("requests.Session.post")
    def test_update_nonexistent_pac_returns_404(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Updating a non-existent PAC returns 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_post.return_value = mock_response

        with pytest.raises(requests.HTTPError, match="404"):
            api_client.update_runtime_cloud("nonexistent-id", {"name": "X"})


class TestPACDeletion:
    """PIV-PAC-003: Ensure PAC is deleted safely (Team TC #4)."""

    @patch("requests.Session.delete")
    def test_delete_pac_success(
        self, mock_delete: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """PAC is deleted successfully with 200 response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        response = api_client.delete_runtime_cloud("cloud-to-delete")

        assert response.status_code == 200

    @patch("requests.Session.delete")
    def test_delete_pac_sends_to_correct_endpoint(
        self, mock_delete: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """DELETE request sent to RuntimeCloud/{cloudId}."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        api_client.delete_runtime_cloud("cloud-del-001")

        call_url = mock_delete.call_args[0][0]
        assert "RuntimeCloud/cloud-del-001" in call_url

    @patch("requests.Session.delete")
    def test_delete_pac_with_attachments_returns_error(
        self, mock_delete: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Deleting PAC with active attachments returns 409 conflict."""
        mock_response = MagicMock()
        mock_response.status_code = 409
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "409 Conflict: Cloud has active attachments"
        )
        mock_delete.return_value = mock_response

        with pytest.raises(requests.HTTPError, match="409"):
            api_client.delete_runtime_cloud("cloud-with-attachments")

    @patch("requests.Session.post")
    def test_query_pac_before_deletion(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """PAC can be queried to confirm existence before deletion."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "numberOfResults": 1,
            "result": [{"cloudId": "cloud-target", "name": "Target_PAC"}],
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.query_runtime_clouds()

        assert result["numberOfResults"] == 1
        assert result["result"][0]["cloudId"] == "cloud-target"


class TestPACConfiguration:
    """PIV-PAC-004: Ensure PAC settings applied (Team TC #14)."""

    @patch("requests.Session.post")
    def test_update_cloud_attachment_properties(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """AccountCloudAttachmentProperties updated successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "cloudId": "cloud-config-001",
            "properties": {"maxConcurrentExecutions": "50"},
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.update_cloud_attachment_properties(
            "cloud-config-001",
            {"properties": {"maxConcurrentExecutions": "50"}},
        )

        assert result["cloudId"] == "cloud-config-001"

    @patch("requests.Session.post")
    def test_pac_config_sends_to_correct_endpoint(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Request sent to AccountCloudAttachmentProperties/{id}/update."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"cloudId": "cloud-001"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        api_client.update_cloud_attachment_properties("cloud-001", {"prop": "val"})

        call_url = mock_post.call_args[0][0]
        assert "AccountCloudAttachmentProperties/cloud-001/update" in call_url

    @patch("requests.Session.post")
    def test_pac_config_invalid_property_returns_error(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Invalid property key returns 400."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "400 Bad Request: Invalid property"
        )
        mock_post.return_value = mock_response

        with pytest.raises(requests.HTTPError, match="400"):
            api_client.update_cloud_attachment_properties(
                "cloud-001", {"invalidProp": "value"}
            )
