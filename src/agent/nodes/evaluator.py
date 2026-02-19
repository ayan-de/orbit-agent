"""
Evaluator node for LangGraph workflow.

Evaluates tool execution results and determines if re-planning is needed.
"""

from typing import Dict, Any, List, Optional
from enum import Enum

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from src.agent.state import AgentState
from src.llm.factory import llm_factory


class EvaluationOutcome(str, Enum):
    """Possible outcomes of evaluation."""
    GOAL_ACHIEVED = "goal_achieved"
    CONTINUE_EXECUTION = "continue_execution"
    NEEDS_REPLANNING = "needs_replanning"
    FATAL_ERROR = "fatal_error"
    INCOMPLETE = "incomplete"


class EvaluatorNode:
    """
    Evaluator node for LangGraph workflow.

    Analyzes execution results and determines next action.
    """

    def __init__(self, llm_factory=llm_factory):
        """
        Initialize evaluator node.

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
            LLM instance
        """
        return self.llm_factory(temperature=temperature)

    async def evaluate(
        self,
        state: AgentState,
        execution_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate execution results and determine next action.

        Args:
            state: Current agent state
            execution_results: Results from tool executions

        Returns:
            Evaluation result with outcome and next action
        """
        # Get the original plan and goal
        plan = state.get("plan", {})
        goal = plan.get("goal", "Unknown goal")
        steps = plan.get("steps", [])
        current_step = state.get("current_step", 0)

        # Check if all steps completed
        total_steps = len(steps)
        all_steps_completed = current_step >= total_steps

        # Check for errors in execution results
        has_errors = any(
            result.get("status") == "failed"
            for result in execution_results
        )

        # Get the most recent execution result
        latest_result = execution_results[-1] if execution_results else None

        # Evaluate based on different scenarios
        if has_errors:
            return await self._evaluate_error(state, execution_results, latest_result)
        elif all_steps_completed:
            return await self._evaluate_completion(state, execution_results, goal)
        else:
            return await self._evaluate_progress(state, execution_results, current_step)

    async def _evaluate_error(
        self,
        state: AgentState,
        execution_results: List[Dict[str, Any]],
        latest_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate when an error occurred.

        Args:
            state: Current agent state
            execution_results: Results from tool executions
            latest_result: Most recent execution result

        Returns:
            Evaluation result
        """
        error_message = latest_result.get("error", "Unknown error") if latest_result else "Unknown error"

        # Analyze if the error is recoverable
        llm = self._get_llm(temperature=0.2)

        analysis_prompt = f"""You are an error analyzer. Determine if this error is recoverable or fatal.

Error message: {error_message}

Tool executed: {latest_result.get('tool_name', 'Unknown') if latest_result else 'Unknown'}

Step description: {latest_result.get('description', 'Unknown') if latest_result else 'Unknown'}

Output format (JSON only):
{{
  "is_recoverable": true/false,
  "suggested_fix": "Brief description of how to fix",
  "needs_replanning": true/false,
  "reasoning": "Brief explanation"
}}

Consider an error fatal if:
- The tool doesn't exist
- Permissions are fundamentally wrong
- The operation is fundamentally impossible

Consider an error recoverable if:
- It's a temporary issue (network, file locked)
- A different approach might work
- Arguments need adjustment"""

        try:
            response = await llm.ainvoke([HumanMessage(content=analysis_prompt)])
            import json
            analysis = self._parse_json_response(response.content)

            if analysis.get("is_recoverable"):
                return {
                    "outcome": EvaluationOutcome.NEEDS_REPLANNING,
                    "next_action": "replan",
                    "reasoning": analysis.get("reasoning", "Error occurred, replanning needed"),
                    "suggested_fix": analysis.get("suggested_fix"),
                    "error_message": error_message
                }
            else:
                return {
                    "outcome": EvaluationOutcome.FATAL_ERROR,
                    "next_action": "abort",
                    "reasoning": analysis.get("reasoning", "Fatal error encountered"),
                    "error_message": error_message
                }
        except Exception as e:
            # Fallback: treat as recoverable
            return {
                "outcome": EvaluationOutcome.NEEDS_REPLANNING,
                "next_action": "replan",
                "reasoning": f"Error occurred, unable to analyze: {str(e)}",
                "error_message": error_message
            }

    async def _evaluate_completion(
        self,
        state: AgentState,
        execution_results: List[Dict[str, Any]],
        goal: str
    ) -> Dict[str, Any]:
        """
        Evaluate when all steps completed.

        Args:
            state: Current agent state
            execution_results: Results from tool executions
            goal: Original goal

        Returns:
            Evaluation result
        """
        # Use LLM to determine if goal was achieved
        llm = self._get_llm(temperature=0.2)

        results_summary = "\n".join([
            f"Step {r.get('step_number')}: {r.get('description')} - {r.get('status')}\n"
            f"Output: {r.get('output', 'No output')}\n"
            f"Error: {r.get('error', 'None')}"
            for r in execution_results
        ])

        completion_prompt = f"""You are a goal evaluator. Determine if the original goal was achieved.

Original goal: {goal}

Execution results:
{results_summary}

Output format (JSON only):
{{
  "goal_achieved": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation",
  "gaps": ["Any gaps or missing results", ...]
}}

Consider goal achieved if:
- All steps completed successfully
- The outputs align with the goal
- No critical errors occurred

Consider goal not achieved if:
- Critical errors occurred
- Outputs don't match the goal
- Important steps failed"""

        try:
            response = await llm.ainvoke([HumanMessage(content=completion_prompt)])
            import json
            analysis = self._parse_json_response(response.content)

            if analysis.get("goal_achieved", False):
                return {
                    "outcome": EvaluationOutcome.GOAL_ACHIEVED,
                    "next_action": "respond",
                    "reasoning": analysis.get("reasoning", "Goal achieved"),
                    "confidence": analysis.get("confidence", 1.0)
                }
            else:
                return {
                    "outcome": EvaluationOutcome.INCOMPLETE,
                    "next_action": "replan",
                    "reasoning": analysis.get("reasoning", "Goal not fully achieved"),
                    "gaps": analysis.get("gaps", [])
                }
        except Exception as e:
            # Fallback: assume complete if no errors
            has_errors = any(r.get("status") == "failed" for r in execution_results)
            if not has_errors:
                return {
                    "outcome": EvaluationOutcome.GOAL_ACHIEVED,
                    "next_action": "respond",
                    "reasoning": "All steps completed without errors",
                    "confidence": 0.8
                }
            else:
                return {
                    "outcome": EvaluationOutcome.INCOMPLETE,
                    "next_action": "replan",
                    "reasoning": f"Unable to evaluate completion, but errors present",
                    "gaps": ["Analysis failed"]
                }

    async def _evaluate_progress(
        self,
        state: AgentState,
        execution_results: List[Dict[str, Any]],
        current_step: int
    ) -> Dict[str, Any]:
        """
        Evaluate progress in the middle of execution.

        Args:
            state: Current agent state
            execution_results: Results from tool executions
            current_step: Current step number

        Returns:
            Evaluation result
        """
        # Get the latest result
        latest_result = execution_results[-1] if execution_results else None

        if not latest_result:
            return {
                "outcome": EvaluationOutcome.CONTINUE_EXECUTION,
                "next_action": "continue",
                "reasoning": "No execution results, continuing"
            }

        status = latest_result.get("status")

        if status == "completed":
            # Step completed successfully, continue to next
            return {
                "outcome": EvaluationOutcome.CONTINUE_EXECUTION,
                "next_action": "continue",
                "reasoning": f"Step {current_step} completed successfully",
                "current_step": current_step + 1
            }
        elif status == "skipped":
            # Step was skipped, check if we should continue
            return await self._evaluate_skipped_step(state, latest_result, current_step)
        else:
            # Unknown status, but not an error (handled elsewhere)
            return {
                "outcome": EvaluationOutcome.CONTINUE_EXECUTION,
                "next_action": "continue",
                "reasoning": f"Step {current_step} status: {status}, continuing",
                "current_step": current_step + 1
            }

    async def _evaluate_skipped_step(
        self,
        state: AgentState,
        skipped_result: Dict[str, Any],
        current_step: int
    ) -> Dict[str, Any]:
        """
        Evaluate when a step was skipped.

        Args:
            state: Current agent state
            skipped_result: The skipped step result
            current_step: Current step number

        Returns:
            Evaluation result
        """
        error_message = skipped_result.get("error", "Step skipped")

        # Check if the skip is recoverable
        if "confirmation" in error_message.lower():
            # Needs user confirmation - should have been handled before
            return {
                "outcome": EvaluationOutcome.NEEDS_REPLANNING,
                "next_action": "replan",
                "reasoning": "Step requires user confirmation, should have been handled earlier",
                "current_step": current_step
            }
        elif "permission" in error_message.lower():
            # Permission issue - needs replanning with different approach
            return {
                "outcome": EvaluationOutcome.NEEDS_REPLANNING,
                "next_action": "replan",
                "reasoning": "Permission denied, need alternative approach",
                "current_step": current_step
            }
        else:
            # Continue to next step
            return {
                "outcome": EvaluationOutcome.CONTINUE_EXECUTION,
                "next_action": "continue",
                "reasoning": f"Step {current_step} skipped but continuing",
                "current_step": current_step + 1
            }

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response as JSON.

        Args:
            response: LLM response string

        Returns:
            Parsed JSON dictionary
        """
        import json

        # Try to extract JSON from response
        response = response.strip()
        json_start = response.find('{')
        json_end = response.rfind('}')

        if json_start != -1 and json_end != -1:
            json_str = response[json_start:json_end+1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # Fallback: try markdown code blocks
        lines = response.split('\n')
        in_code_block = False
        json_lines = []

        for line in lines:
            if '```json' in line or '```' in line:
                in_code_block = True
                continue
            elif in_code_block and '```' in line:
                in_code_block = False

            line = line.strip()
            if line and not line.startswith('-') and not line.startswith('*'):
                try:
                    parsed = json.loads(line)
                    if isinstance(parsed, dict):
                        json_lines.append(parsed)
                except json.JSONDecodeError:
                    pass

        # Return first valid JSON object found
        for item in json_lines:
            if isinstance(item, dict):
                return item

        # Return empty dict as fallback
        return {}

    async def should_continue_execution(
        self,
        evaluation_result: Dict[str, Any]
    ) -> bool:
        """
        Determine if execution should continue.

        Args:
            evaluation_result: Result from evaluate() method

        Returns:
            True if should continue, False otherwise
        """
        outcome = evaluation_result.get("outcome")

        return outcome in [
            EvaluationOutcome.CONTINUE_EXECUTION,
            EvaluationOutcome.INCOMPLETE
        ]

    async def should_replan(
        self,
        evaluation_result: Dict[str, Any]
    ) -> bool:
        """
        Determine if re-planning is needed.

        Args:
            evaluation_result: Result from evaluate() method

        Returns:
            True if re-planning needed, False otherwise
        """
        outcome = evaluation_result.get("outcome")
        next_action = evaluation_result.get("next_action")

        return (
            outcome == EvaluationOutcome.NEEDS_REPLANNING or
            next_action == "replan"
        )

    async def should_respond(
        self,
        evaluation_result: Dict[str, Any]
    ) -> bool:
        """
        Determine if should respond to user.

        Args:
            evaluation_result: Result from evaluate() method

        Returns:
            True if should respond, False otherwise
        """
        outcome = evaluation_result.get("outcome")
        next_action = evaluation_result.get("next_action")

        return (
            outcome == EvaluationOutcome.GOAL_ACHIEVED or
            outcome == EvaluationOutcome.FATAL_ERROR or
            next_action in ["respond", "abort"]
        )

    async def format_evaluation_for_user(
        self,
        evaluation_result: Dict[str, Any]
    ) -> str:
        """
        Format evaluation result for user consumption.

        Args:
            evaluation_result: Result from evaluate() method

        Returns:
            Formatted string
        """
        outcome = evaluation_result.get("outcome")
        reasoning = evaluation_result.get("reasoning", "")

        if outcome == EvaluationOutcome.GOAL_ACHIEVED:
            return f"✓ Goal achieved: {reasoning}"
        elif outcome == EvaluationOutcome.FATAL_ERROR:
            error_msg = evaluation_result.get("error_message", "Unknown error")
            return f"✗ Fatal error: {error_msg}\nReasoning: {reasoning}"
        elif outcome == EvaluationOutcome.NEEDS_REPLANNING:
            fix = evaluation_result.get("suggested_fix", "")
            return f"⚠️ Re-planning needed: {reasoning}\nSuggested fix: {fix}" if fix else f"⚠️ Re-planning needed: {reasoning}"
        elif outcome == EvaluationOutcome.CONTINUE_EXECUTION:
            return f"→ Continuing: {reasoning}"
        elif outcome == EvaluationOutcome.INCOMPLETE:
            gaps = evaluation_result.get("gaps", [])
            gaps_str = "\n- " + "\n- ".join(gaps) if gaps else ""
            return f"⚠️ Incomplete: {reasoning}{gaps_str}"
        else:
            return f"Evaluation: {reasoning}"
