import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.services.ai_service import AIService
from openai import AuthenticationError, RateLimitError, APIError


def _make_effective_config(**overrides):
    """Return a baseline effective config dict, optionally overridden."""
    base = {
        "provider": "OPENAI",
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1000,
        "system_prompt": None,
        "user_prompt_template": None,
        "response_format": None,
    }
    base.update(overrides)
    return base


def _mock_openai_response(content="Hello!", prompt_tokens=10, completion_tokens=20,
                           model="gpt-4o-mini", finish_reason="stop"):
    """Build a mock that mimics openai ChatCompletion response."""
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


@pytest.fixture
def mock_config_service():
    svc = Mock()
    svc.get_effective_config.return_value = _make_effective_config()
    return svc


@pytest.fixture
def ai_service(mock_config_service):
    """Create AIService with mocked OpenAI client and config service."""
    with patch.object(AIService, "__init__", lambda self, *a, **kw: None):
        service = AIService.__new__(AIService)
    service.client = Mock()
    service.client.chat = Mock()
    service.client.chat.completions = Mock()
    service.client.chat.completions.create = AsyncMock(
        return_value=_mock_openai_response()
    )
    service.config_service = mock_config_service
    return service


# ---------------------------------------------------------------------------
# AIService.__init__
# ---------------------------------------------------------------------------

