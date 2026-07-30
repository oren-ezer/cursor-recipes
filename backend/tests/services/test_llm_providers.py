import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.services.llm_providers import (
    OpenAIBackend,
    GoogleBackend,
    AnthropicBackend,
)


def _openai_mock_response(content="Hello!", prompt_tokens=10, completion_tokens=20,
                           model="gpt-4o-mini", finish_reason="stop"):
    choice = Mock()
    choice.message.content = content
    choice.finish_reason = finish_reason

    usage = Mock()
    usage.prompt_tokens = prompt_tokens
    usage.completion_tokens = completion_tokens
    usage.total_tokens = prompt_tokens + completion_tokens

    response = Mock()
    response.choices = [choice]
    response.usage = usage
    response.model = model
    return response


def _anthropic_mock_response(content="Hello!", input_tokens=10, output_tokens=20,
                              model="claude-sonnet-4-20250514", stop_reason="end_turn"):
    text_block = Mock()
    text_block.text = content

    usage = Mock()
    usage.input_tokens = input_tokens
    usage.output_tokens = output_tokens

    response = Mock()
    response.content = [text_block]
    response.usage = usage
    response.model = model
    response.stop_reason = stop_reason
    return response


# ---------------------------------------------------------------------------
# OpenAIBackend
# ---------------------------------------------------------------------------

class TestOpenAIBackend:
    @pytest.mark.asyncio
    async def test_call_returns_normalized_response(self):
        with patch("src.services.llm_providers.AsyncOpenAI") as mock_cls:
            backend = OpenAIBackend(api_key="sk-test")
            backend.client.chat.completions.create = AsyncMock(
                return_value=_openai_mock_response()
            )

            result = await backend.call(
                messages=[{"role": "user", "content": "Hi"}],
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=100,
            )

            assert result["content"] == "Hello!"
            assert result["tokens_used"]["total"] == 30
            assert result["model"] == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_passes_response_format(self):
        with patch("src.services.llm_providers.AsyncOpenAI"):
            backend = OpenAIBackend(api_key="sk-test")
            backend.client.chat.completions.create = AsyncMock(
                return_value=_openai_mock_response(content='{"key":"val"}')
            )

            await backend.call(
                messages=[{"role": "user", "content": "Give JSON"}],
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=100,
                response_format={"type": "json_object"},
            )

            call_kwargs = backend.client.chat.completions.create.call_args[1]
            assert call_kwargs["response_format"] == {"type": "json_object"}

    def test_supports_vision(self):
        with patch("src.services.llm_providers.AsyncOpenAI"):
            backend = OpenAIBackend(api_key="sk-test")
            assert backend.supports_vision() is True


# ---------------------------------------------------------------------------
# GoogleBackend
# ---------------------------------------------------------------------------

def _gemini_mock_response(text="Hello!", prompt_tokens=10, candidates_tokens=20,
                           total_tokens=30, thoughts_tokens=0,
                           model_version="gemini-2.5-flash",
                           finish_reason_name="STOP"):
    """Build a mock that mimics google-genai GenerateContentResponse."""
    usage = Mock()
    usage.prompt_token_count = prompt_tokens
    usage.candidates_token_count = candidates_tokens
    usage.total_token_count = total_tokens
    usage.thoughts_token_count = thoughts_tokens

    finish_reason = Mock()
    finish_reason.name = finish_reason_name

    candidate = Mock()
    candidate.finish_reason = finish_reason

    response = Mock()
    response.text = text
    response.usage_metadata = usage
    response.model_version = model_version
    response.candidates = [candidate]
    return response


