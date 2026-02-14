from typing import List, Dict, Any, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator
from typing import TypedDict, Union

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.services.mcp_client import MCPClient
from app.services.llm_factory import LLMFactory

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
                server_tools = await MCPClient.get_tools(server.url)
                for tool_def in server_tools:
                    # Dynamically create a LangChain tool wrapper
                    
                    # Create a closure for the tool execution
                    async def make_tool_func(s_url=server.url, t_name=tool_def["name"]):
                        async def _exec(**kwargs):
                             res = await MCPClient.call_tool(s_url, t_name, kwargs)
                             # simplified result parsing
                             content = [c.text for c in res.content if c.type == 'text']
                             return "\n".join(content) if content else str(res)
                        return _exec

                    tool_func = await make_tool_func()
                    
                    tool = StructuredTool.from_function(
                        coroutine=tool_func,
                        name=tool_def["name"],
                        description=tool_def.get("description", ""),
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
