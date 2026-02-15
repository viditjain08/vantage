"""
Pytest configuration and fixtures for backend tests.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base


@pytest.fixture
def mock_db_session():
    """Create a mock database session for testing."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def mock_category():
    """Create a mock Category object for testing."""
    category = MagicMock()
    category.id = 1
    category.name = "Test Category"
    category.system_prompt = "You are a test assistant"
    category.llm_provider = "openai"
    category.llm_model = "gpt-4"
    category.llm_provider_type = "direct"
    category.llm_api_key = "test-key"
    category.llm_endpoint = None
    category.llm_api_version = None
    category.llm_deployment_name = None
    category.llm_region = None
    category.mcp_servers = []
    return category


@pytest.fixture
def mock_mcp_server():
    """Create a mock MCPServer object for testing."""
    server = MagicMock()
    server.id = 1
    server.name = "Test Server"
    server.url = "https://test.mcp.server"
    server.type = "sse"
    server.category_id = 1
    server.resource_config = None
    return server


@pytest.fixture
async def test_db_engine():
    """Create a test database engine using SQLite in-memory."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine):
    """Create a test database session."""
    async_session = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session

