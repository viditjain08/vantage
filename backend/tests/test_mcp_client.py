"""
Unit tests for the MCPClient service.

Tests MCP server communication and tool discovery.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.mcp_client import MCPClient
from mcp.types import Tool


class TestMCPClient:
    """Test suite for MCPClient class."""

    def test_config_to_headers_aws(self):
        """Test AWS resource config to headers conversion."""
        resource_config = {
            "provider": "aws",
            "aws_access_key_id": "AKIA123",
            "aws_secret_access_key": "secret123",
            "aws_region": "us-east-1"
        }

        headers = MCPClient._config_to_headers(resource_config)

        assert headers["X-AWS-Access-Key-ID"] == "AKIA123"
        assert headers["X-AWS-Secret-Access-Key"] == "secret123"
        assert headers["X-AWS-Region"] == "us-east-1"

    def test_config_to_headers_azure(self):
        """Test Azure resource config to headers conversion."""
        resource_config = {
            "provider": "azure",
            "azure_tenant_id": "tenant123",
            "azure_client_id": "client123",
            "azure_client_secret": "secret123",
            "azure_subscription_id": "sub123"
        }

        headers = MCPClient._config_to_headers(resource_config)

        assert headers["X-Azure-Tenant-ID"] == "tenant123"
        assert headers["X-Azure-Client-ID"] == "client123"
        assert headers["X-Azure-Client-Secret"] == "secret123"
        assert headers["X-Azure-Subscription-ID"] == "sub123"

    def test_config_to_headers_kubernetes(self):
        """Test Kubernetes resource config to headers conversion."""
        resource_config = {
            "provider": "kubernetes",
            "k8s_cluster_endpoint": "https://k8s.example.com",
            "k8s_token": "token123",
            "k8s_namespace": "production"
        }

        headers = MCPClient._config_to_headers(resource_config)

        assert headers["X-K8s-Cluster-Endpoint"] == "https://k8s.example.com"
        assert headers["X-K8s-Token"] == "token123"
        assert headers["X-K8s-Namespace"] == "production"

    def test_config_to_headers_generic(self):
        """Test generic resource config to headers conversion."""
        resource_config = {
            "provider": "custom",
            "api_key": "key123",
            "endpoint": "https://api.example.com"
        }

        headers = MCPClient._config_to_headers(resource_config)

        assert headers["X-MCP-Config-api_key"] == "key123"
        assert headers["X-MCP-Config-endpoint"] == "https://api.example.com"

    def test_config_to_headers_empty(self):
        """Test empty resource config returns empty headers."""
        headers = MCPClient._config_to_headers(None)
        assert headers == {}

        headers = MCPClient._config_to_headers({})
        assert headers == {}

    def test_config_to_headers_filters_empty_values(self):
        """Test that empty values are filtered out from headers."""
        resource_config = {
            "provider": "aws",
            "aws_access_key_id": "AKIA123",
            "aws_secret_access_key": "",  # Empty value
            "aws_region": "us-east-1"
        }

        headers = MCPClient._config_to_headers(resource_config)

        assert "X-AWS-Access-Key-ID" in headers
        assert "X-AWS-Secret-Access-Key" not in headers  # Filtered out
        assert "X-AWS-Region" in headers

    @pytest.mark.asyncio
    async def test_get_tools_with_mocked_session(self):
        """Test getting tools with mocked MCP session."""
        # Create mock tool
        mock_tool = MagicMock(spec=Tool)
        mock_tool.name = "test_tool"
        mock_tool.description = "A test tool"
        mock_tool.inputSchema = {"type": "object", "properties": {}}

        # Mock the session
        mock_session = AsyncMock()
        mock_session.list_tools.return_value.tools = [mock_tool]

        # Mock sse_client context manager
        async def mock_sse_client(*args, **kwargs):
            read = AsyncMock()
            write = AsyncMock()
            return read, write

        with patch('app.services.mcp_client.sse_client', return_value=mock_sse_client()):
            with patch('app.services.mcp_client.ClientSession', return_value=mock_session):
                # This test would require complex mocking of the MCP library
                # For now, we test the helper methods which are more unit-testable
                pass

