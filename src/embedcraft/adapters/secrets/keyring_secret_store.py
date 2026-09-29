"""Keyring-based secret store implementation targeting Windows Credential Manager."""

from __future__ import annotations

import keyring

from embedcraft.infrastructure.logging import logger

SERVICE_NAME = "EmbedCraft_RAG_Studio"


class KeyringSecretStore:
    def __init__(self, service_name: str = SERVICE_NAME):
        self.service_name = service_name
        self._memory_fallback: dict[str, str] = {}

    def get_secret(self, key: str) -> str | None:
        try:
            val = keyring.get_password(self.service_name, key)
            if val is not None:
                return val
        except Exception as e:  # noqa: BLE001
            logger.warning("keyring_get_failed_fallback_to_memory", key=key, error=str(e))
        return self._memory_fallback.get(key)

    def set_secret(self, key: str, value: str) -> None:
        try:
            keyring.set_password(self.service_name, key, value)
        except Exception as e:  # noqa: BLE001
            logger.warning("keyring_set_failed_fallback_to_memory", key=key, error=str(e))
            self._memory_fallback[key] = value

    def delete_secret(self, key: str) -> bool:
        deleted = False
        try:
            keyring.delete_password(self.service_name, key)
            deleted = True
        except Exception:  # noqa: BLE001, S110
            pass
        if key in self._memory_fallback:
            del self._memory_fallback[key]
            deleted = True
        return deleted
