"""
Planner node for multi-step workflow planning.

Breaks down complex tasks into smaller, executable steps.
"""

import json
import logging
from typing import List, Dict, Any, Optional

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from src.agent.state import AgentState
from src.llm.factory import llm_factory
from src.tools import get_tool_registry
from src.tools.base import ToolCategory, ToolError

logger = logging.getLogger("orbit.planner")


class PlanStep:
    """Represents a single step in a plan."""

    def __init__(
        self,
        step_number: int,
        description: str,
        expected_outcome: str,
        tool_name: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None,
    ):
        self.step_number = step_number
        self.description = description
        self.tool_name = tool_name
        self.arguments = arguments or {}
        self.expected_outcome = expected_outcome


class Plan:
    """Represents a complete execution plan."""

    def __init__(
        self,
        steps: List[PlanStep],
        goal: str,
        estimated_steps: Optional[int] = None,
        requires_confirmation: bool = False,
    ):
        self.steps = steps
        self.goal = goal
        self.estimated_steps = estimated_steps
        self.requires_confirmation = requires_confirmation

    def add_step(self, step: PlanStep) -> None:
        self.steps.append(step)
        self.estimated_steps = len(self.steps)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "steps": [step.__dict__ for step in self.steps],
            "estimated_steps": self.estimated_steps,
            "requires_confirmation": self.requires_confirmation,
        }