class TestAIServiceInit:
    def test_raises_without_api_key(self):
        mock_db = Mock()
        mock_config_svc = Mock()
        with patch("src.services.ai_service.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                AIService(db=mock_db, llm_config_service=mock_config_svc)

    def test_creates_client_with_api_key(self):
        mock_db = Mock()
        mock_config_svc = Mock()
        with patch("src.services.ai_service.settings") as mock_settings, \
             patch("src.services.ai_service.AsyncOpenAI") as mock_openai:
            mock_settings.OPENAI_API_KEY = "sk-test-key"
            mock_settings.OPENAI_ORG_ID = "org-test"
            svc = AIService(db=mock_db, llm_config_service=mock_config_svc)
            mock_openai.assert_called_once_with(api_key="sk-test-key", organization="org-test")
            assert svc.config_service is mock_config_svc

    def test_creates_client_without_org(self):
        mock_db = Mock()
        mock_config_svc = Mock()
        with patch("src.services.ai_service.settings") as mock_settings, \
             patch("src.services.ai_service.AsyncOpenAI") as mock_openai:
            mock_settings.OPENAI_API_KEY = "sk-test-key"
            mock_settings.OPENAI_ORG_ID = None
            AIService(db=mock_db, llm_config_service=mock_config_svc)
            mock_openai.assert_called_once_with(api_key="sk-test-key", organization=None)


# ---------------------------------------------------------------------------
# call_llm
# ---------------------------------------------------------------------------

class TestCallLLM:
    @pytest.mark.asyncio
    async def test_basic_call_returns_expected_shape(self, ai_service, mock_config_service):
        result = await ai_service.call_llm(user_prompt="Hello")

        assert result["content"] == "Hello!"
        assert result["tokens_used"]["prompt"] == 10
        assert result["tokens_used"]["completion"] == 20
        assert result["tokens_used"]["total"] == 30
        assert result["model"] == "gpt-4o-mini"
        assert result["finish_reason"] == "stop"

    @pytest.mark.asyncio
    async def test_passes_system_prompt(self, ai_service, mock_config_service):
        await ai_service.call_llm(user_prompt="Hi", system_prompt="Be helpful")

        call_kwargs = ai_service.client.chat.completions.create.call_args[1]
        messages = call_kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "Be helpful"
        assert messages[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_no_system_prompt_only_user_message(self, ai_service, mock_config_service):
        await ai_service.call_llm(user_prompt="Hi")

        call_kwargs = ai_service.client.chat.completions.create.call_args[1]
        messages = call_kwargs["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_uses_config_service_effective_config(self, ai_service, mock_config_service):
        mock_config_service.get_effective_config.return_value = _make_effective_config(
            model="gpt-4o", temperature=0.3, max_tokens=500
        )
        await ai_service.call_llm(user_prompt="Test")

        call_kwargs = ai_service.client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "gpt-4o"
        assert call_kwargs["temperature"] == 0.3
        assert call_kwargs["max_tokens"] == 500

    @pytest.mark.asyncio
    async def test_runtime_overrides_passed_to_config_service(self, ai_service, mock_config_service):
        await ai_service.call_llm(
            user_prompt="Test",
            model="gpt-4o",
            temperature=0.1,
            max_tokens=200,
        )
        call_args = mock_config_service.get_effective_config.call_args
        override = call_args[1]["override_params"]
        assert override["model"] == "gpt-4o"
        assert override["temperature"] == 0.1
        assert override["max_tokens"] == 200

    @pytest.mark.asyncio
    async def test_json_response_format(self, ai_service, mock_config_service):
        mock_config_service.get_effective_config.return_value = _make_effective_config(
            response_format="json"
        )
        ai_service.client.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response(content='{"key": "value"}')
        )

        result = await ai_service.call_llm(user_prompt="Give JSON")

        assert result["content"] == {"key": "value"}
        call_kwargs = ai_service.client.chat.completions.create.call_args[1]
        assert call_kwargs["response_format"] == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_json_parse_failure_returns_raw_string(self, ai_service, mock_config_service):
        mock_config_service.get_effective_config.return_value = _make_effective_config(
            response_format="json"
        )
        ai_service.client.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response(content="not valid json{")
        )
        result = await ai_service.call_llm(user_prompt="Give JSON")
        assert result["content"] == "not valid json{"

    @pytest.mark.asyncio
    async def test_json_mode_appends_instruction_when_system_lacks_json(
        self, ai_service, mock_config_service
    ):
        mock_config_service.get_effective_config.return_value = _make_effective_config(
            response_format="json", system_prompt="Be helpful"
        )
        ai_service.client.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response(content='{}')
        )
        await ai_service.call_llm(user_prompt="test", system_prompt="Be helpful")

        call_kwargs = ai_service.client.chat.completions.create.call_args[1]
        system_content = call_kwargs["messages"][0]["content"]
        assert "json" in system_content.lower()

    @pytest.mark.asyncio
    async def test_authentication_error_propagates(self, ai_service, mock_config_service):
        ai_service.client.chat.completions.create = AsyncMock(
            side_effect=AuthenticationError(
                message="Invalid API key",
                response=Mock(status_code=401),
                body=None
            )
        )
        with pytest.raises(AuthenticationError):
            await ai_service.call_llm(user_prompt="Test")

    @pytest.mark.asyncio
    async def test_rate_limit_error_propagates(self, ai_service, mock_config_service):
        ai_service.client.chat.completions.create = AsyncMock(
            side_effect=RateLimitError(
                message="Rate limited",
                response=Mock(status_code=429),
                body=None
            )
        )
        with pytest.raises(RateLimitError):
            await ai_service.call_llm(user_prompt="Test")

    @pytest.mark.asyncio
    async def test_api_error_propagates(self, ai_service, mock_config_service):
        ai_service.client.chat.completions.create = AsyncMock(
            side_effect=APIError(
                message="Server error",
                request=Mock(),
                body=None
            )
        )
        with pytest.raises(APIError):
            await ai_service.call_llm(user_prompt="Test")

    @pytest.mark.asyncio
    async def test_unexpected_exception_propagates(self, ai_service, mock_config_service):
        ai_service.client.chat.completions.create = AsyncMock(
            side_effect=RuntimeError("Something broke")
        )
        with pytest.raises(RuntimeError, match="Something broke"):
            await ai_service.call_llm(user_prompt="Test")

    @pytest.mark.asyncio
    async def test_service_name_passed_to_config(self, ai_service, mock_config_service):
        await ai_service.call_llm(user_prompt="Test", service_name="tag_suggestion")
        call_args = mock_config_service.get_effective_config.call_args
        assert call_args[1]["service_name"] == "tag_suggestion"


# ---------------------------------------------------------------------------
# suggest_tags
# ---------------------------------------------------------------------------

