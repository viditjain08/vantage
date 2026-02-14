from typing import List, Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.mcp_client import MCPClient

router = APIRouter()

class ServerUrl(BaseModel):
    url: str

@router.post("/discover", response_model=List[Dict[str, Any]])
async def discover_tools(
    server: ServerUrl,
) -> Any:
    """
    Discover tools from an MCP server URL.
    """
    try:
        tools = await MCPClient.get_tools(server.url)
        return tools
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