class PlannerNode:
    """Planner node for LangGraph workflow."""

    def __init__(self, llm_factory=llm_factory):
        self.llm_factory = llm_factory
        self._tool_registry = None

    def _get_registry(self):
        """Get tool registry lazily."""
        if self._tool_registry is None:
            self._tool_registry = get_tool_registry()
        return self._tool_registry

    def _get_llm(self, temperature: float = 0.3):
        return self.llm_factory(temperature=temperature)

    def _validate_tool_name(self, tool_name: Optional[str]) -> Optional[str]:
        """Validate that a tool name exists in the registry."""
        if not tool_name:
            return None

        registry = self._get_registry()
        if registry.tool_exists(tool_name):
            return tool_name

        logger.warning(f"Invalid tool name: {tool_name}")
        return None

    def _get_available_tools_description(self) -> str:
        """Get formatted description of available tools."""
        registry = self._get_registry()
        tool_names = registry.get_tool_names()

        descriptions = []
        for name in tool_names:
            tool = registry.get_tool(name)
            if tool:
                descriptions.append(f"  - {name}: {tool.description}")

        return "\n".join(descriptions)

    async def create_plan(self, state: AgentState, max_steps: int = 5) -> Plan:
        """Create an execution plan from user's request."""
        if not state["messages"]:
            return Plan(steps=[], goal="No user message to plan for")

        last_message = state["messages"][-1]
        if not isinstance(last_message, HumanMessage):
            return Plan(steps=[], goal="Planning only available for user requests")

        user_request = last_message.content
        if isinstance(user_request, list):
            user_request = " ".join(
                str(part.get("text", part)) if isinstance(part, dict) else str(part)
                for part in user_request
            )

        logger.info(f"Creating plan for: {user_request[:100]}...")

        if await self._is_single_step(state, str(user_request)):
            return await self._create_simple_plan(str(user_request), max_steps)

        return await self._create_multi_step_plan(state, str(user_request), max_steps)

    async def _is_single_step(self, state: AgentState, user_request: str) -> bool:
        """Determine if the request is a simple single-step task."""
        simple_patterns = [
            "what is my",
            "list ",
            "show me",
            "how do i",
            "who am i",
            "tell me about",
            "explain ",
        ]

        request_lower = user_request.lower()
        for pattern in simple_patterns:
            if request_lower.startswith(pattern):
                return True

        return False

    async def _create_simple_plan(self, user_request: str, max_steps: int = 3) -> Plan:
        """Create a simple plan (1-2 steps)."""
        llm = self._get_llm(temperature=0.2)
        tools_description = self._get_available_tools_description()
        tool_names = self._get_registry().get_tool_names()

        system_prompt = f"""You are an AI assistant. Create a simple execution plan for the user's request.

User request: "{user_request}"

Available tools:
{tools_description}

IMPORTANT: Only use tool_name values from this exact list: {tool_names}

Output a JSON object with this structure:
{{
  "goal": "Description of what we're trying to accomplish",
  "steps": [
    {{
      "step_number": 1,
      "description": "Clear description of this step",
      "tool_name": "exact_tool_name_from_list_or_null",
      "arguments": {{"arg1": "value1"}} or null,
      "expected_outcome": "What should happen"
    }}
  ],
  "requires_confirmation": false
}}

Guidelines:
- Use tool_name ONLY if a tool from the list is needed
- If no tool is needed, set tool_name to null
- Keep it simple - maximum {max_steps} steps
- Respond with ONLY valid JSON, no other text"""

        try:
            response = await llm.ainvoke([HumanMessage(content=system_prompt)])
            plan_data = self._parse_llm_plan_response(response.content)

            steps = self._create_validated_steps(plan_data)

            return Plan(
                steps=steps,
                goal=plan_data.get("goal", user_request),
                estimated_steps=len(steps),
                requires_confirmation=plan_data.get("requires_confirmation", False),
            )

        except Exception as e:
            logger.error(f"Simple plan creation failed: {e}")
            return self._create_fallback_plan(user_request)

    async def _create_multi_step_plan(
        self, state: AgentState, user_request: str, max_steps: int
    ) -> Plan:
        """Create a multi-step plan for complex tasks."""
        llm = self._get_llm(temperature=0.3)
        tools_description = self._get_available_tools_description()
        tool_names = self._get_registry().get_tool_names()

        system_prompt = f"""You are an AI assistant that creates execution plans.

User request: "{user_request}"

Available tools:
{tools_description}

IMPORTANT: Only use tool_name values from this exact list: {tool_names}

Output a JSON object with this structure:
{{
  "goal": "Description of overall goal",
  "steps": [
    {{
      "step_number": 1,
      "description": "Create the directory 'wow'",
      "tool_name": "create_directory",
      "arguments": {{"path": "wow"}},
      "expected_outcome": "Directory 'wow' is created"
    }},
    {{
      "step_number": 2,
      "description": "Create file ayan.txt inside wow directory",
      "tool_name": "write_file",
      "arguments": {{"path": "wow/ayan.txt", "content": ""}},
      "expected_outcome": "File 'wow/ayan.txt' is created"
    }}
  ],
  "requires_confirmation": false
}}

Guidelines:
1. Break down complex tasks into sequential steps
2. Use tool_name ONLY from the available tools list
3. If no tool is needed for a step, set tool_name to null
4. Maximum {max_steps} steps
5. Each step should build on previous steps
6. Respond with ONLY valid JSON, no other text"""

        try:
            response = await llm.ainvoke([HumanMessage(content=system_prompt)])
            logger.debug(f"LLM response: {response.content[:500]}...")

            plan_data = self._parse_llm_plan_response(response.content)
            steps = self._create_validated_steps(plan_data)

            if not steps:
                logger.warning("No valid steps created, using fallback")
                return self._create_fallback_plan(user_request)

            registry = self._get_registry()
            requires_confirmation = False
            for step in steps:
                if step.tool_name:
                    tool = registry.get_tool(step.tool_name)
                    if tool and tool.requires_confirmation:
                        requires_confirmation = True
                        break

            return Plan(
                steps=steps,
                goal=plan_data.get("goal", user_request),
                estimated_steps=len(steps),
                requires_confirmation=requires_confirmation,
            )

        except Exception as e:
            logger.error(f"Multi-step plan creation failed: {e}")
            return self._create_fallback_plan(user_request)

    def _create_validated_steps(self, plan_data: Dict[str, Any]) -> List[PlanStep]:
        """Create steps with validated tool names."""
        steps = []
        registry = self._get_registry()

        for i, step_data in enumerate(plan_data.get("steps", []), start=1):
            tool_name = step_data.get("tool_name")

            if tool_name:
                validated_tool = self._validate_tool_name(tool_name)
                if not validated_tool:
                    logger.warning(
                        f"Step {i}: Invalid tool '{tool_name}', will try shell_exec"
                    )
                    if registry.tool_exists("shell_exec"):
                        tool_name = "shell_exec"
                        arguments = step_data.get("arguments", {})
                        if isinstance(arguments, dict) and "command" not in arguments:
                            arguments = {"command": step_data.get("description", "")}
                    else:
                        tool_name = None
                else:
                    tool_name = validated_tool

            step = PlanStep(
                step_number=i,
                description=step_data.get("description", f"Step {i}"),
                tool_name=tool_name,
                arguments=step_data.get("arguments"),
                expected_outcome=step_data.get("expected_outcome", "Complete step"),
            )
            steps.append(step)
            logger.info(f"Step {i}: tool={tool_name}, desc={step.description[:50]}...")

        return steps

    def _create_fallback_plan(self, user_request: str) -> Plan:
        """Create a fallback plan using shell_exec."""
        registry = self._get_registry()

        if registry.tool_exists("shell_exec"):
            return Plan(
                steps=[
                    PlanStep(
                        step_number=1,
                        description=f"Execute: {user_request}",
                        tool_name="shell_exec",
                        arguments={"command": user_request},
                        expected_outcome="Execute the user's request",
                    )
                ],
                goal=user_request,
                requires_confirmation=True,
            )

        return Plan(
            steps=[
                PlanStep(
                    step_number=1,
                    description=f"Respond to: {user_request}",
                    tool_name=None,
                    expected_outcome="Provide helpful response",
                )
            ],
            goal=user_request,
            requires_confirmation=False,
        )

    def _parse_llm_plan_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into plan data."""
        response = response.strip()

        json_start = response.find("{")
        json_end = response.rfind("}")

        if json_start != -1 and json_end != -1:
            json_str = response[json_start : json_end + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error: {e}")

        return {"steps": [], "goal": "Parse the request"}
