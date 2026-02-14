from typing import List, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api import deps
from app.models.category import Category
from app.services.registry import RegistryService

router = APIRouter()

@router.get("/suggest", response_model=List[Dict[str, Any]])
async def suggest_servers(
    category_id: int = Query(...),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Suggest MCP servers based on the category's LLM configuration.
    """
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return await RegistryService.suggest_servers(category)
