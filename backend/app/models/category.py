from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    system_prompt: Mapped[str] = mapped_column(Text)

    # LLM Configuration
    llm_provider: Mapped[str] = mapped_column(String(50), default="openai")  # 'openai' or 'claude'
    llm_model: Mapped[str] = mapped_column(String(100), default="gpt-4")
    llm_provider_type: Mapped[str] = mapped_column(String(50), default="direct")  # 'direct', 'aws', or 'azure'

    # Credential fields (stored per category for flexibility)
    llm_api_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    llm_endpoint: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # For Azure/AWS endpoints
    llm_api_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # For Azure
    llm_deployment_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # For Azure
    llm_region: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # For AWS

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    mcp_servers: Mapped[List["MCPServer"]] = relationship(back_populates="category", cascade="all, delete-orphan")

class MCPServer(Base):
    __tablename__ = "mcp_servers"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(10))  # 'sse', 'http', or 'stdio'
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    resource_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=None)

    category: Mapped["Category"] = relationship(back_populates="mcp_servers")
