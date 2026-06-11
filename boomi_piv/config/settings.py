"""Configuration settings for Boomi PIV tests.

All sensitive values should be provided via environment variables.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BoomiAtomConfig:
    """Configuration for a Boomi Atom/Molecule instance."""

    atom_url: str = field(
        default_factory=lambda: os.getenv("BOOMI_ATOM_URL", "https://localhost:9090")
    )
    atom_id: str = field(
        default_factory=lambda: os.getenv("BOOMI_ATOM_ID", "")
    )
    environment: str = field(
        default_factory=lambda: os.getenv("BOOMI_ENVIRONMENT", "Test")
    )
    classification: str = field(
        default_factory=lambda: os.getenv("BOOMI_CLASSIFICATION", "Test")
    )


@dataclass
class BoomiAPIConfig:
    """Configuration for Boomi AtomSphere API access."""

    base_url: str = field(
        default_factory=lambda: os.getenv(
            "BOOMI_API_BASE_URL", "https://api.boomi.com/api/rest/v1"
        )
    )
    account_id: str = field(
        default_factory=lambda: os.getenv("BOOMI_ACCOUNT_ID", "")
    )
    username: str = field(
        default_factory=lambda: os.getenv("BOOMI_USERNAME", "")
    )
    api_token: str = field(
        default_factory=lambda: os.getenv("BOOMI_API_TOKEN", "")
    )
    timeout: int = field(
        default_factory=lambda: int(os.getenv("BOOMI_API_TIMEOUT", "30"))
    )


@dataclass
class ConnectorConfig:
    """Configuration for connector-specific verification."""

    database_url: Optional[str] = field(
        default_factory=lambda: os.getenv("BOOMI_DB_URL")
    )
    sftp_host: Optional[str] = field(
        default_factory=lambda: os.getenv("BOOMI_SFTP_HOST")
    )
    sftp_port: int = field(
        default_factory=lambda: int(os.getenv("BOOMI_SFTP_PORT", "22"))
    )
    http_endpoint: Optional[str] = field(
        default_factory=lambda: os.getenv("BOOMI_HTTP_ENDPOINT")
    )
    jms_broker_url: Optional[str] = field(
        default_factory=lambda: os.getenv("BOOMI_JMS_BROKER_URL")
    )


@dataclass
class PIVConfig:
    """Top-level configuration for all PIV tests."""

    atom: BoomiAtomConfig = field(default_factory=BoomiAtomConfig)
    api: BoomiAPIConfig = field(default_factory=BoomiAPIConfig)
    connectors: ConnectorConfig = field(default_factory=ConnectorConfig)
    retry_attempts: int = field(
        default_factory=lambda: int(os.getenv("BOOMI_RETRY_ATTEMPTS", "3"))
    )
    retry_delay_seconds: float = field(
        default_factory=lambda: float(os.getenv("BOOMI_RETRY_DELAY", "5.0"))
    )


def load_config() -> PIVConfig:
    """Load PIV configuration from environment variables."""
    return PIVConfig()