class TestGoogleBackend:
    @pytest.mark.asyncio
    async def test_call_returns_normalized_response(self):
        with patch("src.services.llm_providers.genai") as mock_genai:
            backend = GoogleBackend(api_key="goog-test")
            mock_genai.Client.assert_called_once_with(api_key="goog-test")

            backend.client.aio.models.generate_content = AsyncMock(
                return_value=_gemini_mock_response()
            )

            result = await backend.call(
                messages=[{"role": "user", "content": "Hi"}],
                model="gemini-2.5-flash",
                temperature=0.5,
                max_tokens=200,
            )

            assert result["content"] == "Hello!"
            assert result["model"] == "gemini-2.5-flash"
            assert result["tokens_used"]["prompt"] == 10
            assert result["tokens_used"]["completion"] == 20
            assert result["tokens_used"]["total"] == 30
            assert result["finish_reason"] == "stop"

    @pytest.mark.asyncio
    async def test_handles_missing_usage(self):
        with patch("src.services.llm_providers.genai"):
            backend = GoogleBackend(api_key="goog-test")

            response = _gemini_mock_response()
            response.usage_metadata = None
            backend.client.aio.models.generate_content = AsyncMock(return_value=response)

            result = await backend.call(
                messages=[{"role": "user", "content": "Hi"}],
                model="gemini-2.5-flash",
                temperature=0.5,
                max_tokens=200,
            )

            assert result["tokens_used"]["total"] == 0

    @pytest.mark.asyncio
    async def test_extracts_system_instruction(self):
        with patch("src.services.llm_providers.genai"):
            backend = GoogleBackend(api_key="goog-test")
            backend.client.aio.models.generate_content = AsyncMock(
                return_value=_gemini_mock_response()
            )

            await backend.call(
                messages=[
                    {"role": "system", "content": "You are a chef"},
                    {"role": "user", "content": "Hi"},
                ],
                model="gemini-2.5-flash",
                temperature=0.7,
                max_tokens=100,
            )

            call_kwargs = backend.client.aio.models.generate_content.call_args[1]
            assert call_kwargs["config"].system_instruction == "You are a chef"
            assert len(call_kwargs["contents"]) == 1

    @pytest.mark.asyncio
    async def test_json_response_format_not_forced(self):
        """Google backend should NOT set response_mime_type — it degrades vision/OCR quality."""
        with patch("src.services.llm_providers.genai"):
            backend = GoogleBackend(api_key="goog-test")
            backend.client.aio.models.generate_content = AsyncMock(
                return_value=_gemini_mock_response(text='{"key": "val"}')
            )

            await backend.call(
                messages=[{"role": "user", "content": "Give JSON"}],
                model="gemini-2.5-flash",
                temperature=0.7,
                max_tokens=100,
                response_format={"type": "json_object"},
            )

            call_kwargs = backend.client.aio.models.generate_content.call_args[1]
            assert not hasattr(call_kwargs["config"], "response_mime_type") or \
                call_kwargs["config"].response_mime_type is None

    @pytest.mark.asyncio
    async def test_thinking_budget_reserved(self):
        """max_output_tokens must include a thinking buffer so the model
        doesn't exhaust the budget on reasoning and return nothing."""
        with patch("src.services.llm_providers.genai"):
            backend = GoogleBackend(api_key="goog-test")
            backend.client.aio.models.generate_content = AsyncMock(
                return_value=_gemini_mock_response()
            )

            await backend.call(
                messages=[{"role": "user", "content": "Hi"}],
                model="gemini-2.5-flash",
                temperature=0.7,
                max_tokens=4096,
            )

            call_kwargs = backend.client.aio.models.generate_content.call_args[1]
            config = call_kwargs["config"]
            assert config.max_output_tokens == 4096 + GoogleBackend.THINKING_TOKEN_BUDGET
            assert config.thinking_config.thinking_budget == GoogleBackend.THINKING_TOKEN_BUDGET

    @pytest.mark.asyncio
    async def test_raises_on_max_tokens_exhausted_by_thinking(self):
        """If the model spends all tokens on thinking, raise a clear error."""
        with patch("src.services.llm_providers.genai"):
            backend = GoogleBackend(api_key="goog-test")
            response = _gemini_mock_response(
                text="",
                candidates_tokens=0,
                thoughts_tokens=20000,
                total_tokens=20637,
                finish_reason_name="MAX_TOKENS",
            )
            response.text = ""
            backend.client.aio.models.generate_content = AsyncMock(return_value=response)

            with pytest.raises(ValueError, match="exhausted.*output tokens on thinking"):
                await backend.call(
                    messages=[{"role": "user", "content": "Hi"}],
                    model="gemini-2.5-pro",
                    temperature=0.7,
                    max_tokens=4096,
                )

    def test_supports_vision(self):
        with patch("src.services.llm_providers.genai"):
            backend = GoogleBackend(api_key="goog-test")
            assert backend.supports_vision() is True


