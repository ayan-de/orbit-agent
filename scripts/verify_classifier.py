import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from langchain_core.messages import HumanMessage
from src.agent.nodes.classifier import classify_intent
from src.agent.state import AgentState

async def run_test(input_text: str, expected_intent: str):
    print(f"\nTesting Input: '{input_text}'")
    
    # Mock state
    state: AgentState = {
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
        result = await classify_intent(state)
        actual_intent = result["intent"]
        
        if actual_intent == expected_intent:
            print(f"✅ PASS: Classified as '{actual_intent}'")
        else:
            print(f"❌ FAIL: Expected '{expected_intent}', got '{actual_intent}'")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

async def main():
    print("--- Testing Classifier Node ---")
    
    test_cases = [
        ("pwd", "command"),
        ("list files", "command"),
        ("create a folder named src", "command"),
        ("hello, who are you?", "question"),
        ("explain how async python works", "question"),
        ("clone the repo and run tests", "workflow"),
    ]
    
    for text, expected in test_cases:
        await run_test(text, expected)

if __name__ == "__main__":
    asyncio.run(main())
