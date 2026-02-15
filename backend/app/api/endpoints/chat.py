import json
import logging
import traceback
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
from app.services.task_decomposer import TaskDecomposer
from app.services.task_executor import TaskExecutor
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger("app.chat")

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
            await websocket.send_json({"type": "error", "content": "Category not found"})
            await websocket.close()
            return

        # Open persistent MCP sessions for all servers in the category.
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
                    logger.info("Connected to MCP server: %s (%s)", server.name, server.type)
                except Exception as e:
                    logger.error("Failed to connect to MCP server %s (%s): %s", server.name, server.url, e)

            # Build agent using persistent sessions
            logger.info("Building agent for category %d (%s)", category.id, category.name)
            bundle = await AgentService.get_agent_runnable_with_sessions(category, mcp_sessions)
            logger.info("Agent ready with %d tools", len(bundle.tools))

            # Collect tool metadata for the decomposer
            available_tools = [
                {"name": t.name, "description": t.description}
                for t in bundle.tools
            ]

            # Initialize chat history with system prompt
            chat_history = []
            system_prompt = category.system_prompt or ""
            system_prompt += (
                "\n\nFormat your responses in markdown. When presenting structured data, "
                "comparisons, lists of items with attributes, or costs/metrics, "
                "prefer using markdown tables."
            )
            chat_history.append(SystemMessage(content=system_prompt.strip()))

            # Track active task executors
            active_executors: dict[str, TaskExecutor] = {}

            try:
                while True:
                    raw = await websocket.receive_text()
                    try:
                        msg = json.loads(raw)
                    except json.JSONDecodeError:
                        # Fallback: treat as plain text chat message
                        msg = {"type": "chat_message", "content": raw}

                    msg_type = msg.get("type", "chat_message")

                    if msg_type == "chat_message":
                        content = msg.get("content", "")
                        logger.info("[User Message] %s", content[:200])
                        chat_history.append(HumanMessage(content=content))

                        try:
                            # Phase 1: Ask LLM whether to decompose
                            logger.info("Checking if task decomposition is needed...")
                            task_graph = await TaskDecomposer.maybe_decompose(
                                user_message=content,
                                chat_history=chat_history,
                                category=category,
                                available_tools=available_tools,
                            )

                            if task_graph:
                                logger.info("Task decomposed into %d subtasks (task_id=%s)", len(task_graph.subtasks), task_graph.task_id)
                                for s in task_graph.subtasks:
                                    logger.info("  subtask: %s [%s] deps=%s", s.name, s.executor.value, s.dependencies)

                                # Send graph to frontend
                                await websocket.send_json({
                                    "type": "task_graph_created",
                                    "task_id": task_graph.task_id,
                                    "user_message": content,
                                    "subtasks": [s.model_dump() for s in task_graph.subtasks],
                                })

                                # Create executor and start eligible subtasks
                                executor = TaskExecutor(
                                    task_graph=task_graph,
                                    all_tools=bundle.tools,
                                    llm=bundle.llm,
                                    chat_history=chat_history,
                                    websocket=websocket,
                                )
                                active_executors[task_graph.task_id] = executor
                                await executor.execute_ready_subtasks()
                            else:
                                # Normal chat flow
                                logger.info("No decomposition — running normal chat flow")
                                input_state = {"messages": chat_history}
                                final_state = await bundle.graph.ainvoke(input_state)

                                last_msg = final_state["messages"][-1]
                                response_text = last_msg.content

                                chat_history = final_state["messages"]
                                logger.info("[Chat Response] %s", str(response_text)[:300])

                                await websocket.send_json({
                                    "type": "chat_response",
                                    "content": str(response_text),
                                })
                        except Exception as e:
                            logger.error("Error processing message: %s\n%s", e, traceback.format_exc())
                            chat_history.pop()
                            try:
                                await websocket.send_json({
                                    "type": "error",
                                    "content": str(e),
                                })
                            except:
                                pass

                    elif msg_type == "user_subtask_output":
                        task_id = msg.get("task_id")
                        subtask_id = msg.get("subtask_id")
                        output = msg.get("output", "")

                        executor = active_executors.get(task_id)
                        if executor:
                            await executor.handle_user_output(subtask_id, output)
                            if executor.is_complete():
                                del active_executors[task_id]
                        else:
                            await websocket.send_json({
                                "type": "error",
                                "content": f"No active task found for task_id: {task_id}",
                            })

            except WebSocketDisconnect:
                logger.info("Client disconnected from category %d", category_id)

    except Exception as e:
        logger.error("Error in WebSocket setup: %s\n%s", e, traceback.format_exc())
        try:
            await websocket.send_json({"type": "error", "content": str(e)})
        except:
            pass
