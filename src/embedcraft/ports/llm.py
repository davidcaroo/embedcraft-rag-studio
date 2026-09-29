"""LLM provider port definition."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0
    finish_reason: str = "stop"
    raw_response: dict = Field(default_factory=dict)


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for language model providers (Ollama, OpenAI, Anthropic, Mock)."""

    @property
    def model_name(self) -> str: ...

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1000,
    ) -> LLMResponse: ...
