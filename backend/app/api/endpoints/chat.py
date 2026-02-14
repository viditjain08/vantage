from contextlib import AsyncExitStack
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import httpx

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamable_http_client
from mcp.client.stdio import stdio_client, StdioServerParameters

from app.api import deps
from app.models.category import Category
from app.services.agent import AgentService
from app.services.mcp_client import MCPClient
from langchain_core.messages import HumanMessage, SystemMessage

router = APIRouter()

@router.websocket("/ws/chat/{category_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    category_id: int,
    db: AsyncSession = Depends(deps.get_db),
):
    await websocket.accept()
    try:
        # Fetch category with MCP servers eagerly loaded
        result = await db.execute(
            select(Category)
            .where(Category.id == category_id)
            .options(selectinload(Category.mcp_servers))
        )
        category = result.scalars().first()
        if not category:
            await websocket.send_text("Error: Category not found")
            await websocket.close()
            return

        # Open persistent MCP sessions for all servers in the category.
        # AsyncExitStack keeps connections alive for the websocket session
        # and cleans them up on disconnect.
        async with AsyncExitStack() as stack:
            mcp_sessions = {}
            for server in category.mcp_servers:
                try:
                    config = server.resource_config or {}
                    if server.type == 'stdio':
                        server_params = StdioServerParameters(
                            command=config.get("command", ""),
                            args=config.get("args", []),
                            env=config.get("env"),
                        )
                        read, write = await stack.enter_async_context(
                            stdio_client(server_params)
                        )
                    elif server.type == 'http':
                        headers = MCPClient._config_to_headers(config)
                        http_client = None
                        if headers:
                            http_client = await stack.enter_async_context(
                                httpx.AsyncClient(headers=headers)
                            )
                        read, write, _ = await stack.enter_async_context(
                            streamable_http_client(server.url, http_client=http_client)
                        )
                    else:  # 'sse' or default
                        headers = MCPClient._config_to_headers(config)
                        read, write = await stack.enter_async_context(
                            sse_client(server.url, headers=headers)
                        )

                    session = await stack.enter_async_context(
                        ClientSession(read, write)
                    )
                    await session.initialize()
                    mcp_sessions[server.id] = session
                    print(f"Connected to MCP server: {server.name} ({server.type})")
                except Exception as e:
                    print(f"Failed to connect to MCP server {server.name} ({server.url}): {e}")

            # Build agent using persistent sessions
            agent = await AgentService.get_agent_runnable_with_sessions(category, mcp_sessions)

            # Initialize chat history with system prompt
            chat_history = []
            if category.system_prompt:
                chat_history.append(SystemMessage(content=category.system_prompt))

            try:
                while True:
                    data = await websocket.receive_text()
                    user_msg = HumanMessage(content=data)
                    chat_history.append(user_msg)

                    try:
                        input_state = {"messages": chat_history}
                        final_state = await agent.ainvoke(input_state)

                        last_msg = final_state["messages"][-1]
                        response_text = last_msg.content

                        # Update local history with full result
                        chat_history = final_state["messages"]

                        await websocket.send_text(str(response_text))
                    except Exception as e:
                        import traceback
                        print(f"Error processing message: {e}")
                        print(traceback.format_exc())
                        # Remove the failed user message so history stays consistent
                        chat_history.pop()
                        try:
                            await websocket.send_text(f"Error: {str(e)}")
                        except:
                            pass
            except WebSocketDisconnect:
                print(f"Client disconnected from category {category_id}")

    except Exception as e:
        import traceback
        print(f"Error in WebSocket setup: {e}")
        print(traceback.format_exc())
        try:
            await websocket.send_text(f"Error: {str(e)}")
        except:
            pass
