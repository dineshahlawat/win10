"""PIV-RBAC: RBAC User Role Verification Tests.

Test #17 from team test cases:
- RBAC User Deletion (Query user, delete role mapping)
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from boomi_piv.utils.api_client import BoomiAPIClient


class TestRBACUserDeletion:
    """PIV-RBAC-001: Ensure RBAC user removal (Team TC #17)."""

    @patch("requests.Session.post")
    def test_query_user_roles(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """User role mappings can be queried."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "numberOfResults": 2,
            "result": [
                {
                    "userId": "user-001",
                    "roleId": "role-admin",
                    "roleName": "Administrator",
                },
                {
                    "userId": "user-001",
                    "roleId": "role-developer",
                    "roleName": "Developer",
                },
            ],
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.query_user_roles({
            "QueryFilter": {
                "expression": {
                    "property": "userId",
                    "operator": "EQUALS",
                    "argument": ["user-001"],
                }
            }
        })

        assert result["numberOfResults"] == 2
        role_ids = [r["roleId"] for r in result["result"]]
        assert "role-admin" in role_ids

    @patch("requests.Session.delete")
    def test_delete_user_role_mapping(
        self, mock_delete: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """User role mapping deleted successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        response = api_client.delete_user_role("user-001", "role-admin")

        assert response.status_code == 200

    @patch("requests.Session.delete")
    def test_delete_user_role_sends_to_correct_endpoint(
        self, mock_delete: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """DELETE sent to UserRole/{userId}/{roleId}."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        api_client.delete_user_role("user-target", "role-target")

        call_url = mock_delete.call_args[0][0]
        assert "UserRole/user-target/role-target" in call_url

    @patch("requests.Session.delete")
    def test_delete_nonexistent_user_role_returns_404(
        self, mock_delete: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Deleting non-existent role mapping returns 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_delete.return_value = mock_response

        with pytest.raises(requests.HTTPError, match="404"):
            api_client.delete_user_role("user-000", "role-000")

    @patch("requests.Session.post")
    def test_verify_role_removed_after_deletion(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """After deletion, querying returns fewer role mappings."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "numberOfResults": 1,
            "result": [
                {
                    "userId": "user-001",
                    "roleId": "role-developer",
                    "roleName": "Developer",
                },
            ],
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.query_user_roles()

        assert result["numberOfResults"] == 1
        assert result["result"][0]["roleId"] == "role-developer"

    @patch("requests.Session.post")
    def test_query_user_roles_sends_to_correct_endpoint(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Query sent to UserRole/query endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"numberOfResults": 0, "result": []}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        api_client.query_user_roles()

        call_url = mock_post.call_args[0][0]
        assert "UserRole/query" in call_url
