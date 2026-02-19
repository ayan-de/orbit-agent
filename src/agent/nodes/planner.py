"""
Planner node for multi-step workflow planning.

Breaks down complex tasks into smaller, executable steps.
"""

from typing import List, Dict, Any, Optional
from enum import Enum

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from src.agent.state import AgentState
from src.llm.factory import llm_factory
from src.tools import get_tool_registry
from src.tools.base import ToolCategory, ToolError


class PlanStep:
    """Represents a single step in a plan."""

    def __init__(
        self,
        step_number: int,
        description: str,
        tool_name: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None,
        expected_outcome: str
    ):
        """
        Initialize a plan step.

        Args:
            step_number: Step number in the plan
            description: What this step does
            tool_name: Name of tool to use (if any)
            arguments: Tool arguments (if tool is used)
            expected_outcome: Expected result
        """
        self.step_number = step_number
        self.description = description
        self.tool_name = tool_name
        self.arguments = arguments or {}
        self.expected_outcome = expected_outcome


class Plan:
    """
    Represents a complete execution plan.

    Contains multiple steps and overall metadata.
    """

    def __init__(
        self,
        steps: List[PlanStep],
        goal: str,
        estimated_steps: Optional[int] = None,
        requires_confirmation: bool = False
    ):
        """
        Initialize a plan.

        Args:
            steps: List of steps in the plan
            goal: Overall goal of the plan
            estimated_steps: Estimated number of steps (optional)
            requires_confirmation: Whether the plan needs user approval
        """
        self.steps = steps
        self.goal = goal
        self.estimated_steps = estimated_steps
        self.requires_confirmation = requires_confirmation

    def add_step(self, step: PlanStep) -> None:
        """
        Add a step to the plan.

        Args:
            step: PlanStep to add
        """
        self.steps.append(step)
        self.estimated_steps = len(self.steps)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert plan to dictionary.

        Returns:
            Dictionary representation of the plan
        """
        return {
            "goal": self.goal,
            "steps": [step.__dict__ for step in self.steps],
            "estimated_steps": self.estimated_steps,
            "requires_confirmation": self.requires_confirmation,
        }


class PlannerNode:
    """
    Planner node for LangGraph workflow.

    Breaks down complex user requests into executable steps.
    """

    def __init__(self, llm_factory=llm_factory):
        """
        Initialize planner node.

        Args:
            llm_factory: Factory function for creating LLM instances
        """
        self.llm_factory = llm_factory

    def _get_llm(self, temperature: float = 0.3):
        """
        Get LLM instance with specified temperature.

        Args:
            temperature: Temperature for creativity vs consistency

        Returns:
            ChatOpenAI instance
        """
        return self.llm_factory(temperature=temperature)

    async def create_plan(
        self,
        state: AgentState,
        max_steps: int = 5
    ) -> Plan:
        """
        Create an execution plan from user's request.

        Args:
            state: Current agent state containing messages
            max_steps: Maximum number of steps in the plan

        Returns:
            Plan object with steps to execute
        """
        # Get last user message
        if not state["messages"]:
            return Plan(
                steps=[],
                goal="No user message to plan for"
            )

        last_message = state["messages"][-1]
        if last_message["role"] != "user":
            # Only plan for user requests
            return Plan(
                steps=[],
                goal="Planning only available for user requests"
            )

        user_request = last_message["content"]

        # Check if this is a simple single-step task
        if await self._is_single_step(state, user_request):
            return await self._create_simple_plan(user_request)

        # Otherwise, create multi-step plan
        return await self._create_multi_step_plan(state, user_request, max_steps)

    async def _is_single_step(self, state: AgentState, user_request: str) -> bool:
        """
        Determine if the request is a simple single-step task.

        Args:
            state: Agent state
            user_request: User's request

        Returns:
            True if single-step, False otherwise
        """
        # Check if request matches a simple pattern
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

    async def _create_simple_plan(self, user_request: str) -> Plan:
        """
        Create a simple one-step plan.

        Args:
            user_request: User's request

        Returns:
            Plan with one step
        """
        llm = self._get_llm(temperature=0.2)

        # Use available tools to see if any tool is needed
        registry = get_tool_registry()
        available_tools = registry.format_tools_for_llm()

        system_prompt = f"""You are an AI assistant. Your task is to create a simple execution plan for the user's request.

