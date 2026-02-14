from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.types import Tool
from typing import List, Dict, Any

class MCPClient:
    @staticmethod
    async def get_tools(server_url: str) -> List[Dict[str, Any]]:
        """
        Connect to an MCP server via SSE and list available tools.
        """
        try:
            async with sse_client(server_url) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    # Convert Tool objects to dicts
                    return [tool.model_dump() for tool in result.tools]
        except Exception as e:
            print(f"Error listing tools from {server_url}: {e}")
            raise e

    @staticmethod
    async def call_tool(server_url: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Connect to an MCP server via SSE and call a tool.
        """
        try:
            async with sse_client(server_url) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)
                    return result
        except Exception as e:
            print(f"Error calling tool {tool_name} on {server_url}: {e}")
            raise e
