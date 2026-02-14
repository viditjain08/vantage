from typing import Optional, Dict, Any
from pydantic import BaseModel

class MCPServerBase(BaseModel):
    name: str
    url: str = ""  # Not required for stdio servers
    type: str = "sse"  # 'sse', 'http', or 'stdio'

class MCPServerCreate(MCPServerBase):
    category_id: int
    resource_config: Optional[Dict[str, Any]] = None

class MCPServerUpdate(MCPServerBase):
    name: Optional[str] = None
    url: Optional[str] = None
    type: Optional[str] = None
    resource_config: Optional[Dict[str, Any]] = None

class MCPServerInDBBase(MCPServerBase):
    id: int
    category_id: int
    resource_config: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class MCPServer(MCPServerInDBBase):
    pass
