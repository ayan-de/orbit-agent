"""
New _create_simple_plan function with memory_context parameter.
This replaces the existing function in planner.py.
"""

async def _create_simple_plan(
    self,
    state,
    user_request: str,
    max_steps: int = 3,
    memory_context: str = ""
) -> Plan:
    """Create a simple plan (1-2 steps)."""
    llm = self._get_llm(temperature=0.2)
    tools_description = self._get_available_tools_description()
    tool_names = self._get_registry().get_tool_names()
    system_prompt = f"""You are an AI assistant. Create a simple execution plan for the user's request.

Memory Context:
{memory_context}

Available tools:
{tools_description}
   IMPORTANT: Only use tool_name values from this exact list: {tool_names}
