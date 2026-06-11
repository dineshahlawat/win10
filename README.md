# Boomi Integration Post-Installation Verification (PIV) Test Suite

Comprehensive test cases for verifying a Dell Boomi integration platform deployment after installation. These tests validate connectivity, authentication, process execution, data transformation, error handling, and deployment status.

## Test Categories

| Category | Test ID Prefix | Description |
|----------|---------------|-------------|
| **Connectivity** | PIV-CONN | Atom reachability, API endpoints, connector endpoints |
| **Authentication** | PIV-AUTH | API authentication, token validation, account access |
| **Process Execution** | PIV-EXEC | Process execution, schedules, execution records |
| **Data Transformation** | PIV-DATA | Field mapping, type conversion, batch processing |
| **Error Handling** | PIV-ERR | API errors, connection errors, retry behavior |
| **Deployment** | PIV-DEPLOY | Package deployment, environment config, ID validation |

## Prerequisites

- Python 3.10+
- A Boomi AtomSphere account with API access
- A deployed Atom/Molecule for connectivity tests

## Installation

```bash
pip install -e ".[test]"
```

## Configuration

Set the following environment variables before running integration tests:

```bash
export BOOMI_ATOM_URL="https://your-atom-host:9090"
export BOOMI_ATOM_ID="your-atom-uuid"
export BOOMI_API_BASE_URL="https://api.boomi.com/api/rest/v1"
export BOOMI_ACCOUNT_ID="BOOMI_ACCOUNT-XXXXXX"
export BOOMI_USERNAME="your-email@company.com"
export BOOMI_API_TOKEN="your-api-token"
export BOOMI_ENVIRONMENT="Test"
```

## Running Tests

### Run all unit tests (no live Boomi connection required)
```bash
pytest
```

### Run with coverage report
```bash
pytest --cov=boomi_piv --cov-report=term-missing
```

### Run a specific test category
```bash
pytest boomi_piv/tests/connectivity/
pytest boomi_piv/tests/authentication/
pytest boomi_piv/tests/process_execution/
pytest boomi_piv/tests/data_transformation/
pytest boomi_piv/tests/error_handling/
pytest boomi_piv/tests/deployment/
```

### Run with verbose output
```bash
pytest -v
```

## Project Structure

```
boomi_piv/
├── __init__.py
├── config/
│   ├── __init__.py
│   └── settings.py              # Environment-based configuration
├── utils/
│   ├── __init__.py
│   ├── api_client.py            # Boomi AtomSphere API client
│   ├── atom_health.py           # Atom health check utilities
│   └── validators.py            # Validation helpers
└── tests/
    ├── __init__.py
    ├── conftest.py              # Shared test fixtures
    ├── connectivity/
    │   ├── test_atom_connectivity.py     # PIV-CONN-001 to 004
    │   ├── test_api_connectivity.py      # PIV-CONN-005 to 006
    │   └── test_connector_endpoints.py   # PIV-CONN-010 to 013
    ├── authentication/
    │   └── test_api_authentication.py    # PIV-AUTH-001 to 003
    ├── process_execution/
    │   └── test_process_execution.py     # PIV-EXEC-001 to 004
    ├── data_transformation/
    │   └── test_data_mapping.py          # PIV-DATA-001 to 005
    ├── error_handling/
    │   └── test_error_scenarios.py       # PIV-ERR-001 to 005
    └── deployment/
        └── test_deployment_verification.py  # PIV-DEPLOY-001 to 005
```

## Test Coverage Areas

### PIV-CONN: Connectivity Verification
- Atom shared web server reachability (HTTP health endpoint)
- Atom status parsing (ONLINE/OFFLINE/PAUSED/STOPPED)
- AtomSphere REST API endpoint connectivity
- Connector endpoints (HTTP, SFTP, Database, JMS)

### PIV-AUTH: Authentication Verification
- Basic authentication with username + API token
- Account-level API access
- Token configuration validation (non-empty, HTTPS)

### PIV-EXEC: Process Execution Verification
- Process execution via API
- Execution record retrieval and query
- Execution status validation (COMPLETE, ERROR, ABORTED, etc.)
- Process schedule verification

### PIV-DATA: Data Transformation Verification
- Simple 1:1 field mapping
- Nested field mapping (dot notation)
- Data type conversion (numeric, boolean, float)
- Batch/multi-document processing
- XML to JSON transformation patterns

### PIV-ERR: Error Handling Verification
- HTTP error codes (404, 500, 503, 429)
- Network errors (connection, timeout, SSL)
- Error document tracking in executions
- Retry behavior (transient vs permanent failures)
- Audit log error querying

### PIV-DEPLOY: Deployment Verification
- Atom registration and status in platform
- Deployed package existence and state
- Environment classification validation
- ID format validation (UUID/GUID)
- Timestamp format validation (ISO 8601)
