import asyncio
import sys
import os

sys.path.append(os.getcwd())

from langchain_core.messages import HumanMessage
from src.agent.state import AgentState
from src.agent.nodes.planner import PlannerNode

async def test():
    state = {
        "messages": [HumanMessage(content="Create a new folder called wow and inside it create a file called ayan.txt")],
        "intent": "workflow",
        "plan": {},
        "current_step": 0,
        "tool_results": [],
        "needs_confirmation": False,
        "confirmation_prompt": None,
        "is_complete": False,
        "session_id": "test",
        "user_id": "test",
        "iteration_count": 0
    }
    
    planner = PlannerNode()
    plan = await planner.create_plan(state)
    print("----- PARSED PLAN -----")
    import json
    print(json.dumps(plan.to_dict(), indent=2))

if __name__ == "__main__":
    asyncio.run(test())