class TestSuggestTags:
    @pytest.mark.asyncio
    async def test_returns_tags_from_json_response(self, ai_service, mock_config_service):
        ai_service.client.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response(
                content='{"tags": ["italian", "pasta", "dinner"]}'
            )
        )
        mock_config_service.get_effective_config.return_value = _make_effective_config(
            response_format="json"
        )

        tags = await ai_service.suggest_tags(
            recipe_title="Spaghetti Carbonara",
            ingredients=["pasta", "eggs", "bacon", "parmesan"]
        )

        assert tags == ["italian", "pasta", "dinner"]

    @pytest.mark.asyncio
    async def test_returns_empty_list_on_unexpected_format(self, ai_service, mock_config_service):
        ai_service.client.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response(content="Just some text, no JSON")
        )
        mock_config_service.get_effective_config.return_value = _make_effective_config()

        tags = await ai_service.suggest_tags(
            recipe_title="Test", ingredients=["flour"]
        )
        assert tags == []

    @pytest.mark.asyncio
    async def test_returns_empty_list_on_exception(self, ai_service, mock_config_service):
        ai_service.client.chat.completions.create = AsyncMock(
            side_effect=RuntimeError("boom")
        )

        tags = await ai_service.suggest_tags(
            recipe_title="Test", ingredients=["flour"]
        )
        assert tags == []

    @pytest.mark.asyncio
    async def test_passes_existing_tags_in_prompt(self, ai_service, mock_config_service):
        ai_service.client.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response(content='{"tags": ["vegan"]}')
        )
        mock_config_service.get_effective_config.return_value = _make_effective_config(
            response_format="json"
        )

        await ai_service.suggest_tags(
            recipe_title="Salad",
            ingredients=["lettuce", "tomato"],
            existing_tags=["vegetarian"]
        )

        call_kwargs = ai_service.client.chat.completions.create.call_args[1]
        user_msg = [m for m in call_kwargs["messages"] if m["role"] == "user"][0]
        assert "vegetarian" in user_msg["content"]

    @pytest.mark.asyncio
    async def test_uses_template_from_config(self, ai_service, mock_config_service):
        template = "Recipe: {recipe_title}\nIngredients: {ingredients}\nExisting: {existing_tags}"
        mock_config_service.get_effective_config.return_value = _make_effective_config(
            user_prompt_template=template, response_format="json"
        )
        ai_service.client.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response(content='{"tags": ["quick"]}')
        )

        await ai_service.suggest_tags(
            recipe_title="Quick Pasta",
            ingredients=["pasta", "sauce"],
            existing_tags=["italian"]
        )

        call_kwargs = ai_service.client.chat.completions.create.call_args[1]
        user_msg = [m for m in call_kwargs["messages"] if m["role"] == "user"][0]
        assert "Quick Pasta" in user_msg["content"]
        assert "pasta, sauce" in user_msg["content"]
        assert "italian" in user_msg["content"]

    @pytest.mark.asyncio
    async def test_uses_tag_suggestion_service_name(self, ai_service, mock_config_service):
        ai_service.client.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response(content='{"tags": []}')
        )
        mock_config_service.get_effective_config.return_value = _make_effective_config(
            response_format="json"
        )
        await ai_service.suggest_tags(recipe_title="Test", ingredients=["flour"])

        config_calls = mock_config_service.get_effective_config.call_args_list
        service_names = [c[1].get("service_name", c[0][0] if c[0] else None) for c in config_calls]
        assert "tag_suggestion" in service_names


# ---------------------------------------------------------------------------
# parse_natural_language_search
# ---------------------------------------------------------------------------

class TestParseNaturalLanguageSearch:
    @pytest.mark.asyncio
    async def test_returns_parsed_dict(self, ai_service, mock_config_service):
        parsed = {
            "keywords": ["quick", "pasta"],
            "tags": ["italian"],
            "max_prep_time": 15,
            "max_cook_time": 30,
            "difficulty": "Easy"
        }
        ai_service.client.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response(content='{"keywords":["quick","pasta"],"tags":["italian"],"max_prep_time":15,"max_cook_time":30,"difficulty":"Easy"}')
        )
        mock_config_service.get_effective_config.return_value = _make_effective_config(
            response_format="json"
        )

        result = await ai_service.parse_natural_language_search("quick Italian pasta under 30 minutes")

        assert result["keywords"] == ["quick", "pasta"]
        assert result["tags"] == ["italian"]
        assert result["max_cook_time"] == 30

    @pytest.mark.asyncio
    async def test_returns_empty_dict_on_unexpected_format(self, ai_service, mock_config_service):
        ai_service.client.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response(content="just text")
        )
        result = await ai_service.parse_natural_language_search("something")
        assert result == {}

    @pytest.mark.asyncio
    async def test_returns_empty_dict_on_exception(self, ai_service, mock_config_service):
        ai_service.client.chat.completions.create = AsyncMock(
            side_effect=RuntimeError("fail")
        )
        result = await ai_service.parse_natural_language_search("something")
        assert result == {}

    @pytest.mark.asyncio
    async def test_query_included_in_prompt(self, ai_service, mock_config_service):
        ai_service.client.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response(content='{}')
        )
        mock_config_service.get_effective_config.return_value = _make_effective_config(
            response_format="json"
        )
        await ai_service.parse_natural_language_search("vegan dinner ideas")

        call_kwargs = ai_service.client.chat.completions.create.call_args[1]
        user_msg = [m for m in call_kwargs["messages"] if m["role"] == "user"][0]
        assert "vegan dinner ideas" in user_msg["content"]