User request: "{user_request}"

Analyze the request and create a concise, actionable plan with at most {max_steps} steps.

Available tools:
{available_tools}

Guidelines:
- Break down complex tasks into multiple clear steps
- Each step should be specific and executable
- Only use tools that are explicitly requested or clearly needed
- Focus on the user's goal, don't over-plan

Output format:
A single step with:
- step_number (1)
- description: Clear, actionable description
- tool_name: Name of tool to use (if applicable, otherwise null)
- arguments: Tool arguments as JSON object (if tool is used, otherwise null)
- expected_outcome: Expected result

Respond with ONLY a valid JSON object. No other text."""

        response = await llm.ainvoke([HumanMessage(content=system_prompt)])

        try:
            # Parse LLM response as JSON
            plan_data = self._parse_llm_plan_response(response.content)

            # Create Plan object
            steps = []
            for i, step_data in enumerate(plan_data.get("steps", []), start=1):
                step = PlanStep(
                    step_number=i,
                    description=step_data["description"],
                    tool_name=step_data.get("tool_name"),
                    arguments=step_data.get("arguments"),
                    expected_outcome=step_data.get("expected_outcome")
                )
                steps.append(step)

            return Plan(
                steps=steps,
                goal=plan_data.get("goal", user_request),
                estimated_steps=plan_data.get("steps_count", len(steps)),
                requires_confirmation=plan_data.get("requires_confirmation", False)
            )

        except Exception as e:
            # Fallback: single step with error handling
            return Plan(
                steps=[
                    PlanStep(
                        step_number=1,
                        description=f"Process: {user_request}",
                        tool_name=None,
                        expected_outcome="Understand and respond to user"
                    )
                ],
                goal=user_request
            )

    async def _create_multi_step_plan(
        self,
        state: AgentState,
        user_request: str,
        max_steps: int
    ) -> Plan:
        """
        Create a multi-step plan for complex tasks.

        Args:
            state: Agent state
            user_request: User's request
            max_steps: Maximum number of steps

        Returns:
            Plan with multiple steps
        """
        llm = self._get_llm(temperature=0.5)

        # Get conversation context
        context_messages = self._format_messages_for_llm(state["messages"][-10:])  # Last 10 messages

        # Get available tools
        registry = get_tool_registry()
        available_tools = registry.format_tools_for_llm()

        system_prompt = f"""You are an AI assistant that creates execution plans.

Your task is to break down the user's request into clear, executable steps.

User request: "{user_request}"

Recent conversation context (last 10 messages):
{self._format_messages_for_llm(state["messages"][-10:])}

Available tools:
{available_tools}

Guidelines:
1. Analyze what the user wants to accomplish
2. Break it down into {max_steps} clear, sequential steps
3. Each step should be:
   - Specific and actionable
   - Build on previous steps
   - Use available tools when helpful
4. Only create steps that are necessary for the goal
5. If a step needs user confirmation, mark requires_confirmation=true
6. Complex operations should be broken down further

For each step provide:
- step_number (1, 2, 3, ...)
- description: Clear, actionable description
- tool_name: Exact tool name to use (if a tool is needed, otherwise null)
- arguments: JSON object with parameters for the tool (if tool is used, otherwise null)
- expected_outcome: What should be the result of this step

