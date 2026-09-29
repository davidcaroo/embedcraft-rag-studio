"""Sentence Transformers embedding provider with on-demand model download and cache directory support."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from embedcraft.domain.exceptions import ModelError
from embedcraft.infrastructure.logging import logger
from embedcraft.infrastructure.settings import settings


class SentenceTransformerProvider:
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        cache_dir: Path | None = None,
        device: str = "cpu",
    ):
        self._model_name = model_name
        self.cache_dir = cache_dir or settings.models_cache_dir
        self.device = device
        self._model = None
        self._dimension = 384  # default for all-MiniLM-L6-v2

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    def _load_model(self):
        if self._model is not None:
            return self._model

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise ModelError(
                message="El paquete 'sentence-transformers' no está instalado.",
                technical_detail=str(e),
                recommended_action="Instale las dependencias de IA ejecutando: pip install -e .[ai]",
            ) from e

        try:
            logger.info("loading_embedding_model", model=self._model_name, cache_dir=str(self.cache_dir))
            self._model = SentenceTransformer(
                self._model_name,
                cache_folder=str(self.cache_dir),
                device=self.device,
            )
            # Retrieve actual dimension from model
            self._dimension = self._model.get_sentence_embedding_dimension()
            return self._model
        except Exception as e:
            raise ModelError(
                message=f"No se pudo cargar o descargar el modelo de embeddings: {self._model_name}",
                technical_detail=str(e),
                recommended_action="Verifique la conexión a Internet o importe el modelo manualmente a la carpeta de caché.",
            ) from e

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        model = self._load_model()
        try:
            embeddings = model.encode(
                list(texts),
                batch_size=32,
                show_progress_bar=False,
                normalize_embeddings=True,
            )
            return embeddings.tolist()
        except Exception as e:
            raise ModelError(
                message=f"Error durante la inferencia de embeddings con el modelo {self._model_name}.",
                technical_detail=str(e),
            ) from e

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]
