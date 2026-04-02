from __future__ import annotations

import asyncio
import json
from typing import Any

from openai import OpenAI

from app.config import Settings
from app.models.comment import LLMAnnotation


class LLMClientError(RuntimeError):
    """Raised when the LLM backend call fails."""


class NvidiaLLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = OpenAI(
            base_url=self.settings.nvidia_base_url,
            api_key=self.settings.nvidia_api_key,
        )

    async def annotate(self, comment_text: str) -> LLMAnnotation:
        if not self.settings.nvidia_api_key:
            raise LLMClientError("NVIDIA_API_KEY is not configured")

        return await asyncio.to_thread(self._annotate_sync, comment_text)

    def _annotate_sync(self, comment_text: str) -> LLMAnnotation:
        try:
            stream = self.client.chat.completions.create(
                model=self.settings.nvidia_model,
                messages=[
                    {"role": "system", "content": ANNOTATION_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Annotate this comment:\n\n{comment_text}"},
                ],
                temperature=self.settings.nvidia_temperature,
                top_p=self.settings.nvidia_top_p,
                max_tokens=self.settings.nvidia_max_tokens,
                response_format={"type": "json_object"},
                extra_body={
                    "chat_template_kwargs": {
                        "enable_thinking": self.settings.nvidia_enable_thinking,
                    },
                    "reasoning_budget": self.settings.nvidia_reasoning_budget,
                },
                stream=True,
            )
        except Exception as exc:
            raise LLMClientError(f"NVIDIA API request failed: {exc}") from exc

        content_parts: list[str] = []
        reasoning_parts: list[str] = []

        try:
            for chunk in stream:
                if not getattr(chunk, "choices", None):
                    continue
                delta = chunk.choices[0].delta
                reasoning = getattr(delta, "reasoning_content", None)
                if reasoning:
                    reasoning_parts.append(reasoning)
                if delta.content is not None:
                    content_parts.append(delta.content)
        except Exception as exc:
            raise LLMClientError(f"NVIDIA stream failed: {exc}") from exc

        content = "".join(content_parts).strip()
        if not content and reasoning_parts:
            content = "".join(reasoning_parts).strip()
        if not content:
            raise LLMClientError("NVIDIA API returned an empty completion")

        payload = self._extract_json(content)
        return LLMAnnotation.model_validate(payload)

    def _parse_response(self, data: dict[str, Any]) -> LLMAnnotation:
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMClientError("Unexpected NVIDIA API response format") from exc

        payload = self._extract_json(content)
        return LLMAnnotation.model_validate(payload)

    @staticmethod
    def _extract_json(content: str) -> dict[str, Any]:
        content = content.strip()
        if content.startswith("```"):
            lines = [line for line in content.splitlines() if not line.startswith("```")]
            content = "\n".join(lines).strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise LLMClientError("LLM did not return valid JSON")
            try:
                return json.loads(content[start : end + 1])
            except json.JSONDecodeError as exc:
                raise LLMClientError("LLM did not return valid JSON") from exc


ANNOTATION_SYSTEM_PROMPT = """
You are a social media comment analyzer. Given a tweet/comment, return a JSON object with these exact keys:
{
  "sentiment": "positive" | "negative" | "neutral" | "mixed",
  "sentiment_score": <float 0.0-1.0>,
  "topics": [<list of 1-5 short topic tags>],
  "summary": "<one sentence summary>",
  "language": "<ISO 639-1 code>",
  "is_spam": <true|false>
}
Return ONLY valid JSON. No markdown, no explanation.
""".strip()
