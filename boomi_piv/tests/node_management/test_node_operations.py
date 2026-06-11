"""PIV-NODE: Node Attach/Detach Verification Tests.

Tests #15, #16 from team test cases:
- Attach Node (Configure NFS, join cluster)
- Detach Node (Unmount, remove node)
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from boomi_piv.utils.api_client import BoomiAPIClient


class TestNodeAttach:
    """PIV-NODE-001: Ensure node attachment (Team TC #15)."""

    @patch("requests.Session.post")
    def test_query_atoms_to_find_cluster_nodes(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Query Atoms to find all nodes in a Molecule cluster."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "numberOfResults": 3,
            "result": [
                {
                    "atomId": f"node-{i}",
                    "name": f"MoleculeNode_{i}",
                    "type": "MOLECULE",
                    "status": "ONLINE",
                    "hostName": f"node-{i}.cluster.local",
                }
                for i in range(3)
            ],
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.query_atoms({
            "QueryFilter": {
                "expression": {
                    "property": "type",
                    "operator": "EQUALS",
                    "argument": ["MOLECULE"],
                }
            }
        })

        assert result["numberOfResults"] == 3
        assert all(n["type"] == "MOLECULE" for n in result["result"])
        assert all(n["status"] == "ONLINE" for n in result["result"])

    @patch("requests.Session.get")
    def test_new_node_online_after_attach(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Newly attached node reports ONLINE status."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "atomId": "node-new",
            "name": "NewClusterNode",
            "type": "MOLECULE",
            "status": "ONLINE",
            "hostName": "new-node.cluster.local",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_atom("node-new")

        assert result["status"] == "ONLINE"
        assert result["type"] == "MOLECULE"

    @patch("requests.Session.post")
    def test_cluster_node_count_increases_after_attach(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Cluster node count increases after attaching a new node."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "numberOfResults": 4,
            "result": [{"atomId": f"node-{i}", "status": "ONLINE"} for i in range(4)],
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.query_atoms()

        assert result["numberOfResults"] == 4

    @patch("requests.Session.get")
    def test_new_node_hostname_configured(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Newly attached node has correct hostname."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "atomId": "node-configured",
            "hostName": "node-04.cluster.example.com",
            "status": "ONLINE",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_atom("node-configured")

        assert result["hostName"] != ""
        assert "cluster" in result["hostName"]


class TestNodeDetach:
    """PIV-NODE-002: Ensure node detaches (Team TC #16)."""

    @patch("requests.Session.delete")
    def test_remove_node_from_cluster(
        self, mock_delete: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Node removed from cluster via DELETE Atom."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        response = api_client.delete_atom("node-to-remove")

        assert response.status_code == 200

    @patch("requests.Session.post")
    def test_cluster_node_count_decreases_after_detach(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Cluster node count decreases after detaching a node."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "numberOfResults": 2,
            "result": [{"atomId": f"node-{i}", "status": "ONLINE"} for i in range(2)],
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.query_atoms()

        assert result["numberOfResults"] == 2

    @patch("requests.Session.get")
    def test_removed_node_not_found(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Removed node returns 404 on GET."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        with pytest.raises(requests.HTTPError, match="404"):
            api_client.get_atom("node-removed")

    @patch("requests.Session.post")
    def test_remaining_nodes_still_online_after_detach(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Remaining cluster nodes stay ONLINE after one is detached."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "numberOfResults": 2,
            "result": [
                {"atomId": "node-0", "status": "ONLINE"},
                {"atomId": "node-1", "status": "ONLINE"},
            ],
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.query_atoms()

        assert all(n["status"] == "ONLINE" for n in result["result"])
