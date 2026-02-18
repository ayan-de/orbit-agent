from fastapi import APIRouter, HTTPException, BackgroundTasks
from langchain_core.messages import HumanMessage
from src.agent import agent_app
from src.api.schemas import AgentRequest, AgentResponse
import traceback

router = APIRouter()

@router.post("/invoke", response_model=AgentResponse)
async def invoke_agent(request: AgentRequest):
    """
    Invoke the Orbit Agent with a user message.
    """
    try:
        # Initialize state
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "intent": "unknown",
            "command": "",
            "plan": [],
            "current_step": 0,
            "tool_results": [],
            "needs_confirmation": False,
            "confirmation_prompt": None,
            "is_complete": False,
            "session_id": request.session_id,
            "user_id": request.user_id,
            "iteration_count": 0
        }
        
        # Invoke the graph
        final_state = await agent_app.ainvoke(initial_state)

        # Extract response
        messages = final_state.get("messages", [])
        last_message = messages[-1].content if messages else ""
        intent = final_state.get("intent", "unknown")
        command = final_state.get("command", "")

        return AgentResponse(
            messages=[str(last_message)],
            intent=intent,
            command=command,
            status="success"
        )
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")
