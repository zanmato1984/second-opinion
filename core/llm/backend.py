from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LLMRequest:
    prompt: str
    temperature: float = 0.0


class LLMBackend(Protocol):
    def complete(self, request: LLMRequest) -> str:
        ...


class NullBackend:
    def complete(self, request: LLMRequest) -> str:
        raise NotImplementedError("LLM backend is not configured")
