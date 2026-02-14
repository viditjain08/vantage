from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class CategoryBase(BaseModel):
    name: str
    system_prompt: str

    # LLM Configuration
    llm_provider: str = "openai"  # 'openai' or 'claude'
    llm_model: str = "gpt-4"
    llm_provider_type: str = "direct"  # 'direct', 'aws', or 'azure'

    # Credential fields
    llm_api_key: Optional[str] = None
    llm_endpoint: Optional[str] = None
    llm_api_version: Optional[str] = None
    llm_deployment_name: Optional[str] = None
    llm_region: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    system_prompt: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_provider_type: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_endpoint: Optional[str] = None
    llm_api_version: Optional[str] = None
    llm_deployment_name: Optional[str] = None
    llm_region: Optional[str] = None

class CategoryInDBBase(CategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

from app.schemas.mcp_server import MCPServer

class Category(CategoryInDBBase):
    mcp_servers: List[MCPServer] = []
