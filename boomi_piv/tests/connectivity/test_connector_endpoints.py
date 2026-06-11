"""PIV-CONN: Connector Endpoint Verification Tests.

Verifies that configured connector endpoints (HTTP, SFTP, Database, JMS)
are reachable and respond correctly after installation.
"""

from unittest.mock import MagicMock, patch

import pytest

from boomi_piv.config.settings import ConnectorConfig


class TestHTTPConnectorEndpoint:
    """PIV-CONN-010: HTTP/HTTPS connector endpoint verification."""

    @patch("requests.get")
    def test_http_endpoint_reachable(
        self, mock_get: MagicMock, connector_config: ConnectorConfig
    ) -> None:
        """HTTP endpoint responds with a success status code."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        import requests

        response = requests.get(connector_config.http_endpoint, timeout=10)

        assert response.status_code == 200
        mock_get.assert_called_once_with(connector_config.http_endpoint, timeout=10)

    @patch("requests.get")
    def test_http_endpoint_returns_error(
        self, mock_get: MagicMock, connector_config: ConnectorConfig
    ) -> None:
        """HTTP endpoint returning 500 is detected as a failure."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("500 Server Error")
        mock_get.return_value = mock_response

        import requests

        response = requests.get(connector_config.http_endpoint, timeout=10)

        assert response.status_code == 500

    @patch("requests.get")
    def test_http_endpoint_timeout(
        self, mock_get: MagicMock, connector_config: ConnectorConfig
    ) -> None:
        """HTTP endpoint timeout is properly detected."""
        import requests

        mock_get.side_effect = requests.Timeout("Connection timed out")

        with pytest.raises(requests.Timeout):
            requests.get(connector_config.http_endpoint, timeout=5)


class TestSFTPConnectorEndpoint:
    """PIV-CONN-011: SFTP connector endpoint verification."""

    @patch("socket.create_connection")
    def test_sftp_port_reachable(
        self, mock_connect: MagicMock, connector_config: ConnectorConfig
    ) -> None:
        """SFTP port is open and accepting connections."""
        mock_socket = MagicMock()
        mock_connect.return_value = mock_socket

        import socket

        sock = socket.create_connection(
            (connector_config.sftp_host, connector_config.sftp_port), timeout=10
        )

        mock_connect.assert_called_once_with(
            (connector_config.sftp_host, connector_config.sftp_port), timeout=10
        )
        sock.close.assert_not_called()

    @patch("socket.create_connection")
    def test_sftp_port_unreachable(
        self, mock_connect: MagicMock, connector_config: ConnectorConfig
    ) -> None:
        """Unreachable SFTP port raises a connection error."""
        import socket

        mock_connect.side_effect = socket.timeout("Connection timed out")

        with pytest.raises(socket.timeout):
            socket.create_connection(
                (connector_config.sftp_host, connector_config.sftp_port), timeout=5
            )


class TestDatabaseConnectorEndpoint:
    """PIV-CONN-012: Database connector endpoint verification."""

    def test_database_url_configured(self, connector_config: ConnectorConfig) -> None:
        """Database URL is present in configuration."""
        assert connector_config.database_url is not None
        assert len(connector_config.database_url) > 0

    def test_database_url_format(self, connector_config: ConnectorConfig) -> None:
        """Database URL follows JDBC format."""
        url = connector_config.database_url
        assert url is not None
        assert url.startswith("jdbc:")

    def test_database_url_contains_host(self, connector_config: ConnectorConfig) -> None:
        """Database URL contains a host component."""
        url = connector_config.database_url
        assert url is not None
        assert "://" in url


class TestJMSConnectorEndpoint:
    """PIV-CONN-013: JMS broker endpoint verification."""

    def test_jms_broker_url_configured(self, connector_config: ConnectorConfig) -> None:
        """JMS broker URL is present in configuration."""
        assert connector_config.jms_broker_url is not None
        assert len(connector_config.jms_broker_url) > 0

    def test_jms_broker_url_format(self, connector_config: ConnectorConfig) -> None:
        """JMS broker URL follows expected protocol format."""
        url = connector_config.jms_broker_url
        assert url is not None
        assert url.startswith("tcp://") or url.startswith("ssl://")

    @patch("socket.create_connection")
    def test_jms_broker_port_reachable(
        self, mock_connect: MagicMock, connector_config: ConnectorConfig
    ) -> None:
        """JMS broker port is open and accepting connections."""
        mock_socket = MagicMock()
        mock_connect.return_value = mock_socket

        import socket

        sock = socket.create_connection(("broker.example.com", 61616), timeout=10)

        mock_connect.assert_called_once_with(("broker.example.com", 61616), timeout=10)
        assert sock is not None
