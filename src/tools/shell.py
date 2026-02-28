from typing import Optional
import shlex

from pydantic import BaseModel, Field

from src.tools.base import OrbitTool, ToolCategory, ToolInput, ToolError
from src.bridge.orchestrator_client import orchestrator_client, BridgeCommandResponse


class ShellToolInput(ToolInput):
    """Input schema for shell tool."""

    command: str = Field(..., description="The shell command to execute.")
    cwd: Optional[str] = Field(
        None, description="The directory to execute the command in."
    )


class ShellTool(OrbitTool):
    """
    Shell command execution tool.

    Executes shell commands via the NestJS Bridge's SINGLE AUTHORITY endpoint.

    ARCHITECTURE NOTE:
    - This tool calls Bridge's /api/v1/commands/execute (the single authority)
    - Bridge routes to Desktop TUI via WebSocket for actual shell execution
    - NO component except Desktop TUI executes shell commands directly

    Use Cases:
    - Multi-step workflows requiring shell execution during workflow
    - File operations, git commands, running tests, etc.
    - Any tool implementation that needs shell command execution

    Usage Pattern:
    1. Agent includes this tool in workflow execution
    2. Agent calls tool with command
    3. Tool calls Bridge's single authority endpoint
    4. Bridge routes to Desktop TUI
    5. Desktop executes and returns result
    6. Tool returns result to Agent

    Requires confirmation before execution due to high danger level.
    """

    name: str = "shell_exec"
    description: str = "Executes a shell command via the Bridge's single authority endpoint. Use for file operations, git commands, running tests, etc. The Bridge routes commands to the connected Desktop TUI for actual execution."
    category: ToolCategory = ToolCategory.SYSTEM
    danger_level: int = 5  # Shell commands can be dangerous (out of 10)
    requires_confirmation: bool = True  # Always require confirmation
    args_schema: type = ShellToolInput

    async def _arun(self, command: str, cwd: Optional[str] = None) -> str:
        """
        Execute shell command asynchronously.

        Args:
            command: Shell command to execute
            cwd: Working directory (optional)

        Returns:
            Command output or error message
        """
        try:
            # Parse command to separate command from arguments
            parts = shlex.split(command)
            if not parts:
                return "Error: Empty command"

            cmd = parts[0]
            args = parts[1:]

            # Execute via Bridge
            response = await orchestrator_client.execute_command(cmd, args, cwd)

            if response.exit_code != 0:
                error_msg = f"Command failed with exit code {response.exit_code}"
                if response.stderr:
                    error_msg += f": {response.stderr}"
                raise Exception(error_msg)

            return response.stdout

        except Exception as e:
            raise Exception(f"Error executing command: {str(e)}")
