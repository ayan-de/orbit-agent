from typing import Dict, Any
from langchain_core.messages import AIMessage

from src.agent.state import AgentState
from src.llm.factory import llm_factory
from src.agent.prompts.responder import responder_prompt

async def respond(state: AgentState) -> Dict[str, Any]:
    """
    Generates the final response to the user based on the conversation history and tool results.
    """
    messages = state["messages"]
    intent = state.get("intent", "unknown")
    
    # Tool results might be in state["tool_results"] if they were executed as part of a plan
    # Or they might be appended as ToolMessages in state["messages"].
    # For now, let's assume we pass the explicit "tool_results" list for context summary.
    tool_results = state.get("tool_results", [])
    
    # Initialize LLM
    llm = llm_factory(temperature=0.7)
    
    # Create the chain
    chain = responder_prompt | llm
    
    # Execute the chain
    # We pass 'messages' directly. The prompt template handles the placeholder.
    # We also pass the variables for the system prompt.
    response = await chain.ainvoke({
        "messages": messages,
        "intent": intent,
        "tool_results": str(tool_results)
    })
    
    # Normalize response content if it is a list (Gemini sometimes returns parts)
    if isinstance(response.content, list):
        text_parts = [part["text"] for part in response.content if "text" in part]
        response.content = "\n".join(text_parts)
    
    # Return the new message to be appended to state
    # Also mark the workflow as complete
    return {
        "messages": [response],
        "is_complete": True
    }
