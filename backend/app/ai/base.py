from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AIResponse:
    content: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    function_calls: list[dict] = field(default_factory=list)
    finish_reason: Optional[str] = None


@dataclass
class AIMessage:
    role: str
    content: str
    name: Optional[str] = None


class AIProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[AIMessage],
        model: Optional[str] = None,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
    ) -> AIResponse:
        pass

    @abstractmethod
    async def embed(self, texts: list[str], model: Optional[str] = None) -> list[list[float]]:
        pass
