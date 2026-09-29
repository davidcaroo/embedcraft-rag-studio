"""Port for secure credential storage."""

from typing import Protocol


class SecretStore(Protocol):
    """Protocol for secure storage of credentials (e.g. Windows Credential Manager / Keyring)."""

    def get_secret(self, key: str) -> str | None:
        """Retrieve a secret by its reference key."""
        ...

    def set_secret(self, key: str, value: str) -> None:
        """Store a secret securely under a reference key."""
        ...

    def delete_secret(self, key: str) -> bool:
        """Delete a stored secret."""
        ...
