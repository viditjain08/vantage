"""
Unit tests for the LLMFactory service.

Tests LLM instance creation for different providers and configurations.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.llm_factory import LLMFactory


class TestLLMFactory:
    """Test suite for LLMFactory class."""

    def test_create_openai_direct(self):
        """Test creating OpenAI LLM with direct API."""
        with patch('app.services.llm_factory.ChatOpenAI') as mock_chat:
            LLMFactory.create_llm(
                provider="openai",
                model="gpt-4",
                provider_type="direct",
                api_key="test-key"
            )
            mock_chat.assert_called_once()
            call_kwargs = mock_chat.call_args[1]
            assert call_kwargs['model'] == "gpt-4"
            assert call_kwargs['api_key'] == "test-key"

    def test_create_openai_azure(self):
        """Test creating OpenAI LLM with Azure."""
        with patch('app.services.llm_factory.AzureChatOpenAI') as mock_azure:
            LLMFactory.create_llm(
                provider="openai",
                model="gpt-4",
                provider_type="azure",
                endpoint="https://test.openai.azure.com",
                api_version="2024-02-01",
                deployment_name="gpt-4-deployment",
                api_key="azure-key"
            )
            mock_azure.assert_called_once()
            call_kwargs = mock_azure.call_args[1]
            assert call_kwargs['azure_endpoint'] == "https://test.openai.azure.com"
            assert call_kwargs['azure_deployment'] == "gpt-4-deployment"

    def test_create_claude_direct(self):
        """Test creating Claude LLM with direct API."""
        with patch('app.services.llm_factory.ChatAnthropic') as mock_claude:
            LLMFactory.create_llm(
                provider="claude",
                model="claude-3-opus-20240229",
                provider_type="direct",
                api_key="claude-key"
            )
            mock_claude.assert_called_once()
            call_kwargs = mock_claude.call_args[1]
            assert call_kwargs['model'] == "claude-3-opus-20240229"
            assert call_kwargs['api_key'] == "claude-key"

    def test_create_llm_with_temperature(self):
        """Test creating LLM with custom temperature."""
        with patch('app.services.llm_factory.ChatOpenAI') as mock_chat:
            LLMFactory.create_llm(
                provider="openai",
                model="gpt-4",
                provider_type="direct",
                api_key="test-key",
                temperature=0.7
            )
            call_kwargs = mock_chat.call_args[1]
            assert call_kwargs['temperature'] == 0.7

    def test_unsupported_provider_raises_error(self):
        """Test that unsupported provider raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            LLMFactory.create_llm(
                provider="unsupported",
                model="model",
                provider_type="direct"
            )

    def test_unsupported_provider_type_raises_error(self):
        """Test that unsupported provider type raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported provider_type"):
            LLMFactory.create_llm(
                provider="openai",
                model="gpt-4",
                provider_type="unsupported"
            )

