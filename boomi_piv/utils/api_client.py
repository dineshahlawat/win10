"""Boomi AtomSphere API client for PIV tests."""

from typing import Any, Optional

import requests
from requests.auth import HTTPBasicAuth

from boomi_piv.config.settings import BoomiAPIConfig


class BoomiAPIClient:
    """Client for interacting with the Boomi AtomSphere API."""

    def __init__(self, config: BoomiAPIConfig) -> None:
        self.config = config
        self.base_url = f"{config.base_url}/{config.account_id}"
        self.auth = HTTPBasicAuth(config.username, config.api_token)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

    def get(self, endpoint: str, params: Optional[dict[str, Any]] = None) -> requests.Response:
        """Perform a GET request to the Boomi API."""
        url = f"{self.base_url}/{endpoint}"
        return self.session.get(url, params=params, timeout=self.config.timeout)

    def post(self, endpoint: str, data: Optional[dict[str, Any]] = None) -> requests.Response:
        """Perform a POST request to the Boomi API."""
        url = f"{self.base_url}/{endpoint}"
        return self.session.post(url, json=data, timeout=self.config.timeout)

    def get_atom(self, atom_id: str) -> dict[str, Any]:
        """Retrieve Atom details by ID."""
        response = self.get(f"Atom/{atom_id}")
        response.raise_for_status()
        return response.json()

    def query_atoms(self, query_filter: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Query Atoms with optional filters."""
        response = self.post("Atom/query", data=query_filter or {})
        response.raise_for_status()
        return response.json()

    def get_environment(self, environment_id: str) -> dict[str, Any]:
        """Retrieve Environment details by ID."""
        response = self.get(f"Environment/{environment_id}")
        response.raise_for_status()
        return response.json()

    def query_process_schedules(
        self, query_filter: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Query process schedules."""
        response = self.post("ProcessSchedules/query", data=query_filter or {})
        response.raise_for_status()
        return response.json()

    def get_execution_record(self, execution_id: str) -> dict[str, Any]:
        """Retrieve an execution record by ID."""
        response = self.get(f"ExecutionRecord/{execution_id}")
        response.raise_for_status()
        return response.json()

    def query_execution_records(
        self, query_filter: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Query execution records with optional filters."""
        response = self.post("ExecutionRecord/query", data=query_filter or {})
        response.raise_for_status()
        return response.json()

    def execute_process(self, atom_id: str, process_id: str) -> dict[str, Any]:
        """Execute a process on a specific Atom."""
        payload = {"atomId": atom_id, "processId": process_id}
        response = self.post("executeProcess", data=payload)
        response.raise_for_status()
        return response.json()

    def get_deployed_package(self, deployed_package_id: str) -> dict[str, Any]:
        """Retrieve a deployed package by ID."""
        response = self.get(f"DeployedPackage/{deployed_package_id}")
        response.raise_for_status()
        return response.json()

    def query_deployed_packages(
        self, query_filter: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Query deployed packages."""
        response = self.post("DeployedPackage/query", data=query_filter or {})
        response.raise_for_status()
        return response.json()

    def get_audit_log(self, query_filter: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Query the audit log."""
        response = self.post("AuditLog/query", data=query_filter or {})
        response.raise_for_status()
        return response.json()