# ---------------------------------------------------------------------------
# AnthropicBackend
# ---------------------------------------------------------------------------

class TestAnthropicBackend:
    @pytest.mark.asyncio
    async def test_call_returns_normalized_response(self):
        with patch("src.services.llm_providers.AsyncAnthropic"):
            backend = AnthropicBackend(api_key="ant-test")
            backend.client.messages.create = AsyncMock(
                return_value=_anthropic_mock_response()
            )

            result = await backend.call(
                messages=[
                    {"role": "system", "content": "Be helpful"},
                    {"role": "user", "content": "Hi"},
                ],
                model="claude-sonnet-4-20250514",
                temperature=0.7,
                max_tokens=100,
            )

            assert result["content"] == "Hello!"
            assert result["tokens_used"]["prompt"] == 10
            assert result["tokens_used"]["completion"] == 20
            assert result["tokens_used"]["total"] == 30
            assert result["model"] == "claude-sonnet-4-20250514"

    @pytest.mark.asyncio
    async def test_extracts_system_message(self):
        with patch("src.services.llm_providers.AsyncAnthropic"):
            backend = AnthropicBackend(api_key="ant-test")
            backend.client.messages.create = AsyncMock(
                return_value=_anthropic_mock_response()
            )

            await backend.call(
                messages=[
                    {"role": "system", "content": "You are a chef"},
                    {"role": "user", "content": "Hi"},
                ],
                model="claude-sonnet-4-20250514",
                temperature=0.7,
                max_tokens=100,
            )

            call_kwargs = backend.client.messages.create.call_args[1]
            assert call_kwargs["system"] == "You are a chef"
            assert len(call_kwargs["messages"]) == 1
            assert call_kwargs["messages"][0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_no_system_message(self):
        with patch("src.services.llm_providers.AsyncAnthropic"):
            backend = AnthropicBackend(api_key="ant-test")
            backend.client.messages.create = AsyncMock(
                return_value=_anthropic_mock_response()
            )

            await backend.call(
                messages=[{"role": "user", "content": "Hi"}],
                model="claude-sonnet-4-20250514",
                temperature=0.7,
                max_tokens=100,
            )

            call_kwargs = backend.client.messages.create.call_args[1]
            assert "system" not in call_kwargs

    def test_supports_vision(self):
        with patch("src.services.llm_providers.AsyncAnthropic"):
            backend = AnthropicBackend(api_key="ant-test")
            assert backend.supports_vision() is True


class TestAnthropicMessageConversion:
    def test_plain_text_message(self):
        result = AnthropicBackend._convert_message({"role": "user", "content": "Hello"})
        assert result == {"role": "user", "content": "Hello"}

    def test_multimodal_with_base64_image(self):
        msg = {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this"},
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/png;base64,AAAA", "detail": "high"},
                },
            ],
        }
        result = AnthropicBackend._convert_message(msg)
        assert result["role"] == "user"
        assert len(result["content"]) == 2
        assert result["content"][0] == {"type": "text", "text": "Describe this"}
        assert result["content"][1]["type"] == "image"
        assert result["content"][1]["source"]["type"] == "base64"
        assert result["content"][1]["source"]["media_type"] == "image/png"
        assert result["content"][1]["source"]["data"] == "AAAA"

    def test_multimodal_with_http_url(self):
        msg = {
            "role": "user",
            "content": [
                {"type": "text", "text": "What is this?"},
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/img.jpg"},
                },
            ],
        }
        result = AnthropicBackend._convert_message(msg)
        assert result["content"][1]["type"] == "image"
        assert result["content"][1]["source"]["type"] == "url"
        assert result["content"][1]["source"]["url"] == "https://example.com/img.jpg"
