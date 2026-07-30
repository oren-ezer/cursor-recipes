"""
LLM provider backends for multi-provider AI service architecture.

Each backend wraps a specific LLM provider's SDK and normalizes
responses into a common dict format: {content, tokens_used, model, finish_reason}.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import json
import logging

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from google import genai

logger = logging.getLogger(__name__)


class LLMProviderBackend(ABC):
    """Abstract base for LLM provider backends."""

    @abstractmethod
    async def call(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a chat completion call and return a normalized response.

        Returns:
            Dict with keys: content (str), tokens_used (dict), model (str),
            finish_reason (str)
        """

    @abstractmethod
    def supports_vision(self) -> bool:
        """Whether this backend supports image/vision inputs."""


class OpenAIBackend(LLMProviderBackend):
    """Backend wrapping AsyncOpenAI for OpenAI models."""

    def __init__(self, api_key: str, organization: Optional[str] = None):
        self.client = AsyncOpenAI(api_key=api_key, organization=organization)

    async def call(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        request_params: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            request_params["response_format"] = response_format

        try:
            response = await self.client.chat.completions.create(**request_params)
        except (AuthenticationError, RateLimitError, APIError):
            raise
        except Exception:
            raise

        return {
            "content": response.choices[0].message.content,
            "tokens_used": {
                "prompt": response.usage.prompt_tokens,
                "completion": response.usage.completion_tokens,
                "total": response.usage.total_tokens,
            },
            "model": response.model,
            "finish_reason": response.choices[0].finish_reason,
        }

    def supports_vision(self) -> bool:
        return True


class GoogleBackend(LLMProviderBackend):
    """Backend for Google Gemini using the native google-genai SDK.

    Gemini's ``max_output_tokens`` budget covers **both** internal thinking
    tokens and the actual response.  Without a separate thinking budget the
    model can exhaust the entire allowance on reasoning and return nothing.

    To keep ``max_tokens`` (from the caller / DB config) meaningful as "how
    many tokens of *actual output* I want," this backend reserves a separate
    thinking allowance on top:

        max_output_tokens = max_tokens + THINKING_TOKEN_BUDGET
    """

    THINKING_TOKEN_BUDGET = 16384

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    async def call(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        from google.genai import types

        system_instruction = None
        contents: List[types.Content] = []

        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"] if isinstance(msg["content"], str) else str(msg["content"])
            else:
                role = "user" if msg["role"] == "user" else "model"
                parts = self._build_parts(msg["content"])
                contents.append(types.Content(role=role, parts=parts))

        effective_max = max_tokens + self.THINKING_TOKEN_BUDGET

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=effective_max,
            system_instruction=system_instruction,
            thinking_config=types.ThinkingConfig(
                thinking_budget=self.THINKING_TOKEN_BUDGET,
            ),
        )

        print(
            f"[GoogleBackend] calling model={model} "
            f"max_output_tokens={effective_max} "
            f"thinking_budget={self.THINKING_TOKEN_BUDGET} "
            f"temperature={temperature}",
            flush=True,
        )

        response = await self.client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        usage = response.usage_metadata
        thoughts_tokens = getattr(usage, "thoughts_token_count", 0) or 0
        candidate_tokens = usage.candidates_token_count if usage and usage.candidates_token_count else 0
        finish = (
            response.candidates[0].finish_reason.name
            if response.candidates and response.candidates[0].finish_reason
            else "unknown"
        )

        try:
            content_text = response.text or ""
        except ValueError:
            content_text = ""

        print(
            f"[GoogleBackend] response model={response.model_version or model} "
            f"prompt={usage.prompt_token_count if usage else 0} "
            f"candidates={candidate_tokens} thoughts={thoughts_tokens} "
            f"total={usage.total_token_count if usage else 0} "
            f"finish={finish} content_len={len(content_text)}",
            flush=True,
        )

        if not content_text and finish.upper() == "MAX_TOKENS":
            raise ValueError(
                f"Gemini exhausted {effective_max} output tokens on thinking "
                f"({thoughts_tokens} thinking, {candidate_tokens} candidate). "
                f"Increase max_tokens in the LLM config for this service."
            )

        if content_text:
            preview = content_text[:500].replace('\n', ' ')
            print(f"[GoogleBackend] content preview: {preview}", flush=True)

        return {
            "content": content_text,
            "tokens_used": {
                "prompt": usage.prompt_token_count if usage else 0,
                "completion": candidate_tokens,
                "total": usage.total_token_count if usage else 0,
            },
            "model": response.model_version or model,
            "finish_reason": finish.lower(),
        }

    def supports_vision(self) -> bool:
        return True

    @staticmethod
    def _build_parts(content: Any) -> list:
        """Convert OpenAI-format message content to Gemini Part objects."""
        from google.genai import types
        import base64

        if isinstance(content, str):
            return [types.Part.from_text(text=content)]

        parts = []
        for item in content:
            if item["type"] == "text":
                parts.append(types.Part.from_text(text=item["text"]))
            elif item["type"] == "image_url":
                url = item["image_url"]["url"]
                if url.startswith("data:"):
                    header, _, b64_data = url.partition(";base64,")
                    mime_type = header.replace("data:", "")
                    parts.append(types.Part.from_bytes(
                        data=base64.b64decode(b64_data),
                        mime_type=mime_type,
                    ))
                else:
                    parts.append(types.Part.from_uri(file_uri=url, mime_type="image/jpeg"))
        return parts


class AnthropicBackend(LLMProviderBackend):
    """Backend wrapping AsyncAnthropic for Claude models."""

    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)

    async def call(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        system_text = None
        api_messages: List[Dict[str, Any]] = []

        for msg in messages:
            if msg["role"] == "system":
                system_text = msg["content"] if isinstance(msg["content"], str) else str(msg["content"])
            else:
                api_messages.append(self._convert_message(msg))

        request_params: Dict[str, Any] = {
            "model": model,
            "messages": api_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system_text:
            request_params["system"] = system_text

        response = await self.client.messages.create(**request_params)

        content = response.content[0].text if response.content else ""

        return {
            "content": content,
            "tokens_used": {
                "prompt": response.usage.input_tokens,
                "completion": response.usage.output_tokens,
                "total": response.usage.input_tokens + response.usage.output_tokens,
            },
            "model": response.model,
            "finish_reason": response.stop_reason or "end_turn",
        }

    def supports_vision(self) -> bool:
        return True

    @staticmethod
    def _convert_message(msg: Dict[str, Any]) -> Dict[str, Any]:
        """Convert an OpenAI-format message to Anthropic format.

        Handles multimodal content (image_url parts → Anthropic base64 source blocks).
        """
        content = msg["content"]
        if isinstance(content, str):
            return {"role": msg["role"], "content": content}

        anthropic_parts: List[Dict[str, Any]] = []
        for part in content:
            if part["type"] == "text":
                anthropic_parts.append({"type": "text", "text": part["text"]})
            elif part["type"] == "image_url":
                url = part["image_url"]["url"]
                if url.startswith("data:"):
                    media_type, _, b64_data = url.partition(";base64,")
                    media_type = media_type.replace("data:", "")
                    anthropic_parts.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64_data,
                        },
                    })
                else:
                    anthropic_parts.append({
                        "type": "image",
                        "source": {"type": "url", "url": url},
                    })
        return {"role": msg["role"], "content": anthropic_parts}
