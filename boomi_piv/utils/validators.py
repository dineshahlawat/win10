"""Validation utilities for Boomi PIV test assertions."""

import re
from datetime import datetime, timezone
from typing import Any, Optional


def validate_atom_id(atom_id: str) -> bool:
    """Validate the format of a Boomi Atom ID (UUID-like or GUID)."""
    pattern = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    return bool(re.match(pattern, atom_id))


def validate_process_id(process_id: str) -> bool:
    """Validate the format of a Boomi Process ID."""
    pattern = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    return bool(re.match(pattern, process_id))


def validate_url(url: str) -> bool:
    """Validate that a string is a well-formed URL."""
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, url))


def validate_iso_timestamp(timestamp: str) -> bool:
    """Validate that a string is a valid ISO 8601 timestamp."""
    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return True
    except (ValueError, AttributeError):
        return False


def validate_execution_status(status: str) -> bool:
    """Check if the execution status is a recognized Boomi status."""
    valid_statuses = {
        "COMPLETE",
        "COMPLETE_WARN",
        "ERROR",
        "ABORTED",
        "DISCARDED",
        "INPROCESS",
        "STARTED",
    }
    return status.upper() in valid_statuses


def validate_connector_type(connector_type: str) -> bool:
    """Check if the connector type is a recognized Boomi connector."""
    known_connectors = {
        "HTTP",
        "HTTPS",
        "FTP",
        "SFTP",
        "DATABASE",
        "DISK",
        "MAIL",
        "JMS",
        "AS2",
        "SALESFORCE",
        "SAP",
        "NETSUITE",
        "SUCCESSFACTORS",
        "SERVICENOW",
        "WORKDAY",
        "DYNAMICSCRMOL",
        "AMAZONS3",
        "AZUREBLOB",
        "GCPSTORAGE",
        "KAFKA",
        "RABBITMQ",
    }
    return connector_type.upper() in known_connectors


def validate_deployment_response(response: dict[str, Any]) -> list[str]:
    """Validate a deployment API response and return a list of issues found."""
    issues: list[str] = []

    required_fields = ["deploymentId", "packageId", "environmentId", "componentId"]
    for field_name in required_fields:
        if field_name not in response:
            issues.append(f"Missing required field: {field_name}")

    if "deploymentId" in response and not response["deploymentId"]:
        issues.append("Empty deploymentId")

    if "version" in response:
        version = response["version"]
        if not isinstance(version, (int, float)):
            issues.append(f"Invalid version type: {type(version).__name__}")

    return issues


def validate_environment_classification(classification: str) -> bool:
    """Check if the environment classification is valid."""
    valid_classifications = {"TEST", "PRODUCTION", "STAGING", "DEVELOPMENT"}
    return classification.upper() in valid_classifications


def is_timestamp_recent(
    timestamp: str, max_age_seconds: int = 3600
) -> bool:
    """Check if a timestamp is within the specified age window."""
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age = (now - dt).total_seconds()
        return 0 <= age <= max_age_seconds
    except (ValueError, AttributeError):
        return False


def validate_map_function_output(
    input_data: dict[str, Any],
    output_data: dict[str, Any],
    expected_mappings: dict[str, str],
) -> list[str]:
    """Validate that a Boomi map function produced correct field mappings.

    expected_mappings maps source field names to target field names.
    Returns a list of discrepancies found.
    """
    issues: list[str] = []

    for source_field, target_field in expected_mappings.items():
        source_value = _get_nested_value(input_data, source_field)
        target_value = _get_nested_value(output_data, target_field)

        if source_value is None and target_value is None:
            continue

        if source_value is not None and target_value is None:
            issues.append(
                f"Source field '{source_field}' has value but target "
                f"field '{target_field}' is missing"
            )
        elif str(source_value) != str(target_value):
            issues.append(
                f"Mapping mismatch: {source_field}='{source_value}' "
                f"!= {target_field}='{target_value}'"
            )

    return issues


def _get_nested_value(data: dict[str, Any], dotted_key: str) -> Optional[Any]:
    """Get a value from a nested dict using dot notation."""
    keys = dotted_key.split(".")
    current: Any = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current
