from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api import deps
from app.models.category import Category
from app.schemas.category import CategoryCreate, Category as CategorySchema

router = APIRouter()

from sqlalchemy.orm import selectinload

@router.get("/", response_model=List[CategorySchema])
async def read_categories(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve categories with their MCP servers.
    """
    result = await db.execute(select(Category).options(selectinload(Category.mcp_servers)).offset(skip).limit(limit))
    categories = result.scalars().all()
    return categories

@router.post("/", response_model=CategorySchema)
async def create_category(
    *,
    db: AsyncSession = Depends(deps.get_db),
    category_in: CategoryCreate,
) -> Any:
    """
    Create new category.
    """
    category = Category(
        name=category_in.name,
        system_prompt=category_in.system_prompt,
        llm_provider=category_in.llm_provider,
        llm_model=category_in.llm_model,
        llm_provider_type=category_in.llm_provider_type,
        llm_api_key=category_in.llm_api_key,
        llm_endpoint=category_in.llm_endpoint,
        llm_api_version=category_in.llm_api_version,
        llm_deployment_name=category_in.llm_deployment_name,
        llm_region=category_in.llm_region,
    )
    db.add(category)
    await db.commit()
    result = await db.execute(
        select(Category)
        .where(Category.id == category.id)
        .options(selectinload(Category.mcp_servers))
    )
    return result.scalars().first()
