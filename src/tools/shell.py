from typing import Optional, Type, List
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import shlex

from src.bridge.client import bridge_client, BridgeCommandResponse

class ShellToolInput(BaseModel):
    command: str = Field(..., description="The shell command to execute.")
    cwd: Optional[str] = Field(None, description="The directory to execute the command in.")

class ShellTool(BaseTool):
    name: str = "shell_exec"
    description: str = "Executes a shell command on the user's machine via the bridge. Use this for file operations, git commands, running tests, etc."
    args_schema: Type[BaseModel] = ShellToolInput

    def _run(self, command: str, cwd: Optional[str] = None) -> str:
        raise NotImplementedError("Use _arun for async execution")

    async def _arun(self, command: str, cwd: Optional[str] = None) -> str:
        """Executes the shell command asynchronously."""
        try:
            parts = shlex.split(command)
            if not parts:
                return "Error: Empty command"
            
            cmd = parts[0]
            args = parts[1:]
            
            response = await bridge_client.execute_command(cmd, args, cwd)
            
            if response.exit_code != 0:
                result = f"Command failed with exit code {response.exit_code}:\n{response.stderr}"
                if response.stdout:
                     result += f"\nstdout: {response.stdout}"
                return result
            
            return response.stdout
            
        except Exception as e:
            return f"Error executing command: {str(e)}"
