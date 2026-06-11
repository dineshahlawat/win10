"""Utilities for checking Boomi Atom health and status."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import requests

from boomi_piv.config.settings import BoomiAtomConfig


class AtomStatus(Enum):
    """Possible Atom runtime statuses."""

    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    DELETED = "DELETED"
    UNKNOWN = "UNKNOWN"


@dataclass
class AtomHealthResult:
    """Result of an Atom health check."""

    status: AtomStatus
    reachable: bool
    version: Optional[str] = None
    uptime_ms: Optional[int] = None
    error: Optional[str] = None
    raw_response: Optional[dict[str, Any]] = None


def check_atom_reachability(config: BoomiAtomConfig, timeout: int = 10) -> AtomHealthResult:
    """Check if the Atom's shared web server is reachable."""
    try:
        response = requests.get(
            f"{config.atom_url}/ws/status",
            timeout=timeout,
            verify=False,
        )
        if response.status_code == 200:
            return AtomHealthResult(
                status=AtomStatus.ONLINE,
                reachable=True,
                raw_response=_try_parse_json(response),
            )
        return AtomHealthResult(
            status=AtomStatus.UNKNOWN,
            reachable=True,
            error=f"Unexpected status code: {response.status_code}",
        )
    except requests.ConnectionError as e:
        return AtomHealthResult(
            status=AtomStatus.OFFLINE,
            reachable=False,
            error=f"Connection failed: {e}",
        )
    except requests.Timeout:
        return AtomHealthResult(
            status=AtomStatus.UNKNOWN,
            reachable=False,
            error="Connection timed out",
        )


def parse_atom_status(api_response: dict[str, Any]) -> AtomStatus:
    """Parse the Atom status from an API response."""
    status_str = api_response.get("status", "").upper()
    try:
        return AtomStatus(status_str)
    except ValueError:
        return AtomStatus.UNKNOWN


def get_atom_version(api_response: dict[str, Any]) -> Optional[str]:
    """Extract the Atom version from an API response."""
    return api_response.get("currentVersion")


def _try_parse_json(response: requests.Response) -> Optional[dict[str, Any]]:
    """Attempt to parse response body as JSON."""
    try:
        return response.json()
    except (ValueError, AttributeError):
        return None
