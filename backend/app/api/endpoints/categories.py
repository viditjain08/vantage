from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api import deps
from app.models.category import Category
from app.schemas.category import CategoryCreate, Category as CategorySchema
from app.services.llm_factory import LLMFactory
from app.services.prompt_enhancer import PromptEnhancer
from langchain_core.messages import HumanMessage

router = APIRouter()

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
    Create new category. Enhances the user-provided system prompt via LLM before saving.
    """
    enhanced_prompt = await PromptEnhancer.enhance(
        user_prompt=category_in.system_prompt,
        llm_provider=category_in.llm_provider,
        llm_model=category_in.llm_model,
        llm_provider_type=category_in.llm_provider_type,
        llm_api_key=category_in.llm_api_key,
        llm_endpoint=category_in.llm_endpoint,
        llm_api_version=category_in.llm_api_version,
        llm_deployment_name=category_in.llm_deployment_name,
        llm_region=category_in.llm_region,
    )
    category = Category(
        name=category_in.name,
        system_prompt=enhanced_prompt,
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


class EnhancePromptRequest(BaseModel):
    prompt: str


class EnhancePromptResponse(BaseModel):
    enhanced_prompt: str


CHAT_ENHANCE_PROMPT = """\
You are a prompt enhancement assistant. The user has typed a message they want to send to an AI agent. \
Your job is to rewrite it into a clearer, more specific, and more actionable prompt that will get better results.

Guidelines:
- Preserve the user's original intent completely
- Add specificity and structure where helpful
- If the user asks for something vague, make it concrete
- Keep a similar length — don't over-expand simple requests
- Return ONLY the enhanced prompt text, nothing else (no preamble, no explanation)

User's original message:
{prompt}
"""


@router.post("/{category_id}/enhance-prompt", response_model=EnhancePromptResponse)
async def enhance_chat_prompt(
    category_id: int,
    body: EnhancePromptRequest,
    db: AsyncSession = Depends(deps.get_db),
):
    """Enhance a user's chat message using the category's LLM."""
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    llm = LLMFactory.create_llm(
        provider=category.llm_provider,
        model=category.llm_model,
        provider_type=category.llm_provider_type,
        api_key=category.llm_api_key,
        endpoint=category.llm_endpoint,
        api_version=category.llm_api_version,
        deployment_name=category.llm_deployment_name,
        region=category.llm_region,
    )

    message = CHAT_ENHANCE_PROMPT.format(prompt=body.prompt)
    response = await llm.ainvoke([HumanMessage(content=message)])
    enhanced = response.content.strip()

    return EnhancePromptResponse(enhanced_prompt=enhanced or body.prompt)
