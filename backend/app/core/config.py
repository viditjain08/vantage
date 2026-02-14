from pydantic_settings import BaseSettings
from functools import lru_cache

from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Vantage Agent"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str

    # OpenAI Direct
    OPENAI_API_KEY: Optional[str] = None

    # OpenAI Azure
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_VERSION: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT_NAME: Optional[str] = None
    AZURE_OPENAI_API_KEY: Optional[str] = None

    # OpenAI AWS (Bedrock)
    AWS_OPENAI_REGION: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    # Claude Direct (Anthropic)
    ANTHROPIC_API_KEY: Optional[str] = None

    # Claude Azure
    AZURE_CLAUDE_ENDPOINT: Optional[str] = None
    AZURE_CLAUDE_API_VERSION: Optional[str] = None
    AZURE_CLAUDE_DEPLOYMENT_NAME: Optional[str] = None
    AZURE_CLAUDE_API_KEY: Optional[str] = None

    # Claude AWS (Bedrock)
    AWS_CLAUDE_REGION: Optional[str] = None
    # Uses same AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY as OpenAI AWS

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
