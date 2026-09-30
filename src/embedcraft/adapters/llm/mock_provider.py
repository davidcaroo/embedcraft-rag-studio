"""Mock LLM provider for deterministic offline testing and verification."""

from __future__ import annotations

import re
import time

from embedcraft.ports.llm import LLMProvider, LLMResponse


class MockLLMProvider(LLMProvider):
    """Deterministic LLM simulator enforcing strict context grounding."""

    def __init__(self, model_name: str = "mock-gpt-4o"):
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        start_time = time.perf_counter()

        # Check for context presence
        if "NO_CONTEXT_FOUND" in prompt or "CONTEXTO PROPORCIONADO:" not in prompt:
            content = "No cuento con evidencia suficiente en los documentos del proyecto para responder a esta pregunta."
        else:
            # Extract snippet from prompt context to synthesize answer
            context_part = prompt.split("CONTEXTO PROPORCIONADO:")[1].split("PREGUNTA:")[0].strip()
            if not context_part:
                content = "No cuento con evidencia suficiente en los documentos del proyecto para responder a esta pregunta."
            else:
                clean_context = re.sub(r"<[^>]+>", "", context_part)
                lines = [
                    ln.strip()
                    for ln in clean_context.splitlines()
                    if ln.strip() and not ln.startswith("[") and not ln.startswith("<")
                ]
                summary = " ".join(lines[:3]) if lines else "Información extraída de las fuentes del proyecto."
                content = f"Basado en los documentos indexados, {summary} [1]"

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        prompt_tokens = len(prompt.split()) * 2
        completion_tokens = len(content.split()) * 2

        return LLMResponse(
            content=content,
            model=self._model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
        )
