import logging
import time
from typing import List, Dict, Any, Annotated, Optional, Tuple
from dataclasses import dataclass
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import StructuredTool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator
from typing import TypedDict, Union
from pydantic import create_model, Field

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from mcp import ClientSession

from app.models.category import Category
from app.services.mcp_client import MCPClient
from app.services.llm_factory import LLMFactory

logger = logging.getLogger("app.agent")


@dataclass
class AgentBundle:
    """Container for agent components returned by AgentService."""
    graph: Any  # compiled LangGraph workflow
    tools: List[StructuredTool]
    llm: BaseChatModel  # unbound LLM (without tools)


# Mapping from JSON Schema types to Python types
_JSON_TYPE_MAP = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def _json_schema_to_pydantic(schema: Dict[str, Any], model_name: str = "ToolInput"):
    """Convert a JSON Schema object to a dynamic Pydantic model for args_schema."""
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))

    fields: Dict[str, Any] = {}
    for name, prop in properties.items():
        py_type = _JSON_TYPE_MAP.get(prop.get("type", "string"), str)
        description = prop.get("description", "")

        if name in required:
            fields[name] = (py_type, Field(description=description))
        else:
            fields[name] = (Optional[py_type], Field(default=None, description=description))

    return create_model(model_name, **fields)

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]

