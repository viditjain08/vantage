from typing import Optional
from pydantic import BaseModel

class MCPServerBase(BaseModel):
    name: str
    url: str
    type: str = "sse"  # Default to SSE

class MCPServerCreate(MCPServerBase):
    category_id: int

class MCPServerUpdate(MCPServerBase):
    name: Optional[str] = None
    url: Optional[str] = None
    type: Optional[str] = None

class MCPServerInDBBase(MCPServerBase):
    id: int
    category_id: int

    class Config:
        from_attributes = True

class MCPServer(MCPServerInDBBase):
    pass
