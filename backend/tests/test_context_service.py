"""
Unit tests for the ContextService.

Tests context compression and token counting functionality.
"""

import pytest
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.services.context_service import ContextService


class TestContextService:
    """Test suite for ContextService class."""

    def test_get_token_count(self):
        """Test token counting functionality."""
        service = ContextService()
        text = "Hello, world!"
        count = service._get_token_count(text)
        assert isinstance(count, int)
        assert count > 0

    def test_messages_to_text(self):
        """Test converting messages to text."""
        service = ContextService()
        messages = [
            SystemMessage(content="You are a helpful assistant"),
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!")
        ]
        text = service._messages_to_text(messages)
        assert "System:" in text
        assert "User:" in text
        assert "Assistant:" in text
        assert "helpful assistant" in text
        assert "Hello" in text
        assert "Hi there!" in text

    @pytest.mark.asyncio
    async def test_compress_context_no_compression_needed(self):
        """Test that small context is not compressed."""
        service = ContextService()
        messages = [
            HumanMessage(content="Short message"),
            AIMessage(content="Short response")
        ]
        
        result = await service.compress_context(messages, "New message")
        
        # Should return original messages unchanged
        assert len(result) == len(messages)
        assert result == messages

    def test_system_message_extraction(self):
        """Test that system messages are correctly identified."""
        service = ContextService()

        messages = [
            SystemMessage(content="You are a helpful assistant"),
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!")
        ]

        # System message should be first
        assert isinstance(messages[0], SystemMessage)
        assert "helpful assistant" in messages[0].content

        # Test message to text conversion includes system message
        text = service._messages_to_text(messages)
        assert "System:" in text
        assert "helpful assistant" in text

