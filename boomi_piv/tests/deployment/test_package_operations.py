"""PIV-PKG: Package Deployment Operations Verification Tests.

Tests #21, #22, #23 from team test cases:
- Package deployment (Deploy package, Verify)
- Package undeployment (Delete package, Verify)
- Package rollback (Deploy previous version)
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from boomi_piv.utils.api_client import BoomiAPIClient


class TestPackageDeployment:
    """PIV-PKG-001: Ensure deployment (Team TC #21)."""

    @patch("requests.Session.post")
    def test_deploy_package_success(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Package deployed successfully with valid deployment ID."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "@type": "DeployedPackage",
            "deploymentId": "deploy-new-001",
            "packageId": "pkg-001",
            "environmentId": "env-001",
            "componentId": "comp-001",
            "active": True,
            "current": True,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.deploy_package({
            "packageId": "pkg-001",
            "environmentId": "env-001",
        })

        assert result["deploymentId"] == "deploy-new-001"
        assert result["active"] is True
        assert result["current"] is True

    @patch("requests.Session.post")
    def test_deploy_package_sends_to_correct_endpoint(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """POST sent to DeployedPackage endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"deploymentId": "deploy-001"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        api_client.deploy_package({"packageId": "pkg-001", "environmentId": "env-001"})

        call_url = mock_post.call_args[0][0]
        assert call_url.endswith("/DeployedPackage")

    @patch("requests.Session.post")
    def test_deploy_package_sends_correct_payload(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Deployment payload includes packageId and environmentId."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"deploymentId": "d-001"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        api_client.deploy_package({
            "packageId": "pkg-target",
            "environmentId": "env-target",
            "notes": "PIV deployment",
        })

        sent_payload = mock_post.call_args[1]["json"]
        assert sent_payload["packageId"] == "pkg-target"
        assert sent_payload["environmentId"] == "env-target"

    @patch("requests.Session.post")
    def test_deploy_to_invalid_environment_returns_error(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Deploying to non-existent environment returns 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_post.return_value = mock_response

        with pytest.raises(requests.HTTPError, match="404"):
            api_client.deploy_package({
                "packageId": "pkg-001",
                "environmentId": "env-nonexistent",
            })


class TestPackageUndeployment:
    """PIV-PKG-002: Ensure undeployment (Team TC #22)."""

    @patch("requests.Session.delete")
    def test_undeploy_package_success(
        self, mock_delete: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Package undeployed (deleted) successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        response = api_client.undeploy_package("deploy-to-remove")

        assert response.status_code == 200

    @patch("requests.Session.delete")
    def test_undeploy_sends_to_correct_endpoint(
        self, mock_delete: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """DELETE sent to DeployedPackage/{deploymentId}."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        api_client.undeploy_package("deploy-del-001")

        call_url = mock_delete.call_args[0][0]
        assert "DeployedPackage/deploy-del-001" in call_url

    @patch("requests.Session.delete")
    def test_undeploy_nonexistent_package_returns_404(
        self, mock_delete: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Undeploying non-existent package returns 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_delete.return_value = mock_response

        with pytest.raises(requests.HTTPError, match="404"):
            api_client.undeploy_package("nonexistent-deploy")

    @patch("requests.Session.post")
    def test_verify_package_removed_after_undeploy(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """After undeploy, querying returns empty results."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "numberOfResults": 0,
            "result": [],
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.query_deployed_packages({
            "QueryFilter": {
                "expression": {
                    "property": "deploymentId",
                    "operator": "EQUALS",
                    "argument": ["deploy-removed"],
                }
            }
        })

        assert result["numberOfResults"] == 0


class TestPackageRollback:
    """PIV-PKG-003: Ensure rollback (Team TC #23)."""

    @patch("requests.Session.post")
    def test_rollback_deploys_previous_version(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Rolling back deploys the previous package version."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "deploymentId": "deploy-rollback-001",
            "packageId": "pkg-v1",
            "version": 1,
            "active": True,
            "current": True,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.deploy_package({
            "packageId": "pkg-v1",
            "environmentId": "env-rollback",
            "notes": "Rollback to v1",
        })

        assert result["packageId"] == "pkg-v1"
        assert result["version"] == 1
        assert result["current"] is True

    @patch("requests.Session.post")
    def test_rollback_marks_new_deployment_as_current(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Rollback deployment becomes the current active deployment."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "deploymentId": "deploy-rollback-002",
            "packageId": "pkg-previous",
            "active": True,
            "current": True,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.deploy_package({
            "packageId": "pkg-previous",
            "environmentId": "env-prod",
        })

        assert result["active"] is True
        assert result["current"] is True

    @patch("requests.Session.post")
    def test_rollback_to_invalid_package_returns_error(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Rolling back to non-existent package returns error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "404 Not Found: Package version does not exist"
        )
        mock_post.return_value = mock_response

        with pytest.raises(requests.HTTPError, match="404"):
            api_client.deploy_package({
                "packageId": "pkg-nonexistent",
                "environmentId": "env-prod",
            })
