from fastapi import APIRouter, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from langchain_core.messages import HumanMessage, AIMessage
from src.agent import agent_app
from src.api.schemas import AgentRequest, AgentResponse
from src.memory import get_conversation_memory
from typing import Dict, Any, Optional
import traceback
import json
import asyncio

router = APIRouter()

"""
WebSocket Streaming API
====================

/ws/api/v1/agent/stream
-----------------------
Real-time streaming of agent execution.

Client sends:
{
    "session_id": "string",
    "user_id": "string",
    "message": "string"
}

Server sends events:
- "start": Execution started
- "intent": Intent classification result
- "plan": Generated execution plan
- "step": Current execution step
- "tool_result": Result from tool execution
- "evaluation": Evaluation outcome
- "chunk": Streaming message content
- "complete": Execution finished
- "error": Error occurred

/ws/api/v1/agent/stream/checkpoint
----------------------------------------
Streaming with pause/resume support.

Client sends:
{
    "session_id": "string",
    "user_id": "string",
    "message": "string",
    "checkpoint_id": "string"  // Optional, for resume
}

Server sends:
- "start": Execution started (with checkpoint info)
- "state_update": Full state update
- "complete": Execution finished
- "error": Error occurred
"""

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
            "plan": {},
            "current_step": 0,
            "tool_results": [],
            "needs_confirmation": False,
            "confirmation_prompt": None,
            "is_complete": False,
            "evaluation_outcome": None,
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


@router.websocket("/stream")
async def stream_agent(websocket: WebSocket):
    """
    WebSocket endpoint for streaming agent responses.

    Real-time streaming of agent execution, tool calls, and responses.
    """
    await websocket.accept()

    try:
        # Receive initial message
        data = await websocket.receive_json()
        session_id = data.get("session_id", "default")
        user_id = data.get("user_id", "user")
        message = data.get("message", "")

        if not message:
            await websocket.send_json({
                "type": "error",
                "error": "No message provided"
            })
            await websocket.close()
            return

        # Initialize state
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "intent": "unknown",
            "command": "",
            "plan": {},
            "current_step": 0,
            "tool_results": [],
            "needs_confirmation": False,
            "confirmation_prompt": None,
            "is_complete": False,
            "evaluation_outcome": None,
            "session_id": session_id,
            "user_id": user_id,
            "iteration_count": 0
        }

        # Send start message
        await websocket.send_json({
            "type": "start",
            "session_id": session_id,
            "timestamp": _get_timestamp()
        })

        # Track previous state to detect changes
        previous_intent = None
        previous_plan = None
        previous_step = 0
        previous_evaluation = None

        # Stream execution with updates
        async for event in agent_app.astream(initial_state):
            # Check for intent changes
            current_intent = event.get("intent")
            if current_intent != previous_intent:
                await websocket.send_json({
                    "type": "intent",
                    "intent": current_intent,
                    "timestamp": _get_timestamp()
                })
                previous_intent = current_intent

            # Check for plan creation
            current_plan = event.get("plan", {})
            if current_plan and current_plan != previous_plan:
                await websocket.send_json({
                    "type": "plan",
                    "plan": current_plan,
                    "timestamp": _get_timestamp()
                })
                previous_plan = current_plan

            # Check for step execution
            current_step = event.get("current_step", 0)
            if current_step != previous_step:
                await websocket.send_json({
                    "type": "step",
                    "step": current_step,
                    "total_steps": len(current_plan.get("steps", [])),
                    "timestamp": _get_timestamp()
                })
                previous_step = current_step

            # Check for tool results
            tool_results = event.get("tool_results", [])
            if tool_results:
                latest_result = tool_results[-1] if tool_results else None
                if latest_result:
                    await websocket.send_json({
                        "type": "tool_result",
                        "result": latest_result,
                        "timestamp": _get_timestamp()
                    })

            # Check for evaluation
            current_evaluation = event.get("evaluation_outcome")
            if current_evaluation and current_evaluation != previous_evaluation:
                await websocket.send_json({
                    "type": "evaluation",
                    "outcome": current_evaluation,
                    "reasoning": event.get("evaluation_reasoning"),
                    "timestamp": _get_timestamp()
                })
                previous_evaluation = current_evaluation

            # Check for new messages (assistant responses)
            messages = event.get("messages", [])
            if messages:
                last_message = messages[-1]
                if isinstance(last_message, AIMessage):
                    # Stream the message content
                    content = last_message.content
                    if content:
                        # Send in chunks for streaming effect
                        await _stream_message(websocket, content)

        # Save conversation to memory
        try:
            memory = await get_conversation_memory()
            await memory.add_message(
                session_id=session_id,
                role="user",
                content=message
            )

            # Get final assistant message
            final_messages = await memory.get_conversation_history(session_id=session_id)
            assistant_messages = [m for m in final_messages if m.role.value == "assistant"]
            if assistant_messages:
                await memory.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=assistant_messages[-1].content
                )
        except Exception as e:
            # Don't fail the stream if memory save fails
            print(f"Failed to save to memory: {e}")

        # Send completion message
        await websocket.send_json({
            "type": "complete",
            "session_id": session_id,
            "timestamp": _get_timestamp()
        })

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: session_id={session_id}")
    except Exception as e:
        traceback.print_exc()
        await websocket.send_json({
            "type": "error",
            "error": str(e),
            "timestamp": _get_timestamp()
        })
    finally:
        try:
            await websocket.close()
        except:
            pass


