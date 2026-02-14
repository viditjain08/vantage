from typing import List, Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.mcp_client import MCPClient

router = APIRouter()

class ServerUrl(BaseModel):
    url: str
    resource_config: Optional[Dict[str, Any]] = None

@router.post("/discover", response_model=List[Dict[str, Any]])
async def discover_tools(
    server: ServerUrl,
) -> Any:
    """
    Discover tools from an MCP server URL.
    """
    try:
        tools = await MCPClient.get_tools(server.url, resource_config=server.resource_config)
        return tools
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
