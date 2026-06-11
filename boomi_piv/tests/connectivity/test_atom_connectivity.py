"""PIV-CONN: Atom Connectivity Verification Tests.

Verifies that the Boomi Atom/Molecule is reachable, responds to health
checks, and that the shared web server is operational after installation.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from boomi_piv.config.settings import BoomiAtomConfig
from boomi_piv.utils.atom_health import (
    AtomHealthResult,
    AtomStatus,
    check_atom_reachability,
    get_atom_version,
    parse_atom_status,
)


class TestAtomReachability:
    """PIV-CONN-001: Atom shared web server reachability."""

    @patch("boomi_piv.utils.atom_health.requests.get")
    def test_atom_reachable_returns_online(
        self, mock_get: MagicMock, atom_config: BoomiAtomConfig
    ) -> None:
        """Atom returns ONLINE when shared web server responds 200."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_get.return_value = mock_response

        result = check_atom_reachability(atom_config)

        assert result.reachable is True
        assert result.status == AtomStatus.ONLINE
        assert result.error is None
        mock_get.assert_called_once_with(
            f"{atom_config.atom_url}/ws/status",
            timeout=10,
            verify=False,
        )

    @patch("boomi_piv.utils.atom_health.requests.get")
    def test_atom_unreachable_returns_offline(
        self, mock_get: MagicMock, atom_config: BoomiAtomConfig
    ) -> None:
        """Atom returns OFFLINE when connection is refused."""
        mock_get.side_effect = requests.ConnectionError("Connection refused")

        result = check_atom_reachability(atom_config)

        assert result.reachable is False
        assert result.status == AtomStatus.OFFLINE
        assert "Connection failed" in (result.error or "")

    @patch("boomi_piv.utils.atom_health.requests.get")
    def test_atom_timeout_returns_unknown(
        self, mock_get: MagicMock, atom_config: BoomiAtomConfig
    ) -> None:
        """Atom returns UNKNOWN when connection times out."""
        mock_get.side_effect = requests.Timeout("Connection timed out")

        result = check_atom_reachability(atom_config)

        assert result.reachable is False
        assert result.status == AtomStatus.UNKNOWN
        assert "timed out" in (result.error or "")

    @patch("boomi_piv.utils.atom_health.requests.get")
    def test_atom_unexpected_status_code(
        self, mock_get: MagicMock, atom_config: BoomiAtomConfig
    ) -> None:
        """Atom returns UNKNOWN when HTTP status is not 200."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_get.return_value = mock_response

        result = check_atom_reachability(atom_config)

        assert result.reachable is True
        assert result.status == AtomStatus.UNKNOWN
        assert "503" in (result.error or "")

    @patch("boomi_piv.utils.atom_health.requests.get")
    def test_atom_reachability_custom_timeout(
        self, mock_get: MagicMock, atom_config: BoomiAtomConfig
    ) -> None:
        """Custom timeout value is passed through to the request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        check_atom_reachability(atom_config, timeout=60)

        mock_get.assert_called_once_with(
            f"{atom_config.atom_url}/ws/status",
            timeout=60,
            verify=False,
        )


class TestAtomStatusParsing:
    """PIV-CONN-002: Atom status parsing from API responses."""

    @pytest.mark.parametrize(
        "status_str,expected",
        [
            ("ONLINE", AtomStatus.ONLINE),
            ("OFFLINE", AtomStatus.OFFLINE),
            ("PAUSED", AtomStatus.PAUSED),
            ("STOPPED", AtomStatus.STOPPED),
            ("DELETED", AtomStatus.DELETED),
            ("online", AtomStatus.ONLINE),
        ],
    )
    def test_parse_known_statuses(
        self, status_str: str, expected: AtomStatus
    ) -> None:
        """Known status strings are parsed correctly."""
        response = {"status": status_str}
        assert parse_atom_status(response) == expected

    def test_parse_unknown_status(self) -> None:
        """Unknown status strings return UNKNOWN."""
        response = {"status": "MAINTENANCE"}
        assert parse_atom_status(response) == AtomStatus.UNKNOWN

    def test_parse_empty_status(self) -> None:
        """Empty status field returns UNKNOWN."""
        response = {"status": ""}
        assert parse_atom_status(response) == AtomStatus.UNKNOWN

    def test_parse_missing_status(self) -> None:
        """Missing status field returns UNKNOWN."""
        response = {"name": "TestAtom"}
        assert parse_atom_status(response) == AtomStatus.UNKNOWN


class TestAtomVersion:
    """PIV-CONN-003: Atom version extraction from API responses."""

    def test_get_version_present(self, sample_atom_response: dict) -> None:
        """Version is extracted when present."""
        version = get_atom_version(sample_atom_response)
        assert version == "24.01.1234"

    def test_get_version_missing(self) -> None:
        """None returned when version field is missing."""
        response = {"atomId": "test-id"}
        assert get_atom_version(response) is None


class TestAtomHealthResult:
    """PIV-CONN-004: AtomHealthResult data structure validation."""

    def test_health_result_online(self) -> None:
        """Online health result has correct attributes."""
        result = AtomHealthResult(
            status=AtomStatus.ONLINE,
            reachable=True,
            version="24.01.1234",
        )
        assert result.status == AtomStatus.ONLINE
        assert result.reachable is True
        assert result.version == "24.01.1234"
        assert result.error is None

    def test_health_result_offline_with_error(self) -> None:
        """Offline health result stores error message."""
        result = AtomHealthResult(
            status=AtomStatus.OFFLINE,
            reachable=False,
            error="Connection refused",
        )
        assert result.status == AtomStatus.OFFLINE
        assert result.reachable is False
        assert result.error == "Connection refused"
