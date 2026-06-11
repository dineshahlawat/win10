"""PIV-EXEC: Process Execution Verification Tests.

Verifies that Boomi processes can be executed, monitored, and
that execution records are properly generated after installation.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from boomi_piv.config.settings import BoomiAPIConfig
from boomi_piv.utils.api_client import BoomiAPIClient
from boomi_piv.utils.validators import validate_execution_status


class TestProcessExecution:
    """PIV-EXEC-001: Process execution via AtomSphere API."""

    @patch("requests.Session.post")
    def test_execute_process_success(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Process execution returns a valid execution ID."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "requestId": "req-1234-5678",
            "processId": "proc-1234-5678",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.execute_process(
            atom_id="12345678-1234-1234-1234-123456789abc",
            process_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        )

        assert "requestId" in result
        assert result["requestId"] == "req-1234-5678"

    @patch("requests.Session.post")
    def test_execute_process_invalid_atom(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Execution on invalid Atom ID raises HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_post.return_value = mock_response

        with pytest.raises(requests.HTTPError):
            api_client.execute_process(
                atom_id="invalid-atom-id",
                process_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            )

    @patch("requests.Session.post")
    def test_execute_process_sends_correct_payload(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Process execution sends atomId and processId in payload."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"requestId": "req-001"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        api_client.execute_process(
            atom_id="atom-id-123",
            process_id="process-id-456",
        )

        call_kwargs = mock_post.call_args
        payload = call_kwargs[1]["json"] if "json" in call_kwargs[1] else call_kwargs[1].get("data")
        assert payload == {"atomId": "atom-id-123", "processId": "process-id-456"}


class TestExecutionRecordRetrieval:
    """PIV-EXEC-002: Execution record query and retrieval."""

    @patch("requests.Session.get")
    def test_get_execution_record(
        self, mock_get: MagicMock, api_client: BoomiAPIClient, sample_execution_response: dict
    ) -> None:
        """Execution record is retrieved by ID."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_execution_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = api_client.get_execution_record("execution-1234-5678-abcd")

        assert result["executionId"] == "execution-1234-5678-abcd"
        assert result["status"] == "COMPLETE"

    @patch("requests.Session.post")
    def test_query_execution_records_with_filter(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Execution records can be queried with filters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "numberOfResults": 5,
            "result": [
                {"executionId": f"exec-{i}", "status": "COMPLETE"}
                for i in range(5)
            ],
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        query_filter = {
            "QueryFilter": {
                "expression": {
                    "operator": "and",
                    "nestedExpression": [
                        {
                            "argument": ["12345678-1234-1234-1234-123456789abc"],
                            "operator": "EQUALS",
                            "property": "atomId",
                        }
                    ],
                }
            }
        }

        result = api_client.query_execution_records(query_filter)

        assert result["numberOfResults"] == 5
        assert len(result["result"]) == 5


class TestExecutionStatusValidation:
    """PIV-EXEC-003: Execution status validation."""

    @pytest.mark.parametrize(
        "status,is_valid",
        [
            ("COMPLETE", True),
            ("COMPLETE_WARN", True),
            ("ERROR", True),
            ("ABORTED", True),
            ("DISCARDED", True),
            ("INPROCESS", True),
            ("STARTED", True),
            ("INVALID_STATUS", False),
            ("", False),
            ("running", False),
        ],
    )
    def test_execution_status_validation(self, status: str, is_valid: bool) -> None:
        """Known execution statuses are validated correctly."""
        assert validate_execution_status(status) == is_valid

    def test_execution_response_has_required_fields(
        self, sample_execution_response: dict
    ) -> None:
        """Execution response contains all required fields."""
        required_fields = [
            "executionId",
            "processId",
            "processName",
            "atomId",
            "status",
            "executionTime",
        ]
        for field in required_fields:
            assert field in sample_execution_response, f"Missing field: {field}"

    def test_execution_response_document_counts(
        self, sample_execution_response: dict
    ) -> None:
        """Execution response has valid document counts."""
        assert sample_execution_response["inboundDocumentCount"] >= 0
        assert sample_execution_response["outboundDocumentCount"] >= 0
        assert sample_execution_response["inboundErrorDocumentCount"] >= 0
        assert sample_execution_response["outboundErrorDocumentCount"] >= 0

    def test_execution_no_error_documents_on_success(
        self, sample_execution_response: dict
    ) -> None:
        """Successful execution has zero error documents."""
        assert sample_execution_response["status"] == "COMPLETE"
        assert sample_execution_response["inboundErrorDocumentCount"] == 0
        assert sample_execution_response["outboundErrorDocumentCount"] == 0


class TestProcessScheduleVerification:
    """PIV-EXEC-004: Process schedule verification."""

    @patch("requests.Session.post")
    def test_query_process_schedules(
        self, mock_post: MagicMock, api_client: BoomiAPIClient
    ) -> None:
        """Process schedules can be queried via the API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "numberOfResults": 2,
            "result": [
                {
                    "scheduleId": "sched-001",
                    "processId": "proc-001",
                    "atomId": "atom-001",
                    "enabled": True,
                },
                {
                    "scheduleId": "sched-002",
                    "processId": "proc-002",
                    "atomId": "atom-001",
                    "enabled": False,
                },
            ],
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = api_client.query_process_schedules()

        assert result["numberOfResults"] == 2
        enabled_schedules = [s for s in result["result"] if s["enabled"]]
        assert len(enabled_schedules) == 1
