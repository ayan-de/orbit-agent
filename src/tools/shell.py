from typing import Optional
import shlex

from pydantic import BaseModel, Field

from src.tools.base import OrbitTool, ToolCategory, ToolInput, ToolError
from src.bridge.client import bridge_client, BridgeCommandResponse


class ShellToolInput(ToolInput):
    """Input schema for shell tool."""
    command: str = Field(..., description="The shell command to execute.")
    cwd: Optional[str] = Field(None, description="The directory to execute the command in.")


class ShellTool(OrbitTool):
    """
    Shell command execution tool.

    Executes shell commands on the user's machine via the NestJS Bridge.
    Useful for file operations, git commands, running tests, etc.

    Requires confirmation before execution due to high danger level.
    """

    name: str = "shell_exec"
    description: str = "Executes a shell command on the user's machine via the bridge. Use this for file operations, git commands, running tests, etc."
    category: ToolCategory = ToolCategory.SYSTEM
    danger_level: int = 5  # Shell commands can be dangerous (out of 10)
    requires_confirmation: bool = True  # Always require confirmation
    args_schema: type[ShellToolInput] = ShellToolInput

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
            response = await bridge_client.execute_command(cmd, args, cwd)

            if response.exit_code != 0:
                error_msg = f"Command failed with exit code {response.exit_code}"
                if response.stderr:
                    error_msg += f": {response.stderr}"
                raise Exception(error_msg)

            return response.stdout

        except Exception as e:
            raise Exception(f"Error executing command: {str(e)}")