@router.websocket("/stream/checkpoint")
async def stream_agent_with_checkpoint(websocket: WebSocket):
    """
    WebSocket endpoint with checkpoint support for pause/resume.

    Allows streaming and resuming from previous checkpoints.
    """
    await websocket.accept()

    try:
        # Receive initial message
        data = await websocket.receive_json()
        session_id = data.get("session_id", "default")
        user_id = data.get("user_id", "user")
        message = data.get("message", "")
        checkpoint_id = data.get("checkpoint_id")  # Optional resume from checkpoint

        if not message:
            await websocket.send_json({
                "type": "error",
                "error": "No message provided"
            })
            await websocket.close()
            return

        # Initialize state
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "intent": "unknown",
            "command": "",
            "plan": {},
            "current_step": 0,
            "tool_results": [],
            "needs_confirmation": False,
            "confirmation_prompt": None,
            "is_complete": False,
            "evaluation_outcome": None,
            "session_id": session_id,
            "user_id": user_id,
            "iteration_count": 0
        }

        # Config for checkpointer
        config = {
            "configurable": {
                "thread_id": session_id,
            }
        }

        if checkpoint_id:
            config["configurable"]["checkpoint_id"] = checkpoint_id

        # Send start message
        await websocket.send_json({
            "type": "start",
            "session_id": session_id,
            "checkpoint_id": checkpoint_id,
            "timestamp": _get_timestamp()
        })

        # Stream execution with checkpoint support
        async for event in agent_app.astream(initial_state, config=config):
            # Stream state updates
            await websocket.send_json({
                "type": "state_update",
                "state": event,
                "timestamp": _get_timestamp()
            })

            # Check for completion
            if event.get("is_complete"):
                break

        # Send completion message
        await websocket.send_json({
            "type": "complete",
            "session_id": session_id,
            "timestamp": _get_timestamp()
        })

    except WebSocketDisconnect:
        print(f"WebSocket disconnected (checkpoint): session_id={session_id}")
    except Exception as e:
        traceback.print_exc()
        await websocket.send_json({
            "type": "error",
            "error": str(e),
            "timestamp": _get_timestamp()
        })
    finally:
        try:
            await websocket.close()
        except:
            pass


async def _stream_message(websocket: WebSocket, content: str, chunk_size: int = 50):
    """
    Stream message content in chunks.

    Args:
        websocket: WebSocket connection
        content: Message content to stream
        chunk_size: Size of each chunk
    """
    for i in range(0, len(content), chunk_size):
        chunk = content[i:i + chunk_size]
        await websocket.send_json({
            "type": "chunk",
            "content": chunk,
            "timestamp": _get_timestamp()
        })
        # Small delay for streaming effect
        await asyncio.sleep(0.01)


def _get_timestamp() -> str:
    """Get current ISO timestamp."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