Respond with ONLY a valid JSON object. No other text."""

        messages = [HumanMessage(content=system_prompt)] + context_messages
        response = await llm.ainvoke(messages)

        try:
            # Parse LLM response as JSON
            plan_data = self._parse_llm_plan_response(response.content)

            # Create Plan object
            steps = []
            for i, step_data in enumerate(plan_data.get("steps", []), start=1):
                step = PlanStep(
                    step_number=i,
                    description=step_data["description"],
                    tool_name=step_data.get("tool_name"),
                    arguments=step_data.get("arguments"),
                    expected_outcome=step_data.get("expected_outcome")
                )
                steps.append(step)

            # Check if any step requires confirmation
            requires_confirmation = any(
                step.get("tool_name") and not registry.get_tool(step["tool_name"]).is_safe_for_user(1)
                for step in steps if step.tool_name
            )

            return Plan(
                steps=steps,
                goal=plan_data.get("goal", user_request),
                estimated_steps=plan_data.get("steps_count", len(steps)),
                requires_confirmation=requires_confirmation
            )

        except Exception as e:
            # Fallback plan: analyze request directly
            return Plan(
                steps=[
                    PlanStep(
                        step_number=1,
                        description=f"Analyze and respond to: {user_request}",
                        tool_name=None,
                        expected_outcome="Understand and provide information"
                    )
                ],
                goal=user_request,
                requires_confirmation=False
            )

    def _format_messages_for_llm(self, messages: List[Dict[str, Any]]) -> List[HumanMessage]:
        """
        Format messages for LLM context.

        Args:
            messages: List of message dictionaries

        Returns:
            List of HumanMessage instances
        """
        formatted = []
        for msg in messages:
            if msg["role"] == "user":
                formatted.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                formatted.append(AIMessage(content=msg["content"]))

        return formatted

    def _parse_llm_plan_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into plan data.

        Args:
            response: LLM response string

        Returns:
            Dictionary with plan data
        """
        # Try to extract JSON from response
        # Handle cases where JSON might be embedded in text
        response = response.strip()

        # Try to find JSON structure
        json_start = response.find('{')
        json_end = response.rfind('}')

        if json_start != -1 and json_end != -1:
            json_str = response[json_start:json_end+1]
            try:
                import json
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # Fallback: try to extract from markdown code blocks
        # This is a simplified parser - could be more sophisticated
        lines = response.split('\n')
        in_code_block = False
        json_lines = []

        for line in lines:
            if '```json' in line or '```' in line:
                in_code_block = True
                continue
            elif in_code_block and '```' in line:
                in_code_block = False

            # Try to parse as JSON line by line
            line = line.strip()
            if line.startswith('-') or line.startswith('*') or line == '```':
                continue
            try:
                import json
                parsed = json.loads(line)
                if isinstance(parsed, dict):
                    json_lines.append(parsed)
            except json.JSONDecodeError:
                pass

        # Combine all JSON objects
        steps = []
        goal = None
        requires_confirmation = False

        for item in json_lines:
            if isinstance(item, dict):
                if "steps" in item:
                    steps.extend(item["steps"])
                    if "goal" in item:
                        goal = item["goal"]
                    if "requires_confirmation" in item:
                        requires_confirmation = item["requires_confirmation"]

        # If no structured response found, create simple plan from text
        if not steps:
            # Try to create steps from numbered lists
            for item in json_lines:
                if isinstance(item, list):
                    steps_data = {
                        "steps": [
                            {
                                "step_number": i+1,
                                "description": step if isinstance(step, str) else str(step),
                                "tool_name": None,
                                "arguments": None,
                                "expected_outcome": "Complete step"
                            }
                            for i, step in enumerate(item, start=1)
                        ]
                    }
                    if not steps:
                        steps_data = {"steps": steps_data["steps"]}
                    break
                elif isinstance(item, str) and item:
                    # Create single step from string
                    steps_data = {
                        "steps": [
                            {
                                "step_number": 1,
                                "description": item,
                                "tool_name": None,
                                "arguments": None,
                                "expected_outcome": "Process request"
                            }
                        ]
                    }
                    break
                else:
                    break

            return {
                "steps": steps,
                "goal": goal or "Process the request",
                "requires_confirmation": requires_confirmation
            }

        return {
            "steps": steps,
            "goal": goal or "Process the request",
            "requires_confirmation": requires_confirmation
        }
