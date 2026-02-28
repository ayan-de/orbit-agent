import httpx
import logging
from typing import Dict, Any, Optional, List

from src.config import settings
from src.bridge.schemas import BridgeCommandRequest, BridgeCommandResponse

logger = logging.getLogger("orbit.bridge")


class BridgeClient:
    """Client for communicating with NestJS Bridge service."""

    def __init__(
        self,
        base_url: str = settings.BRIDGE_URL,
        api_key: str = settings.BRIDGE_API_KEY,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
        )

    async def close(self):
        """Close the underlying HTTP client."""
        await self.client.aclose()

    async def execute_command(
        self, cmd: str, args: list = None, cwd: str = None, trusted: bool = False
    ) -> BridgeCommandResponse:
        """
        Execute a shell command via the Bridge.

        Args:
            cmd: Command to execute
            args: Command arguments
            cwd: Working directory
            trusted: If True, skip injection character validation (for internal tools)
        """
        if args is None:
            args = []

        payload = BridgeCommandRequest(command=cmd, args=args, cwd=cwd, trusted=trusted)

        try:
            logger.info(f"Executing command via bridge: {cmd} {args}")
            response = await self.client.post(
                "/api/v1/commands/execute", json=payload.model_dump()
            )

            response.raise_for_status()
            data = response.json()

            return BridgeCommandResponse(**data)

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Bridge HTTP Error: {e.response.status_code} - {e.response.text}"
            )
            raise Exception(f"Bridge command failed: {e.response.text}") from e
        except httpx.RequestError as e:
            logger.error(f"Bridge Request Error: {e}")
            raise Exception(f"Failed to connect to Bridge: {e}") from e

    async def list_files(self, path: str = ".") -> BridgeCommandResponse:
        """Helper to list files in a directory."""
        return await self.execute_command("ls", ["-la", path])

    async def read_file(self, path: str) -> BridgeCommandResponse:
        """Helper to read a file."""
        return await self.execute_command("cat", [path])

    async def write_file(
        self,
        path: str,
        content: str,
        mode: str = "write",
        create_dirs: bool = False,
    ) -> BridgeCommandResponse:
        """Helper to write a file."""
        if create_dirs:
            import os

            dir_path = os.path.dirname(path)
            if dir_path:
                await self.create_directory(dir_path, create_parents=True)

        import base64
        
        # We use base64 encoding to bypass the quote escaping hell across
        # the entire network chain (Python -> JSON -> NestJS -> WS -> Desktop App -> Bash)
        b64_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        redirect = ">>" if mode == "append" else ">"
        
        # macOS uses `base64 -D` or `base64 -d`, Linux uses `base64 -d`. 
        # But `base64 --decode` usually works across both.
        # We use single quotes here because Node.js/Desktop gateway likely wraps 
        # the entire argument string in double quotes when reassembling it, and 
        # nested double quotes cause Bash parsing EOF errors.
        shell_cmd = f"echo '{b64_content}' | base64 --decode {redirect} '{path}'"

        return await self.execute_command("sh", ["-c", shell_cmd], trusted=True)

    async def create_directory(
        self, path: str, create_parents: bool = True, mode: str = "0755"
    ) -> BridgeCommandResponse:
        """Helper to create a directory."""
        args = []
        if mode:
            args.extend(["-m", mode])
        if create_parents:
            args.append("-p")
        args.append(path)

        return await self.execute_command("mkdir", args)

    async def delete_path(
        self, path: str, recursive: bool = False, force: bool = False
    ) -> BridgeCommandResponse:
        """Helper to delete a file or directory."""
        args = [path]
        if recursive:
            args.append("-r")
        if force:
            args.append("-f")

        return await self.execute_command("rm", args)

    async def get_file_info(self, path: str) -> BridgeCommandResponse:
        """Helper to get file information."""
        return await self.execute_command("stat", [path])


# Global instance
bridge_client = BridgeClient()
