import logging
from typing import Optional

from openai import APIError, AsyncOpenAI, RateLimitError

from app.ai.base import AIMessage, AIProvider, AIResponse
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class AIProviderError(Exception):
    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.code = code


class OpenAIProvider(AIProvider):
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise AIProviderError("OPENAI_API_KEY is not configured", "missing_api_key")
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def chat(
        self,
        messages: list[AIMessage],
        model: Optional[str] = None,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
    ) -> AIResponse:
        import time

        model = model or settings.DEFAULT_AI_MODEL
        start = time.time()

        kwargs: dict = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        try:
            response = await self.client.chat.completions.create(**kwargs)
        except RateLimitError as e:
            logger.error("OpenAI rate limit: %s", e)
            raise AIProviderError(
                "OpenAI API quota exceeded. Please check billing at platform.openai.com",
                "insufficient_quota",
            ) from e
        except APIError as e:
            logger.error("OpenAI API error: %s", e)
            raise AIProviderError(str(e), getattr(e, "code", None)) from e

        choice = response.choices[0]
        function_calls = []

        if choice.message.tool_calls:
            import json

            for tc in choice.message.tool_calls:
                function_calls.append(
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments),
                    }
                )

        content = choice.message.content or ""
        usage = response.usage
        return AIResponse(
            content=content,
            provider="openai",
            model=model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            function_calls=function_calls,
            finish_reason=choice.finish_reason,
        )

    async def embed(self, texts: list[str], model: Optional[str] = None) -> list[list[float]]:
        model = model or settings.EMBEDDING_MODEL
        try:
            response = await self.client.embeddings.create(model=model, input=texts)
        except (RateLimitError, APIError) as e:
            raise AIProviderError(str(e)) from e
        return [item.embedding for item in response.data]
