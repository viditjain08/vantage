"""
Unit tests for the RegistryService.

Tests MCP server suggestion functionality based on category matching.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.registry import RegistryService, MCP_SERVER_CATALOG


class TestRegistryService:
    """Test suite for RegistryService class."""

    @pytest.mark.asyncio
    async def test_suggest_servers_with_llm_success(self, mock_category):
        """Test suggesting servers using LLM."""
        # Arrange
        mock_category.name = "Coding Assistant"
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = '["GitHub", "GitLab", "Git"]'
        mock_llm.ainvoke.return_value = mock_response

        with patch('app.services.registry.RegistryService._get_llm_from_category', return_value=mock_llm):
            # Act
            result = await RegistryService.suggest_servers(mock_category)

            # Assert
            assert len(result) <= 3
            assert any(server['name'] == "GitHub" for server in result)

    @pytest.mark.asyncio
    async def test_suggest_servers_fallback_to_keyword_matching(self, mock_category):
        """Test fallback to keyword matching when LLM fails."""
        # Arrange
        mock_category.name = "PostgreSQL"

        with patch('app.services.registry.RegistryService._get_llm_from_category', side_effect=Exception("LLM error")):
            # Act
            result = await RegistryService.suggest_servers(mock_category)

            # Assert
            assert len(result) > 0
            assert len(result) <= 3
            # Should match PostgreSQL server
            assert any("PostgreSQL" in server['name'] for server in result)

    @pytest.mark.asyncio
    async def test_suggest_servers_keyword_match_github(self, mock_category):
        """Test keyword matching for GitHub-related category."""
        # Arrange
        mock_category.name = "GitHub Assistant"

        with patch('app.services.registry.RegistryService._get_llm_from_category', side_effect=Exception("LLM error")):
            # Act
            result = await RegistryService.suggest_servers(mock_category)

            # Assert
            assert len(result) > 0
            assert any(server['name'] == "GitHub" for server in result)

    @pytest.mark.asyncio
    async def test_suggest_servers_no_match_returns_top_three(self, mock_category):
        """Test that unmatched category returns top 3 servers from catalog."""
        # Arrange
        mock_category.name = "XYZ Unknown Category"

        with patch('app.services.registry.RegistryService._get_llm_from_category', side_effect=Exception("LLM error")):
            # Act
            result = await RegistryService.suggest_servers(mock_category)

            # Assert
            assert len(result) == 3
            # Should return first 3 from catalog
            assert result[0]['name'] == MCP_SERVER_CATALOG[0]['name']

    @pytest.mark.asyncio
    async def test_suggest_servers_case_insensitive(self):
        """Test that category matching is case-insensitive."""
        # Arrange
        mock_category_lower = MagicMock()
        mock_category_lower.name = "github"
        mock_category_upper = MagicMock()
        mock_category_upper.name = "GITHUB"

        with patch('app.services.registry.RegistryService._get_llm_from_category', side_effect=Exception("LLM error")):
            # Act
            result_lower = await RegistryService.suggest_servers(mock_category_lower)
            result_upper = await RegistryService.suggest_servers(mock_category_upper)

            # Assert
            assert result_lower == result_upper

    def test_mcp_server_catalog_structure(self):
        """Test that MCP server catalog has expected structure."""
        assert len(MCP_SERVER_CATALOG) > 0

        for server in MCP_SERVER_CATALOG:
            assert "name" in server
            assert "description" in server
            # URL may be empty for stdio servers
            assert "url" in server or "stdio_config" in server