class AgentService:
    @staticmethod
    async def get_agent_runnable(category_id: int, db: AsyncSession):
        """
        Build and return a LangGraph executable for the given category context.
        """
        # 1. Fetch Category and Servers
        result = await db.execute(
            select(Category)
            .where(Category.id == category_id)
            .options(selectinload(Category.mcp_servers))
        )
        category = result.scalars().first()
        if not category:
            raise ValueError(f"Category {category_id} not found")

        # 2. Fetch Tools from all servers (in parallel ideally)
        tools = []
        for server in category.mcp_servers:
            try:
                server_tools = await MCPClient.get_tools(server.url, resource_config=server.resource_config)
                for tool_def in server_tools:
                    # Dynamically create a LangChain tool wrapper

                    # Create a closure for the tool execution
                    async def make_tool_func(s_url=server.url, t_name=tool_def["name"], s_config=server.resource_config):
                        async def _exec(**kwargs):
                            try:
                                res = await MCPClient.call_tool(s_url, t_name, kwargs, resource_config=s_config)
                                # simplified result parsing
                                content = [c.text for c in res.content if c.type == 'text']
                                return "\n".join(content) if content else str(res)
                            except Exception as e:
                                error_msg = f"[Tool Error] {t_name} failed: {e}. Make reasonable assumptions based on available context and proceed."
                                logger.warning(error_msg)
                                return error_msg
                        return _exec

                    tool_func = await make_tool_func()

                    input_schema = tool_def.get("inputSchema", {})
                    args_schema = _json_schema_to_pydantic(input_schema, tool_def["name"] + "Input")

                    tool = StructuredTool.from_function(
                        coroutine=tool_func,
                        name=tool_def["name"],
                        description=tool_def.get("description", ""),
                        args_schema=args_schema,
                    )
                    tools.append(tool)
            except Exception as e:
                logger.error("Failed to load tools from %s: %s", server.url, e)

        # 3. Setup LLM using category configuration
        llm = LLMFactory.create_llm(
            provider=category.llm_provider,
            model=category.llm_model,
            provider_type=category.llm_provider_type,
            api_key=category.llm_api_key,
            endpoint=category.llm_endpoint,
            api_version=category.llm_api_version,
            deployment_name=category.llm_deployment_name,
            region=category.llm_region,
            temperature=None,
        )

        if tools:
            llm = llm.bind_tools(tools)

        # 4. Define Graph
        workflow = StateGraph(AgentState)

        def call_model(state: AgentState):
            messages = state["messages"]
            logger.info("[LLM Request] %d messages", len(messages))
            for i, m in enumerate(messages):
                role = m.__class__.__name__
                content_preview = str(m.content)[:300] if m.content else ""
                logger.info("  msg[%d] %s: %s", i, role, content_preview)
            t0 = time.time()
            response = llm.invoke(messages)
            logger.info("[LLM Response] %.2fs | content: %s", time.time() - t0, str(response.content)[:500])
            return {"messages": [response]}

        workflow.add_node("agent", call_model)
        
        if tools:
            tool_node = ToolNode(tools, handle_tool_errors=True)
            workflow.add_node("tools", tool_node)
            workflow.set_entry_point("agent")

            def should_continue(state: AgentState):
                last_message = state["messages"][-1]
                if last_message.tool_calls:
                    return "tools"
                return END

            workflow.add_conditional_edges("agent", should_continue)
            workflow.add_edge("tools", "agent")
        else:
            workflow.set_entry_point("agent")
            workflow.add_edge("agent", END)

        return workflow.compile()

    @staticmethod
    async def get_agent_runnable_with_sessions(
        category: Category,
        mcp_sessions: Dict[int, ClientSession],
    ) -> AgentBundle:
        """
        Build and return a LangGraph executable using pre-opened MCP sessions.
        Sessions are kept alive externally (e.g. by the websocket endpoint).
        Returns an AgentBundle with the compiled graph, tools list, and unbound LLM.
        """
        # 1. Fetch tools from all persistent sessions
        tools = []
        for server_id, session in mcp_sessions.items():
            try:
                result = await session.list_tools()
                server_tools = [tool.model_dump() for tool in result.tools]
                logger.info("Loaded %d tools from MCP session %s", len(server_tools), server_id)
                for tool_def in server_tools:
                    async def make_tool_func(sess=session, t_name=tool_def["name"]):
                        async def _exec(**kwargs):
                            logger.info("[Tool Call] %s | args=%s", t_name, kwargs)
                            t0 = time.time()
                            try:
                                res = await sess.call_tool(t_name, kwargs)
                                content = [c.text for c in res.content if c.type == 'text']
                                output = "\n".join(content) if content else str(res)
                                logger.info("[Tool Result] %s | %.2fs | output=%s", t_name, time.time() - t0, output[:500])
                                return output
                            except Exception as e:
                                error_msg = f"[Tool Error] {t_name} failed: {e}. Make reasonable assumptions based on available context and proceed."
                                logger.warning("[Tool Error] %s | %.2fs | %s", t_name, time.time() - t0, str(e))
                                return error_msg
                        return _exec

                    tool_func = await make_tool_func()

                    input_schema = tool_def.get("inputSchema", {})
                    args_schema = _json_schema_to_pydantic(input_schema, tool_def["name"] + "Input")

                    tool = StructuredTool.from_function(
                        coroutine=tool_func,
                        name=tool_def["name"],
                        description=tool_def.get("description", ""),
                        args_schema=args_schema,
                    )
                    tools.append(tool)
            except Exception as e:
                logger.error("Failed to load tools from session %s: %s", server_id, e)

        # 2. Setup LLM using category configuration
        llm = LLMFactory.create_llm(
            provider=category.llm_provider,
            model=category.llm_model,
            provider_type=category.llm_provider_type,
            api_key=category.llm_api_key,
            endpoint=category.llm_endpoint,
            api_version=category.llm_api_version,
            deployment_name=category.llm_deployment_name,
            region=category.llm_region,
            temperature=None,
        )

        # 3. Build compiled graph
        graph = AgentService.build_graph(llm, tools)

        return AgentBundle(graph=graph, tools=tools, llm=llm)

    @staticmethod
    def build_graph(llm: BaseChatModel, tools: List[StructuredTool]):
        """Build and compile a LangGraph workflow with the given LLM and tools."""
        bound_llm = llm.bind_tools(tools) if tools else llm

        workflow = StateGraph(AgentState)

        def call_model(state: AgentState):
            messages = state["messages"]

            # Log LLM input
            logger.info("=" * 60)
            logger.info("[LLM Request] %d messages", len(messages))
            for i, m in enumerate(messages):
                role = m.__class__.__name__
                content_preview = str(m.content)[:300] if m.content else ""
                logger.info("  msg[%d] %s: %s", i, role, content_preview)
                if hasattr(m, "tool_calls") and m.tool_calls:
                    logger.info("  msg[%d] tool_calls: %s", i, m.tool_calls)

            t0 = time.time()
            response = bound_llm.invoke(messages)
            elapsed = time.time() - t0

            # Log LLM output
            logger.info("[LLM Response] %.2fs", elapsed)
            logger.info("  content: %s", str(response.content)[:500] if response.content else "(empty)")
            if hasattr(response, "tool_calls") and response.tool_calls:
                for tc in response.tool_calls:
                    logger.info("  tool_call: %s(%s)", tc["name"], tc.get("args", {}))
            logger.info("=" * 60)

            return {"messages": [response]}

        workflow.add_node("agent", call_model)

        if tools:
            tool_node = ToolNode(tools, handle_tool_errors=True)
            workflow.add_node("tools", tool_node)
            workflow.set_entry_point("agent")

            def should_continue(state: AgentState):
                last_message = state["messages"][-1]
                if last_message.tool_calls:
                    return "tools"
                return END

            workflow.add_conditional_edges("agent", should_continue)
            workflow.add_edge("tools", "agent")
        else:
            workflow.set_entry_point("agent")
            workflow.add_edge("agent", END)

        return workflow.compile()
