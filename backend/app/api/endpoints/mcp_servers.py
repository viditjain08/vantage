from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api import deps
from app.models.category import MCPServer
from app.schemas.mcp_server import MCPServerCreate, MCPServer as MCPServerSchema

router = APIRouter()

@router.post("/", response_model=MCPServerSchema)
async def create_mcp_server(
    *,
    db: AsyncSession = Depends(deps.get_db),
    server_in: MCPServerCreate,
) -> Any:
    """
    Create new MCP server for a category.
    """
    server = MCPServer(
        name=server_in.name,
        url=server_in.url,
        type=server_in.type,
        category_id=server_in.category_id,
        resource_config=server_in.resource_config,
    )
    db.add(server)
    await db.commit()
    await db.refresh(server)
    return server

@router.delete("/{id}", response_model=MCPServerSchema)
async def delete_mcp_server(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
) -> Any:
    """
    Delete an MCP server.
    """
    result = await db.execute(select(MCPServer).where(MCPServer.id == id))
    server = result.scalars().first()
    if not server:
        raise HTTPException(status_code=404, detail="MCP Server not found")
    
    await db.delete(server)
    await db.commit()
    return server
