"""PIV-EXT: Environment Extension Update Verification Tests.

Tests #24, #25 from team test cases:
- Environment extension update - Connection (Merge config, update, verify)
- Environment extension update - Property (Update properties, verify)
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from boomi_piv.utils.api_client import BoomiAPIClient


class TestConnectionExtensionUpdate:
    """PIV-EXT-001: Ensure connection update (Team TC #24)."""

    @patch("requests.Session.post")
    def test_update_connection_extension(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Connection extension updated successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "environmentId": "env-conn-001",
            "connections": {
                "connection": [
                    {
                        "id": "conn-db-001",
                        "name": "Database_Connection",
                        "field": [
                            {"id": "url", "value": "jdbc:mysql://new-host:3306/db"},
                            {"id": "user", "value": "app_user"},
                        ],
                    }
                ]
            },
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.update_environment_extensions(
            "env-conn-001",
            {
                "connections": {
                    "connection": [
                        {
                            "id": "conn-db-001",
                            "field": [
                                {"id": "url", "value": "jdbc:mysql://new-host:3306/db"},
                            ],
                        }
                    ]
                }
            },
        )

        assert result["environmentId"] == "env-conn-001"
        conn = result["connections"]["connection"][0]
        assert conn["id"] == "conn-db-001"
        url_field = next(f for f in conn["field"] if f["id"] == "url")
        assert "new-host" in url_field["value"]

    @patch("requests.Session.post")
    def test_update_connection_sends_to_correct_endpoint(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """POST sent to EnvironmentExtensions/{envId}/update."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"environmentId": "env-001"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        api_client.update_environment_extensions("env-001", {"connections": {}})

        call_url = mock_post.call_args[0][0]
        assert "EnvironmentExtensions/env-001/update" in call_url

    @patch("requests.Session.post")
    def test_update_multiple_connection_fields(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Multiple connection fields updated in single call."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "environmentId": "env-multi",
            "connections": {
                "connection": [
                    {
                        "id": "conn-sftp-001",
                        "field": [
                            {"id": "host", "value": "sftp.newhost.com"},
                            {"id": "port", "value": "2222"},
                            {"id": "user", "value": "svc_account"},
                        ],
                    }
                ]
            },
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.update_environment_extensions("env-multi", {
            "connections": {
                "connection": [{
                    "id": "conn-sftp-001",
                    "field": [
                        {"id": "host", "value": "sftp.newhost.com"},
                        {"id": "port", "value": "2222"},
                        {"id": "user", "value": "svc_account"},
                    ],
                }]
            }
        })

        fields = result["connections"]["connection"][0]["field"]
        assert len(fields) == 3
        host_val = next(f["value"] for f in fields if f["id"] == "host")
        assert host_val == "sftp.newhost.com"

    @patch("requests.Session.post")
    def test_update_connection_invalid_env_returns_404(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Updating extensions on non-existent environment returns 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_post.return_value = mock_response

        with pytest.raises(requests.HTTPError, match="404"):
            api_client.update_environment_extensions("env-fake", {"connections": {}})

    @patch("requests.Session.get")
    def test_verify_connection_after_update(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """GET EnvironmentExtensions confirms updated connection values."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "environmentId": "env-verify",
            "connections": {
                "connection": [
                    {
                        "id": "conn-db-001",
                        "field": [
                            {"id": "url", "value": "jdbc:mysql://updated-host:3306/db"},
                        ],
                    }
                ]
            },
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_environment_extensions("env-verify")

        conn = result["connections"]["connection"][0]
        url_field = next(f for f in conn["field"] if f["id"] == "url")
        assert "updated-host" in url_field["value"]


class TestPropertyExtensionUpdate:
    """PIV-EXT-002: Ensure property update (Team TC #25)."""

    @patch("requests.Session.post")
    def test_update_process_property(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Process property updated successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "environmentId": "env-prop-001",
            "properties": {
                "property": [
                    {
                        "name": "batch.size",
                        "value": "500",
                        "componentId": "comp-001",
                    },
                    {
                        "name": "retry.count",
                        "value": "3",
                        "componentId": "comp-001",
                    },
                ]
            },
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.update_environment_extensions(
            "env-prop-001",
            {
                "properties": {
                    "property": [
                        {"name": "batch.size", "value": "500", "componentId": "comp-001"},
                    ]
                }
            },
        )

        props = result["properties"]["property"]
        batch_prop = next(p for p in props if p["name"] == "batch.size")
        assert batch_prop["value"] == "500"

    @patch("requests.Session.post")
    def test_update_multiple_properties(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Multiple properties updated in single call."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "environmentId": "env-multi-prop",
            "properties": {
                "property": [
                    {"name": "timeout.seconds", "value": "120"},
                    {"name": "max.records", "value": "10000"},
                    {"name": "enable.logging", "value": "true"},
                ]
            },
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.update_environment_extensions("env-multi-prop", {
            "properties": {
                "property": [
                    {"name": "timeout.seconds", "value": "120"},
                    {"name": "max.records", "value": "10000"},
                    {"name": "enable.logging", "value": "true"},
                ]
            }
        })

        props = result["properties"]["property"]
        assert len(props) == 3
        prop_names = [p["name"] for p in props]
        assert "timeout.seconds" in prop_names
        assert "max.records" in prop_names
        assert "enable.logging" in prop_names

    @patch("requests.Session.get")
    def test_verify_property_after_update(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """GET EnvironmentExtensions confirms updated property values."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "environmentId": "env-prop-verify",
            "properties": {
                "property": [
                    {"name": "batch.size", "value": "1000"},
                ]
            },
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_environment_extensions("env-prop-verify")

        prop = result["properties"]["property"][0]
        assert prop["name"] == "batch.size"
        assert prop["value"] == "1000"

    @patch("requests.Session.post")
    def test_update_property_invalid_component_returns_error(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Updating property for invalid component returns error."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "400 Bad Request: Invalid componentId"
        )
        mock_post.return_value = mock_response

        with pytest.raises(requests.HTTPError, match="400"):
            api_client.update_environment_extensions("env-001", {
                "properties": {
                    "property": [
                        {"name": "x", "value": "y", "componentId": "invalid-comp"},
                    ]
                }
            })
