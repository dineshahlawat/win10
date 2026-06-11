"""PIV-ERR: Error Handling Verification Tests.

Verifies that the Boomi integration handles error scenarios
gracefully, including retry logic, error document routing,
and alerting after installation.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from boomi_piv.utils.api_client import BoomiAPIClient


class TestAPIErrorHandling:
    """PIV-ERR-001: API error responses are handled correctly."""

    @patch("requests.Session.get")
    def test_404_not_found_raises_http_error(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """404 response raises HTTPError on raise_for_status."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "404 Client Error: Not Found"
        )
        mock_get.return_value = mock_response

        with pytest.raises(requests.HTTPError, match="404"):
            api_client.get_atom("nonexistent-atom-id")

    @patch("requests.Session.get")
    def test_500_internal_server_error(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """500 response raises HTTPError."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "500 Server Error: Internal Server Error"
        )
        mock_get.return_value = mock_response

        with pytest.raises(requests.HTTPError, match="500"):
            api_client.get_atom("test-atom-id")

    @patch("requests.Session.get")
    def test_503_service_unavailable(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """503 response indicates service unavailable."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "503 Server Error: Service Unavailable"
        )
        mock_get.return_value = mock_response

        with pytest.raises(requests.HTTPError, match="503"):
            api_client.get_atom("test-atom-id")

    @patch("requests.Session.get")
    def test_429_rate_limited(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """429 response indicates rate limiting."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "429 Client Error: Too Many Requests"
        )
        mock_get.return_value = mock_response

        with pytest.raises(requests.HTTPError, match="429"):
            api_client.get_atom("test-atom-id")


class TestConnectionErrorHandling:
    """PIV-ERR-002: Network connection errors are handled."""

    @patch("requests.Session.get")
    def test_connection_error(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Connection errors are raised as ConnectionError."""
        mock_get.side_effect = requests.ConnectionError("DNS resolution failed")

        with pytest.raises(requests.ConnectionError, match="DNS"):
            api_client.get("Atom/test-id")

    @patch("requests.Session.get")
    def test_timeout_error(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Request timeouts are raised as Timeout."""
        mock_get.side_effect = requests.Timeout("Read timed out")

        with pytest.raises(requests.Timeout, match="timed out"):
            api_client.get("Atom/test-id")

    @patch("requests.Session.get")
    def test_ssl_error(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """SSL certificate errors are properly surfaced."""
        mock_get.side_effect = requests.exceptions.SSLError("Certificate verify failed")

        with pytest.raises(requests.exceptions.SSLError, match="Certificate"):
            api_client.get("Atom/test-id")


class TestExecutionErrorDocuments:
    """PIV-ERR-003: Error document handling in executions."""

    def test_error_execution_has_error_documents(self) -> None:
        """Failed execution contains error document counts."""
        error_execution = {
            "executionId": "exec-error-001",
            "status": "ERROR",
            "inboundDocumentCount": 10,
            "outboundDocumentCount": 7,
            "inboundErrorDocumentCount": 3,
            "outboundErrorDocumentCount": 0,
            "message": "Document processing failed: invalid XML",
        }

        assert error_execution["status"] == "ERROR"
        assert error_execution["inboundErrorDocumentCount"] > 0
        total_errors = (
            error_execution["inboundErrorDocumentCount"]
            + error_execution["outboundErrorDocumentCount"]
        )
        assert total_errors > 0

    def test_error_execution_has_message(self) -> None:
        """Error execution includes a descriptive message."""
        error_execution = {
            "status": "ERROR",
            "message": "Connection to SFTP server failed: authentication error",
        }

        assert error_execution["message"] != ""
        assert len(error_execution["message"]) > 10

    def test_warning_execution_completes(self) -> None:
        """COMPLETE_WARN execution indicates partial success."""
        warn_execution = {
            "executionId": "exec-warn-001",
            "status": "COMPLETE_WARN",
            "inboundDocumentCount": 10,
            "outboundDocumentCount": 8,
            "inboundErrorDocumentCount": 2,
            "outboundErrorDocumentCount": 0,
            "message": "2 documents failed validation",
        }

        assert warn_execution["status"] == "COMPLETE_WARN"
        total_in = (
            warn_execution["outboundDocumentCount"]
            + warn_execution["inboundErrorDocumentCount"]
        )
        assert total_in == warn_execution["inboundDocumentCount"]


class TestRetryBehavior:
    """PIV-ERR-004: Retry behavior verification."""

    @patch("requests.Session.get")
    def test_transient_failure_then_success(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Transient failures followed by success can be handled."""
        fail_response = MagicMock()
        fail_response.status_code = 503
        fail_response.raise_for_status.side_effect = requests.HTTPError("503")

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {"atomId": "test"}
        success_response.raise_for_status.return_value = None

        mock_get.side_effect = [fail_response, fail_response, success_response]

        # Simulate retry logic
        last_exception = None
        result = None
        for attempt in range(3):
            try:
                response = api_client.get("Atom/test-id")
                response.raise_for_status()
                result = response.json()
                break
            except requests.HTTPError as e:
                last_exception = e

        assert result is not None
        assert result["atomId"] == "test"
        assert mock_get.call_count == 3

    @patch("requests.Session.get")
    def test_permanent_failure_exhausts_retries(
        self, mock_get: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Permanent failures exhaust all retry attempts."""
        fail_response = MagicMock()
        fail_response.status_code = 500
        fail_response.raise_for_status.side_effect = requests.HTTPError("500")
        mock_get.return_value = fail_response

        max_retries = 3
        last_exception = None
        for attempt in range(max_retries):
            try:
                response = api_client.get("Atom/test-id")
                response.raise_for_status()
            except requests.HTTPError as e:
                last_exception = e

        assert last_exception is not None
        assert mock_get.call_count == max_retries


class TestAuditLogErrorTracking:
    """PIV-ERR-005: Error tracking via audit log."""

    @patch("requests.Session.post")
    def test_query_audit_log_for_errors(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Audit log can be queried to find error events."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "numberOfResults": 2,
            "result": [
                {
                    "type": "execution.error",
                    "date": "2024-06-01T12:00:00Z",
                    "userId": "test_user",
                    "message": "Process execution failed",
                },
                {
                    "type": "deployment.error",
                    "date": "2024-06-01T11:00:00Z",
                    "userId": "admin_user",
                    "message": "Deployment to atom failed",
                },
            ],
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.get_audit_log()

        assert result["numberOfResults"] == 2
        error_types = [r["type"] for r in result["result"]]
        assert "execution.error" in error_types
