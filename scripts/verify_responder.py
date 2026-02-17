import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.agent.nodes.responder import respond
from src.agent.state import AgentState

async def run_test(intent: str, user_input: str, tool_results: list):
    print(f"\nTesting Intent: '{intent}'")
    print(f"User Input: '{user_input}'")
    print(f"Tool Results: {tool_results}")
    
    # Mock state
    state: AgentState = {
        "messages": [HumanMessage(content=user_input)],
        "intent": intent,
        "plan": [],
        "current_step": 0,
        "tool_results": tool_results,
        "needs_confirmation": False,
        "confirmation_prompt": None,
        "is_complete": False,
        "session_id": "test-session",
        "user_id": "test-user",
        "iteration_count": 0
    }
    
    try:
        result = await respond(state)
        response = result["messages"][0]
        
        print(f"✅ Response: {response.content}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")

async def main():
    print("--- Testing Responder Node ---")
    
    test_cases = [
        ("question", "What is React?", []),
        ("command", "list files in current directory", 
         [{"tool": "shell_exec", "command": "ls -la", "output": "file1.py\nfile2.js\nfile3.txt\n", "status": "success"}]),
        ("command", "read config.json", 
         [{"tool": "shell_exec", "command": "cat config.json", "output": "cat: config.json: No such file or directory", "status": "error"}]),
    ]
    
    for intent, input_text, results in test_cases:
        await run_test(intent, input_text, results)

if __name__ == "__main__":
    asyncio.run(main())
