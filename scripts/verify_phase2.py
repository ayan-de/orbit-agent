import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from langchain_core.messages import HumanMessage
from src.agent.graph import get_compiled_graph

async def run_test(input_text: str):
    print(f"\nTesting Input: '{input_text}'")
    
    # Initialize compiled graph with no checkpointer for this simple test
    app = await get_compiled_graph(with_checkpointer=False)
    
    # Initial state
    initial_state = {
        "messages": [HumanMessage(content=input_text)],
        "intent": "workflow",  # Pre-classify for testing workflow branch directly
        "plan": {},
        "current_step": 0,
        "tool_results": [],
        "needs_confirmation": False,
        "confirmation_prompt": None,
        "is_complete": False,
        "session_id": "test-session",
        "user_id": "test-user",
        "iteration_count": 0
    }
    
    try:
        final_state = await app.ainvoke(initial_state)
        
        intent = final_state.get("intent")
        messages = final_state.get("messages")
        response = messages[-1].content if messages else None
        
        print(f"✅ Intent Classified: {intent}")
        print(f"✅ Response from Agent: {response}")
        print(f"Execution results: {final_state.get('execution_results')}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ ERROR: {e}")

async def main():
    print("--- Testing Agent Multi-Step Execution (Phase 2) ---")
    await run_test("create a folder called wow and create a file called ayan.txt inside it")

if __name__ == "__main__":
    asyncio.run(main())