# ---------------------------------------------------------------------------
# calculate_nutrition
# ---------------------------------------------------------------------------

class TestCalculateNutrition:
    @pytest.mark.asyncio
    async def test_returns_nutrition_dict(self, ai_service, mock_config_service):
        nutrition_json = '{"calories":350,"protein_g":25,"carbs_g":40,"fat_g":10,"fiber_g":5,"sodium_mg":600}'
        ai_service.client.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response(content=nutrition_json)
        )
        mock_config_service.get_effective_config.return_value = _make_effective_config(
            response_format="json"
        )

        result = await ai_service.calculate_nutrition(
            ingredients=[{"name": "chicken", "amount": "200g"}, {"name": "rice", "amount": "1 cup"}],
            servings=2
        )

        assert result["calories"] == 350
        assert result["protein_g"] == 25
        assert result["fat_g"] == 10

    @pytest.mark.asyncio
    async def test_returns_empty_dict_on_unexpected_format(self, ai_service, mock_config_service):
        ai_service.client.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response(content="non-json text")
        )
        result = await ai_service.calculate_nutrition(
            ingredients=[{"name": "flour", "amount": "1 cup"}]
        )
        assert result == {}

    @pytest.mark.asyncio
    async def test_returns_empty_dict_on_exception(self, ai_service, mock_config_service):
        ai_service.client.chat.completions.create = AsyncMock(
            side_effect=RuntimeError("fail")
        )
        result = await ai_service.calculate_nutrition(
            ingredients=[{"name": "flour", "amount": "1 cup"}]
        )
        assert result == {}

    @pytest.mark.asyncio
    async def test_ingredients_formatted_in_prompt(self, ai_service, mock_config_service):
        ai_service.client.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response(content='{}')
        )
        mock_config_service.get_effective_config.return_value = _make_effective_config(
            response_format="json"
        )
        await ai_service.calculate_nutrition(
            ingredients=[{"name": "butter", "amount": "50g"}],
            servings=4
        )

        call_kwargs = ai_service.client.chat.completions.create.call_args[1]
        user_msg = [m for m in call_kwargs["messages"] if m["role"] == "user"][0]
        assert "butter" in user_msg["content"]
        assert "50g" in user_msg["content"]
        assert "4" in user_msg["content"]

    @pytest.mark.asyncio
    async def test_uses_template_from_config(self, ai_service, mock_config_service):
        template = "Ingredients:\n{ingredients}\nServings: {servings}"
        mock_config_service.get_effective_config.return_value = _make_effective_config(
            user_prompt_template=template, response_format="json"
        )
        ai_service.client.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response(content='{}')
        )
        await ai_service.calculate_nutrition(
            ingredients=[{"name": "egg", "amount": "2"}],
            servings=1
        )

        call_kwargs = ai_service.client.chat.completions.create.call_args[1]
        user_msg = [m for m in call_kwargs["messages"] if m["role"] == "user"][0]
        assert "egg" in user_msg["content"]
        assert "Servings: 1" in user_msg["content"]

    @pytest.mark.asyncio
    async def test_uses_nutrition_service_name(self, ai_service, mock_config_service):
        ai_service.client.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response(content='{}')
        )
        mock_config_service.get_effective_config.return_value = _make_effective_config(
            response_format="json"
        )
        await ai_service.calculate_nutrition(
            ingredients=[{"name": "flour", "amount": "1 cup"}]
        )

        config_calls = mock_config_service.get_effective_config.call_args_list
        service_names = [c[1].get("service_name", c[0][0] if c[0] else None) for c in config_calls]
        assert "nutrition_calculation" in service_names
