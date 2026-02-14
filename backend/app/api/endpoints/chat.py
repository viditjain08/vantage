from typing import Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api import deps
from app.services.agent import AgentService
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
        print(f"WebSocket accepted for category {category_id}")
        # Build agent for this category (load tools etc)
        # In production this should be cached/optimized
        print(f"Building agent for category {category_id}...")
        agent = await AgentService.get_agent_runnable(category_id, db)
        print(f"Agent built successfully for category {category_id}")
        
        # Initial system prompt injection could happen here if we tracked session state
        # For now, we instantiate agent per connection (or per message?). 
        # Actually LangGraph state is persistent if we use Checkpointer. 
        # For Phase 1, we keep state in memory for the WS session.
        
        chat_history = []
        
        # Fetch category prompt
        from app.models.category import Category
        result = await db.execute(select(Category).where(Category.id == category_id))
        category = result.scalars().first()
        if category:
             chat_history.append(SystemMessage(content=category.system_prompt))
        
        while True:
            data = await websocket.receive_text()

            # Add user message
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
