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

    def delete(self, endpoint: str) -> requests.Response:
        """Perform a DELETE request to the Boomi API."""
        url = f"{self.base_url}/{endpoint}"
        return self.session.delete(url, timeout=self.config.timeout)

    def put(self, endpoint: str, data: Optional[dict[str, Any]] = None) -> requests.Response:
        """Perform a PUT request to the Boomi API."""
        url = f"{self.base_url}/{endpoint}"
        return self.session.put(url, json=data, timeout=self.config.timeout)

    def get_audit_log(self, query_filter: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Query the audit log."""
        response = self.post("AuditLog/query", data=query_filter or {})
        response.raise_for_status()
        return response.json()

    # --- Runtime Cloud (PAC) operations ---

    def create_runtime_cloud(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a Private Atom Cloud (PAC) via POST RuntimeCloud."""
        response = self.post("RuntimeCloud", data=payload)
        response.raise_for_status()
        return response.json()

    def update_runtime_cloud(self, cloud_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Update a Private Atom Cloud (PAC) via POST RuntimeCloud/{cloudId}/update."""
        response = self.post(f"RuntimeCloud/{cloud_id}/update", data=payload)
        response.raise_for_status()
        return response.json()

    def delete_runtime_cloud(self, cloud_id: str) -> requests.Response:
        """Delete a Private Atom Cloud (PAC)."""
        response = self.delete(f"RuntimeCloud/{cloud_id}")
        response.raise_for_status()
        return response

    def query_runtime_clouds(
        self, query_filter: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Query runtime clouds."""
        response = self.post("RuntimeCloud/query", data=query_filter or {})
        response.raise_for_status()
        return response.json()

    # --- Atom lifecycle operations ---

    def create_atom(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create an Atom via POST."""
        response = self.post("Atom", data=payload)
        response.raise_for_status()
        return response.json()

    def delete_atom(self, atom_id: str) -> requests.Response:
        """Delete an Atom."""
        response = self.delete(f"Atom/{atom_id}")
        response.raise_for_status()
        return response

    def update_atom(self, atom_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Update Atom properties."""
        response = self.post(f"Atom/{atom_id}/update", data=payload)
        response.raise_for_status()
        return response.json()

    # --- Environment operations ---

    def create_environment(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create an Environment."""
        response = self.post("Environment", data=payload)
        response.raise_for_status()
        return response.json()

    def delete_environment(self, environment_id: str) -> requests.Response:
        """Delete an Environment."""
        response = self.delete(f"Environment/{environment_id}")
        response.raise_for_status()
        return response

    def attach_environment(self, atom_id: str, environment_id: str) -> dict[str, Any]:
        """Attach an Environment to an Atom."""
        payload = {"atomId": atom_id, "environmentId": environment_id}
        response = self.post("EnvironmentAtomAttachment", data=payload)
        response.raise_for_status()
        return response.json()

    def detach_environment(self, attachment_id: str) -> requests.Response:
        """Detach an Environment from an Atom."""
        response = self.delete(f"EnvironmentAtomAttachment/{attachment_id}")
        response.raise_for_status()
        return response

    # --- Package deployment operations ---

    def deploy_package(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Deploy a packaged component."""
        response = self.post("DeployedPackage", data=payload)
        response.raise_for_status()
        return response.json()

    def undeploy_package(self, deployed_package_id: str) -> requests.Response:
        """Undeploy (delete) a deployed package."""
        response = self.delete(f"DeployedPackage/{deployed_package_id}")
        response.raise_for_status()
        return response

    # --- Cloud attachment properties (PAC config) ---

    def update_cloud_attachment_properties(
        self, cloud_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Update AccountCloudAttachmentProperties."""
        response = self.post(
            f"AccountCloudAttachmentProperties/{cloud_id}/update", data=payload
        )
        response.raise_for_status()
        return response.json()

    # --- RBAC / User role operations ---

    def delete_user_role(self, user_id: str, role_id: str) -> requests.Response:
        """Delete a user role mapping."""
        response = self.delete(f"UserRole/{user_id}/{role_id}")
        response.raise_for_status()
        return response

    def query_user_roles(
        self, query_filter: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Query user role mappings."""
        response = self.post("UserRole/query", data=query_filter or {})
        response.raise_for_status()
        return response.json()

    # --- Environment extensions ---

    def update_environment_extensions(
        self, environment_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Update environment extensions (connections/properties)."""
        response = self.post(
            f"EnvironmentExtensions/{environment_id}/update", data=payload
        )
        response.raise_for_status()
        return response.json()

    def get_environment_extensions(self, environment_id: str) -> dict[str, Any]:
        """Get environment extensions."""
        response = self.get(f"EnvironmentExtensions/{environment_id}")
        response.raise_for_status()
        return response.json()
