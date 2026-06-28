from typing import Optional

from app.ai.base import AIMessage, AIProvider, AIResponse
from app.ai.claude_provider import ClaudeProvider
from app.ai.openai_provider import OpenAIProvider
from app.config import get_settings

settings = get_settings()


class AIService:
    def __init__(self, provider: Optional[str] = None):
        provider = provider or settings.DEFAULT_AI_PROVIDER
        self.provider_name = provider
        if provider == "anthropic":
            self.provider: AIProvider = ClaudeProvider()
        else:
            self.provider = OpenAIProvider()

    async def chat(
        self,
        messages: list[AIMessage],
        model: Optional[str] = None,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
    ) -> AIResponse:
        return await self.provider.chat(messages, model, tools, temperature)

    async def embed(self, texts: list[str], model: Optional[str] = None) -> list[list[float]]:
        return await self.provider.embed(texts, model)
