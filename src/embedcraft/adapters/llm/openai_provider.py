"""OpenAI-compatible LLM provider adapter supporting local Ollama and remote APIs."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from embedcraft.domain.exceptions import NetworkError
from embedcraft.ports.llm import LLMProvider, LLMResponse


class OpenAICompatibleProvider(LLMProvider):
    """Adapter for Ollama (/v1) and OpenAI-compatible LLM endpoints."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        api_key: str = "ollama",
        model_name: str = "llama3:latest",
        timeout_seconds: float = 60.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._model_name = model_name
        self.timeout = timeout_seconds

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
        url = f"{self.base_url}/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        start = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
                res_json = json.loads(body)
        except urllib.error.URLError as e:
            raise NetworkError(f"Fallo al conectar con endpoint LLM ({url}): {e.reason}") from e
        except Exception as e:
            raise NetworkError(f"Error inesperado invocando LLM: {str(e)}") from e

        latency_ms = (time.perf_counter() - start) * 1000.0

        choice = res_json.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content", "")
        usage = res_json.get("usage", {})

        return LLMResponse(
            content=content,
            model=res_json.get("model", self._model_name),
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            latency_ms=latency_ms,
            raw_response=res_json,
        )
