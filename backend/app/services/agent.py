from typing import List, Dict, Any, Annotated, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
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
                             res = await MCPClient.call_tool(s_url, t_name, kwargs, resource_config=s_config)
                             # simplified result parsing
                             content = [c.text for c in res.content if c.type == 'text']
                             return "\n".join(content) if content else str(res)
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
                print(f"Failed to load tools from {server.url}: {e}")

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
            response = llm.invoke(messages)
            return {"messages": [response]}

        workflow.add_node("agent", call_model)
        
        if tools:
            tool_node = ToolNode(tools)
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
    ):
        """
        Build and return a LangGraph executable using pre-opened MCP sessions.
        Sessions are kept alive externally (e.g. by the websocket endpoint).
        """
        # 1. Fetch tools from all persistent sessions
        tools = []
        for server_id, session in mcp_sessions.items():
            try:
                result = await session.list_tools()
                server_tools = [tool.model_dump() for tool in result.tools]
                for tool_def in server_tools:
                    async def make_tool_func(sess=session, t_name=tool_def["name"]):
                        async def _exec(**kwargs):
                            res = await sess.call_tool(t_name, kwargs)
                            content = [c.text for c in res.content if c.type == 'text']
                            return "\n".join(content) if content else str(res)
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
                print(f"Failed to load tools from session {server_id}: {e}")

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

        if tools:
            llm = llm.bind_tools(tools)

        # 3. Define Graph
        workflow = StateGraph(AgentState)

        def call_model(state: AgentState):
            messages = state["messages"]
            response = llm.invoke(messages)
            return {"messages": [response]}

        workflow.add_node("agent", call_model)

        if tools:
            tool_node = ToolNode(tools)
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
