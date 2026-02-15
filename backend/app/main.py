from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings, setup_logging
from app.api.endpoints import categories, registry, tools, mcp_servers, chat

setup_logging()

app = FastAPI(title=settings.PROJECT_NAME)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories.router, prefix=f"{settings.API_V1_STR}/categories", tags=["categories"])
app.include_router(registry.router, prefix=f"{settings.API_V1_STR}/registry", tags=["registry"])
app.include_router(tools.router, prefix=f"{settings.API_V1_STR}/tools", tags=["tools"])
app.include_router(mcp_servers.router, prefix=f"{settings.API_V1_STR}/mcp-servers", tags=["mcp-servers"])
app.include_router(chat.router, tags=["chat"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Vantage Agent API"}
