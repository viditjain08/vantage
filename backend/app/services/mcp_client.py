import base64
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.types import Tool
from typing import List, Dict, Any, Optional

class MCPClient:
    @staticmethod
    def _config_to_headers(resource_config: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """Convert resource_config into HTTP headers for the MCP server."""
        if not resource_config:
            return {}

        headers = {}
        provider = resource_config.get("provider", "").lower()

        if provider == "aws":
            headers["X-AWS-Access-Key-ID"] = resource_config.get("aws_access_key_id", "")
            headers["X-AWS-Secret-Access-Key"] = resource_config.get("aws_secret_access_key", "")
            headers["X-AWS-Region"] = resource_config.get("aws_region", "")
        elif provider == "azure":
            headers["X-Azure-Tenant-ID"] = resource_config.get("azure_tenant_id", "")
            headers["X-Azure-Client-ID"] = resource_config.get("azure_client_id", "")
            headers["X-Azure-Client-Secret"] = resource_config.get("azure_client_secret", "")
            headers["X-Azure-Subscription-ID"] = resource_config.get("azure_subscription_id", "")
        elif provider == "gcp":
            headers["X-GCP-Project-ID"] = resource_config.get("gcp_project_id", "")
            sa_json = resource_config.get("gcp_service_account_json", "")
            if sa_json:
                headers["X-GCP-Service-Account-JSON"] = base64.b64encode(sa_json.encode()).decode()
        elif provider == "kubernetes":
            headers["X-K8s-Cluster-Endpoint"] = resource_config.get("k8s_cluster_endpoint", "")
            headers["X-K8s-Token"] = resource_config.get("k8s_token", "")
            headers["X-K8s-Namespace"] = resource_config.get("k8s_namespace", "default")
        else:
            # Generic: pass config values as X-MCP-Config-* headers
            for key, value in resource_config.items():
                if key != "provider":
                    headers[f"X-MCP-Config-{key}"] = str(value)

        return {k: v for k, v in headers.items() if v}

    @staticmethod
    async def get_tools(server_url: str, resource_config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Connect to an MCP server via SSE and list available tools.
        """
        try:
            headers = MCPClient._config_to_headers(resource_config)
            async with sse_client(server_url, headers=headers) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    return [tool.model_dump() for tool in result.tools]
        except Exception as e:
            print(f"Error listing tools from {server_url}: {e}")
            raise e

    @staticmethod
    async def call_tool(server_url: str, tool_name: str, arguments: Dict[str, Any], resource_config: Optional[Dict[str, Any]] = None) -> Any:
        """
        Connect to an MCP server via SSE and call a tool.
        """
        try:
            headers = MCPClient._config_to_headers(resource_config)
            async with sse_client(server_url, headers=headers) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)
                    return result
        except Exception as e:
            print(f"Error calling tool {tool_name} on {server_url}: {e}")
            raise e
