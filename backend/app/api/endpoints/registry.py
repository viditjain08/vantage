from typing import List, Any, Dict
from fastapi import APIRouter, Query

from app.services.registry import RegistryService

router = APIRouter()

@router.get("/suggest", response_model=List[Dict[str, str]])
async def suggest_servers(
    category: str = Query(..., min_length=1),
) -> Any:
    """
    Suggest MCP servers based on category name.
    """
    return RegistryService.suggest_servers(category)
