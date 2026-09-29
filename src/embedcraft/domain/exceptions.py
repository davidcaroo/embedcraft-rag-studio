"""Domain exceptions for EmbedCraft RAG Studio.

Standardized error reporting with error codes, human messages, technical details,
recommended user actions, correlation IDs, and retryability.
"""

from __future__ import annotations

import uuid


class EmbedCraftError(Exception):
    """Base exception for all EmbedCraft errors."""

    def __init__(
        self,
        code: str,
        message: str,
        technical_detail: str | None = None,
        recommended_action: str | None = None,
        correlation_id: str | None = None,
        retryable: bool = False,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.technical_detail = technical_detail or ""
        self.recommended_action = recommended_action or "Revise los registros para más detalles."
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.retryable = retryable

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "technical_detail": self.technical_detail,
            "recommended_action": self.recommended_action,
            "correlation_id": self.correlation_id,
            "retryable": self.retryable,
        }


class ConfigurationError(EmbedCraftError):
    """Configuration related errors."""

    def __init__(self, message: str, technical_detail: str | None = None, **kwargs):
        super().__init__(
            code="ERR_CONFIG",
            message=message,
            technical_detail=technical_detail,
            recommended_action="Compruebe los parámetros de configuración en el archivo o la interfaz.",
            retryable=False,
            **kwargs,
        )


class DocumentError(EmbedCraftError):
    """Document extraction, parsing or format error."""

    def __init__(self, message: str, technical_detail: str | None = None, **kwargs):
        super().__init__(
            code="ERR_DOCUMENT",
            message=message,
            technical_detail=technical_detail,
            recommended_action="Verifique la integridad del archivo o su formato.",
            retryable=False,
            **kwargs,
        )


class ModelError(EmbedCraftError):
    """Model download, loading or inference error."""

    def __init__(self, message: str, technical_detail: str | None = None, retryable: bool = True, **kwargs):
        super().__init__(
            code="ERR_MODEL",
            message=message,
            technical_detail=technical_detail,
            recommended_action="Verifique que el modelo esté descargado o que Ollama/API esté activo.",
            retryable=retryable,
            **kwargs,
        )


class NetworkError(EmbedCraftError):
    """Network connection failure."""

    def __init__(self, message: str, technical_detail: str | None = None, **kwargs):
        super().__init__(
            code="ERR_NETWORK",
            message=message,
            technical_detail=technical_detail,
            recommended_action="Compruebe su conexión a Internet o el estado del servidor remoto.",
            retryable=True,
            **kwargs,
        )


class ProviderError(EmbedCraftError):
    """External provider authentication or execution error."""

    def __init__(self, message: str, technical_detail: str | None = None, **kwargs):
        super().__init__(
            code="ERR_PROVIDER",
            message=message,
            technical_detail=technical_detail,
            recommended_action="Verifique las credenciales del proveedor y sus límites de cuota.",
            retryable=False,
            **kwargs,
        )


class VectorStoreError(EmbedCraftError):
    """Vector database operations error."""

    def __init__(self, message: str, technical_detail: str | None = None, **kwargs):
        super().__init__(
            code="ERR_VECTOR_STORE",
            message=message,
            technical_detail=technical_detail,
            recommended_action="Compruebe los permisos en el directorio de índices o la conexión a la base vectorial.",
            retryable=False,
            **kwargs,
        )


class CompatibilityError(EmbedCraftError):
    """Incompatible versions, dimensions or models."""

    def __init__(self, message: str, technical_detail: str | None = None, **kwargs):
        super().__init__(
            code="ERR_COMPATIBILITY",
            message=message,
            technical_detail=technical_detail,
            recommended_action="Asegúrese de usar dimensiones de embeddings y modelos compatibles.",
            retryable=False,
            **kwargs,
        )


class IntegrityError(EmbedCraftError):
    """Checksum or validation error."""

    def __init__(self, message: str, technical_detail: str | None = None, **kwargs):
        super().__init__(
            code="ERR_INTEGRITY",
            message=message,
            technical_detail=technical_detail,
            recommended_action="El paquete o archivo parece estar corrupto. Vuelva a descargarlo o exportarlo.",
            retryable=False,
            **kwargs,
        )


class ExportError(EmbedCraftError):
    """Package export or import failure."""

    def __init__(self, message: str, technical_detail: str | None = None, **kwargs):
        super().__init__(
            code="ERR_EXPORT",
            message=message,
            technical_detail=technical_detail,
            recommended_action="Verifique espacio en disco y permisos de escritura en la ruta de destino.",
            retryable=False,
            **kwargs,
        )


class InternalError(EmbedCraftError):
    """Unexpected internal error."""

    def __init__(self, message: str, technical_detail: str | None = None, **kwargs):
        super().__init__(
            code="ERR_INTERNAL",
            message=message,
            technical_detail=technical_detail,
            recommended_action="Contacte al soporte técnico con el identificador de correlación.",
            retryable=False,
            **kwargs,
        )
