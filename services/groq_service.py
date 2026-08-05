import asyncio
from typing import Any

from groq import Groq


class GroqService:
    def __init__(self, api_key: str, models: list[str]) -> None:
        self.client = Groq(api_key=api_key)
        self.models = [model for model in models if model]

    async def chat(self, messages: list[dict[str, Any]], temperature: float = 0.4, max_tokens: int = 900) -> tuple[str, str]:
        last_error: Exception | None = None

        for model in self.models:
            try:
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_completion_tokens=max_tokens,
                )
                content = response.choices[0].message.content or ""
                return content.strip(), model
            except Exception as exc:
                last_error = exc

        raise last_error or RuntimeError("Groq request failed")
