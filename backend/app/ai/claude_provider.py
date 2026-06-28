import json
import time
from typing import Any, Optional

import anthropic

from app.ai.base import AIMessage, AIProvider, AIResponse
from app.config import get_settings

settings = get_settings()


class ClaudeProvider(AIProvider):
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def chat(
        self,
        messages: list[AIMessage],
        model: Optional[str] = None,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
    ) -> AIResponse:
        model = model or "claude-sonnet-4-20250514"
        system_msg = ""
        claude_messages = []
        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                claude_messages.append({"role": m.role, "content": m.content})

        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": 4096,
            "messages": claude_messages,
            "temperature": temperature,
        }
        if system_msg:
            kwargs["system"] = system_msg
        if tools:
            claude_tools = []
            for t in tools:
                fn = t.get("function", t)
                claude_tools.append(
                    {
                        "name": fn["name"],
                        "description": fn.get("description", ""),
                        "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
                    }
                )
            kwargs["tools"] = claude_tools

        response = await self.client.messages.create(**kwargs)
        content = ""
        function_calls = []
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                function_calls.append(
                    {"id": block.id, "name": block.name, "arguments": block.input}
                )

        return AIResponse(
            content=content,
            provider="anthropic",
            model=model,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            function_calls=function_calls,
        )

    async def embed(self, texts: list[str], model: Optional[str] = None) -> list[list[float]]:
        # Claude doesn't have native embeddings; fall back to OpenAI
        from app.ai.openai_provider import OpenAIProvider

        return await OpenAIProvider().embed(texts, model)
