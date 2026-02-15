"""
Unit tests for the PromptEnhancer service.

This module tests the prompt enhancement functionality including:
- Successful prompt enhancement
- Error handling and fallback to original prompt
- LLM factory integration
- Various provider configurations
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import HumanMessage

from app.services.prompt_enhancer import PromptEnhancer, ENHANCE_PROMPT


class TestPromptEnhancer:
    """Test suite for PromptEnhancer class."""

    @pytest.mark.asyncio
    async def test_enhance_success(self):
        """Test successful prompt enhancement."""
        # Arrange
        user_prompt = "Help me with coding tasks"
        enhanced_text = "You are an expert coding assistant..."

        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = enhanced_text
        mock_llm.ainvoke.return_value = mock_response

        with patch('app.services.prompt_enhancer.LLMFactory.create_llm', return_value=mock_llm):
            # Act
            result = await PromptEnhancer.enhance(
                user_prompt=user_prompt,
                llm_provider="openai",
                llm_model="gpt-4",
                llm_provider_type="direct",
                llm_api_key="test-key"
            )

        # Assert
        assert result == enhanced_text
        mock_llm.ainvoke.assert_called_once()
        call_args = mock_llm.ainvoke.call_args[0][0]
        assert len(call_args) == 1
        assert isinstance(call_args[0], HumanMessage)
        assert user_prompt in call_args[0].content

    @pytest.mark.asyncio
    async def test_enhance_with_azure_provider(self):
        """Test prompt enhancement with Azure OpenAI provider."""
        # Arrange
        user_prompt = "Analyze data"
        enhanced_text = "You are a data analysis expert..."

        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = enhanced_text
        mock_llm.ainvoke.return_value = mock_response

        with patch('app.services.prompt_enhancer.LLMFactory.create_llm', return_value=mock_llm) as mock_factory:
            # Act
            result = await PromptEnhancer.enhance(
                user_prompt=user_prompt,
                llm_provider="openai",
                llm_model="gpt-4",
                llm_provider_type="azure",
                llm_endpoint="https://test.openai.azure.com",
                llm_api_version="2024-02-01",
                llm_deployment_name="gpt-4-deployment",
                llm_api_key="azure-key"
            )

        # Assert
        assert result == enhanced_text
        mock_factory.assert_called_once_with(
            provider="openai",
            model="gpt-4",
            provider_type="azure",
            api_key="azure-key",
            endpoint="https://test.openai.azure.com",
            api_version="2024-02-01",
            deployment_name="gpt-4-deployment",
            region=None
        )

    @pytest.mark.asyncio
    async def test_enhance_error_returns_original_prompt(self):
        """Test that enhancement errors fall back to original prompt."""
        # Arrange
        user_prompt = "Original prompt text"

        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = Exception("API Error")

        with patch('app.services.prompt_enhancer.LLMFactory.create_llm', return_value=mock_llm):
            # Act
            result = await PromptEnhancer.enhance(
                user_prompt=user_prompt,
                llm_provider="openai",
                llm_model="gpt-4",
                llm_provider_type="direct",
                llm_api_key="test-key"
            )

        # Assert
        assert result == user_prompt

    @pytest.mark.asyncio
    async def test_enhance_empty_response_returns_original(self):
        """Test that empty enhanced response falls back to original prompt."""
        # Arrange
        user_prompt = "Original prompt"

        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "   "  # Whitespace only
        mock_llm.ainvoke.return_value = mock_response

        with patch('app.services.prompt_enhancer.LLMFactory.create_llm', return_value=mock_llm):
            # Act
            result = await PromptEnhancer.enhance(
                user_prompt=user_prompt,
                llm_provider="openai",
                llm_model="gpt-4",
                llm_provider_type="direct"
            )

        # Assert
        assert result == user_prompt

