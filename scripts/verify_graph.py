import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from langchain_core.messages import HumanMessage
from src.agent import agent_app

async def run_test(input_text: str):
    print(f"\nTesting Input: '{input_text}'")
    
    # Initial state
    initial_state = {
        "messages": [HumanMessage(content=input_text)],
        "intent": "unknown",
        "plan": [],
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
        # invoke is sync (but supports async runnables underneath in LangGraph?), 
        # but since nodes are async, it's safer to use ainvoke.
        final_state = await agent_app.ainvoke(initial_state)
        
        intent = final_state.get("intent")
        messages = final_state.get("messages")
        response = messages[-1].content
        
        print(f"✅ Intent Classified: {intent}")
        print(f"✅ Response: {response}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ ERROR: {e}")

async def main():
    print("--- Testing Agent Graph (Classify -> Respond) ---")
    
    test_cases = [
        "What is Docker?",
        "list files in this directory",
        "Explain Python decorators",
    ]
    
    for text in test_cases:
        await run_test(text)

if __name__ == "__main__":
    asyncio.run(main())
