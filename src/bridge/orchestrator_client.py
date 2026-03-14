import httpx
import logging
import uuid
from typing import Dict, Any, Optional, List
import asyncio

from src.config import settings
from src.bridge.schemas import (
    BridgeCommandRequest,
    BridgeCommandResponse,
    ConfirmationRequest,
    ConfirmationResponse,
    ConfirmationType,
)

logger = logging.getLogger("orbit.bridge")


class OrchestratorClient:
    """
    Client for communicating with NestJS Bridge service.

    ARCHITECTURE NOTE:
    The Bridge's CommandsController is the SINGLE AUTHORITY for shell command execution.

    Usage Guidelines:
    - This client calls Bridge's /api/v1/commands/execute endpoint
    - Bridge routes to Desktop TUI via WebSocket for actual shell execution
    - NO component except Desktop TUI should execute shell commands directly

    When to use this client:
    - Multi-step workflows where Agent needs to execute commands during workflow
    - Tool implementations that require shell command execution
    - File system operations that require shell commands

    When NOT to use this client:
    - Simple NLP-to-command translation (use agent response instead)
    - Direct shell access (should only happen in Desktop TUI)
    """

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

    # =========================================================================
    # Human-in-Loop Confirmation Methods
    # =========================================================================

    async def request_confirmation(
        self,
        confirmation_type: ConfirmationType,
        title: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        danger_level: int = 0,
        timeout_seconds: Optional[int] = 60,
    ) -> ConfirmationResponse:
        """
        Request user confirmation via Bridge.

        Sends a confirmation request to the Bridge, which forwards it to
        the user's desktop client. Waits for the response.

        Args:
            confirmation_type: Type of confirmation needed
            title: Short title for the confirmation
            message: Detailed message explaining what needs confirmation
            details: Additional context (command, tool name, etc.)
            danger_level: Risk level (0=safe to 4=critical)
            timeout_seconds: Auto-deny timeout

        Returns:
            ConfirmationResponse with user's decision
        """
        confirmation_id = str(uuid.uuid4())

        request = ConfirmationRequest(
            confirmation_id=confirmation_id,
            confirmation_type=confirmation_type,
            title=title,
            message=message,
            details=details or {},
            danger_level=danger_level,
            timeout_seconds=timeout_seconds,
        )

        try:
            logger.info(f"Requesting confirmation: {confirmation_id} - {title}")

            # Send confirmation request to Bridge
            response = await self.client.post(
                "/api/v1/confirmations/request",
                json=request.model_dump(),
            )
            response.raise_for_status()

            # Poll for response (Bridge will notify when user responds)
            # In production, this would use WebSockets for real-time updates
            max_polls = (timeout_seconds or 60) // 2
            for _ in range(max_polls):
                poll_response = await self.client.get(
                    f"/api/v1/confirmations/{confirmation_id}/response"
                )

                if poll_response.status_code == 200:
                    data = poll_response.json()
                    if data.get("status") == "responded":
                        logger.info(f"Confirmation {confirmation_id}: {'approved' if data.get('approved') else 'denied'}")
                        return ConfirmationResponse(**data)

                # Wait before polling again
                await asyncio.sleep(2)

            # Timeout - auto-deny
            logger.warning(f"Confirmation {confirmation_id} timed out")
            return ConfirmationResponse(
                confirmation_id=confirmation_id,
                approved=False,
                response="Confirmation timed out",
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"Confirmation request failed: {e.response.status_code}")
            # Default to deny on error
            return ConfirmationResponse(
                confirmation_id=confirmation_id,
                approved=False,
                response=f"Error: {e.response.text}",
            )
        except Exception as e:
            logger.error(f"Confirmation request error: {e}")
            return ConfirmationResponse(
                confirmation_id=confirmation_id,
                approved=False,
                response=f"Error: {str(e)}",
            )

    async def send_confirmation_response(
        self,
        confirmation_id: str,
        approved: bool,
        response: Optional[str] = None,
        remember_decision: bool = False,
    ) -> bool:
        """
        Send a confirmation response (used by Bridge to respond).

        This is typically called by the Bridge when user responds via desktop client.

        Args:
            confirmation_id: ID of the confirmation request
            approved: Whether user approved
            response: Optional user message
            remember_decision: Whether to remember this decision

        Returns:
            True if response was recorded successfully
        """
        try:
            response_data = ConfirmationResponse(
                confirmation_id=confirmation_id,
                approved=approved,
                response=response,
                remember_decision=remember_decision,
            )

            resp = await self.client.post(
                f"/api/v1/confirmations/{confirmation_id}/respond",
                json=response_data.model_dump(),
            )
            resp.raise_for_status()
            return True

        except Exception as e:
            logger.error(f"Failed to send confirmation response: {e}")
            return False


# Global instance
orchestrator_client = OrchestratorClient()
